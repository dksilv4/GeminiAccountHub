# Contributing to Gemini Account Hub

Thank you for your interest in contributing! This project is dedicated to providing a lightweight, borderless, zero-dependency tool for developers using Google Antigravity & Gemini code models.

---

## 🛠️ Architecture Principles

1. **Zero External Dependencies**:
   - The core application strictly relies on Python 3.10+ standard library (`ctypes`, `http.server`, `urllib`, `json`, `winreg`, `threading`).
   - Please avoid adding external pip packages (like `requests`, `pystray`, `flask`) unless absolutely necessary and optional.
2. **Win32 & Windows Credential Manager Security**:
   - Tokens must always remain 100% local. Never transmit or log tokens anywhere outside `127.0.0.1` and Google's official OAuth endpoints.
3. **Tasteful & Minimal UI**:
   - No garish neon glows or boxy borders. Maintain calm, elegant glassmorphic surfaces and high-contrast typography.

---

## 🚀 Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/gemini-account-hub.git
   cd gemini-account-hub
   ```

2. **Run in Development Mode**:
   ```bash
   # Run server in debug mode:
   python server.py

   # Or run full app with System Tray:
   python app.py
   ```

3. **CLI commands**:
   ```bash
   python cli.py list
   python cli.py refresh
   ```

---

## 📬 Pull Request Guidelines

1. Ensure code follows PEP 8 conventions.
2. Verify all UI components render cleanly on both light and dark themes.
3. Test account hot-swapping and ensure language server re-authentication operates cleanly.
4. Submit pull requests with descriptive titles and summaries.
