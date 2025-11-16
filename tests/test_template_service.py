"""
Unit tests for template service
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from jinja2 import TemplateError

from app.services.template_service import TemplateService


class TestTemplateService:
    """Test cases for TemplateService"""
    
    @pytest.fixture
    def service(self):
        """Create template service instance"""
        return TemplateService()
    
    @pytest.fixture
    def service_no_datetime(self):
        """Create template service without auto datetime injection"""
        return TemplateService(auto_inject_datetime=False)
    
    def test_initialization(self):
        """Test service initialization"""
        service = TemplateService(auto_inject_datetime=True)
        assert service.auto_inject_datetime is True
        
        service2 = TemplateService(auto_inject_datetime=False)
        assert service2.auto_inject_datetime is False
    
    def test_render_string_simple(self, service):
        """Test rendering simple template"""
        template = "Hello {{ name }}!"
        params = {"name": "World"}
        
        result = service.render_string(template, params)
        
        assert result == "Hello World!"
    
    def test_render_string_with_auto_datetime(self, service):
        """Test that datetime is auto-injected"""
        template = "Date: {{ now.year }}"
        params = {}
        
        result = service.render_string(template, params)
        
        current_year = datetime.now().year
        assert f"Date: {current_year}" == result
    
    def test_render_string_without_auto_datetime(self, service_no_datetime):
        """Test rendering without auto datetime injection"""
        template = "Date: {{ now.year }}"
        params = {}
        
        # Should fail because 'now' is undefined
        with pytest.raises(TemplateError):
            service_no_datetime.render_string(template, params)
    
    def test_render_string_datetime_not_overridden(self, service):
        """Test that user-provided 'now' is not overridden"""
        template = "Year: {{ now }}"
        custom_now = "2099"
        params = {"now": custom_now}
        
        result = service.render_string(template, params)
        
        assert result == "Year: 2099"
    
    def test_render_string_with_loops(self, service):
        """Test rendering template with loops"""
        template = "{% for item in items %}{{ item }},{% endfor %}"
        params = {"items": ["a", "b", "c"]}
        
        result = service.render_string(template, params)
        
        assert result == "a,b,c,"
    
    def test_render_string_with_conditionals(self, service):
        """Test rendering template with conditionals"""
        template = "{% if show %}visible{% else %}hidden{% endif %}"
        
        result1 = service.render_string(template, {"show": True})
        assert result1 == "visible"
        
        result2 = service.render_string(template, {"show": False})
        assert result2 == "hidden"
    
    def test_render_string_syntax_error(self, service):
        """Test handling of template syntax errors"""
        template = "{{ unclosed"
        
        with pytest.raises(TemplateError):
            service.render_string(template, {})
    
    def test_render_string_undefined_variable(self, service):
        """Test handling of undefined variables"""
        template = "{{ undefined_var }}"
        
        # Jinja2 by default uses 'undefined' which returns empty string
        # To make it raise an error, we need StrictUndefined
        # But our service uses default behavior, so this should render as empty
        result = service.render_string(template, {})
        
        # Default Jinja2 behavior renders undefined as empty string
        assert result == ""
    
    def test_render_string_no_params(self, service):
        """Test rendering without parameters"""
        template = "Static content"
        
        result = service.render_string(template)
        
        assert result == "Static content"
    
    def test_render_file_simple(self, service):
        """Test rendering from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("<h1>Hello {{ name }}!</h1>")
            template_path = Path(f.name)
        
        try:
            result = service.render_file(template_path, {"name": "World"})
            assert result == "<h1>Hello World!</h1>"
        finally:
            template_path.unlink()
    
    def test_render_file_not_found(self, service):
        """Test rendering non-existent file"""
        template_path = Path("/nonexistent/template.html")
        
        with pytest.raises(FileNotFoundError):
            service.render_file(template_path, {})
    
    def test_render_file_with_base_dir(self, service):
        """Test rendering with custom base directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            template_file = base_dir / "template.html"
            template_file.write_text("Hello {{ name }}!")
            
            result = service.render_file(
                template_file,
                {"name": "Test"},
                base_dir=base_dir
            )
            
            assert result == "Hello Test!"
    
    def test_render_file_with_inheritance(self, service):
        """Test rendering with template inheritance"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            
            # Create base template
            base_template = base_dir / "base.html"
            base_template.write_text(
                "<html>{% block content %}default{% endblock %}</html>"
            )
            
            # Create child template
            child_template = base_dir / "child.html"
            child_template.write_text(
                "{% extends 'base.html' %}{% block content %}custom{% endblock %}"
            )
            
            result = service.render_file(child_template, {}, base_dir=base_dir)
            
            assert "<html>custom</html>" in result
    
    def test_render_file_with_includes(self, service):
        """Test rendering with template includes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            
            # Create partial template
            partial = base_dir / "partial.html"
            partial.write_text("<div>{{ content }}</div>")
            
            # Create main template
            main_template = base_dir / "main.html"
            main_template.write_text("{% include 'partial.html' %}")
            
            result = service.render_file(
                main_template,
                {"content": "test"},
                base_dir=base_dir
            )
            
            assert result == "<div>test</div>"
    
    def test_render_with_fallback_success(self, service):
        """Test fallback when file rendering succeeds"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("Hello {{ name }}!")
            template_path = Path(f.name)
        
        try:
            result = service.render_with_fallback(template_path, {"name": "World"})
            assert result == "Hello World!"
        finally:
            template_path.unlink()
    
    def test_render_with_fallback_uses_fallback(self, service):
        """Test fallback when file rendering fails"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            # Write template with extends that will fail in fallback
            f.write("{% extends 'nonexistent.html' %}{{ name }}")
            template_path = Path(f.name)
        
        try:
            # Should fail and try fallback (which will also fail for extends)
            with pytest.raises(TemplateError):
                service.render_with_fallback(template_path, {"name": "Test"})
        finally:
            template_path.unlink()
    
    def test_render_with_fallback_simple_template(self, service):
        """Test fallback succeeds for simple template"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            template_file = base_dir / "template.html"
            template_file.write_text("Simple {{ text }}")
            
            # Even if file rendering has issues, fallback should work
            result = service.render_with_fallback(
                template_file,
                {"text": "test"}
            )
            
            assert "Simple test" in result
    
    def test_validate_template_valid(self, service):
        """Test validating valid template"""
        template = "Hello {{ name }}!"
        
        is_valid, error = service.validate_template(template)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_template_invalid_syntax(self, service):
        """Test validating invalid template"""
        template = "{{ unclosed"
        
        is_valid, error = service.validate_template(template)
        
        assert is_valid is False
        assert error is not None
        assert "unexpected" in error.lower() or "expected" in error.lower()
    
    def test_validate_template_undefined_ok(self, service):
        """Test that undefined variables don't fail validation"""
        template = "{{ undefined_var }}"
        
        # Validation only checks syntax, not variable availability
        is_valid, error = service.validate_template(template)
        
        assert is_valid is True
    
    def test_prepare_context_adds_datetime(self, service):
        """Test that _prepare_context adds datetime"""
        params = {"key": "value"}
        
        context = service._prepare_context(params)
        
        assert "key" in context
        assert "now" in context
        assert isinstance(context["now"], datetime)
    
    def test_prepare_context_preserves_user_now(self, service):
        """Test that user-provided 'now' is preserved"""
        custom_now = "custom"
        params = {"now": custom_now}
        
        context = service._prepare_context(params)
        
        assert context["now"] == custom_now
    
    def test_prepare_context_no_datetime_injection(self, service_no_datetime):
        """Test _prepare_context without datetime injection"""
        params = {"key": "value"}
        
        context = service_no_datetime._prepare_context(params)
        
        assert "key" in context
        assert "now" not in context
    
    def test_complex_template_with_filters(self, service):
        """Test rendering template with Jinja2 filters"""
        template = "{{ name | upper }}"
        params = {"name": "hello"}
        
        result = service.render_string(template, params)
        
        assert result == "HELLO"
    
    def test_nested_data_structures(self, service):
        """Test rendering with nested data"""
        template = "{{ user.name }} - {{ user.email }}"
        params = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com"
            }
        }
        
        result = service.render_string(template, params)
        
        assert result == "John Doe - john@example.com"


