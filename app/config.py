"""
Application configuration management
"""
import os
from pathlib import Path
from datetime import timedelta


class Config:
    """Base configuration"""
    
    # Application
    APP_NAME = "WeasyPrint Sandbox - Vitor Hugo da Silva Lima"
    VERSION = "1.0.0"
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    WORKSPACES_DIR = BASE_DIR / "workspaces"
    TEMPLATE_DIR = BASE_DIR / "playground_files"
    TEMPLATES_DIR = BASE_DIR / "templates"
    
    # Workspace Settings
    WORKSPACE_EXPIRY_HOURS = 1
    CLEANUP_INTERVAL_MINUTES = 5
    
    # Watcher Settings
    WATCHER_DEBOUNCE_SECONDS = 0.5
    WATCHER_USE_POLLING = True  # Better for Docker
    WATCHER_POLL_INTERVAL = 1.0  # seconds
    
    # PDF Settings
    PDF_DEFAULT_SIZE = 'A4'
    PDF_DEFAULT_MARGIN = '2cm'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', None)
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    @classmethod
    def init_app(cls):
        """Initialize application directories"""
        cls.WORKSPACES_DIR.mkdir(exist_ok=True)
        if not cls.TEMPLATE_DIR.exists():
            cls.TEMPLATE_DIR.mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    WATCHER_USE_POLLING = True


class TestConfig(Config):
    """Testing configuration"""
    TESTING = True
    WORKSPACE_EXPIRY_HOURS = 0.1  # 6 minutes for testing
    CLEANUP_INTERVAL_MINUTES = 1


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration object
    
    Args:
        config_name: Configuration name (development, production, test)
    
    Returns:
        Config: Configuration object
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config_by_name.get(config_name, DevelopmentConfig)

