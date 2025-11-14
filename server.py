#!/usr/bin/env python3
"""
WeasyPrint Sandbox - Web Server
Provides a browser-based interface for live PDF preview
"""
import os
import time
import json
import base64
import uuid
import shutil
import threading
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, render_template, send_file, jsonify, Response, request, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader, Template
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'weasyprint-sandbox-secret')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
WATCH_DIR = Path(__file__).parent
WORKSPACES_DIR = WATCH_DIR / "workspaces"
TEMPLATE_DIR = WATCH_DIR / "playground_files"  # Template files for new workspaces
OUTPUT_PDF = WATCH_DIR / "output.pdf"

# Create workspaces directory
WORKSPACES_DIR.mkdir(exist_ok=True)

# Session metadata storage (for tracking last access time and cleanup)
SESSION_METADATA = {}

# Global state
last_error = None
last_generated = 0


# ============================================================================
# Workspace Management
# ============================================================================

def get_or_create_user_session():
    """Get or create a user session with workspace"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session.permanent = True
        session['created_at'] = datetime.now().isoformat()
        print(f"📝 New session created: {session['user_id']}")
    
    # Update last access time
    SESSION_METADATA[session['user_id']] = {
        'last_access': datetime.now(),
        'created_at': datetime.fromisoformat(session.get('created_at', datetime.now().isoformat()))
    }
    
    return session['user_id']


def get_user_workspace():
    """Get the workspace directory for the current user"""
    user_id = get_or_create_user_session()
    workspace = WORKSPACES_DIR / user_id
    
    # Create workspace if it doesn't exist
    if not workspace.exists():
        print(f"🆕 Creating new workspace for user: {user_id}")
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Copy template files to new workspace
        if TEMPLATE_DIR.exists():
            for item in TEMPLATE_DIR.iterdir():
                if item.is_file():
                    shutil.copy2(item, workspace / item.name)
                elif item.is_dir():
                    shutil.copytree(item, workspace / item.name, dirs_exist_ok=True)
            print(f"✅ Workspace initialized with template files")
    
    return workspace


def cleanup_expired_workspaces():
    """Clean up workspaces that haven't been accessed for over 1 hour"""
    now = datetime.now()
    expired_sessions = []
    
    for user_id, metadata in list(SESSION_METADATA.items()):
        age = now - metadata['last_access']
        if age > timedelta(hours=1):
            expired_sessions.append((user_id, age))
    
    for user_id, age in expired_sessions:
        workspace = WORKSPACES_DIR / user_id
        if workspace.exists():
            try:
                shutil.rmtree(workspace)
                print(f"🗑️  Deleted expired workspace: {user_id[:8]}... (age: {int(age.total_seconds()/60)}min)")
            except Exception as e:
                print(f"⚠️  Failed to delete workspace {user_id[:8]}...: {e}")
        
        # Remove from metadata
        SESSION_METADATA.pop(user_id, None)
    
    if expired_sessions:
        print(f"✨ Cleaned up {len(expired_sessions)} expired workspace(s)")


