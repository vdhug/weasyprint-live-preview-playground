#!/usr/bin/env python3
"""
WeasyPrint Sandbox - Web Server
Provides a browser-based interface for live PDF preview
"""
import os
import time
import json
import base64
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, send_file, jsonify, Response, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader, Template
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = 'weasyprint-sandbox-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
WATCH_DIR = Path(__file__).parent
PLAYGROUND_DIR = WATCH_DIR / "playground_files"
HTML_FILE = PLAYGROUND_DIR / "index.html"
CSS_FILE = PLAYGROUND_DIR / "styles.css"
PARAMS_FILE = PLAYGROUND_DIR / "params.json"
OUTPUT_PDF = WATCH_DIR / "output.pdf"

# Global state
last_error = None
last_generated = 0


def load_params():
    """Load parameters from params.json"""
    if PARAMS_FILE.exists():
        try:
            with open(PARAMS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load params.json: {e}")
            return {}
    return {}


def render_template_with_params(html_content, params, template_name='index.html'):
    """Render HTML template with Jinja2 parameters
    
    Supports both simple string templates and advanced features like
    template inheritance (extends) and includes.
    """
    # Add common variables that are always available
    context = {
        'now': datetime.now(),
        **params
    }
    
    # Try to use FileSystemLoader for template inheritance support
    try:
        env = Environment(loader=FileSystemLoader(str(PLAYGROUND_DIR)))
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        # Fallback to simple string template if file-based loading fails
        print(f"Warning: Template loading issue, using fallback: {e}")
        template = Template(html_content)
        return template.render(**context)


class PDFGenerator(FileSystemEventHandler):
    """Watches files and generates PDFs"""
    
    def __init__(self):
        self.debounce_seconds = 0.5
        self.last_gen_time = 0
    
    def generate_pdf(self, notify=True):
        """Generate PDF from HTML file"""
        global last_error, last_generated
        
        now = time.time()
        if now - self.last_gen_time < self.debounce_seconds:
            return
        
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Generating PDF...", end=" ")
            
            # Load parameters
            params = load_params()
            
            # Read HTML template (for fallback)
            with open(HTML_FILE, 'r') as f:
                html_content = f.read()
            
            # Render with FileSystemLoader to support extends/includes
            rendered_html = render_template_with_params(html_content, params, 'index.html')
            
            # Generate PDF from rendered HTML
            html = HTML(string=rendered_html, base_url=str(PLAYGROUND_DIR))
            html.write_pdf(str(OUTPUT_PDF))
            
            self.last_gen_time = now
            last_generated = now
            last_error = None
            
            file_size = OUTPUT_PDF.stat().st_size / 1024
            print(f"✓ Done! ({file_size:.1f} KB)")
            
            # Notify clients via WebSocket
            if notify:
                socketio.emit('pdf_updated', {
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'size': f"{file_size:.1f} KB"
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
            print(f"Change detected: {Path(event.src_path).name}")
            self.generate_pdf(notify=True)


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
    """List all files in playground directory"""
    files = []
    try:
        for file_path in PLAYGROUND_DIR.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                rel_path = file_path.relative_to(PLAYGROUND_DIR)
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
    """Read a file from playground directory"""
    try:
        file_path = PLAYGROUND_DIR / filename
        
        # Security: ensure path is within playground directory
        if not file_path.resolve().is_relative_to(PLAYGROUND_DIR.resolve()):
            return jsonify({'error': 'Invalid file path'}), 403
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        content = file_path.read_text(encoding='utf-8')
        return jsonify({
            'content': content,
            'filename': filename,
            'path': str(file_path.relative_to(PLAYGROUND_DIR))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<path:filename>', methods=['PUT'])
def write_file(filename):
    """Write a file to playground directory"""
    try:
        file_path = PLAYGROUND_DIR / filename
        
        # Security: ensure path is within playground directory
        if not file_path.resolve().is_relative_to(PLAYGROUND_DIR.resolve()):
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
    """Delete a file from playground directory"""
    try:
        file_path = PLAYGROUND_DIR / filename
        
        # Security: ensure path is within playground directory
        if not file_path.resolve().is_relative_to(PLAYGROUND_DIR.resolve()):
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
        if HTML_FILE.exists():
            # Load parameters
            params = load_params()
            
            # Read HTML template (for fallback)
            with open(HTML_FILE, 'r') as f:
                html_content = f.read()
            
            # Render with FileSystemLoader to support extends/includes
            rendered_html = render_template_with_params(html_content, params, 'index.html')
            
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
    """Serve the generated PDF"""
    if OUTPUT_PDF.exists():
        return send_file(OUTPUT_PDF, mimetype='application/pdf')
    return "PDF not generated yet", 404


@app.route('/styles.css')
def serve_css():
    """Serve the main CSS file"""
    if CSS_FILE.exists():
        return send_file(CSS_FILE, mimetype='text/css')
    return "", 404


@app.route('/<path:filename>')
def serve_playground_files(filename):
    """Serve CSS and other static files from playground directory"""
    # Only serve CSS files for security
    if filename.endswith('.css'):
        file_path = PLAYGROUND_DIR / filename
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
    """Force regenerate PDF"""
    pdf_generator.generate_pdf(notify=True)
    return jsonify({'status': 'success'})


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
    observer.schedule(pdf_generator, str(PLAYGROUND_DIR), recursive=False)
    observer.start()
    print("📁 File watcher started (polling mode for Docker compatibility)")
    print(f"   Watching: {PLAYGROUND_DIR}")
    return observer


if __name__ == '__main__':
    print("=" * 60)
    print("WeasyPrint Live Preview Server")
    print("=" * 60)
    print(f"Playground: {PLAYGROUND_DIR}")
    print(f"  - HTML: {HTML_FILE.name}")
    print(f"  - CSS: {CSS_FILE.name}")
    print(f"  - Params: {PARAMS_FILE.name}")
    print(f"Output: {OUTPUT_PDF.name}")
    print("=" * 60)
    
    # Generate initial PDF
    pdf_generator.generate_pdf(notify=False)
    
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
