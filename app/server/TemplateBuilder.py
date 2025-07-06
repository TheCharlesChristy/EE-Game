"""
TemplateBuilder Class - Multi-Team Gaming System
===============================================

A simple Python utility that builds HTML templates with component CSS/JS embedded.

Usage:
1. Instantiate with component directory: builder = TemplateBuilder("app/components")
2. Call build_template with template name: html = builder.build_template("HomePage")

Returns complete HTML string with all component CSS and JS embedded inline.

Author: Multi-Team Gaming System Development Team
Version: 2.0.0 MVP (Ultra-Simplified)
"""

import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


class TemplateBuilder:
    """
    Simple template builder that loads templates and embeds component CSS/JS.
    
    Simple workflow:
    1. Load template by name
    2. Find components referenced in template
    3. Embed component CSS and JS directly into HTML
    4. Return complete HTML string
    """
    
    def __init__(self, components_root: str = "components"):
        """Initialize with component directory path."""
        # Get the base app directory (parent of server directory)
        app_dir = Path(__file__).parent.parent
        
        self.components_root = app_dir / components_root
        self.templates_root = app_dir / "templates"
        
        print(f"TemplateBuilder initialized:")
        print(f"  App dir: {app_dir}")
        print(f"  Components root: {self.components_root}")
        print(f"  Templates root: {self.templates_root}")
        print(f"  Templates root exists: {self.templates_root.exists()}")
        
        # Setup Jinja2 environment with absolute paths
        self.jinja_env = Environment(
            loader=FileSystemLoader([str(self.templates_root), str(app_dir)]),
            autoescape=True
        )
        
        # Verify directories exist
        if not self.components_root.exists():
            raise FileNotFoundError(f"Components directory not found: {self.components_root}")
        if not self.templates_root.exists():
            raise FileNotFoundError(f"Templates directory not found: {self.templates_root}")
    
    def build_template(self, template_name: str) -> str:
        """
        Build complete template with component CSS and JS injected.
        
        Args:
            template_name: Name of the template (e.g., "HomePage")
            
        Returns:
            Complete HTML string with component includes rendered and CSS/JS embedded
        """
        # Load and render the template with Jinja2 to process includes
        template_path = f"{template_name}/{template_name}.html"
        
        try:
            template = self.jinja_env.get_template(template_path)
            html = template.render()
        except Exception as e:
            raise FileNotFoundError(f"Template not found or error rendering: {template_path} - {e}")
        
        # Find components referenced in the original template (before rendering)
        template_file_path = self.templates_root / template_name / f"{template_name}.html"
        with open(template_file_path, 'r', encoding='utf-8') as f:
            original_html = f.read()
        
        components = self._find_components(original_html)
        
        # Load global CSS first
        global_css = self._load_global_css()
        css_content = []
        js_content = []
        
        if global_css.strip():
            css_content.append(f"/* Global Styles */\n{global_css}")

        # Add global JS if it exists
        global_js_file = Path("app/globals.js")
        if global_js_file.exists():
            with open(global_js_file, 'r', encoding='utf-8') as f:
                global_js = f.read()
            if global_js.strip():
                js_content.append(f"/* Global Scripts */\n{global_js}")

        # Add template CSS
        template_css_file = self.templates_root / template_name / f"{template_name}.css"
        if template_css_file.exists():
            with open(template_css_file, 'r', encoding='utf-8') as f:
                template_css = f.read()
            if template_css.strip():
                css_content.append(f"/* {template_name} Template Styles */\n{template_css}")

        # Add the template JS
        template_js_file = self.templates_root / template_name / f"{template_name}.js"
        if template_js_file.exists():
            with open(template_js_file, 'r', encoding='utf-8') as f:
                template_js = f.read()
            if template_js.strip():
                js_content.append(f"/* {template_name} Template Scripts */\n{template_js}")
        
        # Load CSS and JS for each component
        for component_name in components:
            css = self._load_component_css(component_name)
            js = self._load_component_js(component_name)
            
            if css.strip():
                css_content.append(f"/* {component_name} Component */\n{css}")
            
            if js.strip():
                js_content.append(f"/* {component_name} Component */\n{js}")
        
        # Inject CSS and JS directly into HTML
        if css_content:
            combined_css = '\n\n'.join(css_content)
            html = self._inject_css_styles(html, combined_css)
        
        if js_content:
            combined_js = '\n\n'.join(js_content)
            html = self._inject_js_scripts(html, combined_js)
        
        return html
    
    def _find_components(self, html: str) -> list:
        """Find component names from Jinja2 includes."""
        pattern = r'{%\s*include\s+["\']components/(\w+)/\w+\.html["\'].*?%}'
        return list(set(re.findall(pattern, html, re.IGNORECASE)))
    
    def _load_global_css(self) -> str:
        """Load global CSS file."""
        css_file = Path("app/globals.css")
        if css_file.exists():
            with open(css_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _load_component_css(self, component_name: str) -> str:
        """Load CSS content for a component."""
        css_file = self.components_root / component_name / f"{component_name}.css"
        if css_file.exists():
            with open(css_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _load_component_js(self, component_name: str) -> str:
        """Load JavaScript content for a component."""
        js_file = self.components_root / component_name / f"{component_name}.js"
        if js_file.exists():
            with open(js_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _inject_css_styles(self, html: str, css_content: str) -> str:
        """Inject CSS styles directly into HTML."""
        css_block = f'<style>\n{css_content}\n</style>'
        
        if "<!-- CSS INJECTION POINT -->" in html:
            return html.replace("<!-- CSS INJECTION POINT -->", f"\n    {css_block}\n")
        elif "</head>" in html:
            return html.replace("</head>", f"\n    {css_block}\n</head>")
        else:
            return f"{css_block}\n{html}"
    
    def _inject_js_scripts(self, html: str, js_content: str) -> str:
        """Inject JavaScript directly into HTML."""
        js_block = f'<script>\n{js_content}\n</script>'
        
        if "<!-- JS INJECTION POINT -->" in html:
            return html.replace("<!-- JS INJECTION POINT -->", f"\n    {js_block}\n")
        elif "</body>" in html:
            return html.replace("</body>", f"\n    {js_block}\n</body>")
        else:
            return f"{html}\n{js_block}"


# Simple usage example
if __name__ == "__main__":
    try:
        builder = TemplateBuilder("app/components")
        html = builder.build_template("HomePage")
        print(f"✓ Built HomePage template: {len(html):,} characters")
        print("✓ All component CSS and JS embedded directly in HTML")
        # Save the HTML to a file for verification
        output_path = Path("output/HomePage.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("This is expected when running without the full project structure.")