"""
Unit tests for workspace service
"""
import pytest
import time
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from app.services.workspace_service import WorkspaceService


class TestWorkspaceService:
    """Test cases for WorkspaceService"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as workspaces_tmp, \
             tempfile.TemporaryDirectory() as template_tmp:
            
            workspaces_dir = Path(workspaces_tmp)
            template_dir = Path(template_tmp)
            
            # Create some template files
            (template_dir / "index.html").write_text("<html></html>")
            (template_dir / "styles.css").write_text("body {}")
            (template_dir / "params.json").write_text("{}")
            
            yield workspaces_dir, template_dir
    
    @pytest.fixture
    def service(self, temp_dirs):
        """Create workspace service instance"""
        workspaces_dir, template_dir = temp_dirs
        return WorkspaceService(
            workspaces_dir=workspaces_dir,
            template_dir=template_dir,
            session_lifetime_hours=1
        )
    
    def test_initialization(self, temp_dirs):
        """Test service initialization"""
        workspaces_dir, template_dir = temp_dirs
        
        service = WorkspaceService(
            workspaces_dir=workspaces_dir,
            template_dir=template_dir,
            session_lifetime_hours=2,
            cleanup_interval_seconds=600
        )
        
        assert service.workspaces_dir == workspaces_dir
        assert service.template_dir == template_dir
        assert service.session_lifetime_hours == 2
        assert service.cleanup_interval_seconds == 600
        assert service.session_metadata == {}
        assert workspaces_dir.exists()
    
    def test_create_session_id(self, service):
        """Test session ID creation"""
        session_id = service.create_session_id()
        
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID format
        
        # Should be unique
        session_id2 = service.create_session_id()
        assert session_id != session_id2
    
    def test_register_session(self, service):
        """Test session registration"""
        session_id = "test-session-123"
        
        assert session_id not in service.session_metadata
        
        service.register_session(session_id)
        
        assert session_id in service.session_metadata
        metadata = service.session_metadata[session_id]
        assert 'created_at' in metadata
        assert 'last_access' in metadata
        assert isinstance(metadata['created_at'], datetime)
        assert isinstance(metadata['last_access'], datetime)
    
    def test_update_session_access(self, service):
        """Test updating session access time"""
        session_id = "test-session-123"
        service.register_session(session_id)
        
        original_time = service.session_metadata[session_id]['last_access']
        time.sleep(0.1)
        
        service.update_session_access(session_id)
        
        new_time = service.session_metadata[session_id]['last_access']
        assert new_time > original_time
    
    def test_update_session_access_creates_if_missing(self, service):
        """Test that update_session_access creates session if missing"""
        session_id = "new-session"
        
        assert session_id not in service.session_metadata
        
        service.update_session_access(session_id)
        
        assert session_id in service.session_metadata
    
    def test_get_workspace_path(self, service):
        """Test getting workspace path"""
        session_id = "test-session-123"
        
        path = service.get_workspace_path(session_id)
        
        assert isinstance(path, Path)
        assert path.name == session_id
        assert path.parent == service.workspaces_dir
    
    def test_workspace_exists(self, service):
        """Test checking workspace existence"""
        session_id = "test-session-123"
        
        assert service.workspace_exists(session_id) is False
        
        # Create workspace
        workspace = service.get_workspace_path(session_id)
        workspace.mkdir(parents=True)
        
        assert service.workspace_exists(session_id) is True
    
    def test_create_workspace(self, service):
        """Test workspace creation"""
        session_id = "test-session-123"
        
        assert not service.workspace_exists(session_id)
        
        workspace = service.create_workspace(session_id)
        
        assert workspace.exists()
        assert workspace.is_dir()
        assert (workspace / "index.html").exists()
        assert (workspace / "styles.css").exists()
        assert (workspace / "params.json").exists()
    
    def test_create_workspace_idempotent(self, service):
        """Test that creating existing workspace is idempotent"""
        session_id = "test-session-123"
        
        workspace1 = service.create_workspace(session_id)
        workspace2 = service.create_workspace(session_id)
        
        assert workspace1 == workspace2
        assert workspace1.exists()
    
    def test_create_workspace_without_template(self, temp_dirs):
        """Test workspace creation when template doesn't exist"""
        workspaces_dir, _ = temp_dirs
        non_existent_template = workspaces_dir / "nonexistent"
        
        service = WorkspaceService(
            workspaces_dir=workspaces_dir,
            template_dir=non_existent_template
        )
        
        session_id = "test-session"
        workspace = service.create_workspace(session_id)
        
        # Should still create workspace directory
        assert workspace.exists()
        # But no template files
        assert not (workspace / "index.html").exists()
    
    def test_get_or_create_workspace_creates_new(self, service):
        """Test get_or_create when workspace doesn't exist"""
        session_id = "test-session-123"
        
        workspace = service.get_or_create_workspace(session_id)
        
        assert workspace.exists()
        assert session_id in service.session_metadata
    
    def test_get_or_create_workspace_returns_existing(self, service):
        """Test get_or_create when workspace exists"""
        session_id = "test-session-123"
        
        # Create workspace first
        workspace1 = service.create_workspace(session_id)
        
        # Create a marker file
        marker = workspace1 / "marker.txt"
        marker.write_text("test")
        
        # Get or create should return same workspace
        workspace2 = service.get_or_create_workspace(session_id)
        
        assert workspace1 == workspace2
        assert (workspace2 / "marker.txt").exists()
    
    def test_get_or_create_workspace_updates_access(self, service):
        """Test that get_or_create updates access time"""
        session_id = "test-session-123"
        service.register_session(session_id)
        
        original_time = service.session_metadata[session_id]['last_access']
        time.sleep(0.1)
        
        service.get_or_create_workspace(session_id)
        
        new_time = service.session_metadata[session_id]['last_access']
        assert new_time > original_time
    
    def test_delete_workspace(self, service):
        """Test workspace deletion"""
        session_id = "test-session-123"
        workspace = service.create_workspace(session_id)
        
        assert workspace.exists()
        
        result = service.delete_workspace(session_id)
        
        assert result is True
        assert not workspace.exists()
    
    def test_delete_nonexistent_workspace(self, service):
        """Test deleting non-existent workspace"""
        session_id = "nonexistent"
        
        result = service.delete_workspace(session_id)
        
        assert result is False
    
    def test_get_expired_sessions(self, service):
        """Test getting expired sessions"""
        # Create some sessions
        session1 = "session-1"
        session2 = "session-2"
        session3 = "session-3"
        
        service.register_session(session1)
        service.register_session(session2)
        service.register_session(session3)
        
        # Manually expire session1 and session2
        old_time = datetime.now() - timedelta(hours=2)
        service.session_metadata[session1]['last_access'] = old_time
        service.session_metadata[session2]['last_access'] = old_time
        
        expired = service.get_expired_sessions()
        
        assert len(expired) == 2
        expired_ids = [sid for sid, _ in expired]
        assert session1 in expired_ids
        assert session2 in expired_ids
        assert session3 not in expired_ids
    
    def test_cleanup_expired_sessions(self, service):
        """Test cleaning up expired sessions"""
        # Create workspaces for sessions
        session1 = "session-1"
        session2 = "session-2"
        session3 = "session-3"
        
        service.create_workspace(session1)
        service.create_workspace(session2)
        service.create_workspace(session3)
        
        # Expire session1 and session2
        old_time = datetime.now() - timedelta(hours=2)
        service.session_metadata[session1]['last_access'] = old_time
        service.session_metadata[session2]['last_access'] = old_time
        
        deleted, failed = service.cleanup_expired_sessions()
        
        assert deleted == 2
        assert failed == 0
        assert not service.workspace_exists(session1)
        assert not service.workspace_exists(session2)
        assert service.workspace_exists(session3)
        assert session1 not in service.session_metadata
        assert session2 not in service.session_metadata
        assert session3 in service.session_metadata
    
    def test_cleanup_expired_sessions_no_expired(self, service):
        """Test cleanup when no sessions are expired"""
        session_id = "active-session"
        service.create_workspace(session_id)
        
        deleted, failed = service.cleanup_expired_sessions()
        
        assert deleted == 0
        assert failed == 0
        assert service.workspace_exists(session_id)
    
    def test_get_session_info(self, service):
        """Test getting session information"""
        session_id = "test-session"
        service.register_session(session_id)
        service.create_workspace(session_id)
        
        info = service.get_session_info(session_id)
        
        assert info is not None
        assert info['session_id'] == session_id
        assert 'created_at' in info
        assert 'last_access' in info
        assert 'expires_in_seconds' in info
        assert 'expires_in_minutes' in info
        assert info['workspace_exists'] is True
        assert info['expires_in_seconds'] > 0
    
    def test_get_session_info_nonexistent(self, service):
        """Test getting info for non-existent session"""
        info = service.get_session_info("nonexistent")
        
        assert info is None
    
    def test_get_active_sessions_count(self, service):
        """Test getting active sessions count"""
        assert service.get_active_sessions_count() == 0
        
        service.register_session("session-1")
        assert service.get_active_sessions_count() == 1
        
        service.register_session("session-2")
        service.register_session("session-3")
        assert service.get_active_sessions_count() == 3
    
    def test_list_workspace_files(self, service):
        """Test listing workspace files"""
        session_id = "test-session"
        workspace = service.create_workspace(session_id)
        
        # Add an extra file
        (workspace / "custom.txt").write_text("test")
        
        files = service.list_workspace_files(session_id)
        
        assert len(files) >= 4  # index.html, styles.css, params.json, custom.txt
        
        file_names = [f['name'] for f in files]
        assert 'index.html' in file_names
        assert 'styles.css' in file_names
        assert 'params.json' in file_names
        assert 'custom.txt' in file_names
        
        # Check file info structure
        for file_info in files:
            assert 'path' in file_info
            assert 'name' in file_info
            assert 'size' in file_info
            assert 'modified' in file_info
    
    def test_list_workspace_files_nonexistent(self, service):
        """Test listing files for non-existent workspace"""
        files = service.list_workspace_files("nonexistent")
        
        assert files == []
    
    def test_list_workspace_files_ignores_hidden(self, service):
        """Test that hidden files are ignored"""
        session_id = "test-session"
        workspace = service.create_workspace(session_id)
        
        # Create hidden file
        (workspace / ".hidden").write_text("secret")
        
        files = service.list_workspace_files(session_id)
        
        file_names = [f['name'] for f in files]
        assert '.hidden' not in file_names
    
    def test_copy_template_files_with_subdirectories(self, temp_dirs):
        """Test copying template files including subdirectories"""
        workspaces_dir, template_dir = temp_dirs
        
        # Create nested structure
        subdir = template_dir / "base"
        subdir.mkdir()
        (subdir / "layout.html").write_text("<layout></layout>")
        
        service = WorkspaceService(
            workspaces_dir=workspaces_dir,
            template_dir=template_dir
        )
        
        session_id = "test-session"
        workspace = service.create_workspace(session_id)
        
        # Check nested files copied
        assert (workspace / "base" / "layout.html").exists()


