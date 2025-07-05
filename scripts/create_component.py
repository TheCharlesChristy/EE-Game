from pathlib import Path

app_path = Path(__file__).parent.parent / "app"
components_path = app_path / "components"

def create_component(component_name: str):
    component_path = components_path / component_name
    if not component_path.exists():
        component_path.mkdir(parents=True)
        for extension in ['.js', '.css', '.html']:
            (component_path / f"{component_name}{extension}").touch()
        print(f"Component '{component_name}' created at {component_path}")
    else:
        print(f"Component '{component_name}' already exists at {component_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        component_name = input("Please enter the component name (leave empty to exit): ")
        if component_name:
            create_component(component_name)
    else:
        create_component(sys.argv[1])