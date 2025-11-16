"""
PDF generation service using WeasyPrint
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any

from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from app.utils.logger import get_logger, LoggerMixin


logger = get_logger(__name__)


class PDFService(LoggerMixin):
    """
    Service for generating PDFs from HTML
    """
    
    def __init__(self):
        """Initialize PDF service"""
        self.font_config = FontConfiguration()
        self.logger.info("PDFService initialized")
    
    def generate_pdf(
        self,
        html_content: str,
        output_path: Path,
        base_url: Optional[str] = None
    ) -> Path:
        """
        Generate PDF from HTML content
        
        Args:
            html_content: Rendered HTML content
            output_path: Path where PDF should be saved
            base_url: Base URL for resolving relative paths
        
        Returns:
            Path: Path to generated PDF file
        
        Raises:
            Exception: If PDF generation fails
        """
        try:
            self.logger.debug(f"Generating PDF: {output_path.name}")
            
            # Create HTML object
            html = HTML(
                string=html_content,
                base_url=base_url
            )
            
            # Generate PDF
            html.write_pdf(
                str(output_path),
                font_config=self.font_config
            )
            
            # Get file size
            file_size = output_path.stat().st_size / 1024  # KB
            self.logger.info(
                f"PDF generated successfully: {output_path.name} ({file_size:.1f} KB)"
            )
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"PDF generation failed: {e}", exc_info=True)
            raise
    
    def generate_pdf_from_file(
        self,
        html_file: Path,
        output_path: Path,
        base_url: Optional[str] = None
    ) -> Path:
        """
        Generate PDF from HTML file
        
        Args:
            html_file: Path to HTML file
            output_path: Path where PDF should be saved
            base_url: Base URL for resolving relative paths
        
        Returns:
            Path: Path to generated PDF file
        """
        if not html_file.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file}")
        
        html_content = html_file.read_text()
        return self.generate_pdf(html_content, output_path, base_url)
    
    def load_params(self, params_file: Path) -> Dict[str, Any]:
        """
        Load parameters from JSON file
        
        Args:
            params_file: Path to params.json
        
        Returns:
            dict: Parameters dictionary
        """
        if not params_file.exists():
            self.logger.warning(f"Params file not found: {params_file}")
            return {}
        
        try:
            with open(params_file, 'r') as f:
                params = json.load(f)
            self.logger.debug(f"Loaded {len(params)} parameters")
            return params
        except Exception as e:
            self.logger.error(f"Error loading params: {e}")
            return {}
    
    def get_pdf_info(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """
        Get information about a PDF file
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            dict: PDF information or None if file doesn't exist
        """
        if not pdf_path.exists():
            return None
        
        try:
            stat = pdf_path.stat()
            return {
                'path': str(pdf_path),
                'size_bytes': stat.st_size,
                'size_kb': stat.st_size / 1024,
                'size_mb': stat.st_size / (1024 * 1024),
                'exists': True
            }
        except Exception as e:
            self.logger.error(f"Error getting PDF info: {e}")
            return None