class TestTemplateServiceIntegration:
    """Integration tests for template service"""
    
    def test_complex_invoice_template(self):
        """Test rendering complex invoice template"""
        service = TemplateService()
        
        template = """
        <html>
        <head><title>{{ title }}</title></head>
        <body>
            <h1>{{ title }}</h1>
            <p>Date: {{ now.strftime('%Y-%m-%d') }}</p>
            <table>
            {% for item in items %}
                <tr>
                    <td>{{ item.name }}</td>
                    <td>${{ "%.2f"|format(item.price) }}</td>
                </tr>
            {% endfor %}
            </table>
            <p>Total: ${{ "%.2f"|format(total) }}</p>
        </body>
        </html>
        """
        
        params = {
            "title": "Invoice #123",
            "items": [
                {"name": "Item A", "price": 10.50},
                {"name": "Item B", "price": 25.00}
            ],
            "total": 35.50
        }
        
        result = service.render_string(template, params)
        
        assert "Invoice #123" in result
        assert "Item A" in result
        assert "$10.50" in result
        assert "$35.50" in result
        assert datetime.now().strftime('%Y-%m-%d') in result
    
    def test_template_with_nested_includes(self):
        """Test template with multiple levels of includes"""
        service = TemplateService()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            
            # Create nested structure
            (base_dir / "header.html").write_text("<header>{{ title }}</header>")
            (base_dir / "footer.html").write_text("<footer>{{ year }}</footer>")
            (base_dir / "main.html").write_text(
                "{% include 'header.html' %}"
                "<main>Content</main>"
                "{% include 'footer.html' %}"
            )
            
            result = service.render_file(
                base_dir / "main.html",
                {"title": "Test", "year": 2024},
                base_dir=base_dir
            )
            
            assert "<header>Test</header>" in result
            assert "<main>Content</main>" in result
            assert "<footer>2024</footer>" in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