class TestWorkspaceServiceIntegration:
    """Integration tests for workspace service"""
    
    @pytest.fixture
    def service_with_data(self):
        """Create service with pre-populated data"""
        with tempfile.TemporaryDirectory() as workspaces_tmp, \
             tempfile.TemporaryDirectory() as template_tmp:
            
            workspaces_dir = Path(workspaces_tmp)
            template_dir = Path(template_tmp)
            
            # Create template
            (template_dir / "index.html").write_text("<html></html>")
            
            service = WorkspaceService(
                workspaces_dir=workspaces_dir,
                template_dir=template_dir,
                session_lifetime_hours=1
            )
            
            # Create multiple sessions and workspaces
            for i in range(5):
                session_id = f"session-{i}"
                service.create_workspace(session_id)
            
            yield service
    
    def test_multiple_concurrent_sessions(self, service_with_data):
        """Test handling multiple concurrent sessions"""
        service = service_with_data
        
        assert service.get_active_sessions_count() == 5
        
        # All workspaces should exist
        for i in range(5):
            assert service.workspace_exists(f"session-{i}")
    
    def test_partial_cleanup(self, service_with_data):
        """Test cleanup with mix of expired and active sessions"""
        service = service_with_data
        
        # Expire sessions 0, 1, 2
        old_time = datetime.now() - timedelta(hours=2)
        for i in range(3):
            session_id = f"session-{i}"
            service.session_metadata[session_id]['last_access'] = old_time
        
        deleted, failed = service.cleanup_expired_sessions()
        
        assert deleted == 3
        assert service.get_active_sessions_count() == 2
        
        # Check correct sessions removed
        for i in range(3):
            assert not service.workspace_exists(f"session-{i}")
        for i in range(3, 5):
            assert service.workspace_exists(f"session-{i}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

