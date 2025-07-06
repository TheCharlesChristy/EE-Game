#!/usr/bin/env python3
"""
Quick setup script to make EEGame imports persistent.
Run this once to enable imports like: from EEGame.app.server import SomeModule
"""

import sys
import site
from pathlib import Path

def setup_persistent_path():
    """Create a .pth file for persistent Python path."""
    # Get the EEGame workspace path
    script_dir = Path(__file__).parent.absolute()
    workspace_root = script_dir.parent
    workspace_path = str(workspace_root.parent)
    
    # Get user site-packages directory (doesn't require admin privileges)
    user_site = site.getusersitepackages()
    
    # Create user site-packages if it doesn't exist
    Path(user_site).mkdir(parents=True, exist_ok=True)
    
    # Create the .pth file
    pth_file = Path(user_site) / "EEGame.pth"
    
    try:
        with open(pth_file, 'w') as f:
            f.write(f"{workspace_path}\n")
        
        print(f"✓ Created persistent path file: {pth_file}")
        print(f"✓ Added path: {workspace_path}")
        print("\n🎉 Setup complete! EEGame imports will now work in all Python sessions.")
        print("\nTest it by opening a new Python session and running:")
        print("  from EEGame.app.server.EEtypes import *")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("Setting up persistent Python path for EEGame...")
    setup_persistent_path()
