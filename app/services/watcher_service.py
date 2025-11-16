"""
File watcher service for monitoring workspace changes
"""
import time
from pathlib import Path
from typing import Optional, Callable
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from app.utils.logger import get_logger, LoggerMixin


logger = get_logger(__name__)


class WorkspaceChangeHandler(FileSystemEventHandler, LoggerMixin):
    """
    Handles file system events in user workspaces
    """
    
    def __init__(
        self,
        on_change_callback: Callable[[Path], None],
        debounce_seconds: float = 0.5,
        watched_extensions: tuple = ('.html', '.css', '.json')
    ):
        """
        Initialize the change handler
        
        Args:
            on_change_callback: Function to call when files change
            debounce_seconds: Minimum time between processing changes
            watched_extensions: File extensions to watch
        """
        super().__init__()
        self.on_change_callback = on_change_callback
        self.debounce_seconds = debounce_seconds
        self.watched_extensions = watched_extensions
        self.last_processed = {}  # Track last process time per workspace
        
        self.logger.info(
            f"Change handler initialized (debounce: {debounce_seconds}s, "
            f"extensions: {watched_extensions})"
        )
    
    def should_process(self, workspace_id: str) -> bool:
        """
        Check if enough time has passed to process changes
        
        Args:
            workspace_id: Workspace identifier
        
        Returns:
            bool: True if should process
        """
        now = time.time()
        last_time = self.last_processed.get(workspace_id, 0)
        
        if now - last_time < self.debounce_seconds:
            self.logger.debug(
                f"Skipping change for {workspace_id} (debounce)"
            )
            return False
        
        self.last_processed[workspace_id] = now
        return True
    
    def extract_workspace_from_path(self, file_path: Path, base_dir: Path) -> Optional[Path]:
        """
        Extract workspace directory from a file path
        
        Args:
            file_path: Path to the changed file
            base_dir: Base workspaces directory
        
        Returns:
            Path: Workspace directory or None
        """
        try:
            # Navigate up to find workspace directory
            current = file_path.parent
            while current != base_dir and current.parent != base_dir:
                current = current.parent
            
            if current.parent == base_dir:
                return current
        except Exception as e:
            self.logger.error(f"Error extracting workspace from {file_path}: {e}")
        
        return None
    
    def on_modified(self, event: FileSystemEvent):
        """
        Handle file modification events
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if file extension is watched
        if not file_path.suffix in self.watched_extensions:
            return
        
        self.logger.debug(f"File modified: {file_path.name}")
        
        try:
            # Extract workspace from path
            # We need to pass this through callback
            self.on_change_callback(file_path)
            
        except Exception as e:
            self.logger.error(f"Error processing change for {file_path}: {e}", exc_info=True)


class WatcherService(LoggerMixin):
    """
    Service for watching file changes in workspaces
    """
    
    def __init__(
        self,
        watch_directory: Path,
        on_change_callback: Callable[[Path], None],
        use_polling: bool = True,
        poll_interval: float = 1.0,
        debounce_seconds: float = 0.5
    ):
        """
        Initialize the watcher service
        
        Args:
            watch_directory: Directory to watch
            on_change_callback: Callback for file changes
            use_polling: Use polling observer (better for Docker)
            poll_interval: Polling interval in seconds
            debounce_seconds: Debounce time for changes
        """
        self.watch_directory = Path(watch_directory)
        self.on_change_callback = on_change_callback
        self.use_polling = use_polling
        self.poll_interval = poll_interval
        self.debounce_seconds = debounce_seconds
        
        # Create change handler
        self.handler = WorkspaceChangeHandler(
            on_change_callback=self._handle_change,
            debounce_seconds=debounce_seconds
        )
        
        # Create observer
        if use_polling:
            self.observer = PollingObserver(timeout=poll_interval)
            self.logger.info(f"Using polling observer (interval: {poll_interval}s)")
        else:
            self.observer = Observer()
            self.logger.info("Using native observer")
        
        self._is_running = False
    
    def _handle_change(self, file_path: Path):
        """
        Internal change handler with workspace extraction
        
        Args:
            file_path: Path to changed file
        """
        workspace = self.handler.extract_workspace_from_path(
            file_path,
            self.watch_directory
        )
        
        if workspace:
            workspace_id = workspace.name
            if self.handler.should_process(workspace_id):
                self.logger.info(f"Processing change in workspace {workspace_id[:8]}...")
                self.on_change_callback(workspace)
    
    def start(self):
        """Start watching for file changes"""
        if self._is_running:
            self.logger.warning("Watcher already running")
            return
        
        if not self.watch_directory.exists():
            self.watch_directory.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created watch directory: {self.watch_directory}")
        
        # Schedule watching
        self.observer.schedule(
            self.handler,
            str(self.watch_directory),
            recursive=True
        )
        
        self.observer.start()
        self._is_running = True
        
        self.logger.info(
            f"File watcher started"
            f"\n  Directory: {self.watch_directory}"
            f"\n  Mode: {'Polling' if self.use_polling else 'Native'}"
            f"\n  Recursive: True"
        )
    
    def stop(self):
        """Stop watching for file changes"""
        if not self._is_running:
            self.logger.warning("Watcher not running")
            return
        
        self.observer.stop()
        self.observer.join()
        self._is_running = False
        
        self.logger.info("File watcher stopped")
    
    def is_running(self) -> bool:
        """Check if watcher is running"""
        return self._is_running
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()

