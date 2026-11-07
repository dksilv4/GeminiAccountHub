"""
Gemini Multi-Account CLI Switcher & Quota Inspector
Usage:
  python cli.py list
  python cli.py switch <email>
  python cli.py refresh
  python cli.py add
"""

import sys
import gemini_auth
from datetime import datetime

def format_quota(q):
    if not q or 'groups' not in q:
        return "No quota data"
    lines = []
    for g in q.get('groups', []):
        lines.append(f"  [{g.get('displayName')}]")
        for b in g.get('buckets', []):
            pct = round(b.get('remainingFraction', 1.0) * 100)
            reset = b.get('resetTime', 'N/A')
            lines.append(f"    - {b.get('displayName')}: {pct}% remaining (Resets: {reset})")
    return "\n".join(lines)

def main():
    store = gemini_auth.AccountStore()
    active_email = store.get_active_email()

    if len(sys.argv) < 2 or sys.argv[1] in ('list', 'ls', 'status'):
        print("\n" + "=" * 65)
        print(" Gemini Multi-Account Quota & Switcher Status")
        print("=" * 65)
        print(f"Active Account in Antigravity: {active_email or 'None'}\n")
        
        for email, acc in store.accounts.items():
            is_active = (email.lower() == active_email.lower())
            status = "[ACTIVE]" if is_active else "[STANDBY]"
            name = acc.get('name', 'N/A')
            print(f"{status} {name} <{email}>")
            quota = acc.get('quota')
            if quota:
                print(format_quota(quota))
            else:
                print("  No quota fetched yet. Run 'python cli.py refresh'.")
            print("-" * 65)
        print()

    elif sys.argv[1] == 'switch':
        if len(sys.argv) < 3:
            print("Error: Specify email to switch to. e.g. python cli.py switch user@gmail.com")
            sys.exit(1)
        target = sys.argv[2]
        print(f"Switching active account to {target}...")
        success, res = store.switch_active_account(target, restart_language_server=True)
        if success:
            print(f"Success! Switched to {target}.")
            print("Antigravity credentials updated and language server restarted.")
        else:
            print(f"Failed to switch: {res}")
            sys.exit(1)

    elif sys.argv[1] == 'refresh':
        print("Refreshing quotas for all accounts from Google Cloud Code API...")
        for email in list(store.accounts.keys()):
            q, err = store.refresh_account_quota(email)
            if q:
                print(f"  + {email}: Updated successfully")
            else:
                print(f"  - {email}: Failed ({err})")
        print("Done!")

    elif sys.argv[1] == 'add':
        import server
        print("Starting local server to authenticate new Google account...")
        print("Opening browser for OAuth consent...")
        server.start_server(open_browser=True)

    else:
        print("Unknown command. Available commands: list, switch <email>, refresh, add")

if __name__ == '__main__':
    main()
