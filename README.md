# WeasyPrint Sandbox - Live PDF Generator

A browser-based development environment for WeasyPrint with live split-view preview. Edit HTML/CSS files and watch your PDF update in real-time!

## ✨ Features

- 🌐 **Browser-based interface** - Split view with HTML preview (left) and PDF output (right)
- ⚡ **Live updates** - Automatic PDF regeneration on file changes
- ✏️ **Integrated code editor** - Edit files directly in your browser with Monaco Editor (VS Code's editor)
- 🔴 **Error display** - See compilation errors directly in the browser
- 🔄 **WebSocket updates** - Real-time notifications without page refresh
- 💾 **Auto-save** - Changes are automatically saved as you type
- 📱 **Responsive** - Resizable panels to adjust your workspace
- 🐳 **Dockerized** - No local dependencies needed

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **One command to start everything:**
   ```bash
   make up
   ```
   This will build the image and start the container. Your browser will automatically open to `http://localhost:5000`

   *Alternatively, run these commands separately:*
   ```bash
   make build  # Build the Docker image
   make run    # Start the container
   ```

2. **Start editing:**
   
   **Option A: Use the web editor** (Recommended)
   - Click the "⚡ Editor" button in the preview interface
   - Edit files directly in your browser with syntax highlighting
   - Changes auto-save and PDF regenerates automatically
   - Supports `index.html`, `styles.css`, `params.json`, and other files
   
   **Option B: Use your favorite editor**
   - Edit files in `playground_files/` directory:
     - `index.html` - Your HTML template with Jinja2 syntax
     - `styles.css` - Your CSS styles
     - `params.json` - Your dynamic data
   - Save your changes
   - Watch the split-view update automatically!
   
   **Preview:**
   - Left panel: Rendered HTML preview
   - Right panel: PDF output

3. **See live logs (optional):**
   ```bash
   make logs
   ```

4. **Stop when done:**
   ```bash
   make stop
   ```

### Option 2: Local Python

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the web server:**
   ```bash
   python3 server.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:5000`

4. **Edit files and watch the magic!**

## ⚠️ Important: Required File Names

The system expects specific file names in the `playground_files/` directory:

- **`index.html`** (REQUIRED) - Must be named exactly `index.html` - this is your main entry point
- **`params.json`** (REQUIRED for dynamic content) - Must be named exactly `params.json` - contains all your template variables
- **`styles.css`** (Optional) - Your CSS styles, can reference other CSS files

**Example structure:**
```
playground_files/
├── index.html    ← REQUIRED: Your main template
├── params.json   ← REQUIRED: Your data
└── styles.css    ← Optional: Your styles
```

## 📁 Project Structure

### Core Files
- `Dockerfile` - Docker image configuration
- `docker-compose.yml` - Docker Compose configuration  
- `Makefile` - Convenient command shortcuts
- `requirements.txt` - Python dependencies
- `server.py` - Flask web server with live preview
- `watcher.py` - Legacy file watcher script (for CLI usage)
- `templates/viewer.html` - Browser interface with split view
- `output.pdf` - Generated PDF (auto-updates)

### 📝 Playground Files (Edit These!)
The `playground_files/` directory contains all your editable files:

**Required Files:**
- **`index.html`** ⚠️ MUST be named `index.html` - Your main HTML template with Jinja2 syntax
- **`params.json`** ⚠️ MUST be named `params.json` - Your dynamic data in JSON format

**Optional Files:**
- **`styles.css`** - Your CSS styles
- **Other CSS files** - Can be organized in subdirectories (e.g., `base/layout.css`)
- **Template partials** - For use with `{% include %}` and `{% extends %}`
- **`README.md`** - Guide for using the playground files

All files in this directory are watched for changes and will trigger automatic PDF regeneration!

**Simple Example:**

`index.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>Hello {{ name }}!</h1>
</body>
</html>
```

`params.json`:
```json
{
  "title": "My PDF",
  "name": "World"
}
```

## ✏️ Web-Based Code Editor

The sandbox includes a powerful browser-based code editor powered by Monaco Editor (the same editor used in VS Code).

### Accessing the Editor

1. **From the main interface**: Click the "⚡ Editor" button in the header
2. **Direct URL**: Open `http://localhost:5000/editor` in your browser

### Features

- **Syntax highlighting** for HTML, CSS, JSON, Markdown, and more
- **Auto-save** - Changes are saved automatically after 1 second of inactivity
- **File tree** - Browse all files in your `playground_files/` directory
- **Keyboard shortcuts**:
  - `Ctrl+S` / `Cmd+S` - Manual save
  - Standard editor shortcuts work (Ctrl+F for find, etc.)
- **File protection** - Cannot delete required files (`index.html`, `params.json`)
- **Live feedback** - Status indicator shows save state
- **Dark theme** - Easy on the eyes for long coding sessions

### Editor Interface

```
┌──────────────────────────────────────────────────────┐
│ ⚡ Code Editor                    [Status] [Actions] │
├──────────┬───────────────────────────────────────────┤
│ Files    │ Editor Area                               │
│ ├─ ★ index.html                                      │
│ ├─ ★ params.json    Your code appears here          │
│ ├─  styles.css      with syntax highlighting         │
│ └─  README.md       and line numbers                 │
└──────────┴───────────────────────────────────────────┘
```

### API Endpoints

The editor uses these REST API endpoints:

- `GET /api/files` - List all files
- `GET /api/file/<path>` - Read file content
- `PUT /api/file/<path>` - Update file content
- `DELETE /api/file/<path>` - Delete file (except required files)

**📖 For detailed editor documentation, see [EDITOR_GUIDE.md](EDITOR_GUIDE.md)**

## 🐳 Docker Commands (via Makefile)

Run `make` or `make help` to see all available commands:

```bash
# Quick start
make up        # 🚀 Build and run (one command - recommended!)

# Step-by-step
make build     # Build the Docker image
make run       # Run the container (starts watcher)

# Management
make stop      # Stop the container
make restart   # Restart the container
make logs      # View container logs (follow mode)
make shell     # Open a shell inside the container
make status    # Show container status
make rebuild   # Rebuild image and restart container
make clean     # Stop and remove container and image

# Testing
make test           # Run a quick test to generate PDF
make test-unit      # Run unit tests locally
make test-cov       # Run tests with coverage report
make test-watch     # Run tests in watch mode
make test-docker    # Run tests inside Docker container
```

**Example workflows:**

**First time setup:**
```bash
make up      # Builds and starts everything!
# Edit files in playground_files/ directory
# Watch updates happen live in the browser!
make stop    # When done
```

**Development workflow:**
```bash
make up           # Start the app
make test-watch   # In another terminal, run tests in watch mode
# Edit code, tests run automatically!
```

## ⚙️ How It Works

### Browser Interface

When you run `make run`, a Flask web server starts and your browser opens to show:

**Left Panel - Rendered HTML Preview**
- Live rendering of your HTML with all parameters injected
- Updates automatically when you save changes to any playground file
- Shows the fully rendered content with CSS applied
- Exactly what will be converted to PDF

**Right Panel - PDF Output**
- The generated PDF displayed inline
- Auto-refreshes when PDF is regenerated
- Shows compilation errors with full stack traces if generation fails

**Features:**
- Real-time WebSocket updates (no page refresh needed)
- Resizable panels (drag the divider)
- Status indicator showing connection and generation status
- Manual regenerate button
- Toast notifications for updates and errors

### The file watcher:
1. Monitors all files in `playground_files/` directory (`*.html`, `*.css`, `*.json`)
2. Regenerates the PDF immediately when any file is saved
3. Uses polling mode for reliable Docker compatibility on macOS
4. Includes debouncing to prevent multiple rapid regenerations
5. Shows generation status with timestamps

### Docker Setup Details

The Docker configuration:
- Uses Python 3.11 with all WeasyPrint system dependencies
- Mounts `playground_files/` directory as volume (edit on host, runs in container)
- The `output.pdf` is also mounted, so it updates on your host machine
- Container runs the file watcher continuously using polling mode
- All changes to playground files are detected automatically (~1 second polling interval)

## 💡 Tips

### Auto-Refresh PDF Viewers
Some PDF viewers automatically refresh when the file changes:
- **Chrome/Brave:** Open PDF in browser tab
- **Firefox:** Built-in PDF viewer auto-refreshes
- **Preview (macOS):** Usually auto-refreshes
- **Evince (Linux):** Auto-refreshes by default

### Page Setup
Control page size and margins with CSS:
```css
@page {
    size: A4;  /* or Letter, A3, etc. */
    margin: 2cm;
}
```

### Adding Images
Just use regular HTML:
```html
<img src="my-image.png" alt="Description" style="width: 100%;">
```

### Multiple CSS Files
Add more stylesheets in your HTML:
```html
<link rel="stylesheet" href="additional.css">
```

## 🎨 Customization

### Change Watch Files
Edit `watcher.py` to watch different files:
```python
html_file = watch_dir / "your-file.html"
output_pdf = watch_dir / "your-output.pdf"
```

### Adjust Debounce
Change regeneration delay in `watcher.py`:
```python
self.debounce_seconds = 1.0  # Wait 1 second between regenerations
```

## 🐛 Troubleshooting

### Docker Issues

**Container won't start?**
- Run `make logs` to see error messages
- Try `make rebuild` to rebuild from scratch
- Ensure Docker is running: `docker ps`

**Changes not detected?**
- Make sure you're editing the files in the sandbox directory (not inside the container)
- The volume mounts should be working - check with `make status`
- Try restarting: `make restart`

**Permission issues with output.pdf?**
- The container creates the file with specific permissions
- If you can't edit it, run: `chmod 666 output.pdf`

### General Issues

**PDF not updating?**
- Check terminal for error messages
- Ensure your PDF viewer isn't locking the file
- Try closing and reopening the PDF

**Changes not detected?**
- Make sure you're saving the file
- Check that you're editing files in the watched directory
- File extensions must be `.html` or `.css`

**CSS not applying?**
- Check for syntax errors in your CSS
- Ensure `<link>` tags point to correct files
- WeasyPrint supports most CSS3 features

## 📚 Resources

- [WeasyPrint Documentation](https://doc.courtbouillon.org/weasyprint/)
- [CSS Print Specifications](https://developer.mozilla.org/en-US/docs/Web/CSS/@page)

## 🎯 Example Use Cases

- Invoice generation
- Report templates
- Certificates
- Business documents
- Styled resumes
- Print-ready web content

Happy PDF generating! 🎉
