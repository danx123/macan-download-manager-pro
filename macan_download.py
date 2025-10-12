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

# --- SVG ICONS (XML Embedded) ---
# Menggunakan icon dari Feather Icons (https://feathericons.com/)
SVG_ADD_URL = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-plus-circle">
  <circle cx="12" cy="12" r="10"></circle>
  <line x1="12" y1="8" x2="12" y2="16"></line>
  <line x1="8" y1="12" x2="16" y2="12"></line>
</svg>
"""

SVG_START = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-play">
  <polygon points="5 3 19 12 5 21 5 3"></polygon>
</svg>
"""

SVG_STOP = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-pause">
  <rect x="6" y="4" width="4" height="16"></rect>
  <rect x="14" y="4" width="4" height="16"></rect>
</svg>
"""

SVG_SETTINGS = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-settings">
  <circle cx="12" cy="12" r="3"></circle>
  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V12a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
</svg>
"""

# --- Helper Function for PyInstaller (_MEIPASS) ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Helper Function to Create Icon from SVG XML ---
def create_svg_icon(svg_xml, color="white"):
    """Creates a QIcon from an SVG XML string."""
    # Replace stroke color
    svg_xml_colored = svg_xml.replace('stroke="currentColor"', f'stroke="{color}"')
    
    # Use QByteArray to load XML data
    svg_bytes = svg_xml_colored.encode('utf-8')
    
    renderer = QSvgRenderer(svg_bytes)
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return QIcon(pixmap)

