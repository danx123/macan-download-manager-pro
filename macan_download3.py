import sys
import os
import time
import json
import requests
from enum import Enum
from urllib.parse import urlparse

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QLabel, QTableView, QHeaderView, QAbstractItemView,
    QProgressBar, QDialog, QLineEdit, QPushButton, QFileDialog,
    QMessageBox, QListWidget, QSplitter, QMenu, QSystemTrayIcon, QStyledItemDelegate
)
from PySide6.QtGui import QIcon, QAction, QColor, QPainter, QPixmap, QStandardItemModel, QStandardItem
from PySide6.QtCore import (
    Qt, QSize, QThread, QObject, Signal, Slot, QAbstractTableModel, QModelIndex, QSettings
)
from PySide6.QtSvg import QSvgRenderer

# --- SVG ICONS (Tetap sama) ---
SVG_ADD_URL = """<svg xmlns="http://www.w.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>"""
SVG_START = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>"""
SVG_PAUSE = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>"""
SVG_STOP = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><rect x="9" y="9" width="6" height="6"></rect></svg>"""
SVG_SETTINGS = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V12a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>"""

# --- Helper Functions (Tetap sama) ---
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

# --- ENUM & Data Class untuk Model ---
class DownloadStatus(Enum):
    QUEUED = "Queued"
    DOWNLOADING = "Downloading"
    PAUSED = "Paused"
    FINISHED = "Finished"
    ERROR = "Error"
    STOPPED = "Stopped"

class DownloadItem:
    def __init__(self, url, filepath):
        self.url = url
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.status = DownloadStatus.QUEUED
        self.total_size = 0
        self.downloaded_size = 0
        self.progress = 0
        self.speed = "N/A"
        self.time_left = "N/A"
        self.date_added = time.strftime("%Y-%m-%d %H:%M")
        # Untuk worker
        self.worker = None
        self.thread = None

# --- Download Worker (dengan Pause/Resume) ---
class DownloadWorker(QObject):
    started = Signal(str, int)  # uid, total_size
    progress = Signal(str, int) # uid, downloaded_size
    finished = Signal(str)      # uid
    error = Signal(str, str)    # uid, error_message
    status_changed = Signal(str, DownloadStatus) # uid, new_status

    def __init__(self, uid, url, filepath):
        super().__init__()
        self.uid = uid
        self.url = url
        self.filepath = filepath
        self.is_running = True
        self.is_paused = False

    @Slot()
    def run(self):
        try:
            resume_byte_pos = 0
            headers = {}
            if os.path.exists(self.filepath):
                resume_byte_pos = os.path.getsize(self.filepath)
                headers['Range'] = f'bytes={resume_byte_pos}-'

            with requests.get(self.url, stream=True, timeout=15, headers=headers) as r:
                r.raise_for_status()
                
                # Cek jika server mendukung Range requests
                if r.status_code == 206: # Partial Content
                    print(f"Resuming download for {self.uid} from byte {resume_byte_pos}")
                    total_size = int(r.headers.get('content-length', 0)) + resume_byte_pos
                else: # Download dari awal
                    resume_byte_pos = 0
                    total_size = int(r.headers.get('content-length', 0))

                self.started.emit(self.uid, total_size)
                self.status_changed.emit(self.uid, DownloadStatus.DOWNLOADING)

                downloaded_size = resume_byte_pos
                
                # Buka file dalam mode 'append binary' ('ab') untuk resume
                with open(self.filepath, 'ab') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        while self.is_paused:
                            if not self.is_running: break
                            time.sleep(0.5)
                        
                        if not self.is_running or not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        self.progress.emit(self.uid, downloaded_size)
            
            if self.is_running:
                # Verifikasi sederhana
                if total_size != 0 and downloaded_size != total_size:
                     raise Exception("File size mismatch")
                self.status_changed.emit(self.uid, DownloadStatus.FINISHED)
                self.finished.emit(self.uid)
            else:
                 self.status_changed.emit(self.uid, DownloadStatus.STOPPED)

        except requests.exceptions.RequestException as e:
            self.error.emit(self.uid, f"Network Error: {e}")
        except Exception as e:
            self.error.emit(self.uid, str(e))

    def stop(self):
        self.is_running = False

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        new_status = DownloadStatus.PAUSED if self.is_paused else DownloadStatus.DOWNLOADING
        self.status_changed.emit(self.uid, new_status)


