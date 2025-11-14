# WeasyPrint Sandbox - Docker Architecture

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      YOUR COMPUTER                          │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │ Text Editor  │      │ PDF Viewer   │                   │
│  │              │      │              │                   │
│  │ Edit:        │      │ View:        │                   │
│  │ index.html   │      │ output.pdf   │                   │
│  │ styles.css   │      │              │                   │
│  └──────┬───────┘      └──────▲───────┘                   │
│         │                     │                            │
│         │ Save                │ Auto-refresh               │
│         ▼                     │                            │
│  ┌─────────────────────────────────────┐                  │
│  │    Project Directory                │                  │
│  │    weasyprint_sandbox/              │                  │
│  │    ├── index.html    ◄──────┐       │                  │
│  │    ├── styles.css    ◄──────┤       │                  │
│  │    └── output.pdf    ◄──────┤       │                  │
│  └────────────────────┬────────┼───────┘                  │
│                       │        │                           │
│         Docker Volume │        │ Volume Mount              │
│         Mapping       │        │                           │
│                       ▼        │                           │
│  ┌────────────────────────────────────────────────┐       │
│  │          DOCKER CONTAINER                      │       │
│  │          weasyprint-sandbox                    │       │
│  │                                                 │       │
│  │  ┌─────────────────────────────────────┐      │       │
│  │  │   /app/ directory                   │      │       │
│  │  │   ├── index.html    ◄────────┐      │      │       │
│  │  │   ├── styles.css    ◄────────┤      │      │       │
│  │  │   └── output.pdf    ◄────────┤      │      │       │
│  │  └────────┬──────────────┬──────┼──────┘      │       │
│  │           │              │      │              │       │
│  │           │ Watch        │ Read │ Write        │       │
│  │           ▼              ▼      │              │       │
│  │  ┌──────────────────────────────────┐         │       │
│  │  │   Python Watcher (watcher.py)   │         │       │
│  │  │                                  │         │       │
│  │  │  1. Detects file changes        │         │       │
│  │  │  2. Triggers PDF generation     │         │       │
│  │  │  3. Writes output.pdf ──────────┘         │       │
│  │  └──────────────────────────────────┘         │       │
│  │                                                 │       │
│  │  System Dependencies:                          │       │
│  │  • Python 3.11                                 │       │
│  │  • WeasyPrint + all libraries                  │       │
│  │  • Cairo, Pango, GDK-PixBuf                    │       │
│  │  • watchdog (file monitoring)                  │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 How It Works

### 1. **File Editing (On Your Computer)**
   - You edit `index.html` or `styles.css` using your favorite editor
   - Files are saved to your local filesystem

### 2. **Volume Mounting (Docker Magic)**
   - Docker mounts your local files into the container
   - Changes on your computer appear instantly in the container
   - This is bidirectional - changes in the container appear on your computer

### 3. **File Watching (Inside Container)**
   - The `watcher.py` script runs continuously inside the container
   - It monitors the mounted files for changes
   - When a change is detected, it triggers PDF generation

### 4. **PDF Generation (Inside Container)**
   - WeasyPrint reads the HTML/CSS files
   - Generates a new PDF
   - Writes `output.pdf` to the mounted volume

### 5. **PDF Viewing (On Your Computer)**
   - The PDF appears on your local filesystem
   - Your PDF viewer can auto-refresh to show changes
   - No manual intervention needed!

## 📦 Docker Components

### Dockerfile
Defines the container image:
- Base: Python 3.11 Slim
- System packages: Cairo, Pango, etc. (required by WeasyPrint)
- Python packages: weasyprint, watchdog
- Entry point: watcher.py

### docker-compose.yml
Orchestrates the container:
- Service name: `weasyprint-sandbox`
- Volume mounts: Maps local files to container
- Restart policy: Always restart unless stopped
- TTY: Keeps container running

### Makefile
Provides convenient commands:
- `make build` - Build the Docker image
- `make run` - Start the container
- `make logs` - View live output
- `make stop` - Stop the container
- And more...

## 🎯 Benefits of This Setup

### ✅ Isolation
- All dependencies contained in Docker
- No need to install WeasyPrint on your system
- No conflicts with other Python projects

### ✅ Portability
- Works on any system with Docker (Linux, macOS, Windows)
- Same environment for all developers
- "It works on my machine" → "It works everywhere"

### ✅ Simplicity
- One `make run` command to start
- No manual dependency management
- Clean removal with `make clean`

### ✅ Development Speed
- Near real-time PDF generation
- Edit on host, run in container
- No copy/paste or manual file transfers

## 🚀 Quick Commands Reference

```bash
# First time setup
make build          # Build the Docker image

# Daily workflow
make run           # Start the sandbox
make logs          # Watch the logs (optional)
# Edit index.html or styles.css
# View output.pdf
make stop          # Stop when done

# Utility commands
make shell         # Open shell in container
make test          # Test PDF generation
make restart       # Restart the container
make rebuild       # Rebuild everything
make clean         # Remove everything
```

## 🔧 Volume Mounts Explained

The `docker-compose.yml` file contains these volume mounts:

```yaml
volumes:
  - ./index.html:/app/index.html      # HTML file
  - ./styles.css:/app/styles.css      # CSS file
  - ./output.pdf:/app/output.pdf      # Generated PDF
```

This means:
- `./index.html` on your computer → `/app/index.html` in container
- Changes to local file instantly visible in container
- Changes to container file instantly visible locally

## 🎨 Customization

### Add More Files to Watch
Edit `docker-compose.yml` and add more volume mounts:
```yaml
volumes:
  - ./index.html:/app/index.html
  - ./styles.css:/app/styles.css
  - ./custom.css:/app/custom.css      # Add this
  - ./output.pdf:/app/output.pdf
```

### Use Different Python Version
Edit `Dockerfile`:
```dockerfile
FROM python:3.12-slim  # Change version here
```

### Add More Dependencies
Edit `requirements.txt`:
```
weasyprint==61.2
watchdog==4.0.0
pillow==10.0.0       # Add image processing
```

## 🐛 Troubleshooting

### Container won't start
```bash
make logs           # Check for errors
docker ps -a        # See if container exists
make rebuild        # Nuclear option: rebuild everything
```

### Files not syncing
```bash
make status         # Check if volumes are mounted
docker-compose config  # Validate docker-compose.yml
```

### Permission issues
```bash
# If you can't edit output.pdf
chmod 666 output.pdf

# If Docker can't write files
# Check Docker Desktop settings (macOS/Windows)
# or user permissions (Linux)
```

## 📚 Learn More

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [WeasyPrint Documentation](https://doc.courtbouillon.org/weasyprint/)
- [Make Documentation](https://www.gnu.org/software/make/manual/)

---

**Pro Tip:** Keep this file open as a reference while developing! 📖
