# 🦁 Macan Download Manager Pro

Macan Download Manager Pro is a modern and professional download manager application based on Python + PySide6 (Qt6).

Developed by Danx Exodus under the Macan Angkasa Independent Technology Ecosystem, this application delivers multi-threaded performance, a dark modern UI, and a fast, stable, and elegant download experience.

---

## 🚀 Key Features

### ⚡ Performance and Stability
- Multi-threaded downloader based on requests and QThread, with a dynamic queue system.
- Automatic resume support using the HTTP Range Header.
- Speed ​​limit control and maximum concurrent downloads can be set in settings.
- Auto-retry system with up to three attempts when the connection fails.

### 🎨 Modern Interface
- **Dark modern theme** typical of Macan Angkasa.
- Toolbar with **SVG vector icons** (Play, Pause, Stop, Settings, etc.).
- **Sidebar filter** (All, Downloading, Paused, Finished, Error).
- **Animated progress bar** and real-time speed indicator.
- **Search bar** to filter files by name.

### ⚙️ Complete Management
- Add new URLs directly through an interactive dialog.
- Download categories (General, Video, Music, Documents, Software).
- **Pause / Resume / Stop / Retry / Stop All** functions.
- Automatically save the download list to a JSON file.
- Open downloaded files or folders directly from the application.

### 🖥️ System Integration
- **System Tray Icon**: the application remains running in the background.
- **Download completion notification** automatically appears from the tray.
- Drag & Drop: Simply drag the URL into the application window to start downloading.
- Minimize to Tray on Close — users can set their preferences.

---
## 📸 Screenshot
<img width="1000" height="630" alt="Screenshot 2025-10-25 200355" src="https://github.com/user-attachments/assets/0fd5f473-e1b8-4b4e-b155-8aca3d2cfcef" />
<img width="1000" height="635" alt="Screenshot 2025-10-25 200520" src="https://github.com/user-attachments/assets/01e8d252-fc66-4092-9a5d-8eeefe78eada" />



---
## 📝 Changelog v4.7.0
- Update framework




---
## 💼 Technologies Used

| Components | Technology |
|-----------|------------|
| Framework | PySide6 (Qt for Python) |
| Engine | QThread, Qt MVC Model Architecture |
| Networking | Requests |
| Storage | JSON Persistent Storage |
| Icons | SVG Inline Renderer |
| Notifications | QSystemTrayIcon |
| Compatibility | Windows / Linux / macOS |

---

## 🧠 Internal Architecture

This application is built on the principles of modularity and event-drivenness:
- **Model / View / Controller (Qt MVC)** — a clear separation between data, logic, and display.
- **Threaded Worker System** — each download process runs independently on its own thread.
- **Signal-Slot Mechanism** — real-time communication between components for lag-free progress updates.

---

🧩 Settings
Through the Settings → Preferences menu, you can set:

Default download folder

Maximum number of simultaneous downloads

Global speed limit (KB/s)

Minimize to system tray mode

---

🏆 Advantages Compared to Other Download Managers

Does not depend on external CLI libraries (such as wget or aria2c).

Can be run completely independently without additional installation.

Supports download categories and advanced filtering.

Designed with Macan Angkasa's professional UI/UX.

Open source and can be further developed by the community.

---

📜 License
MIT License
© 2026 Macan Angkasa Independent Technology Ecosystem
