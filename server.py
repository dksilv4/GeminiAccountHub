"""
Gemini Multi-Account Dashboard & Local Switcher Server
Runs a local web server providing real-time quota tracking,
multi-account Google OAuth sign-in, and instant local account switching.
"""

import os
import sys
import json
import time
import urllib.parse
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading

import gemini_auth

PORT = 54321
HOST = "127.0.0.1"
REDIRECT_URI = f"http://{HOST}:{PORT}/oauth/callback"

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

store = gemini_auth.AccountStore()

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Static assets fallback
        if path == "/" or path == "/index.html":
            self.send_index()
            return
        elif path == "/oauth/callback":
            self.handle_oauth_callback(query)
            return
        elif path == "/api/status":
            self.handle_api_status()
            return
        elif path == "/api/accounts":
            self.handle_api_accounts()
            return
        elif path == "/api/auth/start":
            self.handle_api_auth_start(query)
            return
        elif path == "/api/app/config":
            self.handle_api_app_config()
            return
        
        # Serve static file if exists
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = b"{}"
        if content_length > 0:
            post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data.decode('utf-8')) if post_data else {}
        except Exception:
            body = {}

        if path == "/api/accounts/switch":
            self.handle_account_switch(body)
            return
        elif path == "/api/accounts/refresh":
            self.handle_account_refresh(body)
            return
        elif path == "/api/accounts/refresh-all":
            self.handle_account_refresh_all()
            return
        elif path == "/api/accounts/delete":
            self.handle_account_delete(body)
            return
        elif path == "/api/settings":
            self.handle_update_settings(body)
            return
        elif path == "/api/apikey/save":
            self.handle_apikey_save(body)
            return
        elif path == "/api/apikey/test":
            self.handle_apikey_test(body)
            return
        elif path == "/api/apikey/activate":
            self.handle_apikey_activate(body)
            return
        elif path == "/api/accounts/manual-add":
            self.handle_manual_account_add(body)
            return
        elif path == "/api/app/config":
            self.handle_update_app_config(body)
            return
        elif path == "/api/app/open-window":
            gemini_auth.launch_desktop_window()
            self.send_json_response({"success": True})
            return

        self.send_json_response({"error": "Endpoint not found"}, status=404)

    def send_json_response(self, data, status=200):
        resp_bytes = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)

    def send_index(self):
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "index.html not found")

    def handle_api_status(self):
        active_email = store.get_active_email()
        sys_key = gemini_auth.get_current_system_gemini_api_key()
        masked_key = (sys_key[:6] + "..." + sys_key[-4:]) if len(sys_key) > 10 else ("Set" if sys_key else "Not Set")
        self.send_json_response({
            "status": "online",
            "active_email": active_email,
            "total_accounts": len(store.accounts),
            "system_gemini_api_key": masked_key,
            "settings": store.settings
        })

    def handle_api_accounts(self):
        store.load()
        active_email = store.get_active_email()
        accounts_list = []
        for email, acc in store.accounts.items():
            acc_copy = dict(acc)
            # Hide secret tokens from frontend
            acc_copy.pop('refresh_token', None)
            acc_copy.pop('access_token', None)
            acc_copy.pop('id_token', None)
            acc_copy['is_active'] = (email.lower() == active_email.lower())
            accounts_list.append(acc_copy)

        # Sort: active account first, then by email
        accounts_list.sort(key=lambda x: (not x['is_active'], x['email']))

        self.send_json_response({
            "active_email": active_email,
            "accounts": accounts_list,
            "settings": store.settings
        })

    def handle_api_auth_start(self, query):
        """Generates Google OAuth URL with prompt=select_account so the user can choose any account."""
        state = f"gemini_hub_{int(time.time())}"
        scope_str = " ".join(gemini_auth.SCOPES)
        auth_url = (
            f"{gemini_auth.AUTH_ENDPOINT}?"
            f"client_id={gemini_auth.CLIENT_ID}&"
            f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
            f"response_type=code&"
            f"scope={urllib.parse.quote(scope_str)}&"
            f"access_type=offline&"
            f"prompt=select_account&"
            f"state={state}"
        )
        auto_open = query.get('open', ['false'])[0].lower() == 'true'
        if auto_open:
            webbrowser.open(auth_url)

        self.send_json_response({
            "auth_url": auth_url,
            "redirect_uri": REDIRECT_URI
        })

    def handle_oauth_callback(self, query):
        code = query.get('code', [None])[0]
        error = query.get('error', [None])[0]

        if error or not code:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Authentication Failed</title></head>
            <body style="background:#0f172a;color:#f87171;font-family:sans-serif;text-align:center;padding:50px;">
                <h2>Authentication Failed</h2>
                <p>Google OAuth returned error: {error or 'No code returned'}</p>
                <p><a href="/" style="color:#60a5fa;">Return to Dashboard</a></p>
            </body>
            </html>
            """
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return

        try:
            # Exchange code for tokens
            token_resp = gemini_auth.exchange_auth_code(code, REDIRECT_URI)
            access_tok = token_resp.get('access_token')
            refresh_tok = token_resp.get('refresh_token')
            id_token = token_resp.get('id_token', '')

            if not access_tok:
                raise Exception("Missing access_token from token endpoint")

            # Fetch user profile
            profile = gemini_auth.fetch_user_profile(access_tok)
            user_email = profile.get('email')

            if not user_email:
                raise Exception("Could not fetch user email from Google Profile")

            # Fetch initial quota
            quota = None
            try:
                quota = gemini_auth.fetch_quota_summary(access_tok)
            except Exception as q_err:
                print(f"Warning: Initial quota fetch failed for {user_email}: {q_err}", file=sys.stderr)

            # Save to store
            store.add_or_update_account(
                email=user_email,
                refresh_token=refresh_tok,
                access_token=access_tok,
                id_token=id_token,
                profile=profile,
                quota=quota
            )

            # Redirect back to home with success
            self.send_response(302)
            self.send_header("Location", f"/?login_success={urllib.parse.quote(user_email)}")
            self.end_headers()

        except Exception as e:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Authentication Error</title></head>
            <body style="background:#0f172a;color:#f87171;font-family:sans-serif;text-align:center;padding:50px;">
                <h2>Authentication Error</h2>
                <p>{str(e)}</p>
                <p><a href="/" style="color:#60a5fa;">Return to Dashboard</a></p>
            </body>
            </html>
            """
            self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

    def handle_account_switch(self, body):
        email = body.get('email')
        restart_ls = body.get('restart_language_server', True)
        if not email:
            self.send_json_response({"error": "Missing email"}, status=400)
            return

        success, result = store.switch_active_account(email, restart_language_server=restart_ls)
        if success:
            self.send_json_response({
                "success": True,
                "active_email": email,
                "result": result
            })
        else:
            self.send_json_response({
                "success": False,
                "error": str(result)
            }, status=500)

    def handle_account_refresh(self, body):
        email = body.get('email')
        if not email:
            self.send_json_response({"error": "Missing email"}, status=400)
            return

        quota, err = store.refresh_account_quota(email)
        if quota:
            self.send_json_response({
                "success": True,
                "email": email,
                "quota": quota
            })
        else:
            self.send_json_response({
                "success": False,
                "error": err
            }, status=500)

    def handle_account_refresh_all(self):
        results = {}
        for email in list(store.accounts.keys()):
            quota, err = store.refresh_account_quota(email)
            results[email] = {"success": bool(quota), "quota": quota, "error": err}
        self.send_json_response({
            "success": True,
            "results": results
        })

    def handle_account_delete(self, body):
        email = body.get('email')
        if not email:
            self.send_json_response({"error": "Missing email"}, status=400)
            return

        active_email = store.get_active_email()
        if email.lower() == active_email.lower():
            self.send_json_response({
                "error": "Cannot remove the currently active Antigravity account. Switch to another account first."
            }, status=400)
            return

        success = store.remove_account(email)
        self.send_json_response({"success": success})

    def handle_update_settings(self, body):
        if "auto_refresh_seconds" in body:
            store.settings["auto_refresh_seconds"] = int(body["auto_refresh_seconds"])
        if "auto_switch_enabled" in body:
            store.settings["auto_switch_enabled"] = bool(body["auto_switch_enabled"])
        if "auto_switch_threshold" in body:
            store.settings["auto_switch_threshold"] = float(body["auto_switch_threshold"])
        store.save()
        self.send_json_response({"success": True, "settings": store.settings})

    def handle_apikey_save(self, body):
        email = body.get('email')
        api_key = body.get('api_key', '').strip()
        if not email or not api_key:
            self.send_json_response({"error": "Missing email or api_key"}, status=400)
            return

        success = store.set_account_api_key(email, api_key)
        self.send_json_response({"success": success})

    def handle_apikey_test(self, body):
        api_key = body.get('api_key', '').strip()
        if not api_key:
            self.send_json_response({"error": "Missing api_key"}, status=400)
            return

        valid, models = gemini_auth.test_gemini_api_key(api_key)
        self.send_json_response({
            "valid": valid,
            "models": models if valid else [],
            "error": None if valid else models
        })

    def handle_apikey_activate(self, body):
        api_key = body.get('api_key', '').strip()
        if not api_key:
            self.send_json_response({"error": "Missing api_key"}, status=400)
            return

        success = gemini_auth.set_system_gemini_api_key(api_key)
        self.send_json_response({"success": success})

    def handle_manual_account_add(self, body):
        refresh_token = body.get('refresh_token', '').strip()
        if not refresh_token:
            self.send_json_response({"error": "Missing refresh_token"}, status=400)
            return

        try:
            tokens = gemini_auth.refresh_access_token(refresh_token)
            access_tok = tokens.get('access_token')
            if not access_tok:
                raise Exception("Failed to acquire access_token from refresh_token")

            profile = gemini_auth.fetch_user_profile(access_tok)
            email = profile.get('email')
            if not email:
                raise Exception("Could not fetch user email")

            quota = None
            try:
                quota = gemini_auth.fetch_quota_summary(access_tok)
            except Exception:
                pass

            acc = store.add_or_update_account(
                email=email,
                refresh_token=refresh_token,
                access_token=access_tok,
                profile=profile,
                quota=quota
            )
            self.send_json_response({"success": True, "account": acc})
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, status=400)

    def handle_api_app_config(self):
        reg_enabled, reg_minimized = gemini_auth.get_startup_status()
        self.send_json_response({
            "run_on_startup": reg_enabled,
            "start_minimized": reg_minimized or store.settings.get("start_minimized", True),
            "edge_installed": bool(gemini_auth.get_edge_path())
        })

    def handle_update_app_config(self, body):
        enabled = bool(body.get("run_on_startup", False))
        minimized = bool(body.get("start_minimized", True))

        store.settings["run_on_startup"] = enabled
        store.settings["start_minimized"] = minimized
        store.save()

        success = gemini_auth.set_startup_status(enabled=enabled, start_minimized=minimized)
        self.send_json_response({
            "success": success,
            "run_on_startup": enabled,
            "start_minimized": minimized
        })