# --- Download Worker (Handles download in a separate thread) ---
class DownloadWorker(QObject):
    progress = Signal(int, int, float, str)  # row, bytes_downloaded, speed_mbps, time_left_str
    finished = Signal(int)
    error = Signal(int, str)

    def __init__(self, row, url, filepath):
        super().__init__()
        self.row = row
        self.url = url
        self.filepath = filepath
        self.is_running = True

    @Slot()
    def run(self):
        try:
            with requests.get(self.url, stream=True, timeout=10) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                start_time = time.time()
                last_update_time = start_time
                last_downloaded_size = 0

                with open(self.filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not self.is_running:
                            break
                        
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            current_time = time.time()
                            elapsed_time_since_update = current_time - last_update_time
                            
                            if elapsed_time_since_update >= 1: # Update speed every second
                                speed_bytes_per_sec = (downloaded_size - last_downloaded_size) / elapsed_time_since_update
                                speed_mbps = speed_bytes_per_sec / (1024 * 1024)
                                
                                time_left_str = "Calculating..."
                                if speed_bytes_per_sec > 0:
                                    remaining_bytes = total_size - downloaded_size
                                    time_left_sec = remaining_bytes / speed_bytes_per_sec
                                    mins, secs = divmod(time_left_sec, 60)
                                    time_left_str = f"{int(mins)} m {int(secs)} s left"
                                
                                self.progress.emit(self.row, downloaded_size, speed_mbps, time_left_str)
                                
                                last_update_time = current_time
                                last_downloaded_size = downloaded_size

            if self.is_running:
                self.finished.emit(self.row)
        except Exception as e:
            self.error.emit(self.row, str(e))

# --- Add Download Dialog ---
class AddDownloadDialog(QDialog):
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

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macan Download Manager")
        
        # Menggunakan _MEIPASS helper untuk icon aplikasi
        app_icon_path = resource_path('icon.ico')
        if os.path.exists(app_icon_path):
             self.setWindowIcon(QIcon(app_icon_path))
        else:
            print(f"Warning: icon.ico not found at {app_icon_path}")

        self.resize(1000, 600)

        self.downloads = {} # {row: (thread, worker)}

        self.setup_ui()
        self.apply_stylesheet()

    def setup_ui(self):
        # --- Toolbar ---
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        action_add = QAction(create_svg_icon(SVG_ADD_URL), "Add URL", self)
        action_add.triggered.connect(self.show_add_download_dialog)
        toolbar.addAction(action_add)

        action_start = QAction(create_svg_icon(SVG_START), "Start Queue", self)
        toolbar.addAction(action_start)
        
        action_stop = QAction(create_svg_icon(SVG_STOP), "Stop Queue", self)
        toolbar.addAction(action_stop)
        
        toolbar.addSeparator()

        action_settings = QAction(create_svg_icon(SVG_SETTINGS), "Settings", self)
        toolbar.addAction(action_settings)

        # --- Main Layout (Sidebar + Table) ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        
        # --- Sidebar ---
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItem(QListWidgetItem("All"))
        self.sidebar.addItem(QListWidgetItem("Image"))
        self.sidebar.addItem(QListWidgetItem("Music"))
        self.sidebar.addItem(QListWidgetItem("Video"))
        self.sidebar.addItem(QListWidgetItem("Apps"))
        self.sidebar.addItem(QListWidgetItem("Document"))
        self.sidebar.addItem(QListWidgetItem("Compressed"))
        
        splitter.addWidget(self.sidebar)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "Size", "Status", "Speed", "Time Left", "Date Added"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        splitter.addWidget(self.table)
        splitter.setSizes([200, 800])
        main_layout.addWidget(splitter)
        

    def show_add_download_dialog(self):
        dialog = AddDownloadDialog(self)
        if dialog.exec():
            url, path = dialog.get_data()
            if url and path:
                filename = url.split('/')[-1] or "download"
                filepath = os.path.join(path, filename)
                self.add_download_to_table(url, filepath)

    def add_download_to_table(self, url, filepath):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(os.path.basename(filepath)))
        self.table.setItem(row, 1, QTableWidgetItem("...")) # Size
        
        # --- Progress Bar for Status ---
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        progress_bar.setFormat("Starting...")
        self.table.setCellWidget(row, 2, progress_bar)
        
        self.table.setItem(row, 3, QTableWidgetItem("0 MB/s")) # Speed
        self.table.setItem(row, 4, QTableWidgetItem("...")) # Time Left
        self.table.setItem(row, 5, QTableWidgetItem(time.strftime("%Y-%m-%d %H:%M")))

        self.start_download(row, url, filepath)
    
    def start_download(self, row, url, filepath):
        thread = QThread()
        worker = DownloadWorker(row, url, filepath)
        
        self.downloads[row] = (thread, worker)

        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        worker.progress.connect(self.update_progress)
        worker.finished.connect(self.on_download_finished)
        worker.error.connect(self.on_download_error)

        thread.start()

    @Slot(int, int, float, str)
    def update_progress(self, row, downloaded_size, speed_mbps, time_left_str):
        # Dapatkan total size dari header (perlu disimpan saat memulai)
        # Untuk demo ini, kita asumsikan 100MB jika tidak tahu
        # Dalam aplikasi nyata, Anda akan mengambilnya dari worker.
        total_size = 100 * 1024 * 1024 
        
        progress_bar = self.table.cellWidget(row, 2)
        if progress_bar:
            # Ini hanya perkiraan, idealnya worker mengirim total_size
            try:
                # Perkiraan kasar jika kita tidak tahu total size
                # Dalam aplikasi nyata, dapatkan total_size dari worker
                # Untuk sekarang, kita asumsikan progress bar akan bergerak
                # tapi mungkin tidak akurat secara persentase
                if total_size > 0 :
                     percentage = int((downloaded_size / total_size) * 100) if total_size else 0
                else: # Jika tidak ada content-length
                    percentage = 0 
                
                downloaded_mb = downloaded_size / (1024*1024)
                
                # Update progress bar
                progress_bar.setFormat(f"{downloaded_mb:.2f} MB / ?? MB")
                progress_bar.setValue(percentage if percentage <= 100 else 100)
            except Exception:
                progress_bar.setFormat(f"{downloaded_mb:.2f} MB")
                progress_bar.setValue(0)


        self.table.item(row, 3).setText(f"{speed_mbps:.2f} MB/s")
        self.table.item(row, 4).setText(time_left_str)


    @Slot(int)
    def on_download_finished(self, row):
        progress_bar = self.table.cellWidget(row, 2)
        if progress_bar:
            progress_bar.setValue(100)
            progress_bar.setFormat("Finished")
        self.table.item(row, 3).setText("✓")
        self.table.item(row, 4).setText("-")

    @Slot(int, str)
    def on_download_error(self, row, error_message):
        progress_bar = self.table.cellWidget(row, 2)
        if progress_bar:
            progress_bar.setFormat(f"Error")
            # Style error bar
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #E53935; }")
        
        QMessageBox.critical(self, "Download Error", f"Error on row {row+1}: {error_message}")

    def closeEvent(self, event):
        # Stop all running threads before closing
        for row, (thread, worker) in self.downloads.items():
            if thread.isRunning():
                worker.is_running = False
                thread.quit()
                thread.wait() # Wait for thread to finish
        event.accept()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #262626;
                color: #FFFFFF;
            }
            QToolBar {
                background-color: #333333;
                border: none;
                padding: 5px;
            }
            QToolBar QToolButton {
                padding: 6px;
                margin: 2px;
                border-radius: 4px;
            }
            QToolBar QToolButton:hover {
                background-color: #454545;
            }
            QListWidget {
                background-color: #2F2F2F;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px 15px;
            }
            QListWidget::item:selected, QListWidget::item:hover {
                background-color: #4A4A4A;
                border-left: 3px solid #8E44AD;
            }
            QTableWidget {
                background-color: #262626;
                border: none;
                gridline-color: #454545;
                color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #333333;
                color: white;
                padding: 4px;
                border: 1px solid #454545;
                font-weight: bold;
            }
            QTableWidget::item {
                padding-left: 5px;
            }
            QProgressBar {
                border: 1px solid #454545;
                border-radius: 4px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: QLinearGradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8E44AD, stop:1 #9B59B6);
                border-radius: 4px;
            }
            QLineEdit, QPushButton {
                padding: 5px;
                background-color: #333;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #8E44AD;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9B59B6;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())