"""
Builds a clean zip distribution for GitHub Releases.
"""

import os
import zipfile
import shutil

VERSION = "1.0.0"
DIST_DIR = os.path.abspath("dist")
OUTPUT_ZIP = os.path.join(DIST_DIR, f"Gemini-Account-Hub-v{VERSION}.zip")

# Files and directories to include in release
INCLUDE_FILES = [
    "app.py",
    "server.py",
    "gemini_auth.py",
    "tray.py",
    "cli.py",
    "setup_shortcut.py",
    "install.bat",
    "install.ps1",
    "Launch_Gemini_Hub.bat",
    "launch_silent.vbs",
    "Open_Dashboard.bat",
    "start_dashboard.bat",
    "start_dashboard.ps1",
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "requirements.txt",
    "pyproject.toml"
]

INCLUDE_DIRS = [
    "web"
]

def build_release():
    os.makedirs(DIST_DIR, exist_ok=True)
    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)

    print(f"Creating release archive: {OUTPUT_ZIP}...")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in INCLUDE_FILES:
            if os.path.exists(f):
                zipf.write(f, f)
                print(f"  + Added file: {f}")

        for d in INCLUDE_DIRS:
            for root, _, files in os.walk(d):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, ".")
                    zipf.write(full_path, rel_path)
                    print(f"  + Added file: {rel_path}")

    size_kb = os.path.getsize(OUTPUT_ZIP) / 1024
    print(f"\n[SUCCESS] Package created successfully!")
    print(f"Location: {OUTPUT_ZIP}")
    print(f"Size: {size_kb:.1f} KB")

if __name__ == "__main__":
    build_release()
