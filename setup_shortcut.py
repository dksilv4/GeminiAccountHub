"""
Cross-user Windows Desktop Shortcut Creator for Gemini Account Hub.
"""

import os
import sys
import subprocess

def get_desktop_dir():
    userprofile = os.environ.get("USERPROFILE", "")
    candidates = [
        os.path.join(userprofile, "OneDrive", "Desktop"),
        os.path.join(userprofile, "Desktop"),
    ]
    for d in candidates:
        if os.path.exists(d):
            return d
    return os.path.join(userprofile, "Desktop")

def create_desktop_shortcut():
    desktop = get_desktop_dir()
    base_dir = os.path.abspath(os.path.dirname(__file__))
    target_bat = os.path.join(base_dir, "Launch_Gemini_Hub.bat")
    shortcut_path = os.path.join(desktop, "Gemini Hub.lnk")

    vbs_content = f"""Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target_bat}"
oLink.WorkingDirectory = "{base_dir}"
oLink.Description = "Gemini Multi-Account Quota Hub"
oLink.Save
"""
    vbs_path = os.path.join(base_dir, "_temp_shortcut.vbs")
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)

        subprocess.run(["cscript", "//nologo", vbs_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"[OK] Created Desktop Shortcut: {shortcut_path}")
        return True
    except Exception as e:
        print(f"[Warning] Could not create Desktop shortcut: {e}", file=sys.stderr)
        return False
    finally:
        if os.path.exists(vbs_path):
            try:
                os.remove(vbs_path)
            except Exception:
                pass

if __name__ == "__main__":
    create_desktop_shortcut()
