"""
Unit tests for the watcher service
"""
import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, call

from app.services.watcher_service import (
    WorkspaceChangeHandler,
    WatcherService
)


class TestWorkspaceChangeHandler:
    """Test cases for WorkspaceChangeHandler"""
    
    def test_initialization(self):
        """Test handler initialization"""
        callback = Mock()
        handler = WorkspaceChangeHandler(
            on_change_callback=callback,
            debounce_seconds=0.5,
            watched_extensions=('.html', '.css')
        )
        
        assert handler.on_change_callback == callback
        assert handler.debounce_seconds == 0.5
        assert handler.watched_extensions == ('.html', '.css')
        assert handler.last_processed == {}
    
    def test_should_process_first_time(self):
        """Test that first change is always processed"""
        callback = Mock()
        handler = WorkspaceChangeHandler(callback, debounce_seconds=1.0)
        
        assert handler.should_process('workspace-1') is True
    
    def test_should_process_debounce(self):
        """Test debounce prevents rapid processing"""
        callback = Mock()
        handler = WorkspaceChangeHandler(callback, debounce_seconds=0.5)
        
        # First call should process
        assert handler.should_process('workspace-1') is True
        
        # Immediate second call should be blocked
        assert handler.should_process('workspace-1') is False
        
        # After debounce time, should process again
        time.sleep(0.6)
        assert handler.should_process('workspace-1') is True
    
    def test_extract_workspace_from_path(self):
        """Test workspace extraction from file path"""
        callback = Mock()
        handler = WorkspaceChangeHandler(callback)
        
        base_dir = Path("/app/workspaces")
        file_path = Path("/app/workspaces/user-123/index.html")
        
        workspace = handler.extract_workspace_from_path(file_path, base_dir)
        
        assert workspace == Path("/app/workspaces/user-123")
        assert workspace.name == "user-123"
    
    def test_extract_workspace_from_nested_path(self):
        """Test workspace extraction from nested file"""
        callback = Mock()
        handler = WorkspaceChangeHandler(callback)
        
        base_dir = Path("/app/workspaces")
        file_path = Path("/app/workspaces/user-123/base/layout.html")
        
        workspace = handler.extract_workspace_from_path(file_path, base_dir)
        
        assert workspace == Path("/app/workspaces/user-123")
    
    def test_on_modified_ignores_directories(self):
        """Test that directory events are ignored"""
        callback = Mock()
        handler = WorkspaceChangeHandler(callback)
        
        event = Mock()
        event.is_directory = True
        event.src_path = "/app/workspaces/user-123"
        
        handler.on_modified(event)
        
        callback.assert_not_called()
    
    def test_on_modified_ignores_unwatched_extensions(self):
        """Test that non-watched file extensions are ignored"""
        callback = Mock()
        handler = WorkspaceChangeHandler(
            callback,
            watched_extensions=('.html', '.css')
        )
        
        event = Mock()
        event.is_directory = False
        event.src_path = "/app/workspaces/user-123/file.txt"
        
        handler.on_modified(event)
        
        callback.assert_not_called()
    
    def test_on_modified_processes_html_files(self):
        """Test that HTML files trigger callback"""
        callback = Mock()
        handler = WorkspaceChangeHandler(callback)
        
        event = Mock()
        event.is_directory = False
        event.src_path = "/app/workspaces/user-123/index.html"
        
        handler.on_modified(event)
        
        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert str(call_args).endswith('index.html')


