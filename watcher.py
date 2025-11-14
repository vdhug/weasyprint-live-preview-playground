#!/usr/bin/env python3
"""
WeasyPrint Sandbox - Live PDF Generator
Watches HTML/CSS files and automatically regenerates PDFs on changes.
"""
import os
import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from weasyprint import HTML, CSS
from datetime import datetime


class PDFGenerator(FileSystemEventHandler):
    def __init__(self, html_file, output_pdf, watch_dir):
        self.html_file = Path(html_file)
        self.output_pdf = Path(output_pdf)
        self.watch_dir = Path(watch_dir)
        self.last_generated = 0
        self.debounce_seconds = 0.5  # Prevent multiple rapid regenerations
        
    def generate_pdf(self):
        """Generate PDF from HTML file"""
        now = time.time()
        if now - self.last_generated < self.debounce_seconds:
            return
            
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Generating PDF...", end=" ")
            
            # Generate PDF
            html = HTML(filename=str(self.html_file))
            html.write_pdf(str(self.output_pdf))
            
            self.last_generated = now
            file_size = self.output_pdf.stat().st_size / 1024  # KB
            print(f"✓ Done! ({file_size:.1f} KB)")
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return
            
        # Only react to HTML and CSS files
        if event.src_path.endswith(('.html', '.css')):
            print(f"Change detected: {Path(event.src_path).name}")
            self.generate_pdf()


def main():
    # Configuration
    watch_dir = Path(__file__).parent
    html_file = watch_dir / "index.html"
    output_pdf = watch_dir / "output.pdf"
    
    # Check if HTML file exists
    if not html_file.exists():
        print(f"Error: {html_file} not found!")
        print("Please create an index.html file in the same directory.")
        sys.exit(1)
    
    # Initial PDF generation
    generator = PDFGenerator(html_file, output_pdf, watch_dir)
    print("=" * 60)
    print("WeasyPrint Live PDF Generator")
    print("=" * 60)
    print(f"Watching: {watch_dir}")
    print(f"HTML file: {html_file.name}")
    print(f"Output: {output_pdf.name}")
    print("=" * 60)
    
    generator.generate_pdf()
    print("\nWatching for changes... (Press Ctrl+C to stop)")
    
    # Set up file watcher
    observer = Observer()
    observer.schedule(generator, str(watch_dir), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping watcher...")
        observer.stop()
    
    observer.join()
    print("Goodbye!")


if __name__ == "__main__":
    main()
