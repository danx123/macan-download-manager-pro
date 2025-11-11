import sys
import os
import time
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QLabel, QTableWidget, QHeaderView, QAbstractItemView,
    QTableWidgetItem, QProgressBar, QDialog, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QSplitter
)
from PySide6.QtGui import QIcon, QAction, QColor, QPainter, QPixmap
from PySide6.QtCore import Qt, QSize, QThread, QObject, Signal, Slot
from PySide6.QtSvg import QSvgRenderer

# --- SVG ICONS (Tetap sama) ---
SVG_ADD_URL = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>"""
SVG_START = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>"""
SVG_PAUSE = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>"""
SVG_STOP = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><rect x="9" y="9" width="6" height="6"></rect></svg>"""
SVG_SETTINGS = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V12a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>"""

# --- Helper Functions (Tetap sama) ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def create_svg_icon(svg_xml, color="white"):
    svg_bytes = svg_xml.replace('stroke="currentColor"', f'stroke="{color}"').encode('utf-8')
    renderer = QSvgRenderer(svg_bytes)
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)
    
def format_size(size_bytes):
    """Formats size in bytes to a human-readable string."""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(size_bytes).bit_length() // 10
    power = 1024 ** i
    size = round(size_bytes / power, 2)
    return f"{size} {size_name[i]}"

# --- Download Worker (DITINGKATKAN) ---
class DownloadWorker(QObject):
    started = Signal(int, int)  # row, total_size
    progress = Signal(int, int) # row, downloaded_size
    finished = Signal(int)
    error = Signal(int, str)

    def __init__(self, row, url, filepath, headers=None):
        super().__init__()
        self.row = row
        self.url = url
        self.filepath = filepath
        self.headers = headers or {}
        self.is_running = True
        self.is_paused = False

    @Slot()
    def run(self):
        try:
            with requests.get(self.url, stream=True, timeout=15, headers=self.headers) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                self.started.emit(self.row, total_size)

                downloaded_size = 0
                with open(self.filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        while self.is_paused:
                            time.sleep(0.5)
                        
                        if not self.is_running or not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        self.progress.emit(self.row, downloaded_size)
            
            if self.is_running:
                self.finished.emit(self.row)

        except requests.exceptions.RequestException as e:
            self.error.emit(self.row, f"Network Error: {e}")
        except Exception as e:
            self.error.emit(self.row, str(e))

    def stop(self):
        self.is_running = False

    def toggle_pause(self):
        self.is_paused = not self.is_paused

# --- Add Download Dialog (Sama) ---
class AddDownloadDialog(QDialog):
    # ... (Tidak ada perubahan, salin dari kode asli)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Download")
        self.setMinimumWidth(500)
        self.layout = QVBoxLayout(self)
        self.url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/file.zip")
        self.layout.addWidget(self.url_label)
        self.layout.addWidget(self.url_input)
        self.path_layout = QHBoxLayout()
        self.path_label = QLabel("Save to:")
        self.path_input = QLineEdit(os.path.join(os.path.expanduser("~"), "Downloads"))
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_path)
        self.path_layout.addWidget(self.path_label)
        self.path_layout.addWidget(self.path_input)
        self.path_layout.addWidget(self.browse_button)
        self.layout.addLayout(self.path_layout)
        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Download")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)
        self.ok_button.setStyleSheet("padding: 5px 15px;")
        self.cancel_button.setStyleSheet("padding: 5px 15px;")
    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Folder")
        if directory:
            self.path_input.setText(directory)
    def get_data(self):
        return self.url_input.text(), self.path_input.text()

# --- Main Application Window (DITINGKATKAN SECARA SIGNIFIKAN) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macan Download Manager Pro")
        self.resize(1000, 600)
        app_icon_path = resource_path('icon.ico')
        if os.path.exists(app_icon_path):
             self.setWindowIcon(QIcon(app_icon_path))
        else:
            print(f"Warning: icon.ico not found at {app_icon_path}")
        
        # {row: {'thread': QThread, 'worker': DownloadWorker, 'total_size': int, 'downloaded': int, 'start_time': float}}
        self.downloads = {} 

        self.setup_ui()
        self.apply_stylesheet()

    def setup_ui(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        action_add = QAction(create_svg_icon(SVG_ADD_URL), "Add URL", self)
        action_add.triggered.connect(self.show_add_download_dialog)
        toolbar.addAction(action_add)

        self.action_pause = QAction(create_svg_icon(SVG_PAUSE), "Pause Selected", self)
        # self.action_pause.triggered.connect(self.pause_selected_download)
        toolbar.addAction(self.action_pause)
        
        self.action_stop = QAction(create_svg_icon(SVG_STOP), "Stop Selected", self)
        # self.action_stop.triggered.connect(self.stop_selected_download)
        toolbar.addAction(self.action_stop)
        
        toolbar.addSeparator()

        action_settings = QAction(create_svg_icon(SVG_SETTINGS), "Settings", self)
        toolbar.addAction(action_settings)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItems(["All", "Downloading", "Finished", "Error"])
        splitter.addWidget(self.sidebar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "Total Size", "Status", "Speed", "Time Left", "Date Added"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        splitter.addWidget(self.table)
        splitter.setSizes([200, 800])
        main_layout.addWidget(splitter)
        
        # Ganti dengan ini
        self.statusBar().showMessage("Ready")

    def show_add_download_dialog(self):
        dialog = AddDownloadDialog(self)
        if dialog.exec():
            url, path = dialog.get_data()
            if url and path:
                # Cek jika direktori ada, jika tidak buatkan
                if not os.path.exists(path):
                    try:
                        os.makedirs(path)
                    except OSError as e:
                        QMessageBox.critical(self, "Error", f"Could not create directory: {path}\n{e}")
                        return
                
                filename = url.split('/')[-1] or "download"
                filepath = os.path.join(path, filename)
                self.add_download_to_table(url, filepath)

    def add_download_to_table(self, url, filepath):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(os.path.basename(filepath)))
        self.table.setItem(row, 1, QTableWidgetItem("...")) 
        
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        progress_bar.setFormat("Connecting...")
        self.table.setCellWidget(row, 2, progress_bar)
        
        self.table.setItem(row, 3, QTableWidgetItem("N/A"))
        self.table.setItem(row, 4, QTableWidgetItem("N/A"))
        self.table.setItem(row, 5, QTableWidgetItem(time.strftime("%Y-%m-%d %H:%M")))

        self.start_download(row, url, filepath)
    
    def start_download(self, row, url, filepath):
        thread = QThread()
        worker = DownloadWorker(row, url, filepath)
        
        self.downloads[row] = {
            'thread': thread, 
            'worker': worker,
            'total_size': 0,
            'downloaded': 0,
            'start_time': time.time(),
            'last_update_time': time.time(),
            'last_downloaded_size': 0
        }

        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        worker.started.connect(self.on_download_started)
        worker.progress.connect(self.update_progress)
        worker.finished.connect(self.on_download_finished)
        worker.error.connect(self.on_download_error)

        thread.start()

    @Slot(int, int)
    def on_download_started(self, row, total_size):
        self.downloads[row]['total_size'] = total_size
        self.table.item(row, 1).setText(format_size(total_size))
        self.statusBar().showMessage(f"Starting download for {self.table.item(row, 0).text()}...", 5000)

    @Slot(int, int)
    def update_progress(self, row, downloaded_size):
        if row not in self.downloads: return
        
        state = self.downloads[row]
        state['downloaded'] = downloaded_size
        total_size = state['total_size']
        
        progress_bar = self.table.cellWidget(row, 2)
        if progress_bar:
            percentage = 0
            if total_size > 0:
                percentage = int((downloaded_size / total_size) * 100)
                progress_bar.setFormat(f"{format_size(downloaded_size)} / {format_size(total_size)}")
            else: # Ukuran file tidak diketahui (stream)
                progress_bar.setFormat(f"{format_size(downloaded_size)}")
                progress_bar.setRange(0,0) # Indeterminate progress
            
            progress_bar.setValue(percentage)

        # Kalkulasi kecepatan dan sisa waktu
        current_time = time.time()
        if current_time - state['last_update_time'] >= 1: # Update tiap 1 detik
            elapsed_since_last = current_time - state['last_update_time']
            bytes_since_last = downloaded_size - state['last_downloaded_size']
            
            speed_bps = bytes_since_last / elapsed_since_last if elapsed_since_last > 0 else 0
            
            self.table.item(row, 3).setText(f"{format_size(speed_bps)}/s")
            
            time_left_str = "N/A"
            if speed_bps > 0 and total_size > 0:
                remaining_bytes = total_size - downloaded_size
                time_left_sec = remaining_bytes / speed_bps
                mins, secs = divmod(time_left_sec, 60)
                time_left_str = f"{int(mins)}m {int(secs)}s"
            self.table.item(row, 4).setText(time_left_str)

            state['last_update_time'] = current_time
            state['last_downloaded_size'] = downloaded_size


    @Slot(int)
    def on_download_finished(self, row):
        progress_bar = self.table.cellWidget(row, 2)
        if progress_bar:
            progress_bar.setValue(100)
            progress_bar.setFormat("Finished")
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #2ECC71; }")
        
        self.table.item(row, 3).setText("✓")
        self.table.item(row, 4).setText("-")
        self.statusBar().showMessage(f"Download completed: {self.table.item(row, 0).text()}", 5000)
        del self.downloads[row]

    @Slot(int, str)
    def on_download_error(self, row, error_message):
        progress_bar = self.table.cellWidget(row, 2)
        if progress_bar:
            progress_bar.setFormat(f"Error")
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #E74C3C; }")
        
        self.statusBar().showMessage(f"Error on row {row+1}: {error_message}", 10000)
        if row in self.downloads:
            del self.downloads[row]

    def closeEvent(self, event):
        for row, data in self.downloads.items():
            if data['thread'].isRunning():
                data['worker'].stop()
                data['thread'].quit()
                data['thread'].wait(2000) # Tunggu maks 2 detik
        event.accept()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            /* ... (Salin stylesheet dari kode asli, tidak ada perubahan) ... */
            QMainWindow, QDialog { background-color: #262626; color: #FFFFFF; }
            QToolBar { background-color: #333333; border: none; padding: 5px; }
            QToolBar QToolButton { padding: 6px; margin: 2px; border-radius: 4px; }
            QToolBar QToolButton:hover { background-color: #454545; }
            QListWidget { background-color: #2F2F2F; border: none; font-size: 14px; }
            QListWidget::item { padding: 10px 15px; }
            QListWidget::item:selected, QListWidget::item:hover { background-color: #4A4A4A; border-left: 3px solid #8E44AD; }
            QTableWidget { background-color: #262626; border: none; gridline-color: #454545; color: #E0E0E0; }
            QHeaderView::section { background-color: #333333; color: white; padding: 4px; border: 1px solid #454545; font-weight: bold; }
            QTableWidget::item { padding-left: 5px; }
            QProgressBar { border: 1px solid #454545; border-radius: 4px; text-align: center; color: white; }
            QProgressBar::chunk { background: QLinearGradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8E44AD, stop:1 #9B59B6); border-radius: 4px; }
            QLineEdit, QPushButton { padding: 5px; background-color: #333; border: 1px solid #555; border-radius: 4px; }
            QPushButton { background-color: #8E44AD; font-weight: bold; }
            QPushButton:hover { background-color: #9B59B6; }
            QStatusBar { color: white; font-weight: bold; }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())