class TestWatcherService:
    """Test cases for WatcherService"""
    
    def test_initialization_with_polling(self):
        """Test service initialization with polling observer"""
        callback = Mock()
        watch_dir = Path("/tmp/test_watch")
        
        service = WatcherService(
            watch_directory=watch_dir,
            on_change_callback=callback,
            use_polling=True,
            poll_interval=1.0
        )
        
        assert service.watch_directory == watch_dir
        assert service.use_polling is True
        assert service.poll_interval == 1.0
        assert service.is_running() is False
    
    def test_initialization_without_polling(self):
        """Test service initialization with native observer"""
        callback = Mock()
        watch_dir = Path("/tmp/test_watch")
        
        service = WatcherService(
            watch_directory=watch_dir,
            on_change_callback=callback,
            use_polling=False
        )
        
        assert service.use_polling is False
        assert service.is_running() is False
    
    @pytest.fixture
    def temp_watch_dir(self):
        """Create temporary watch directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_start_creates_directory(self, temp_watch_dir):
        """Test that start creates watch directory if it doesn't exist"""
        callback = Mock()
        watch_dir = temp_watch_dir / "workspaces"
        
        assert not watch_dir.exists()
        
        service = WatcherService(
            watch_directory=watch_dir,
            on_change_callback=callback,
            use_polling=True
        )
        
        service.start()
        
        assert watch_dir.exists()
        assert service.is_running() is True
        
        service.stop()
    
    def test_start_and_stop(self, temp_watch_dir):
        """Test starting and stopping the watcher"""
        callback = Mock()
        
        service = WatcherService(
            watch_directory=temp_watch_dir,
            on_change_callback=callback,
            use_polling=True
        )
        
        # Initially not running
        assert service.is_running() is False
        
        # Start watcher
        service.start()
        assert service.is_running() is True
        
        # Stop watcher
        service.stop()
        assert service.is_running() is False
    
    def test_context_manager(self, temp_watch_dir):
        """Test using watcher as context manager"""
        callback = Mock()
        
        with WatcherService(
            watch_directory=temp_watch_dir,
            on_change_callback=callback,
            use_polling=True
        ) as service:
            assert service.is_running() is True
        
        assert service.is_running() is False
    
    def test_start_when_already_running(self, temp_watch_dir):
        """Test that calling start twice doesn't cause issues"""
        callback = Mock()
        
        service = WatcherService(
            watch_directory=temp_watch_dir,
            on_change_callback=callback,
            use_polling=True
        )
        
        service.start()
        assert service.is_running() is True
        
        # Try to start again
        service.start()
        assert service.is_running() is True
        
        service.stop()
    
    def test_stop_when_not_running(self):
        """Test that calling stop when not running doesn't cause issues"""
        callback = Mock()
        watch_dir = Path("/tmp/test_watch")
        
        service = WatcherService(
            watch_directory=watch_dir,
            on_change_callback=callback,
            use_polling=True
        )
        
        assert service.is_running() is False
        
        # Try to stop when not running
        service.stop()
        assert service.is_running() is False
    
    def test_file_change_triggers_callback(self, temp_watch_dir):
        """Test that file changes trigger the callback"""
        callback = Mock()
        workspace_dir = temp_watch_dir / "user-123"
        workspace_dir.mkdir()
        
        service = WatcherService(
            watch_directory=temp_watch_dir,
            on_change_callback=callback,
            use_polling=True,
            poll_interval=0.5,
            debounce_seconds=0.1
        )
        
        service.start()
        
        # Create a test file
        test_file = workspace_dir / "index.html"
        test_file.write_text("<html></html>")
        
        # Wait for watcher to detect change
        time.sleep(1.5)
        
        # Callback should have been called
        assert callback.called
        
        service.stop()


class TestIntegration:
    """Integration tests for watcher service"""
    
    @pytest.fixture
    def workspace_structure(self):
        """Create a workspace structure for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create workspaces
            ws1 = base / "workspace-1"
            ws1.mkdir()
            (ws1 / "index.html").write_text("<html></html>")
            (ws1 / "styles.css").write_text("body {}")
            
            ws2 = base / "workspace-2"
            ws2.mkdir()
            (ws2 / "index.html").write_text("<html></html>")
            
            yield base
    
    def test_multiple_workspace_changes(self, workspace_structure):
        """Test handling changes in multiple workspaces"""
        changes = []
        
        def callback(workspace: Path):
            changes.append(workspace.name)
        
        service = WatcherService(
            watch_directory=workspace_structure,
            on_change_callback=callback,
            use_polling=True,
            poll_interval=0.5,
            debounce_seconds=0.1
        )
        
        service.start()
        
        # Modify files in different workspaces
        (workspace_structure / "workspace-1" / "index.html").write_text("<html>Modified</html>")
        time.sleep(1.0)
        
        (workspace_structure / "workspace-2" / "index.html").write_text("<html>Modified2</html>")
        time.sleep(1.0)
        
        service.stop()
        
        # Both workspaces should have triggered callbacks
        assert "workspace-1" in changes
        assert "workspace-2" in changes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