# --- Arsitektur Model/View ---
class DownloadTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.headers = ["Name", "Total Size", "Progress", "Status", "Speed", "Time Left"]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            item = self._data[index.row()]
            col = index.column()
            if col == 0: return item.filename
            if col == 1: return format_size(item.total_size) if item.total_size > 0 else "..."
            if col == 2: return item.progress # Akan dihandle oleh delegate
            if col == 3: return item.status.value
            if col == 4: return item.speed
            if col == 5: return item.time_left
        return None

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self.headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

# --- Progress Bar Delegate untuk Tabel ---
from PySide6.QtWidgets import QStyle, QStyleOptionProgressBar

class ProgressBarDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.column() == 2: # Hanya untuk kolom progress
            progress = index.data()
            
            progress_bar_option = QStyleOptionProgressBar()
            progress_bar_option.rect = option.rect
            progress_bar_option.minimum = 0
            progress_bar_option.maximum = 100
            progress_bar_option.progress = progress
            progress_bar_option.text = f"{progress}%"
            progress_bar_option.textVisible = True
            progress_bar_option.textAlignment = Qt.AlignCenter
            
            QApplication.style().drawControl(QStyle.CE_ProgressBar, progress_bar_option, painter)
        else:
            super().paint(painter, option, index)

# --- Download Manager (Otak Aplikasi) ---
class DownloadManager(QObject):
    model_updated = Signal()

    def __init__(self, max_concurrent=3):
        super().__init__()
        self.downloads = []
        self.download_queue = []
        self.active_downloads = {} # {uid: DownloadItem}
        self.max_concurrent_downloads = max_concurrent
        # Untuk kalkulasi kecepatan
        self.last_updates = {} # {uid: (timestamp, last_size)}

    def add_download(self, url, filepath):
        uid = f"{os.path.basename(filepath)}-{int(time.time())}"
        item = DownloadItem(url, filepath)
        self.downloads.append(item)
        self.download_queue.append(uid)
        self.last_updates[uid] = (time.time(), 0)
        self.start_next_in_queue()
        self.model_updated.emit()
        return item
    
    def get_item_by_uid(self, uid):
        for item in self.downloads:
            if f"{item.filename}-{int(time.mktime(time.strptime(item.date_added, '%Y-%m-%d %H:%M')))}" == uid:
                return item
        return None

    def start_next_in_queue(self):
        while len(self.active_downloads) < self.max_concurrent_downloads and self.download_queue:
            uid_to_start = self.download_queue.pop(0)
            item = self.get_item_by_uid(uid_to_start)
            if item:
                self.active_downloads[uid_to_start] = item
                self.start_worker(item)

    def start_worker(self, item):
        uid = f"{item.filename}-{int(time.mktime(time.strptime(item.date_added, '%Y-%m-%d %H:%M')))}"
        thread = QThread()
        worker = DownloadWorker(uid, item.url, item.filepath)
        
        item.thread = thread
        item.worker = worker
        
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self.on_worker_finished)
        worker.error.connect(self.on_worker_error)
        worker.progress.connect(self.on_worker_progress)
        worker.started.connect(self.on_worker_started)
        worker.status_changed.connect(self.on_worker_status_changed)
        
        # Cleanup
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        thread.start()
    
    @Slot(str, int)
    def on_worker_started(self, uid, total_size):
        item = self.get_item_by_uid(uid)
        if item:
            item.total_size = total_size
            self.model_updated.emit()

    @Slot(str, int)
    def on_worker_progress(self, uid, downloaded_size):
        item = self.get_item_by_uid(uid)
        if not item: return

        item.downloaded_size = downloaded_size
        if item.total_size > 0:
            item.progress = int((downloaded_size / item.total_size) * 100)
        
        # Kalkulasi Kecepatan
        current_time = time.time()
        last_time, last_size = self.last_updates.get(uid, (current_time, downloaded_size))
        
        time_diff = current_time - last_time
        if time_diff >= 1: # Update tiap 1 detik
            size_diff = downloaded_size - last_size
            speed_bps = size_diff / time_diff
            item.speed = f"{format_size(speed_bps)}/s"
            
            if speed_bps > 0 and item.total_size > 0:
                remaining_bytes = item.total_size - downloaded_size
                time_left_sec = remaining_bytes / speed_bps
                mins, secs = divmod(time_left_sec, 60)
                item.time_left = f"{int(mins)}m {int(secs)}s"
            else:
                item.time_left = "N/A"
            
            self.last_updates[uid] = (current_time, downloaded_size)

        self.model_updated.emit()

    @Slot(str)
    def on_worker_finished(self, uid):
        if uid in self.active_downloads:
            del self.active_downloads[uid]
        self.start_next_in_queue()
        # TODO: Verifikasi checksum
    
    @Slot(str, str)
    def on_worker_error(self, uid, error_message):
        item = self.get_item_by_uid(uid)
        if item:
            item.status = DownloadStatus.ERROR
            print(f"Error for {uid}: {error_message}")
        if uid in self.active_downloads:
            del self.active_downloads[uid]
        self.start_next_in_queue()
        self.model_updated.emit()
        # TODO: Implementasi logika retry

    @Slot(str, DownloadStatus)
    def on_worker_status_changed(self, uid, status):
        item = self.get_item_by_uid(uid)
        if item:
            item.status = status
            self.model_updated.emit()
    
    def pause_download(self, index):
        item = self.downloads[index.row()]
        if item and item.worker and item.status == DownloadStatus.DOWNLOADING:
            item.worker.toggle_pause()

    def resume_download(self, index):
        item = self.downloads[index.row()]
        if item and item.worker and item.status == DownloadStatus.PAUSED:
            item.worker.toggle_pause()

    def stop_download(self, index):
        item = self.downloads[index.row()]
        if item and item.worker:
            item.worker.stop()
            
