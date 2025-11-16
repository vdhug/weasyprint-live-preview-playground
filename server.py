#!/usr/bin/env python3
"""
WeasyPrint Sandbox - Web Server (Refactored)
Provides a browser-based interface for live PDF preview using modular services
"""
import time
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, send_file, jsonify, Response, request, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import traceback

# Import configuration and services
from app.config import get_config
from app.utils.logger import get_logger
from app.services import (
    WorkspaceService,
    TemplateService,
    PDFService,
    WatcherService
)

# Initialize
config = get_config()
logger = get_logger(__name__)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = config.PERMANENT_SESSION_LIFETIME
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize services
workspace_service = WorkspaceService(
    workspaces_dir=config.WORKSPACES_DIR,
    template_dir=config.TEMPLATE_DIR,
    session_lifetime_hours=config.WORKSPACE_EXPIRY_HOURS,
    cleanup_interval_seconds=config.CLEANUP_INTERVAL_MINUTES * 60
)

template_service = TemplateService(auto_inject_datetime=True)
pdf_service = PDFService()

# Global state for error tracking
last_error = None
last_generated = 0

logger.info(f"WeasyPrint Sandbox Server v{config.VERSION} initialized")


# ============================================================================
# Helper Functions
# ============================================================================

def get_or_create_user_session() -> str:
    """Get or create user session"""
    if 'user_id' not in session:
        session['user_id'] = workspace_service.create_session_id()
        session.permanent = True
        workspace_service.register_session(session['user_id'])
        logger.info(f"New session created: {session['user_id'][:8]}...")
    else:
        workspace_service.update_session_access(session['user_id'])
    
    return session['user_id']


def get_user_workspace() -> Path:
    """Get current user's workspace"""
    user_id = get_or_create_user_session()
    return workspace_service.get_or_create_workspace(user_id)


def generate_pdf_for_workspace(workspace: Path, notify: bool = True) -> None:
    """
    Generate PDF for a workspace
    
    Args:
        workspace: Workspace directory path
        notify: Whether to send WebSocket notifications
    """
    global last_error, last_generated
    
    user_id = workspace.name
    
    try:
        logger.info(f"Generating PDF for {user_id[:8]}...")
        
        # Get the selected main HTML file (defaults to index.html)
        main_html_filename = workspace_service.get_main_html_file(user_id)
        html_file = workspace / main_html_filename
        
        # Check if HTML file exists
        if not html_file.exists():
            logger.warning(f"{main_html_filename} not found for {user_id[:8]}...")
            return
        
        # Check if HTML file is empty - if so, skip generation gracefully
        html_content = html_file.read_text()
        if not html_content.strip():
            logger.info(f"{main_html_filename} is empty for {user_id[:8]}... skipping PDF generation")
            return
        
        # Load parameters
        params_file = workspace / "params.json"
        params = pdf_service.load_params(params_file)
        
        # Render template
        rendered_html = template_service.render_with_fallback(
            html_file,
            params,
            base_dir=workspace
        )
        
        # Generate PDF
        pdf_output = workspace / "output.pdf"
        pdf_service.generate_pdf(
            rendered_html,
            pdf_output,
            base_url=str(workspace)
        )
        
        last_generated = time.time()
        last_error = None
        
        # Get PDF info
        pdf_info = pdf_service.get_pdf_info(pdf_output)
        
        if pdf_info and notify:
            socketio.emit('pdf_updated', {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'size': f"{pdf_info['size_kb']:.1f} KB",
                'user_id': user_id,
                'main_html': main_html_filename
            })
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        last_error = {
            'message': error_msg,
            'traceback': error_trace,
            'timestamp': datetime.now().isoformat()
        }
        logger.error(f"PDF generation error for {user_id[:8]}...: {error_msg}")
        logger.debug(error_trace)
        
        if notify:
            socketio.emit('pdf_error', last_error)
    

# ============================================================================
# Background Tasks
# ============================================================================