def get_workspace_info():
    """Get information about the current user's workspace"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    metadata = SESSION_METADATA.get(user_id)
    if not metadata:
        return None
    
    age = datetime.now() - metadata['last_access']
    expires_in = timedelta(hours=1) - age
    
    return {
        'user_id': user_id,
        'created_at': metadata['created_at'].isoformat(),
        'last_access': metadata['last_access'].isoformat(),
        'expires_in_seconds': int(expires_in.total_seconds()),
        'expires_in_minutes': int(expires_in.total_seconds() / 60)
    }


# Start background cleanup thread
def background_cleanup():
    """Background thread to periodically clean up expired workspaces"""
    while True:
        time.sleep(300)  # Run every 5 minutes
        try:
            cleanup_expired_workspaces()
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")

cleanup_thread = threading.Thread(target=background_cleanup, daemon=True)
cleanup_thread.start()
print("🧹 Background cleanup thread started")


# ============================================================================
# Helper Functions
# ============================================================================

def load_params(workspace=None):
    """Load parameters from params.json"""
    if workspace is None:
        workspace = get_user_workspace()
    
    params_file = workspace / "params.json"
    if params_file.exists():
        try:
            with open(params_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load params.json: {e}")
            return {}
    return {}


def render_template_with_params(html_content, params, template_name='index.html', workspace=None):
    """Render HTML template with Jinja2 parameters
    
    Supports both simple string templates and advanced features like
    template inheritance (extends) and includes.
    """
    if workspace is None:
        workspace = get_user_workspace()
    
    # Add common variables that are always available
    context = {
        'now': datetime.now(),
        **params
    }
    
    # Try to use FileSystemLoader for template inheritance support
    try:
        env = Environment(loader=FileSystemLoader(str(workspace)))
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        # Fallback to simple string template if file-based loading fails
        print(f"Warning: Template loading issue, using fallback: {e}")
        template = Template(html_content)
        return template.render(**context)


class PDFGenerator(FileSystemEventHandler):
    """Watches files and generates PDFs for user workspaces"""
    
    def __init__(self):
        self.debounce_seconds = 0.5
        self.last_gen_times = {}  # Track per-workspace
    
    def generate_pdf_for_workspace(self, workspace_path, notify=True):
        """Generate PDF for a specific workspace"""
        global last_error, last_generated
        
        workspace = Path(workspace_path)
        user_id = workspace.name
        
        now = time.time()
        if now - self.last_gen_times.get(user_id, 0) < self.debounce_seconds:
            return
        
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Generating PDF for {user_id[:8]}...", end=" ")
            
            html_file = workspace / "index.html"
            if not html_file.exists():
                print("✗ index.html not found")
                return
            
            # Load parameters
            params = load_params(workspace)
            
            # Read HTML template
            with open(html_file, 'r') as f:
                html_content = f.read()
            
            # Render with FileSystemLoader to support extends/includes
            rendered_html = render_template_with_params(html_content, params, 'index.html', workspace)
            
            # Generate PDF from rendered HTML
            pdf_output = workspace / "output.pdf"
            html = HTML(string=rendered_html, base_url=str(workspace))
            html.write_pdf(str(pdf_output))
            
            self.last_gen_times[user_id] = now
            last_generated = now
            last_error = None
            
            file_size = pdf_output.stat().st_size / 1024
            print(f"✓ Done! ({file_size:.1f} KB)")
            
            # Notify clients via WebSocket (broadcast to all - they'll filter by session)
            if notify:
                socketio.emit('pdf_updated', {
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'size': f"{file_size:.1f} KB",
                    'user_id': user_id
                })
            
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            last_error = {
                'message': error_msg,
                'traceback': error_trace,
                'timestamp': datetime.now().isoformat()
            }
            print(f"✗ Error: {error_msg}")
            
            # Notify clients of error
            if notify:
                socketio.emit('pdf_error', last_error)
    
    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return
        
        if event.src_path.endswith(('.html', '.css', '.json')):
            file_path = Path(event.src_path)
            print(f"Change detected: {file_path.name}")
            
            # Find the workspace directory (parent of the changed file)
            workspace = file_path.parent
            while workspace.parent != WORKSPACES_DIR and workspace != WORKSPACES_DIR:
                workspace = workspace.parent
            
            if workspace.parent == WORKSPACES_DIR:
                self.generate_pdf_for_workspace(workspace, notify=True)


# Initialize PDF generator
pdf_generator = PDFGenerator()


@app.route('/')
def index():
    """Serve the main interface"""
    return render_template('viewer.html')


@app.route('/editor')
def editor():
    """Serve the code editor interface"""
    return render_template('editor.html')


@app.route('/api/files', methods=['GET'])
def list_files():
    """List all files in user's workspace"""
    files = []
    try:
        workspace = get_user_workspace()
        for file_path in workspace.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                rel_path = file_path.relative_to(workspace)
                files.append({
                    'path': str(rel_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size
                })
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<path:filename>', methods=['GET'])
def read_file(filename):
    """Read a file from user's workspace"""
    try:
        workspace = get_user_workspace()
        file_path = workspace / filename
        
        # Security: ensure path is within user's workspace
        if not file_path.resolve().is_relative_to(workspace.resolve()):
            return jsonify({'error': 'Invalid file path'}), 403
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        content = file_path.read_text(encoding='utf-8')
        return jsonify({
            'content': content,
            'filename': filename,
            'path': str(file_path.relative_to(workspace))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<path:filename>', methods=['PUT'])
def write_file(filename):
    """Write a file to user's workspace"""
    try:
        workspace = get_user_workspace()
        file_path = workspace / filename
        
        # Security: ensure path is within user's workspace
        if not file_path.resolve().is_relative_to(workspace.resolve()):
            return jsonify({'error': 'Invalid file path'}), 403
        
        data = request.get_json()
        content = data.get('content', '')
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        file_path.write_text(content, encoding='utf-8')
        
        return jsonify({
            'status': 'success',
            'message': f'File {filename} saved successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<path:filename>', methods=['DELETE'])
def delete_file_api(filename):
    """Delete a file from user's workspace"""
    try:
        workspace = get_user_workspace()
        file_path = workspace / filename
        
        # Security: ensure path is within user's workspace
        if not file_path.resolve().is_relative_to(workspace.resolve()):
            return jsonify({'error': 'Invalid file path'}), 403
        
        # Don't allow deleting required files
        if filename in ['index.html', 'params.json']:
            return jsonify({'error': 'Cannot delete required files'}), 403
        
        if file_path.exists():
            file_path.unlink()
            return jsonify({'status': 'success', 'message': f'File {filename} deleted'})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/preview')
def preview():
    """Serve the rendered HTML content for preview"""
    try:
        workspace = get_user_workspace()
        html_file = workspace / "index.html"
        
        if html_file.exists():
            # Load parameters
            params = load_params(workspace)
            
            # Read HTML template (for fallback)
            with open(html_file, 'r') as f:
                html_content = f.read()
            
            # Render with FileSystemLoader to support extends/includes
            rendered_html = render_template_with_params(html_content, params, 'index.html', workspace)
            
            # Return the rendered HTML
            return Response(rendered_html, mimetype='text/html')
        return "No HTML file found", 404
    except Exception as e:
        import traceback as tb
        error_trace = tb.format_exc()
        error_html = f"""
        <html>
        <head><title>Preview Error</title></head>
        <body style="font-family: monospace; padding: 20px; background: #fee;">
            <h2 style="color: #c00;">Template Error</h2>
            <pre style="background: #fff; padding: 15px; border-left: 4px solid #c00;">{str(e)}\n\n{error_trace}</pre>
        </body>
        </html>
        """
        return Response(error_html, mimetype='text/html', status=500)


@app.route('/pdf')
def serve_pdf():
    """Serve the generated PDF for user's workspace"""
    try:
        workspace = get_user_workspace()
        pdf_file = workspace / "output.pdf"
        
        # Generate PDF if it doesn't exist yet
        if not pdf_file.exists():
            pdf_generator.generate_pdf_for_workspace(workspace, notify=False)
        
        if pdf_file.exists():
            return send_file(pdf_file, mimetype='application/pdf')
        return "PDF not generated yet", 404
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/styles.css')
def serve_css():
    """Serve the main CSS file from user's workspace"""
    try:
        workspace = get_user_workspace()
        css_file = workspace / "styles.css"
        if css_file.exists():
            return send_file(css_file, mimetype='text/css')
        return "", 404
    except Exception as e:
        return "", 404


@app.route('/<path:filename>')
def serve_playground_files(filename):
    """Serve CSS and other static files from user's workspace"""
    # Only serve CSS files for security
    if filename.endswith('.css'):
        workspace = get_user_workspace()
        file_path = workspace / filename
        if file_path.exists() and file_path.is_file():
            return send_file(file_path, mimetype='text/css')
    return "", 404


@app.route('/status')
def status():
    """Get current status"""
    return jsonify({
        'pdf_exists': OUTPUT_PDF.exists(),
        'last_error': last_error,
        'last_generated': last_generated
    })


@app.route('/regenerate', methods=['POST'])
def regenerate():
    """Force regenerate PDF for user's workspace"""
    try:
        workspace = get_user_workspace()
        pdf_generator.generate_pdf_for_workspace(workspace, notify=True)
        
        pdf_file = workspace / "output.pdf"
        if pdf_file.exists():
            pdf_size = pdf_file.stat().st_size / 1024  # KB
            return jsonify({'status': 'success', 'size': pdf_size})
        else:
            return jsonify({'error': 'PDF generation failed'}), 500
    except Exception as e:
        import traceback as tb
        error_trace = tb.format_exc()
        print(f"PDF generation error: {error_trace}")
        return jsonify({'error': str(e), 'trace': error_trace}), 500


@app.route('/api/workspace/info', methods=['GET'])
def workspace_info():
    """Get information about the current user's workspace"""
    try:
        info = get_workspace_info()
        if info:
            return jsonify(info)
        return jsonify({'error': 'No active session'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/workspace/cleanup', methods=['POST'])
def manual_cleanup():
    """Manually trigger workspace cleanup (admin endpoint)"""
    try:
        cleanup_expired_workspaces()
        active_count = len(SESSION_METADATA)
        return jsonify({
            'status': 'success',
            'active_workspaces': active_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print(f"Client connected: {datetime.now().strftime('%H:%M:%S')}")
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print(f"Client disconnected: {datetime.now().strftime('%H:%M:%S')}")


def start_file_watcher():
    """Start watching files for changes"""
    # Use polling observer for better Docker compatibility on macOS
    from watchdog.observers.polling import PollingObserver
    observer = PollingObserver()
    
    # Watch the workspaces directory (will catch all user workspace changes)
    observer.schedule(pdf_generator, str(WORKSPACES_DIR), recursive=True)
    observer.start()
    print("📁 File watcher started (polling mode for Docker compatibility)")
    print(f"   Watching all user workspaces: {WORKSPACES_DIR}")
    return observer


if __name__ == '__main__':
    print("=" * 60)
    print("WeasyPrint Live Preview Server")
    print("=" * 60)
    print(f"Template directory: {TEMPLATE_DIR}")
    print(f"Workspaces directory: {WORKSPACES_DIR}")
    print(f"  - HTML: index.html")
    print(f"  - CSS: styles.css")
    print(f"  - Params: params.json")
    print(f"Output: User-specific PDFs in workspaces")
    print("=" * 60)
    
    # Don't generate initial PDF - it requires a session context
    
    # Start file watcher
    observer = start_file_watcher()
    
    print("\n🌐 Starting web server...")
    print("   Open: http://localhost:5000")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        # Run Flask with SocketIO
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n\nStopping server...")
        observer.stop()
    
    observer.join()
    print("Goodbye!")
