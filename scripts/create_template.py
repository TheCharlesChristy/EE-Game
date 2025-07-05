from pathlib import Path

app_path = Path(__file__).parent.parent / "app"
templates_path = app_path / "templates"

def create_template(template_name: str):
    template_path = templates_path / template_name
    if not template_path.exists():
        template_path.mkdir(parents=True)
        for extension in ['.js', '.css', '.html']:
            (template_path / f"{template_name}{extension}").touch()
        print(f"template '{template_name}' created at {template_path}")
    else:
        print(f"template '{template_name}' already exists at {template_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        template_name = input("Please enter the template name (leave empty to exit): ")
        if template_name:
            create_template(template_name)
    else:
        create_template(sys.argv[1])