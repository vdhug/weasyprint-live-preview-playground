"""
Template service for Jinja2 rendering
"""
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from jinja2 import Environment, FileSystemLoader, Template, TemplateError

from app.utils.logger import get_logger, LoggerMixin


logger = get_logger(__name__)


class TemplateService(LoggerMixin):
    """
    Service for rendering Jinja2 templates
    """
    
    def __init__(self, auto_inject_datetime: bool = True):
        """
        Initialize template service
        
        Args:
            auto_inject_datetime: Automatically inject 'now' variable
        """
        self.auto_inject_datetime = auto_inject_datetime
        self.logger.info("TemplateService initialized")
    
    def _prepare_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare template context with auto-injected variables
        
        Args:
            params: User-provided parameters
        
        Returns:
            dict: Complete template context
        """
        context = dict(params)
        
        if self.auto_inject_datetime and 'now' not in context:
            context['now'] = datetime.now()
        
        return context
    
    def render_string(
        self,
        template_string: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render a template from a string
        
        Args:
            template_string: Template content as string
            params: Template parameters
        
        Returns:
            str: Rendered template
        
        Raises:
            TemplateError: If template rendering fails
        """
        if params is None:
            params = {}
        
        try:
            context = self._prepare_context(params)
            template = Template(template_string)
            rendered = template.render(**context)
            
            self.logger.debug("Template rendered successfully from string")
            return rendered
            
        except TemplateError as e:
            self.logger.error(f"Template rendering error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error rendering template: {e}", exc_info=True)
            raise TemplateError(f"Template rendering failed: {e}")
    
    def render_file(
        self,
        template_path: Path,
        params: Optional[Dict[str, Any]] = None,
        base_dir: Optional[Path] = None
    ) -> str:
        """
        Render a template from a file
        
        This method uses FileSystemLoader to support template inheritance
        (extends, includes) and relative paths.
        
        Args:
            template_path: Path to template file
            params: Template parameters
            base_dir: Base directory for template loader (defaults to template's parent)
        
        Returns:
            str: Rendered template
        
        Raises:
            TemplateError: If template rendering fails
            FileNotFoundError: If template file doesn't exist
        """
        if params is None:
            params = {}
        
        template_path = Path(template_path)
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        # Determine base directory
        if base_dir is None:
            base_dir = template_path.parent
        else:
            base_dir = Path(base_dir)
        
        try:
            context = self._prepare_context(params)
            
            # Create environment with FileSystemLoader
            env = Environment(loader=FileSystemLoader(str(base_dir)))
            
            # Get template name relative to base_dir
            template_name = template_path.relative_to(base_dir)
            template = env.get_template(str(template_name))
            
            rendered = template.render(**context)
            
            self.logger.debug(f"Template rendered successfully: {template_path.name}")
            return rendered
            
        except TemplateError as e:
            self.logger.error(f"Template rendering error for {template_path.name}: {e}")
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error rendering template {template_path.name}: {e}",
                exc_info=True
            )
            raise TemplateError(f"Template rendering failed: {e}")
    
    def render_with_fallback(
        self,
        template_path: Path,
        params: Optional[Dict[str, Any]] = None,
        base_dir: Optional[Path] = None
    ) -> str:
        """
        Render template with fallback to string rendering
        
        First tries to render with FileSystemLoader (supports extends/includes).
        If that fails, falls back to simple string rendering.
        
        Args:
            template_path: Path to template file
            params: Template parameters
            base_dir: Base directory for template loader
        
        Returns:
            str: Rendered template
        
        Raises:
            TemplateError: If both methods fail
        """
        try:
            return self.render_file(template_path, params, base_dir)
        except Exception as e:
            self.logger.warning(
                f"File-based rendering failed for {template_path.name}, "
                f"trying fallback: {e}"
            )
            
            try:
                # Read file and render as string
                template_content = template_path.read_text()
                return self.render_string(template_content, params)
            except Exception as fallback_error:
                self.logger.error(
                    f"Fallback rendering also failed for {template_path.name}: "
                    f"{fallback_error}"
                )
                raise TemplateError(
                    f"Template rendering failed with both methods: {fallback_error}"
                )
    
    def validate_template(self, template_string: str) -> tuple[bool, Optional[str]]:
        """
        Validate template syntax without rendering
        
        Args:
            template_string: Template content to validate
        
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            Template(template_string)
            return (True, None)
        except TemplateError as e:
            return (False, str(e))
        except Exception as e:
            return (False, f"Unexpected error: {e}")
    
    def get_template_variables(self, template_string: str) -> set:
        """
        Extract variable names from a template
        
        Args:
            template_string: Template content
        
        Returns:
            set: Set of variable names used in template
        """
        try:
            template = Template(template_string)
            # Get undeclared variables (variables not defined in template)
            variables = template.module.__dict__.get('undeclared_variables', set())
            return variables
        except Exception as e:
            self.logger.warning(f"Could not extract variables: {e}")
            return set()

