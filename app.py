"""
Gemini Multi-Account Hub - Standalone Lightweight Windows Application
Integrates:
  1. Embedded ultra-light HTTP server
  2. Native Windows System Tray Companion
  3. Standalone Borderless Desktop Window (Edge app mode)
  4. Run on Startup & Start Minimized preferences
"""

import os
import sys
import time
import socket
import threading
import subprocess
from datetime import datetime

import gemini_auth
import server
import tray

APP_PORT = server.PORT
APP_URL = f"http://127.0.0.1:{APP_PORT}"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_background_server():
    if not is_port_in_use(APP_PORT):
        print(f"[App] Starting embedded server on port {APP_PORT}...")
        server_thread = threading.Thread(
            target=lambda: server.start_server(port=APP_PORT, open_browser=False),
            daemon=True
        )
        server_thread.start()
        # Wait until port is ready
        for _ in range(20):
            if is_port_in_use(APP_PORT):
                break
            time.sleep(0.1)
    else:
        print(f"[App] Server already listening on port {APP_PORT}.")

class GeminiDesktopApp(tray.GeminiTrayApp):
    def __init__(self, start_minimized=False):
        super().__init__(api_base=APP_URL)
        self.start_minimized = start_minimized

    def on_command(self, cmd_id):
        # Override commands for app-specific actions
        if cmd_id == 1:
            # Open Desktop Window
            gemini_auth.launch_desktop_window(APP_URL)
        elif cmd_id == 80:
            # Toggle Run on Startup
            curr, min_state = gemini_auth.get_startup_status()
            gemini_auth.set_startup_status(enabled=not curr, start_minimized=min_state)
            self.show_notification(
                "Startup Preference",
                "Gemini Hub will start with Windows." if not curr else "Removed from Windows startup."
            )
        elif cmd_id == 81:
            # Toggle Smart Auto-Switch
            is_auto = server.store.settings.get("auto_switch_enabled", False)
            server.store.settings["auto_switch_enabled"] = not is_auto
            server.store.save()
            self.show_notification(
                "Smart Auto-Switch",
                "Auto-switch enabled." if not is_auto else "Auto-switch disabled."
            )
        else:
            super().on_command(cmd_id)

    def build_and_show_menu(self):
        hmenu = tray.CreatePopupMenu()
        self.cmd_map.clear()
        self.next_cmd_id = 1000

        # Title
        tray.AppendMenuW(hmenu, tray.MF_STRING, 1, "Open Gemini Hub Window")
        tray.AppendMenuW(hmenu, tray.MF_STRING, 2, "Refresh All Quotas")
        tray.AppendMenuW(hmenu, tray.MF_SEPARATOR, 0, None)

        # Accounts List
        if self.accounts_cache:
            tray.AppendMenuW(hmenu, tray.MF_STRING, 0, "--- Switch Active Account ---")
            for acc in self.accounts_cache:
                cmd_id = self.next_cmd_id
                self.next_cmd_id += 1
                email = acc.get('email', '')
                is_active = acc.get('is_active', False)
                self.cmd_map[cmd_id] = email

                # Quota fraction
                pct = ""
                gem_grp = next((g for g in (acc.get('quota') or {}).get('groups', []) if 'gemini' in g.get('displayName', '').lower()), None)
                if gem_grp:
                    b5h = next((b for b in gem_grp.get('buckets', []) if '5h' in b.get('bucketId', '')), None)
                    if b5h:
                        pct = f" ({round(b5h.get('remainingFraction', 1)*100)}% 5h)"

                flags = tray.MF_CHECKED if is_active else tray.MF_STRING
                label = f"{'✓ ' if is_active else '   '}{email}{pct}"
                tray.AppendMenuW(hmenu, flags, cmd_id, label)

        tray.AppendMenuW(hmenu, tray.MF_SEPARATOR, 0, None)

        # System Preferences
        is_startup, _ = gemini_auth.get_startup_status()
        startup_flag = tray.MF_CHECKED if is_startup else tray.MF_STRING
        tray.AppendMenuW(hmenu, startup_flag, 80, "Run on Windows Startup")

        is_auto = server.store.settings.get("auto_switch_enabled", False)
        auto_flag = tray.MF_CHECKED if is_auto else tray.MF_STRING
        tray.AppendMenuW(hmenu, auto_flag, 81, "Smart Auto-Switch (Low Quota)")

        tray.AppendMenuW(hmenu, tray.MF_SEPARATOR, 0, None)
        tray.AppendMenuW(hmenu, tray.MF_STRING, 99, "Exit Gemini Hub")

        pt = tray.wintypes.POINT()
        tray.GetCursorPos(tray.ctypes.byref(pt))
        tray.SetForegroundWindow(self.hwnd)
        tray.TrackPopupMenu(hmenu, tray.TPM_RIGHTBUTTON, pt.x, pt.y, 0, self.hwnd, None)
        tray.DestroyMenu(hmenu)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == tray.WM_TRAYICON:
            if lparam == tray.WM_LBUTTONDBLCLK or lparam == 0x0202:  # Single click or double click
                gemini_auth.launch_desktop_window(APP_URL)
                return 0
        return super().wnd_proc(hwnd, msg, wparam, lparam)


def main():
    start_minimized = ("--minimized" in sys.argv) or ("--startup" in sys.argv)

    # 1. Start embedded server if needed
    start_background_server()

    # 2. Launch window if not starting minimized
    if not start_minimized:
        gemini_auth.launch_desktop_window(APP_URL)

    # 3. Enter System Tray message loop
    print("[App] Running in Windows System Tray...")
    desktop_app = GeminiDesktopApp(start_minimized=start_minimized)
    desktop_app.start()


if __name__ == "__main__":
    main()
