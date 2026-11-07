"""
Gemini Hub - Native Windows System Tray Companion
Runs in the Windows notification area with real-time quota tooltips,
one-click account switching menu, and threshold warning notifications.
Zero external pip dependencies (uses Win32 API via ctypes).
"""

import sys
import time
import json
import urllib.request
import webbrowser
import threading
import ctypes
from ctypes import wintypes

# Win32 Constants
WM_USER = 0x0400
WM_TRAYICON = WM_USER + 20
WM_COMMAND = 0x0111
WM_RBUTTONUP = 0x0205
WM_LBUTTONDBLCLK = 0x0203
WM_DESTROY = 0x0002

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002

NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010

NIIF_INFO = 0x00000001
NIIF_WARNING = 0x00000002

MF_STRING = 0x00000000
MF_SEPARATOR = 0x00000800
MF_CHECKED = 0x00000008
TPM_RIGHTBUTTON = 0x0002

IDI_APPLICATION = 32512

class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
    ]

# Win32 Function definitions
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32

DefWindowProcW = user32.DefWindowProcW
RegisterClassExW = user32.RegisterClassExW
CreateWindowExW = user32.CreateWindowExW
DestroyWindow = user32.DestroyWindow
PostQuitMessage = user32.PostQuitMessage
GetMessageW = user32.GetMessageW
TranslateMessage = user32.TranslateMessage
DispatchMessageW = user32.DispatchMessageW
CreatePopupMenu = user32.CreatePopupMenu
AppendMenuW = user32.AppendMenuW
DestroyMenu = user32.DestroyMenu
TrackPopupMenu = user32.TrackPopupMenu
GetCursorPos = user32.GetCursorPos
SetForegroundWindow = user32.SetForegroundWindow
LoadIconW = user32.LoadIconW
Shell_NotifyIconW = shell32.Shell_NotifyIconW

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HICON),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]

