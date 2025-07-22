"""
Patcher module for PyInstaller compatibility with Streamlit.
This creates a version.py module that avoids the need for importlib.metadata
"""
import os
import sys
import shutil
import tempfile

def patch_streamlit():
    """Patch streamlit for PyInstaller compatibility"""
    import streamlit
    streamlit_dir = os.path.dirname(streamlit.__file__)
    version_path = os.path.join(streamlit_dir, 'version.py')
    
    # Create a backup of the original file
    if os.path.exists(version_path):
        with open(version_path, 'r') as f:
            original_content = f.read()
            
        # Create backup
        backup_path = version_path + '.bak'
        shutil.copy2(version_path, backup_path)
        
        # Create new content
        patched_content = f'''"""
Streamlit version module (patched for PyInstaller).
"""

# The version string
__version__ = "1.46.1"  # Hardcoded version
'''
        
        # Write patched file
        with open(version_path, 'w') as f:
            f.write(patched_content)
            
        print(f"Patched {version_path} for PyInstaller compatibility")
        return True
    
    return False

if __name__ == "__main__":
    # Run this script to apply the patch
    if patch_streamlit():
        print("Streamlit patched successfully!")
    else:
        print("Failed to patch Streamlit")
