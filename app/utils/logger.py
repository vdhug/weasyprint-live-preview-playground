"""
Logging configuration for the application
"""
import logging
import sys
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Configure application-wide logging
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional file path for log output
    """
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('watchdog').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name):
    """
    Get a logger instance for a module
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self):
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger

