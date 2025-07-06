#!/usr/bin/env python3
"""
Script to add the EE-Game directory to the Python path.
This allows modules within the project to be imported correctly when running scripts directly.
"""

import sys
import os
from pathlib import Path

def add_project_to_path():
    """Add the EE-Game project root directory to Python path."""
    # Get the directory where this script is located (project root)
    script_dir = Path(__file__).parent.parent.absolute()
    project_root = str(script_dir)
    
    # Add to Python path if not already present
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added {project_root} to Python path")
    else:
        print(f"Project root {project_root} already in Python path")
    
    return project_root

if __name__ == "__main__":
    # When run directly, just add the path and show current Python path
    project_root = add_project_to_path()
    print("\nCurrent Python path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    
    print(f"\nProject root: {project_root}")
    print("You can now import modules from the EE-Game project structure.")