class GeminiTrayApp:
    def __init__(self, api_base="http://127.0.0.1:54321"):
        self.api_base = api_base
        self.hwnd = None
        self.nid = None
        self.hicon = LoadIconW(None, IDI_APPLICATION)
        self.accounts_cache = []
        self.active_email = ""
        self.running = True
        self.cmd_map = {}  # menu ID -> email
        self.next_cmd_id = 1000

    def query_api(self, endpoint, method="GET", data=None):
        try:
            url = f"{self.api_base}{endpoint}"
            body = json.dumps(data).encode('utf-8') if data else None
            req = urllib.request.Request(url, data=body, method=method)
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception:
            return None

    def update_status(self):
        data = self.query_api("/api/accounts")
        if data:
            self.active_email = data.get("active_email", "")
            self.accounts_cache = data.get("accounts", [])
            # Find active quota
            active_acc = next((a for a in self.accounts_cache if a.get('is_active')), None)
            pct_5h = "--"
            if active_acc and active_acc.get('quota'):
                groups = active_acc['quota'].get('groups', [])
                gem_grp = next((g for g in groups if 'gemini' in g.get('displayName', '').lower()), None)
                if gem_grp:
                    b5h = next((b for b in gem_grp.get('buckets', []) if '5h' in b.get('bucketId', '')), None)
                    if b5h:
                        pct_5h = f"{round(b5h.get('remainingFraction', 1) * 100)}%"

            tip_text = f"Gemini Hub: {self.active_email}\n5-Hour Limit: {pct_5h}"
            self.set_tooltip(tip_text[:127])

    def set_tooltip(self, text):
        if self.nid:
            self.nid.uFlags = NIF_TIP
            self.nid.szTip = text
            Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self.nid))

    def show_notification(self, title, msg, is_warning=False):
        if self.nid:
            self.nid.uFlags = NIF_INFO
            self.nid.szInfoTitle = title[:63]
            self.nid.szInfo = msg[:255]
            self.nid.dwInfoFlags = NIIF_WARNING if is_warning else NIIF_INFO
            Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self.nid))

    def build_and_show_menu(self):
        hmenu = CreatePopupMenu()
        self.cmd_map.clear()
        self.next_cmd_id = 1000

        # Title / Open Dashboard
        AppendMenuW(hmenu, MF_STRING, 1, "Gemini Account Hub (Open Dashboard)")
        AppendMenuW(hmenu, MF_STRING, 2, "Refresh All Quotas")
        AppendMenuW(hmenu, MF_SEPARATOR, 0, None)

        # Accounts List for Switching
        if self.accounts_cache:
            AppendMenuW(hmenu, MF_STRING, 0, "--- Switch Active Account ---")
            for acc in self.accounts_cache:
                cmd_id = self.next_cmd_id
                self.next_cmd_id += 1
                email = acc.get('email', '')
                is_active = acc.get('is_active', False)
                self.cmd_map[cmd_id] = email

                # Format quota
                pct = ""
                gem_grp = next((g for g in (acc.get('quota') or {}).get('groups', []) if 'gemini' in g.get('displayName', '').lower()), None)
                if gem_grp:
                    b5h = next((b for b in gem_grp.get('buckets', []) if '5h' in b.get('bucketId', '')), None)
                    if b5h:
                        pct = f" ({round(b5h.get('remainingFraction', 1)*100)}% 5h)"

                flags = MF_CHECKED if is_active else MF_STRING
                label = f"{'✓ ' if is_active else '   '}{email}{pct}"
                AppendMenuW(hmenu, flags, cmd_id, label)
        else:
            AppendMenuW(hmenu, MF_STRING, 0, "No accounts connected")

        AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
        AppendMenuW(hmenu, MF_STRING, 99, "Exit Tray")

        # Track popup menu at mouse cursor
        pt = wintypes.POINT()
        GetCursorPos(ctypes.byref(pt))
        SetForegroundWindow(self.hwnd)
        TrackPopupMenu(hmenu, TPM_RIGHTBUTTON, pt.x, pt.y, 0, self.hwnd, None)
        DestroyMenu(hmenu)

    def on_command(self, cmd_id):
        if cmd_id == 1:
            webbrowser.open("http://127.0.0.1:54321")
        elif cmd_id == 2:
            self.query_api("/api/accounts/refresh-all", method="POST")
            self.update_status()
            self.show_notification("Quotas Refreshed", "All Gemini account limits updated.")
        elif cmd_id in self.cmd_map:
            target_email = self.cmd_map[cmd_id]
            if target_email.lower() != self.active_email.lower():
                res = self.query_api("/api/accounts/switch", method="POST", data={"email": target_email, "restart_language_server": True})
                if res and res.get('success'):
                    self.show_notification("Switched Account", f"Active account switched to {target_email}.")
                else:
                    self.show_notification("Switch Failed", f"Could not switch to {target_email}.", is_warning=True)
                self.update_status()
        elif cmd_id == 99:
            self.cleanup()
            PostQuitMessage(0)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAYICON:
            if lparam == WM_RBUTTONUP:
                self.update_status()
                self.build_and_show_menu()
            elif lparam == WM_LBUTTONDBLCLK:
                webbrowser.open("http://127.0.0.1:54321")
            return 0
        elif msg == WM_COMMAND:
            self.on_command(wparam & 0xFFFF)
            return 0
        elif msg == WM_DESTROY:
            self.cleanup()
            PostQuitMessage(0)
            return 0
        return DefWindowProcW(hwnd, msg, wparam, lparam)

    def cleanup(self):
        if self.nid:
            Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self.nid))
            self.nid = None

    def start(self):
        # Register window class
        cls_name = "GeminiTrayClass"
        self._wndproc = WNDPROC(self.wnd_proc)

        wndclass = WNDCLASSEXW()
        wndclass.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wndclass.style = 0
        wndclass.lpfnWndProc = self._wndproc
        wndclass.cbClsExtra = 0
        wndclass.cbWndExtra = 0
        wndclass.hInstance = kernel32.GetModuleHandleW(None)
        wndclass.hIcon = self.hicon
        wndclass.hCursor = None
        wndclass.hbrBackground = None
        wndclass.lpszMenuName = None
        wndclass.lpszClassName = cls_name
        wndclass.hIconSm = self.hicon

        RegisterClassExW(ctypes.byref(wndclass))

        self.hwnd = CreateWindowExW(
            0, cls_name, "Gemini Tray Hidden Window",
            0, 0, 0, 0, 0, None, None, wndclass.hInstance, None
        )

        # Create notify icon
        self.nid = NOTIFYICONDATAW()
        self.nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        self.nid.hWnd = self.hwnd
        self.nid.uID = 1
        self.nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        self.nid.uCallbackMessage = WM_TRAYICON
        self.nid.hIcon = self.hicon
        self.nid.szTip = "Gemini Account & Quota Hub"

        Shell_NotifyIconW(NIM_ADD, ctypes.byref(self.nid))
        self.update_status()

        # Background updater thread
        def poll_loop():
            while self.running:
                time.sleep(30)
                try:
                    self.update_status()
                except Exception:
                    pass
        threading.Thread(target=poll_loop, daemon=True).start()

        # Win32 Message Loop
        msg = wintypes.MSG()
        while GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            TranslateMessage(ctypes.byref(msg))
            DispatchMessageW(ctypes.byref(msg))

if __name__ == '__main__':
    print("Starting Gemini Hub Windows System Tray App...")
    app = GeminiTrayApp()
    app.start()
