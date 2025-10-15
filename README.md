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
<img width="1002" height="634" alt="Screenshot 2025-10-13 001945" src="https://github.com/user-attachments/assets/8209afe5-f9e1-4228-9adb-99e80c993a2c" />
<img width="1003" height="628" alt="Screenshot 2025-10-13 002001" src="https://github.com/user-attachments/assets/4d03d80f-f424-4d26-86c4-f78b53bc3ca5" />
<img width="1002" height="629" alt="Screenshot 2025-10-13 002015" src="https://github.com/user-attachments/assets/14c256f2-bea1-45dc-aa5a-462e3c97d945" />
<img width="1001" height="635" alt="Screenshot 2025-10-13 002029" src="https://github.com/user-attachments/assets/5fe0211c-2782-4fb6-8324-9b892001790c" />

---
## 📝 Changelog v3.0.0
This update brings significant improvements in download speed and stability with the implementation of Multi-Connection Download (Split Download) and improvements to the Windows Autostart feature.

- Major New Features & Improvements
Multi-Connection Download (Split Download):
Implements a new Download Manager mechanism that can split files into multiple connections (splits) for simultaneous downloads. This can significantly increase download speeds (depending on the server).
Adds a new field/option (splits) to download items to set the number of connections.
DownloadWorker has been refactored to handle downloads by byte range.
Server capability checks (Accept-Ranges) are performed in a separate thread to avoid freezing the main UI when adding downloads.
Windows Autostart Improvements:
Fixed Windows Autostart logic to work correctly for both script (.py) and executable (.exe) builds.
The "Start with Windows" configuration implementation in the Settings Dialog has been fully integrated.

- UI/UX Improvements & Improvements
Download Progress Dialog Improvements:
The download progress dialog window (DownloadProgressDialog) has been widened (minimum height 350px to 380px) to accommodate more detailed connection/split information.
Junk File Cleanup:
Improved the download deletion logic to ensure that part files (.part0, .part1, etc.) created during the split download process are also deleted when the item is removed from the list and the physical file is deleted.
Code Improvements:
The dialog code structure (macan_dialog.py) has been simplified by removing unnecessary comments related to modularization, demonstrating cleaner component separation.
Added threading imports and new PySide6 widgets such as QFileIconProvider to support multi-connection features and improved file display.

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
© 2025 Macan Angkasa Independent Technology Ecosystem
