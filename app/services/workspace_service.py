"""
Workspace service for managing user sessions and workspaces
"""
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from app.utils.logger import get_logger, LoggerMixin


logger = get_logger(__name__)


class WorkspaceService(LoggerMixin):
    """
    Service for managing user workspaces and sessions
    """
    
    def __init__(
        self,
        workspaces_dir: Path,
        template_dir: Path,
        session_lifetime_hours: int = 1,
        cleanup_interval_seconds: int = 300
    ):
        """
        Initialize workspace service
        
        Args:
            workspaces_dir: Root directory for user workspaces
            template_dir: Directory containing template files
            session_lifetime_hours: Session lifetime in hours
            cleanup_interval_seconds: How often to run cleanup
        """
        self.workspaces_dir = Path(workspaces_dir)
        self.template_dir = Path(template_dir)
        self.session_lifetime_hours = session_lifetime_hours
        self.cleanup_interval_seconds = cleanup_interval_seconds
        
        # Session metadata storage
        self.session_metadata: Dict[str, dict] = {}
        
        # Ensure directories exist
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(
            f"WorkspaceService initialized (workspaces: {workspaces_dir}, "
            f"lifetime: {session_lifetime_hours}h)"
        )
    
    def create_session_id(self) -> str:
        """
        Create a new session ID
        
        Returns:
            str: New session ID (UUID)
        """
        return str(uuid.uuid4())
    
    def register_session(self, session_id: str) -> None:
        """
        Register a new session with metadata
        
        Args:
            session_id: Session identifier
        """
        now = datetime.now()
        self.session_metadata[session_id] = {
            'created_at': now,
            'last_access': now
        }
        self.logger.info(f"Session registered: {session_id[:8]}...")
    
    def update_session_access(self, session_id: str) -> None:
        """
        Update last access time for a session
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.session_metadata:
            self.session_metadata[session_id]['last_access'] = datetime.now()
        else:
            # Session doesn't exist, create it
            self.register_session(session_id)
    
    def get_workspace_path(self, session_id: str) -> Path:
        """
        Get the workspace path for a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Path: Workspace directory path
        """
        return self.workspaces_dir / session_id
    
    def workspace_exists(self, session_id: str) -> bool:
        """
        Check if workspace exists for a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            bool: True if workspace exists
        """
        return self.get_workspace_path(session_id).exists()
    
    def create_workspace(self, session_id: str) -> Path:
        """
        Create a new workspace from template
        
        Args:
            session_id: Session identifier
        
        Returns:
            Path: Created workspace directory
        """
        workspace = self.get_workspace_path(session_id)
        
        if workspace.exists():
            self.logger.debug(f"Workspace already exists: {session_id[:8]}...")
            return workspace
        
        # Register session if not already registered
        if session_id not in self.session_metadata:
            self.register_session(session_id)
        
        self.logger.info(f"Creating workspace for session: {session_id[:8]}...")
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Copy template files
        if self.template_dir.exists():
            self._copy_template_files(self.template_dir, workspace)
            self.logger.info(f"Workspace initialized with template files: {session_id[:8]}...")
        else:
            self.logger.warning(f"Template directory not found: {self.template_dir}")
        
        return workspace
    
    def _copy_template_files(self, source: Path, destination: Path) -> None:
        """
        Copy template files to workspace
        
        Args:
            source: Source template directory
            destination: Destination workspace directory
        """
        for item in source.iterdir():
            dest_item = destination / item.name
            
            if item.is_file():
                shutil.copy2(item, dest_item)
            elif item.is_dir():
                shutil.copytree(item, dest_item, dirs_exist_ok=True)
    
    def get_or_create_workspace(self, session_id: str) -> Path:
        """
        Get existing workspace or create new one
        
        Args:
            session_id: Session identifier
        
        Returns:
            Path: Workspace directory
        """
        self.update_session_access(session_id)
        
        if not self.workspace_exists(session_id):
            return self.create_workspace(session_id)
        
        return self.get_workspace_path(session_id)
    
    def get_expired_sessions(self) -> list:
        """
        Get list of expired sessions
        
        Returns:
            list: List of (session_id, age) tuples for expired sessions
        """
        now = datetime.now()
        expired = []
        lifetime = timedelta(hours=self.session_lifetime_hours)
        
        for session_id, metadata in list(self.session_metadata.items()):
            age = now - metadata['last_access']
            if age > lifetime:
                expired.append((session_id, age))
        
        return expired
    
    def delete_workspace(self, session_id: str) -> bool:
        """
        Delete a workspace directory
        
        Args:
            session_id: Session identifier
        
        Returns:
            bool: True if deleted successfully
        """
        workspace = self.get_workspace_path(session_id)
        
        if not workspace.exists():
            return False
        
        try:
            shutil.rmtree(workspace)
            self.logger.info(f"Deleted workspace: {session_id[:8]}...")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete workspace {session_id[:8]}...: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> Tuple[int, int]:
        """
        Clean up expired sessions and their workspaces
        
        Returns:
            tuple: (deleted_count, failed_count)
        """
        expired = self.get_expired_sessions()
        
        if not expired:
            return (0, 0)
        
        deleted = 0
        failed = 0
        
        for session_id, age in expired:
            age_minutes = int(age.total_seconds() / 60)
            
            if self.delete_workspace(session_id):
                deleted += 1
                self.logger.info(
                    f"Cleaned up expired session: {session_id[:8]}... "
                    f"(age: {age_minutes}min)"
                )
            else:
                failed += 1
            
            # Remove from metadata
            self.session_metadata.pop(session_id, None)
        
        self.logger.info(
            f"Cleanup complete: {deleted} deleted, {failed} failed, "
            f"{len(self.session_metadata)} active"
        )
        
        return (deleted, failed)
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get information about a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            dict: Session info or None if not found
        """
        metadata = self.session_metadata.get(session_id)
        
        if not metadata:
            return None
        
        now = datetime.now()
        age = now - metadata['last_access']
        lifetime = timedelta(hours=self.session_lifetime_hours)
        expires_in = lifetime - age
        
        return {
            'session_id': session_id,
            'created_at': metadata['created_at'].isoformat(),
            'last_access': metadata['last_access'].isoformat(),
            'expires_in_seconds': int(expires_in.total_seconds()),
            'expires_in_minutes': int(expires_in.total_seconds() / 60),
            'workspace_exists': self.workspace_exists(session_id)
        }
    
    def get_active_sessions_count(self) -> int:
        """
        Get count of active sessions
        
        Returns:
            int: Number of active sessions
        """
        return len(self.session_metadata)
    
    def list_workspace_files(self, session_id: str) -> list:
        """
        List all files in a workspace
        
        Args:
            session_id: Session identifier
        
        Returns:
            list: List of file info dictionaries
        """
        workspace = self.get_workspace_path(session_id)
        
        if not workspace.exists():
            return []
        
        files = []
        for file_path in workspace.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    rel_path = file_path.relative_to(workspace)
                    files.append({
                        'path': str(rel_path),
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat()
                    })
                except Exception as e:
                    self.logger.warning(f"Error getting file info for {file_path}: {e}")
        
        return files