def background_quota_watcher():
    """Periodically refreshes quotas and executes auto-switch if enabled and threshold breached."""
    while True:
        try:
            refresh_interval = store.settings.get("auto_refresh_seconds", 60)
            if refresh_interval > 0:
                time.sleep(refresh_interval)
            else:
                time.sleep(60)

            # Refresh all accounts
            active_email = store.get_active_email()
            active_quota = None

            for email in list(store.accounts.keys()):
                q, _ = store.refresh_account_quota(email)
                if email.lower() == active_email.lower():
                    active_quota = q

            # Check Auto-Switch
            if store.settings.get("auto_switch_enabled", False) and active_quota and len(store.accounts) > 1:
                threshold = store.settings.get("auto_switch_threshold", 0.05)
                # Find lowest remaining fraction in active account's Gemini group
                active_remaining = 1.0
                for group in active_quota.get('groups', []):
                    if 'gemini' in group.get('displayName', '').lower():
                        for b in group.get('buckets', []):
                            rem = b.get('remainingFraction', 1.0)
                            if rem < active_remaining:
                                active_remaining = rem

                if active_remaining < threshold:
                    print(f"[Auto-Switch] Active account {active_email} quota below threshold ({active_remaining:.1%} < {threshold:.1%})!")
                    # Find candidate account with highest quota
                    best_email = None
                    best_remaining = -1.0
                    for cand_email, cand_acc in store.accounts.items():
                        if cand_email.lower() == active_email.lower():
                            continue
                        cand_quota = cand_acc.get('quota')
                        if not cand_quota:
                            continue
                        cand_min_rem = 1.0
                        for g in cand_quota.get('groups', []):
                            if 'gemini' in g.get('displayName', '').lower():
                                for b in g.get('buckets', []):
                                    r = b.get('remainingFraction', 1.0)
                                    if r < cand_min_rem:
                                        cand_min_rem = r
                        if cand_min_rem > best_remaining:
                            best_remaining = cand_min_rem
                            best_email = cand_email

                    if best_email and best_remaining > active_remaining:
                        print(f"[Auto-Switch] Seamlessly switching to {best_email} (has {best_remaining:.1%} quota)...")
                        store.switch_active_account(best_email, restart_language_server=True)

        except Exception as e:
            print(f"Error in background quota watcher: {e}", file=sys.stderr)
            time.sleep(10)


def start_server(port=PORT, open_browser=True):
    # Ensure initial quota for active account is fresh
    active_email = store.get_active_email()
    if active_email:
        store.refresh_account_quota(active_email)

    # Start background watcher thread
    watcher = threading.Thread(target=background_quota_watcher, daemon=True)
    watcher.start()

    server = ThreadingHTTPServer((HOST, port), DashboardHandler)
    url = f"http://{HOST}:{port}"
    print("=" * 60)
    print(f"  Gemini Multi-Account Quota & Switcher Hub")
    print(f"  Running at: {url}")
    print(f"  Active Antigravity Account: {store.get_active_email()}")
    print("=" * 60)

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gemini Multi-Account Dashboard & Switcher")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port to run on (default: {PORT})")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open the browser")
    args = parser.parse_args()

    start_server(port=args.port, open_browser=not args.no_browser)
