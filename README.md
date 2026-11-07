# Gemini Account Hub & Local Switcher 🚀

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white)](#)
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Stdlib%20Only)-success)](#)
[![Package Size](https://img.shields.io/badge/Release%20Size-~33%20KB-orange)](#)

**A lightweight, borderless desktop dashboard and local switcher for multiple Google accounts and Gemini coding quotas in Google Antigravity.**

[Features](#-key-features) • [Installation](#-1-click-installation) • [How It Works](#-how-it-works-under-the-hood) • [Security & Privacy](#-security--privacy)

</div>

---

## 💡 Why Gemini Account Hub?

When coding with **Google Antigravity** and Gemini models (Flash, Pro, Claude Sonnet), heavy developers frequently hit:
- Rolling **5-Hour Capacity Limits**
- Individual **Weekly Tier Quotas**

**Gemini Account Hub** allows you to connect multiple Google accounts, inspect live remaining quota fractions and exact reset countdowns, and **hot-swap your active account locally with a single click** without manual logins or IDE restarts.

---

## ✨ Key Features

- **Multi-Account Google OAuth**: Sign in to unlimited Google accounts directly through official Google OAuth consent screens (`prompt=select_account`).
- **Real-Time Quota Telemetry**:
  - Direct integration with Google Cloud Code's internal quota API (`retrieveUserQuotaSummary`).
  - **5-Hour Rolling Limit**: Remaining capacity percentage + live countdown timer until reset.
  - **Weekly Tier Limit**: Remaining cycle percentage + refresh date.
  - Multi-group support: Gemini Models (Flash, Pro) and partner models (Claude 3.5 Sonnet, Opus, GPT-OSS).
- **1-Click Local Hot-Swap**:
  - Updates Windows Credential Manager (`gemini:antigravity`).
  - Synchronizes Antigravity's internal storage (`jetski.onboarding.lastLoginUsername`).
  - Signals Antigravity's language server to reload credentials in ~1.5s — no need to restart your IDE manually.
- **Smart Quota Guard (Auto-Switch)**:
  - Background watchdog that detects when your active account's 5-hour quota falls below 5%.
  - Automatically switches Antigravity to the standby account with the highest available capacity.
- **Native Windows System Tray Companion**:
  - Sits quietly in your notification area (by the system clock).
  - Hover tooltip displays active account & live quota (e.g., `Gemini Hub: user@gmail.com (91% 5h)`).
  - Right-click menu to switch accounts or refresh quotas on the fly.
- **Lightweight Standalone App Mode**:
  - Runs in a clean, borderless window via Windows Edge WebView engine (`--app=...`).
  - No browser address bars or tabs.
  - Closes to tray so background monitors remain active.
- **Windows Startup Integration**:
  - Option to automatically start on boot, either minimized to tray or open as a window.
- **Zero External Dependencies**:
  - Built 100% with the Python 3.10+ Standard Library (`ctypes`, `http.server`, `urllib`, `winreg`, `json`, `threading`).
  - **No `pip install` required!** Runs out of the box on Windows 10 & 11.

---

## 🚀 1-Click Installation

### Option 1: Download Release Archive (Recommended)
1. Download the latest `Gemini-Account-Hub-v1.0.0.zip` from [Releases](https://github.com/your-username/gemini-account-hub/releases).
2. Extract the folder anywhere.
3. Double-click **`install.bat`** (or run `.\install.ps1` in PowerShell).

*That's it! It automatically verifies Python, creates a Desktop shortcut, and launches the app in your system tray.*

### Option 2: Clone from Git
```bash
git clone https://github.com/your-username/gemini-account-hub.git
cd gemini-account-hub

# Launch the app
python app.py
```

---

## 🖥️ Usage

### Desktop Application
- Double-click **`Gemini Hub`** on your Desktop or run **`Launch_Gemini_Hub.bat`**.
- The app will start silently in the background and appear in your System Tray.
- Right-click the tray icon to switch accounts or open the full dashboard.

### Web Dashboard
You can also access the full visual dashboard from any browser:
👉 **[http://localhost:54321](http://localhost:54321)**

### Terminal CLI
If you prefer terminal commands:
```bash
# View all accounts and quota percentages:
python cli.py list

# Seamlessly switch active account:
python cli.py switch user@gmail.com

# Force refresh quota from Google's servers:
python cli.py refresh

# Add another Google account:
python cli.py add
```

---

## ⚙️ How It Works Under The Hood

```
   ┌─────────────────────────────────────────────────────────────┐
   │                    Gemini Account Hub                       │
   │                                                             │
   │  ┌────────────────────┐          ┌───────────────────────┐  │
   │  │   System Tray      │          │  Standalone App Window │  │
   │  │ (Win32 Shell Notify│          │    (Edge App Mode)    │  │
   │  └─────────┬──────────┘          └───────────┬───────────┘  │
   │            │                                 │              │
   │            └────────────────┬────────────────┘              │
   │                             ▼                               │
   │             ┌───────────────────────────────┐               │
   │             │   Local Embedded HTTP API     │               │
   │             │       (127.0.0.1:54321)       │               │
   │             └───────────────┬───────────────┘               │
   └─────────────────────────────┼───────────────────────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌──────────────────────────────┐              ┌──────────────────────┐
│  Windows Credential Manager  │              │  Google Cloud Code   │
│     (gemini:antigravity)     │              │    Quota Endpoint    │
│  + Antigravity app_storage   │              │  (daily-cloudcode-pa)│
└──────────────────────────────┘              └──────────────────────┘
```

1. **OAuth Authentication**: Uses Google OAuth 2.0 with Antigravity client credentials. When you authenticate an account, refresh tokens are saved locally in `~/.gemini/multi_accounts.json`.
2. **Live Telemetry**: Queries `https://daily-cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary` with OAuth Bearer tokens to inspect precise remaining fractions (`remainingFraction`) and reset timestamps (`resetTime`).
3. **Local Switching**: Uses Windows Win32 API `Advapi32.dll` (`CredWriteW`) to update the persistent `gemini:antigravity` generic credential, updates `app_storage.json`, and triggers the Antigravity language server to reload credentials cleanly.

---

## 🔒 Security & Privacy

- **100% Local**: All tokens, credentials, and settings remain strictly on your local machine in Windows Credential Manager and `~/.gemini/multi_accounts.json`.
- **No Third-Party Servers**: Requests are made solely between your machine and official Google API endpoints (`accounts.google.com`, `daily-cloudcode-pa.googleapis.com`, `oauth2.googleapis.com`).
- **Localhost Bound**: The internal API server binds strictly to `127.0.0.1` and is completely inaccessible from external networks.

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on code style and testing.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