def background_cleanup():
    """Background thread to periodically clean up expired workspaces"""
    while True:
        time.sleep(config.CLEANUP_INTERVAL_MINUTES * 60)
        try:
            deleted, failed = workspace_service.cleanup_expired_sessions()
            if deleted > 0:
                logger.info(f"Cleanup: {deleted} deleted, {failed} failed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# Start background cleanup
cleanup_thread = threading.Thread(target=background_cleanup, daemon=True)
cleanup_thread.start()
logger.info("Background cleanup thread started")


# ============================================================================
# Web Routes
# ============================================================================

@app.route('/')
def index():
    """Serve the landing page"""
    return render_template('index.html')


@app.route('/viewer')
def viewer():
    """Serve the live preview interface"""
    return render_template('viewer.html')


@app.route('/editor')
def editor():
    """Serve the code editor interface"""
    return render_template('editor.html')


@app.route('/preview')
def preview():
    """Serve the rendered HTML content for preview"""
    try:
        workspace = get_user_workspace()
        user_id = get_or_create_user_session()
        
        # Get the selected main HTML file
        main_html_filename = workspace_service.get_main_html_file(user_id)
        html_file = workspace / main_html_filename
        
        if not html_file.exists():
            return f"<html><body><h1>HTML file not found</h1><p>File '{main_html_filename}' does not exist in your workspace.</p></body></html>", 404
        
        # Handle empty HTML file gracefully
        html_content = html_file.read_text()
        if not html_content.strip():
            return "<html><body><h1>Empty HTML File</h1><p>The selected HTML file is empty. Please add some content.</p></body></html>", 200
        
        # Load and render template
        params_file = workspace / "params.json"
        params = pdf_service.load_params(params_file)
        
        rendered_html = template_service.render_with_fallback(
            html_file,
            params,
            base_dir=workspace
        )
        
        return Response(rendered_html, mimetype='text/html')
    
    except Exception as e:
        error_trace = traceback.format_exc()
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
    try:
        workspace = get_user_workspace()
        pdf_file = workspace / "output.pdf"
        
        # Generate if doesn't exist
        if not pdf_file.exists():
            generate_pdf_for_workspace(workspace, notify=False)
        
        if pdf_file.exists():
            return send_file(pdf_file, mimetype='application/pdf')
        
        return "PDF not generated yet", 404
    
    except Exception as e:
        logger.error(f"Error serving PDF: {e}")
        return f"Error: {str(e)}", 500


@app.route('/styles.css')
def serve_css():
    """Serve the main CSS file"""
    try:
        workspace = get_user_workspace()
        css_file = workspace / "styles.css"
        
        if css_file.exists():
            return send_file(css_file, mimetype='text/css')
        
        return "", 404
        
    except Exception as e:
        return "", 404


@app.route('/<path:filename>')
def serve_files(filename):
    """Serve CSS and other static files from workspace"""
    if filename.endswith('.css'):
        workspace = get_user_workspace()
        file_path = workspace / filename
        
        if file_path.exists() and file_path.is_file():
            return send_file(file_path, mimetype='text/css')
    
    return "", 404


@app.route('/status')
def status():
    """Get current status"""
    workspace = get_user_workspace()
    pdf_file = workspace / "output.pdf"
    
    return jsonify({
        'pdf_exists': pdf_file.exists(),
        'last_error': last_error,
        'last_generated': last_generated
    })


@app.route('/regenerate', methods=['POST'])
def regenerate():
    """Force regenerate PDF"""
    try:
        workspace = get_user_workspace()
        generate_pdf_for_workspace(workspace, notify=True)
        
        pdf_file = workspace / "output.pdf"
        if pdf_file.exists():
            pdf_info = pdf_service.get_pdf_info(pdf_file)
            return jsonify({'status': 'success', 'size': pdf_info['size_kb']})
        
        return jsonify({'error': 'PDF generation failed'}), 500
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Regenerate error: {error_trace}")
        return jsonify({'error': str(e), 'trace': error_trace}), 500


# ============================================================================
# API Routes - Files
# ============================================================================

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all files in user's workspace"""
    try:
        user_id = get_or_create_user_session()
        files = workspace_service.list_workspace_files(user_id)
        return jsonify({'files': files})
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<path:filename>', methods=['GET'])
def read_file(filename):
    """Read a file from workspace"""
    try:
        workspace = get_user_workspace()
        file_path = workspace / filename
        
        # Security check
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
        logger.error(f"Error reading file: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<path:filename>', methods=['PUT'])
def write_file(filename):
    """Write a file to workspace"""
    try:
        workspace = get_user_workspace()
        file_path = workspace / filename
        
        # Security check
        if not file_path.resolve().is_relative_to(workspace.resolve()):
            return jsonify({'error': 'Invalid file path'}), 403
        
        data = request.get_json()
        content = data.get('content', '')
        
        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        
        logger.debug(f"File written: {filename}")
        return jsonify({
            'status': 'success',
            'message': f'File {filename} saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/create', methods=['POST'])
def create_file():
    """Create a new file in workspace"""
    try:
        workspace = get_user_workspace()
        data = request.get_json()
        filename = data.get('filename')
        content = data.get('content', '')
        
        if not filename:
            return jsonify({'error': 'filename is required'}), 400
        
        file_path = workspace / filename
        
        # Security check
        if not file_path.resolve().is_relative_to(workspace.resolve()):
            return jsonify({'error': 'Invalid file path'}), 403
        
        # Check if file already exists
        if file_path.exists():
            return jsonify({'error': 'File already exists'}), 409
        
        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        
        logger.info(f"File created: {filename}")
        return jsonify({
            'status': 'success',
            'message': f'File {filename} created successfully',
            'filename': filename
        })
        
    except Exception as e:
        logger.error(f"Error creating file: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file from workspace"""
    try:
        workspace = get_user_workspace()
        file_path = workspace / filename
        
        # Security check
        if not file_path.resolve().is_relative_to(workspace.resolve()):
            return jsonify({'error': 'Invalid file path'}), 403
        
        # Don't allow deleting required files
        if filename in ['index.html', 'params.json']:
            return jsonify({'error': 'Cannot delete required files'}), 403
        
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"File deleted: {filename}")
            return jsonify({'status': 'success', 'message': f'File {filename} deleted'})
        
        return jsonify({'error': 'File not found'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API Routes - Workspace
# ============================================================================

@app.route('/api/workspace/info', methods=['GET'])
def workspace_info():
    """Get workspace information"""
    try:
        user_id = get_or_create_user_session()
        info = workspace_service.get_session_info(user_id)
        
        if info:
            return jsonify(info)
        
        return jsonify({'error': 'No active session'}), 404
        
    except Exception as e:
        logger.error(f"Error getting workspace info: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workspace/cleanup', methods=['POST'])
def manual_cleanup():
    """Manually trigger cleanup (admin endpoint)"""
    try:
        deleted, failed = workspace_service.cleanup_expired_sessions()
        active_count = workspace_service.get_active_sessions_count()
        
        return jsonify({
            'status': 'success',
            'deleted': deleted,
            'failed': failed,
            'active_workspaces': active_count
        })
        
    except Exception as e:
        logger.error(f"Error in manual cleanup: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workspace/main-html', methods=['GET'])
def get_main_html():
    """Get the currently selected main HTML file"""
    try:
        user_id = get_or_create_user_session()
        main_html = workspace_service.get_main_html_file(user_id)
        
        return jsonify({
            'main_html': main_html
        })
        
    except Exception as e:
        logger.error(f"Error getting main HTML file: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workspace/main-html', methods=['POST'])
def set_main_html():
    """Set the main HTML file for PDF generation"""
    try:
        user_id = get_or_create_user_session()
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'filename is required'}), 400
        
        # Validate it's an HTML file
        if not filename.endswith('.html'):
            return jsonify({'error': 'File must be an HTML file'}), 400
        
        success = workspace_service.set_main_html_file(user_id, filename)
        
        if success:
            # Trigger PDF regeneration with new main file
            workspace = workspace_service.get_or_create_workspace(user_id)
            generate_pdf_for_workspace(workspace, notify=True)
            
            return jsonify({
                'status': 'success',
                'main_html': filename,
                'message': f'Main HTML file set to {filename}'
            })
        else:
            return jsonify({'error': 'Failed to set main HTML file'}), 500
        
    except Exception as e:
        logger.error(f"Error setting main HTML file: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workspace/html-files', methods=['GET'])
def list_html_files():
    """List all HTML files in the workspace"""
    try:
        user_id = get_or_create_user_session()
        all_files = workspace_service.list_workspace_files(user_id)
        
        # Filter for HTML files only
        html_files = [f for f in all_files if f['name'].endswith('.html')]
        
        return jsonify({'html_files': html_files})
        
    except Exception as e:
        logger.error(f"Error listing HTML files: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# WebSocket Events
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    logger.info("Client connected")
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    logger.info("Client disconnected")


# ============================================================================
# File Watcher
# ============================================================================

# Global watcher
watcher_service = None


def start_file_watcher():
    """Start watching files for changes"""
    global watcher_service
    
    watcher_service = WatcherService(
        watch_directory=config.WORKSPACES_DIR,
        on_change_callback=lambda workspace: generate_pdf_for_workspace(workspace, notify=True),
        use_polling=config.WATCHER_USE_POLLING,
        poll_interval=config.WATCHER_POLL_INTERVAL,
        debounce_seconds=config.WATCHER_DEBOUNCE_SECONDS
    )
    
    watcher_service.start()
    logger.info(f"File watcher started (watching {config.WORKSPACES_DIR})")
    
    return watcher_service


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info(f"{config.APP_NAME} - v{config.VERSION}")
    logger.info("=" * 60)
    logger.info(f"Template directory: {config.TEMPLATE_DIR}")
    logger.info(f"Workspaces directory: {config.WORKSPACES_DIR}")
    logger.info(f"Session lifetime: {config.WORKSPACE_EXPIRY_HOURS}h")
    logger.info("=" * 60)
    
    # Start file watcher
    observer = start_file_watcher()
    
    logger.info("Starting web server on http://0.0.0.0:5000")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Run Flask with SocketIO
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=config.DEBUG,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        if watcher_service:
            watcher_service.stop()
    
    logger.info("Server stopped. Goodbye!")