# --- UI/UX Lainnya ---
class AddDownloadDialog(QDialog):
    # ... (Sama seperti kode asli)
    def __init__(self, parent=None, default_path=""):
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
        self.path_input = QLineEdit(default_path)
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_path)
        self.path_layout.addWidget(self.path_label)
        self.path_layout.addWidget(self.path_input)
        self.path_layout.addWidget(self.browse_button)
        self.layout.addLayout(self.path_layout)
        # ... Tombol OK/Cancel sama
        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Download")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)
    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Folder", self.path_input.text())
        if directory: self.path_input.setText(directory)
    def get_data(self): return self.url_input.text(), self.path_input.text()

class SettingsDialog(QDialog):
    # TODO: UI untuk mengubah pengaturan
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        # Tambahkan QLineEdit untuk Default Folder, QSpinBox untuk Max Downloads, dll.

# --- Main Window (Menggunakan Model/View) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macan Download Manager Pro")
        self.resize(1000, 600)
        self.setWindowIcon(create_svg_icon(SVG_START, "purple"))
        
        self.load_settings()
        self.manager = DownloadManager(max_concurrent=self.settings.value("max_concurrent_downloads", 3))

        self.setup_ui()
        self.apply_stylesheet()
        
        self.manager.model_updated.connect(self.update_view)
        
        # Fitur Drag & Drop
        self.setAcceptDrops(True)
        # Fitur System Tray
        self.create_tray_icon()


    def load_settings(self):
        self.settings = QSettings("MacanTech", "MacanDownloader")
        self.default_download_path = self.settings.value("default_download_path", os.path.join(os.path.expanduser("~"), "Downloads"))

    def save_settings(self):
        self.settings.setValue("default_download_path", self.default_download_path)
        self.settings.setValue("max_concurrent_downloads", self.manager.max_concurrent_downloads)

    def setup_ui(self):
        toolbar = QToolBar("Main Toolbar")
        # ... (Sama seperti kode asli, koneksi diubah)
        self.addToolBar(toolbar)
        action_add = QAction(create_svg_icon(SVG_ADD_URL), "Add URL", self)
        action_add.triggered.connect(self.show_add_download_dialog)
        toolbar.addAction(action_add)
        action_settings = QAction(create_svg_icon(SVG_SETTINGS), "Settings", self)
        action_settings.triggered.connect(self.show_settings_dialog)
        toolbar.addAction(action_settings)


        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)

        splitter = QSplitter(Qt.Horizontal)
        
        # Sidebar Fungsional
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItems(["All", "Downloading", "Paused", "Finished", "Error"])
        self.sidebar.currentItemChanged.connect(self.filter_downloads)
        splitter.addWidget(self.sidebar)

        # Menggunakan QTableView, bukan QTableWidget
        self.table_view = QTableView()
        self.model = DownloadTableModel(self.manager.downloads)
        self.table_view.setModel(self.model)
        
        # Set Delegate untuk progress bar
        self.table_view.setItemDelegateForColumn(2, ProgressBarDelegate(self))

        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Menu Konteks (Klik Kanan)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.create_context_menu)

        splitter.addWidget(self.table_view)
        splitter.setSizes([150, 850])
        main_layout.addWidget(splitter)
        
        self.statusBar().showMessage("Ready")

    def show_add_download_dialog(self):
        dialog = AddDownloadDialog(self, self.default_download_path)
        if dialog.exec():
            url, path = dialog.get_data()
            if url and path:
                if not os.path.exists(path): os.makedirs(path, exist_ok=True)
                
                filename = os.path.basename(urlparse(url).path) or "download"
                filepath = os.path.join(path, filename)
                self.manager.add_download(url, filepath)

    def update_view(self):
        self.model.layoutChanged.emit()

    def filter_downloads(self, current, previous):
        # TODO: Implementasi filter menggunakan QSortFilterProxyModel untuk performa lebih baik
        # Untuk saat ini, ini hanya contoh visual
        category = current.text()
        print(f"Filtering by: {category}")
        self.statusBar().showMessage(f"View: {category}")

    def create_context_menu(self, pos):
        selected_indexes = self.table_view.selectedIndexes()
        if not selected_indexes: return
        
        selected_row_index = selected_indexes[0]
        item = self.manager.downloads[selected_row_index.row()]
        
        menu = QMenu()
        if item.status == DownloadStatus.DOWNLOADING:
            pause_action = menu.addAction("Pause")
            pause_action.triggered.connect(lambda: self.manager.pause_download(selected_row_index))
        
        if item.status == DownloadStatus.PAUSED:
            resume_action = menu.addAction("Resume")
            resume_action.triggered.connect(lambda: self.manager.resume_download(selected_row_index))
        
        if item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED, DownloadStatus.QUEUED]:
            stop_action = menu.addAction("Stop")
            stop_action.triggered.connect(lambda: self.manager.stop_download(selected_row_index))
        
        menu.addSeparator()
        open_folder_action = menu.addAction("Open Containing Folder")
        # ... tambahkan action lain
        
        menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def show_settings_dialog(self):
        # TODO: Implementasi dialog pengaturan
        dialog = SettingsDialog(self)
        dialog.exec()
    
    # --- Event Handlers untuk Fitur Lanjutan ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = [url.toLocalFile() for url in event.mimeData().urls()]
        for url in urls:
            # Asumsi ini adalah link, bukan file lokal
            print(f"Dropped URL: {url}")
            # Tampilkan dialog konfirmasi sebelum menambahkan
            self.manager.add_download(url, self.default_download_path)

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.windowIcon())
        self.tray_icon.setToolTip("Macan Download Manager")

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        self.save_settings()
        # TODO: Tampilkan konfirmasi jika masih ada unduhan aktif
        # Hentikan semua thread
        for item in self.manager.downloads:
            if item.thread and item.thread.isRunning():
                item.worker.stop()
                item.thread.quit()
                item.thread.wait(1000)
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