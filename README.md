# WeasyPrint Sandbox - Live PDF Generator

A browser-based development environment for WeasyPrint with live split-view preview. Edit HTML/CSS files and watch your PDF update in real-time!

## ✨ Features

- 🌐 **Browser-based interface** - Split view with HTML preview (left) and PDF output (right)
- ⚡ **Live updates** - Automatic PDF regeneration on file changes
- 🔴 **Error display** - See compilation errors directly in the browser
- 🔄 **WebSocket updates** - Real-time notifications without page refresh
- 📱 **Responsive** - Resizable panels to adjust your workspace
- 🐳 **Dockerized** - No local dependencies needed

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Build and start:**
   ```bash
   make build
   make run
   ```
   Your browser will automatically open to `http://localhost:5000`

2. **Start editing:**
   - Edit files in `playground_files/` directory:
     - `index.html` - Your HTML template with Jinja2 syntax
     - `styles.css` - Your CSS styles
     - `params.json` - Your dynamic data
   - Save your changes
   - Watch the split-view update automatically!
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
- **`index.html`** - Your HTML template with Jinja2 syntax
- **`styles.css`** - Your CSS styles  
- **`params.json`** - Your dynamic data in JSON format
- **`README.md`** - Guide for using the playground files

All files in this directory are watched for changes and will trigger automatic PDF regeneration!

## 🐳 Docker Commands (via Makefile)

Run `make` or `make help` to see all available commands:

```bash
make build     # Build the Docker image
make run       # Run the container (starts watcher)
make stop      # Stop the container
make restart   # Restart the container
make logs      # View container logs (follow mode)
make shell     # Open a shell inside the container
make status    # Show container status
make test      # Run a quick test to generate PDF
make rebuild   # Rebuild image and restart container
make clean     # Stop and remove container and image
```

**Example workflow:**
```bash
make build    # First time only
make run      # Starts server and opens browser
# Edit files in playground_files/ directory in your favorite editor
# Watch updates happen live in the browser!
make stop     # When done
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
