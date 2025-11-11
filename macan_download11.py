import sys
import os
import time
import json
import uuid
import requests
from functools import partial
from enum import Enum
from urllib.parse import urlparse
if sys.platform == "win32":
    import winreg

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QLabel, QTableView, QHeaderView, QAbstractItemView,
    QProgressBar, QDialog, QLineEdit, QPushButton, QFileDialog,
    QMessageBox, QListWidget, QSplitter, QMenu, QSystemTrayIcon,
    QStyledItemDelegate, QStyle, QStyleOptionProgressBar, QSpinBox,
    QComboBox, QFormLayout, QCheckBox, QSizePolicy
)
from PySide6.QtGui import QIcon, QAction, QPixmap, QStandardItemModel, QStandardItem, QPainter
from PySide6.QtCore import (
    Qt, QSize, QThread, QObject, Signal, Slot, QAbstractTableModel,
    QModelIndex, QSettings, QSortFilterProxyModel
)
from PySide6.QtSvg import QSvgRenderer
from macan_dialog import DownloadProgressDialog, DownloadStatus

# --- SVG ICONS ---
SVG_ADD_URL = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>"""
SVG_START = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>"""
SVG_PAUSE = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>"""
SVG_STOP = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><rect x="9" y="9" width="6" height="6"></rect></svg>"""
SVG_SETTINGS = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V12a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>"""
SVG_STOP_ALL = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="9" x2="15" y2="15"></line><line x1="15" y1="9" x2="9" y2="15"></line></svg>"""
SVG_SEARCH = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>"""
SVG_ABOUT = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>"""
SVG_CLEAR_ALL = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>"""

# --- Helper Functions ---
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
    if size_bytes is None or size_bytes < 0: return "0 B"
    if size_bytes == 0: return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(size_bytes).bit_length() // 10
    power = 1024 ** i
    size = round(size_bytes / power, 2)
    return f"{size} {size_name[i]}"

def set_autostart(enabled=True):
    """Mengatur aplikasi untuk start otomatis di Windows."""
    if sys.platform != "win32":
        print("Autostart feature is only available on Windows.")
        return

    APP_NAME = "MacanDownloaderPro"
    # Path ke registry key
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    APP_NAME = "MacanDownloaderPro"
    # Path ke registry key
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        # Buka registry key, HKEY_CURRENT_USER tidak butuh admin rights
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            # Ambil path ke python interpreter dan script ini
            python_exe = sys.executable
            script_path = os.path.abspath(__file__)
            # Value yang akan ditulis: "C:\path\to\python.exe" "C:\path\to\script.py" --tray
            value = f'"{python_exe}" "{script_path}" --tray'
            
            winreg.SetValueEx(reg_key, APP_NAME, 0, winreg.REG_SZ, value)
            print(f"Autostart enabled for {APP_NAME}.")
        else:
            winreg.DeleteValue(reg_key, APP_NAME)
            print(f"Autostart disabled for {APP_NAME}.")
        winreg.CloseKey(reg_key)
    except FileNotFoundError:
        print(f"Autostart entry for {APP_NAME} not found, nothing to disable.")
    except Exception as e:
        print(f"Failed to set autostart: {e}")

# --- ENUM & Data Class untuk Model ---
class DownloadStatus(Enum):
    QUEUED = "Queued"
    DOWNLOADING = "Downloading"
    PAUSED = "Paused"
    FINISHED = "Finished"
    ERROR = "Error"
    STOPPED = "Stopped"

class DownloadItem:
    def __init__(self, url, filepath, category="General"):
        self.uid = str(uuid.uuid4())
        self.url = url
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.status = DownloadStatus.QUEUED
        self.category = category
        self.total_size = 0
        self.downloaded_size = 0
        self.progress = 0
        self.speed = "N/A"
        self.time_left = "N/A"
        self.date_added = time.strftime("%Y-%m-%d %H:%M:%S")
        self.retries = 0
        self.worker = None
        self.thread = None

    def to_dict(self):
        return {
            'uid': self.uid,
            'url': self.url,
            'filepath': self.filepath,
            'status': self.status.value,
            'category': self.category,
            'total_size': self.total_size,
            'downloaded_size': self.downloaded_size,
            'date_added': self.date_added
        }

    @staticmethod
    def from_dict(data):
        item = DownloadItem(data['url'], data['filepath'], data.get('category', 'General'))
        item.uid = data['uid']
        status_val = data['status']
        if status_val == DownloadStatus.FINISHED.value:
            item.status = DownloadStatus.FINISHED
            item.progress = 100
        elif status_val in [DownloadStatus.DOWNLOADING.value, DownloadStatus.PAUSED.value]:
            item.status = DownloadStatus.PAUSED
        else:
            item.status = DownloadStatus.QUEUED
        item.total_size = data['total_size']
        item.downloaded_size = data['downloaded_size']
        if item.total_size > 0:
            item.progress = int((item.downloaded_size / item.total_size) * 100)
        item.date_added = data['date_added']
        return item

# --- Download Worker ---
class DownloadWorker(QObject):
    started = Signal(str, int)
    progress = Signal(str, int)
    finished = Signal(str)
    error = Signal(str, str)
    status_changed = Signal(str, DownloadStatus)

    def __init__(self, uid, url, filepath, speed_limit_kbps=0):
        super().__init__()
        self.uid = uid
        self.url = url
        self.filepath = filepath
        self.is_running = True
        self.is_paused = False
        self.speed_limit_bytes = speed_limit_kbps * 1024 if speed_limit_kbps > 0 else 0

    @Slot()
    def run(self):
        try:
            resume_byte_pos = 0
            headers = {}
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            if os.path.exists(self.filepath):
                resume_byte_pos = os.path.getsize(self.filepath)
                if resume_byte_pos > 0:
                    headers['Range'] = f'bytes={resume_byte_pos}-'
            with requests.get(self.url, stream=True, timeout=30, headers=headers) as r:
                r.raise_for_status()
                if r.status_code == 206:
                    content_range = r.headers.get('content-range', '0/0')
                    total_size = int(content_range.split('/')[-1])
                else:
                    resume_byte_pos = 0
                    total_size = int(r.headers.get('content-length', 0))
                self.started.emit(self.uid, total_size)
                self.status_changed.emit(self.uid, DownloadStatus.DOWNLOADING)
                downloaded_size = resume_byte_pos
                chunk_size = 8192
                with open(self.filepath, 'ab') as f:
                    start_time = time.time()
                    bytes_since_last_check = 0
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        while self.is_paused:
                            if not self.is_running: break
                            time.sleep(0.5)
                        if not self.is_running or not chunk: break
                        f.write(chunk)
                        chunk_len = len(chunk)
                        downloaded_size += chunk_len
                        bytes_since_last_check += chunk_len
                        self.progress.emit(self.uid, downloaded_size)
                        if self.speed_limit_bytes > 0:
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                current_speed = bytes_since_last_check / elapsed_time
                                if current_speed > self.speed_limit_bytes:
                                    sleep_time = (bytes_since_last_check / self.speed_limit_bytes) - elapsed_time
                                    if sleep_time > 0:
                                        time.sleep(sleep_time)
                            if elapsed_time >= 1.0:
                                start_time = time.time()
                                bytes_since_last_check = 0
            if self.is_running:
                if total_size != 0 and downloaded_size < total_size:
                     raise IOError(f"File download incomplete: size mismatch ({downloaded_size}/{total_size})")
                self.status_changed.emit(self.uid, DownloadStatus.FINISHED)
                self.finished.emit(self.uid)
            else:
                 self.status_changed.emit(self.uid, DownloadStatus.STOPPED)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 416:
                print(f"Info: Received 416 for {self.filepath}. File is already complete.")
                file_size = os.path.getsize(self.filepath)
                self.started.emit(self.uid, file_size)
                self.progress.emit(self.uid, file_size)
                self.status_changed.emit(self.uid, DownloadStatus.FINISHED)
                self.finished.emit(self.uid)
            else:
                self.error.emit(self.uid, f"HTTP Error: {e}")
        except requests.exceptions.RequestException as e:
            self.error.emit(self.uid, f"Network Error: {e}")
        except Exception as e:
            self.error.emit(self.uid, str(e))

    def stop(self): self.is_running = False
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        new_status = DownloadStatus.PAUSED if self.is_paused else DownloadStatus.DOWNLOADING
        self.status_changed.emit(self.uid, new_status)

# --- Model/View Architecture ---
class DownloadTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.headers = ["Name", "Total Size", "Progress", "Status", "Speed", "Time Left", "Category"]
    def data(self, index, role):
        if not index.isValid(): return None
        item = self._data[index.row()]
        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0: return item.filename
            if col == 1: return format_size(item.total_size) if item.total_size > 0 else "..."
            if col == 2: return item.progress
            if col == 3: return item.status.value
            if col == 4: return item.speed
            if col == 5: return item.time_left
            if col == 6: return item.category
        if role == Qt.UserRole: return item.status.value
        if role == (Qt.UserRole + 1): return item.category
        return None
    def rowCount(self, index): return len(self._data)
    def columnCount(self, index): return len(self.headers)
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal: return self.headers[section]
        return None

class CustomFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_filter = ""
        self._text_filter = ""

    def set_status_filter(self, status):
        self._status_filter = status
        self.invalidateFilter()

    def set_text_filter(self, text):
        self._text_filter = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        filename_index = self.sourceModel().index(source_row, 0, source_parent)
        status_index = self.sourceModel().index(source_row, 3, source_parent)
        filename = self.sourceModel().data(filename_index, Qt.DisplayRole)
        status = self.sourceModel().data(status_index, Qt.DisplayRole)
        status_ok = True
        if self._status_filter and self._status_filter != "All":
            status_ok = (status == self._status_filter)
        text_ok = True
        if self._text_filter:
            text_ok = self._text_filter in filename.lower()
        return status_ok and text_ok

# --- Progress Bar Delegate ---
class ProgressBarDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.column() == 2:
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

# --- Download Manager ---
class DownloadManager(QObject):
    model_updated = Signal()
    download_finished_notification = Signal(str)  # <<< BARU: Sinyal untuk notifikasi (nama file)
    item_updated = Signal(object)
    MAX_RETRIES = 3
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.downloads = []
        self.download_queue = []
        self.active_downloads = {}
        self.last_updates = {}
        self.load_downloads()
    @property
    def max_concurrent_downloads(self): return self.settings.value("max_concurrent_downloads", 3, type=int)
    @property
    def speed_limit_kbps(self): return self.settings.value("speed_limit_kbps", 0, type=int)
    def load_downloads(self):
        save_path = self.settings.value("download_list_path", "")
        if save_path and os.path.exists(save_path):
            try:
                with open(save_path, 'r') as f:
                    data = json.load(f)
                    for item_data in data:
                        item = DownloadItem.from_dict(item_data)
                        self.downloads.append(item)
                        if item.status not in [DownloadStatus.FINISHED, DownloadStatus.STOPPED, DownloadStatus.ERROR]:
                            self.download_queue.append(item.uid)
                self.model_updated.emit()
            except (json.JSONDecodeError, KeyError) as e: print(f"Could not load download list: {e}")
    def save_downloads(self):
        save_path = self.settings.value("download_list_path", "")
        if save_path:
            try:
                with open(save_path, 'w') as f: json.dump([item.to_dict() for item in self.downloads], f, indent=4)
            except IOError as e: print(f"Could not save download list: {e}")
    def add_download(self, url, filepath, category):
        item = DownloadItem(url, filepath, category)
        self.downloads.append(item)
        self.download_queue.append(item.uid)
        self.last_updates[item.uid] = (time.time(), 0)
        self.start_next_in_queue()
        self.model_updated.emit()
        return item
    def get_item_by_uid(self, uid): return next((item for item in self.downloads if item.uid == uid), None)
    def start_next_in_queue(self):
        while len(self.active_downloads) < self.max_concurrent_downloads and self.download_queue:
            uid_to_start = self.download_queue.pop(0)
            item = self.get_item_by_uid(uid_to_start)
            if item and item.status not in [DownloadStatus.DOWNLOADING, DownloadStatus.FINISHED]:
                self.active_downloads[uid_to_start] = item
                self.start_worker(item)
    def start_worker(self, item):
        thread = QThread()
        worker = DownloadWorker(item.uid, item.url, item.filepath, self.speed_limit_kbps)
        item.thread = thread
        item.worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self.on_worker_finished)
        worker.error.connect(self.on_worker_error)
        worker.progress.connect(self.on_worker_progress)
        worker.started.connect(self.on_worker_started)
        worker.status_changed.connect(self.on_worker_status_changed)
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
            self.item_updated.emit(item)
    @Slot(str, int)
    def on_worker_progress(self, uid, downloaded_size):
        item = self.get_item_by_uid(uid)
        if not item: return
        item.downloaded_size = downloaded_size
        if item.total_size > 0: item.progress = int((downloaded_size / item.total_size) * 100)
        current_time = time.time()
        last_time, last_size = self.last_updates.get(uid, (current_time, downloaded_size))
        time_diff = current_time - last_time
        if time_diff >= 1:
            size_diff = downloaded_size - last_size
            speed_bps = size_diff / time_diff
            item.speed = f"{format_size(speed_bps)}/s"
            if speed_bps > 0 and item.total_size > 0:
                remaining_bytes = item.total_size - downloaded_size
                time_left_sec = remaining_bytes / speed_bps
                mins, secs = divmod(time_left_sec, 60)
                item.time_left = f"{int(mins)}m {int(secs)}s" if time_left_sec < 3600 else ">1h"
            else: item.time_left = "N/A"
            self.last_updates[uid] = (current_time, downloaded_size)
        self.model_updated.emit()
        self.item_updated.emit(item)
    @Slot(str)
    def on_worker_finished(self, uid):
        if uid in self.active_downloads: del self.active_downloads[uid]
        self.start_next_in_queue()
    @Slot(str, str)
    def on_worker_error(self, uid, error_message):
        item = self.get_item_by_uid(uid)
        if item:
            print(f"Error for {uid}: {error_message}")
            if item.retries < self.MAX_RETRIES:
                item.retries += 1
                item.status = DownloadStatus.QUEUED
                print(f"Retrying download for {uid} ({item.retries}/{self.MAX_RETRIES})")
                self.download_queue.insert(0, uid)
            else: item.status = DownloadStatus.ERROR
        if uid in self.active_downloads: del self.active_downloads[uid]
        self.start_next_in_queue()
        self.model_updated.emit()
    @Slot(str, DownloadStatus)
    def on_worker_status_changed(self, uid, status):
        item = self.get_item_by_uid(uid)
        if item:
            item.status = status
            if status == DownloadStatus.FINISHED:
                self.download_finished_notification.emit(item.filename)
            self.model_updated.emit()
            self.item_updated.emit(item)
    def control_download(self, uid, action):
        item = self.get_item_by_uid(uid)
        if not item: return
        if action == 'pause' and item.worker and item.status == DownloadStatus.DOWNLOADING: item.worker.toggle_pause()
        elif action == 'resume' and item.status == DownloadStatus.PAUSED:
            if item.worker: item.worker.toggle_pause()
            else:
                self.download_queue.insert(0, uid)
                self.start_next_in_queue()
        elif action == 'stop' and item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED, DownloadStatus.QUEUED]:
            if item.worker: item.worker.stop()
            else:
                 if uid in self.download_queue: self.download_queue.remove(uid)
                 item.status = DownloadStatus.STOPPED
                 self.model_updated.emit()
        elif action == 'retry' and item.status in [DownloadStatus.ERROR, DownloadStatus.STOPPED]:
            item.status = DownloadStatus.QUEUED
            item.retries = 0
            self.download_queue.insert(0, uid)
            self.start_next_in_queue()
    def remove_download(self, uid, delete_file=False):
        item = self.get_item_by_uid(uid)
        if item:
            if item.worker: item.worker.stop()
            self.downloads.remove(item)
            if delete_file and os.path.exists(item.filepath):
                try: os.remove(item.filepath)
                except OSError as e: print(f"Failed to delete file {item.filepath}: {e}")
            self.model_updated.emit()
    def clear_completed_downloads(self):
        downloads_to_keep = [
            item for item in self.downloads 
            if item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED, DownloadStatus.QUEUED]
        ]
        if len(downloads_to_keep) < len(self.downloads):
            self.downloads = downloads_to_keep
            print(f"Cleared completed downloads. Kept {len(self.downloads)} active items.")
            self.model_updated.emit()

# --- UI/UX Lainnya ---
class AddDownloadDialog(QDialog):
    def __init__(self, parent=None, default_path="", default_url=""):
        super().__init__(parent)
        self.setWindowTitle("Add New Download")
        self.setMinimumWidth(500)
        self.layout = QVBoxLayout(self)
        self.url_input = QLineEdit(default_url)
        self.url_input.setPlaceholderText("https://example.com/file.zip")
        self.path_input = QLineEdit(default_path)
        self.category_input = QComboBox()
        self.category_input.addItems(["General", "Video", "Music", "Documents", "Software"])
        self.category_input.setEditable(True)
        form_layout = QFormLayout()
        form_layout.addRow("URL:", self.url_input)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_button)
        form_layout.addRow("Save to:", path_layout)
        form_layout.addRow("Category:", self.category_input)
        self.layout.addLayout(form_layout)
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Download")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        self.layout.addLayout(button_layout)
    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Folder", self.path_input.text())
        if directory: self.path_input.setText(directory)
    def get_data(self): return self.url_input.text(), self.path_input.text(), self.category_input.currentText()

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = settings
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.path_input = QLineEdit(self.settings.value("default_download_path", ""))
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_path)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        form_layout.addRow("Default Download Folder:", path_layout)
        self.max_downloads_spin = QSpinBox()
        self.max_downloads_spin.setRange(1, 10)
        self.max_downloads_spin.setValue(self.settings.value("max_concurrent_downloads", 3, type=int))
        form_layout.addRow("Max Concurrent Downloads:", self.max_downloads_spin)
        self.speed_limit_spin = QSpinBox()
        self.speed_limit_spin.setRange(0, 100000)
        self.speed_limit_spin.setSuffix(" KB/s (0=Unlimited)")
        self.speed_limit_spin.setValue(self.settings.value("speed_limit_kbps", 0, type=int))
        form_layout.addRow("Global Speed Limit:", self.speed_limit_spin)
        
        # --- TAMBAHAN --- Opsi minimize to tray
        self.minimize_to_tray_check = QCheckBox()
        self.minimize_to_tray_check.setChecked(self.settings.value("minimize_to_tray", True, type=bool))
        form_layout.addRow("Minimize to tray on close:", self.minimize_to_tray_check)
        self.start_with_windows_check = QCheckBox()
        if sys.platform == "win32":
            self.start_with_windows_check.setChecked(self.settings.value("start_with_windows", False, type=bool))
        else:
            self.start_with_windows_check.setEnabled(False)
            self.start_with_windows_check.setToolTip("This feature is only available on Windows.")
        form_layout.addRow("Start with Windows (tray mode):", self.start_with_windows_check)
        
        layout.addLayout(form_layout)
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.save_and_accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Folder", self.path_input.text())
        if directory: self.path_input.setText(directory)
    def save_and_accept(self):
        self.settings.setValue("default_download_path", self.path_input.text())
        self.settings.setValue("max_concurrent_downloads", self.max_downloads_spin.value())
        self.settings.setValue("speed_limit_kbps", self.speed_limit_spin.value())
        self.settings.setValue("minimize_to_tray", self.minimize_to_tray_check.isChecked()) # <<< BARU
        start_with_windows = self.start_with_windows_check.isChecked()
        self.settings.setValue("start_with_windows", start_with_windows)
        if sys.platform == "win32":
            set_autostart(start_with_windows)
        self.accept()

# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macan Download Manager Pro")
        self.resize(1000, 600)
        self.setWindowIcon(create_svg_icon(SVG_START, "#8E44AD"))
        self.setup_settings()
        self.manager = DownloadManager(self.settings)
        self.progress_dialogs = {}
        self.setup_ui()
        self.apply_stylesheet()
        self.manager.model_updated.connect(self.update_view)
        self.setAcceptDrops(True)
        self.create_tray_icon()
        self.is_exiting = False  # Flag untuk membedakan minimize dan exit
        self.manager.download_finished_notification.connect(self.show_download_complete_notification)
        self.manager.item_updated.connect(self.update_progress_dialog)

    def setup_settings(self):
        self.settings = QSettings("MacanTech", "MacanDownloaderPro")
        if not self.settings.value("default_download_path"):
            self.settings.setValue("default_download_path", os.path.join(os.path.expanduser("~"), "Downloads"))
        config_dir = os.path.dirname(self.settings.fileName())
        os.makedirs(config_dir, exist_ok=True)
        self.settings.setValue("download_list_path", os.path.join(config_dir, "downloads.json"))

    def setup_ui(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        action_add = QAction(create_svg_icon(SVG_ADD_URL), "Add URL", self)
        action_add.triggered.connect(lambda: self.show_add_download_dialog())

        self.action_pause = QAction(create_svg_icon(SVG_PAUSE), "Pause Selected", self)
        self.action_pause.triggered.connect(self.pause_selected)
        self.action_pause.setEnabled(False)

        self.action_stop = QAction(create_svg_icon(SVG_STOP), "Stop Selected", self)
        self.action_stop.triggered.connect(self.stop_selected)
        self.action_stop.setEnabled(False)

        self.action_stop_all = QAction(create_svg_icon(SVG_STOP_ALL, "orange"), "Stop All", self)
        self.action_stop_all.triggered.connect(self.stop_all)

        action_settings = QAction(create_svg_icon(SVG_SETTINGS), "Settings", self)
        action_settings.triggered.connect(self.show_settings_dialog)
        
        action_about = QAction(create_svg_icon(SVG_ABOUT), "About", self)
        action_about.triggered.connect(self.show_about_dialog)
        
        toolbar.addAction(action_add)
        toolbar.addSeparator()
        toolbar.addAction(self.action_pause)
        toolbar.addAction(self.action_stop)
        toolbar.addAction(self.action_stop_all)
        toolbar.addSeparator()
        toolbar.addAction(action_settings)
        toolbar.addAction(action_about)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

        search_icon_label = QLabel()
        search_icon_label.setPixmap(create_svg_icon(SVG_SEARCH).pixmap(16, 16))
        toolbar.addWidget(search_icon_label)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search from list...")
        self.search_input.setMaximumWidth(250)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        toolbar.addWidget(self.search_input)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        splitter = QSplitter(Qt.Horizontal)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItems(["All", "Downloading", "Paused", "Finished", "Error"])
        self.sidebar.currentItemChanged.connect(self.filter_downloads)
        splitter.addWidget(self.sidebar)
        self.table_view = QTableView()
        self.source_model = DownloadTableModel(self.manager.downloads)
        
        self.proxy_model = CustomFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)
        
        self.table_view.setModel(self.proxy_model)
        self.table_view.setItemDelegateForColumn(2, ProgressBarDelegate(self))
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_view.setColumnHidden(6, True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.setSortingEnabled(True)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.create_context_menu)
        self.table_view.doubleClicked.connect(self.on_table_double_clicked)
        
        self.table_view.selectionModel().selectionChanged.connect(self.update_toolbar_actions_state)
        
        splitter.addWidget(self.table_view)
        splitter.setSizes([150, 850])
        main_layout.addWidget(splitter)
        self.statusBar().showMessage("Ready")

    def get_selected_items(self):
        items = []
        selected_indexes = self.table_view.selectionModel().selectedRows()
        for proxy_index in selected_indexes:
            source_index = self.proxy_model.mapToSource(proxy_index)
            item = self.manager.downloads[source_index.row()]
            items.append(item)
        return items

    def pause_selected(self):
        items = self.get_selected_items()
        for item in items:
            if item.status == DownloadStatus.DOWNLOADING:
                self.manager.control_download(item.uid, 'pause')
            elif item.status == DownloadStatus.PAUSED:
                self.manager.control_download(item.uid, 'resume')

    def stop_selected(self):
        items = self.get_selected_items()
        if not items: return
        reply = QMessageBox.question(self, 'Confirm Stop',
            f"Are you sure you want to stop {len(items)} selected download(s)?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for item in items:
                self.manager.control_download(item.uid, 'stop')

    def stop_all(self):
        active_downloads = [item for item in self.manager.downloads if item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED, DownloadStatus.QUEUED]]
        if not active_downloads:
            self.statusBar().showMessage("No active downloads to stop.")
            return
        reply = QMessageBox.question(self, 'Confirm Stop All',
            "Are you sure you want to stop all active downloads?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for item in active_downloads:
                self.manager.control_download(item.uid, 'stop')

    def clear_completed_list(self):
        items_to_clear = [
            item for item in self.manager.downloads 
            if item.status in [DownloadStatus.FINISHED, DownloadStatus.ERROR, DownloadStatus.STOPPED]
        ]
        if not items_to_clear:
            self.statusBar().showMessage("No completed downloads to clear.", 3000)
            return
        reply = QMessageBox.question(self, 'Confirm Clear',
            f"Are you sure you want to remove {len(items_to_clear)} completed/stopped/error item(s) from the list?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.table_view.clearSelection() 
            self.manager.clear_completed_downloads()
            self.statusBar().showMessage("Completed downloads cleared.", 3000)    

    def on_table_double_clicked(self, proxy_index):
        if not proxy_index.isValid(): return
        source_index = self.proxy_model.mapToSource(proxy_index)
        item = self.manager.downloads[source_index.row()]
        if item.status == DownloadStatus.FINISHED:
            if os.path.exists(item.filepath):
                try:
                    if sys.platform == "win32": os.startfile(item.filepath)
                    elif sys.platform == "darwin": os.system(f'open "{item.filepath}"')
                    else: os.system(f'xdg-open "{item.filepath}"')
                    self.statusBar().showMessage(f"Opening {item.filename}...", 3000)
                except Exception as e:
                    self.statusBar().showMessage(f"Error opening file: {e}", 5000)
                    QMessageBox.warning(self, "Error", f"Could not open the file:\n{item.filepath}\n\nReason: {e}")
            else:
                self.statusBar().showMessage(f"File not found: {item.filename}", 5000)
                QMessageBox.warning(self, "File Not Found", f"The file could not be found at the path:\n{item.filepath}")

    @Slot()
    def on_search_text_changed(self):
        search_text = self.search_input.text()
        self.proxy_model.set_text_filter(search_text)

    @Slot()
    def update_toolbar_actions_state(self):
        selected_items = self.get_selected_items()
        can_pause = False
        can_stop = False
        if selected_items:
            can_pause = any(item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED] for item in selected_items)
            can_stop = any(item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED, DownloadStatus.QUEUED] for item in selected_items)
        self.action_pause.setEnabled(can_pause)
        self.action_stop.setEnabled(can_stop)

    def show_add_download_dialog(self, url=""):
        default_path = self.settings.value("default_download_path")
        dialog = AddDownloadDialog(self, default_path, url)
        if dialog.exec():
            url, path, category = dialog.get_data()
            if url and path:
                if not os.path.exists(path): os.makedirs(path, exist_ok=True)
                filename = os.path.basename(urlparse(url).path) or "download"
                filepath = os.path.join(path, filename)
                item = self.manager.add_download(url, filepath, category)
                self.show_download_progress_dialog(item)

    @Slot()
    def update_view(self):
        self.source_model.layoutChanged.emit()
        self.update_toolbar_actions_state()

    def filter_downloads(self, current, previous):
        if not current: return
        category = current.text()
        self.proxy_model.set_status_filter(category)
        self.statusBar().showMessage(f"View: {category}")

    def open_item_folder(self, item):
        if not item or not os.path.exists(item.filepath):
            self.statusBar().showMessage(f"File not found: {item.filename}", 5000)
            QMessageBox.warning(self, "File Not Found", f"The file could not be found at the path:\n{item.filepath}")
            return
        folder_path = os.path.dirname(item.filepath)
        try:
            if sys.platform == "win32": os.startfile(folder_path)
            elif sys.platform == "darwin": os.system(f'open "{folder_path}"')
            else: os.system(f'xdg-open "{folder_path}"')
            self.statusBar().showMessage(f"Opening folder for {item.filename}...", 3000)
        except Exception as e:
            self.statusBar().showMessage(f"Error opening folder: {e}", 5000)
            QMessageBox.warning(self, "Error", f"Could not open the folder:\n{folder_path}\n\nReason: {e}")

    def create_context_menu(self, pos):
        proxy_index = self.table_view.indexAt(pos)
        if not proxy_index.isValid(): return
        
        source_index = self.proxy_model.mapToSource(proxy_index)
        item = self.manager.downloads[source_index.row()]
        menu = QMenu()

        if item.status == DownloadStatus.DOWNLOADING:
            pause_action = menu.addAction("Pause")
            pause_action.triggered.connect(partial(self.manager.control_download, item.uid, 'pause'))
        if item.status == DownloadStatus.PAUSED:
            resume_action = menu.addAction("Resume")
            resume_action.triggered.connect(partial(self.manager.control_download, item.uid, 'resume'))
        if item.status in [DownloadStatus.ERROR, DownloadStatus.STOPPED]:
            retry_action = menu.addAction("Retry")
            retry_action.triggered.connect(partial(self.manager.control_download, item.uid, 'retry'))
        if item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED, DownloadStatus.QUEUED]:
            stop_action = menu.addAction("Stop")
            stop_action.triggered.connect(partial(self.manager.control_download, item.uid, 'stop'))
        
        menu.addSeparator()
        remove_action = menu.addAction("Remove")
        remove_menu = QMenu()
        remove_from_list = remove_menu.addAction("From List")
        remove_and_delete = remove_menu.addAction("From List and Delete File")
        remove_action.setMenu(remove_menu)
        remove_from_list.triggered.connect(partial(self.manager.remove_download, item.uid, delete_file=False))
        remove_and_delete.triggered.connect(partial(self.manager.remove_download, item.uid, delete_file=True))
        
        if item.status == DownloadStatus.FINISHED:
            open_folder_action = menu.addAction("Open Containing Folder")
            open_folder_action.triggered.connect(partial(self.open_item_folder, item))
        menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def show_download_progress_dialog(self, item):
        """Membuat dan menampilkan dialog progres untuk item download baru."""
        if item.uid in self.progress_dialogs:
            # Jika dialog sudah ada, bawa ke depan saja
            self.progress_dialogs[item.uid].show()
            self.progress_dialogs[item.uid].raise_()
            return
        
        dialog = DownloadProgressDialog(item, self)
        # Hubungkan sinyal dari dialog ke aksi di manager
        dialog.pause_resume_requested.connect(self._on_dialog_pause_resume_request)
        dialog.finished.connect(lambda: self.progress_dialogs.pop(item.uid, None)) # Hapus dari dict saat ditutup
        self.progress_dialogs[item.uid] = dialog
        dialog.show()

    @Slot(object)
    def update_progress_dialog(self, item):
        """Menerima sinyal update dari manager dan meneruskannya ke dialog yang sesuai."""
        if item.uid in self.progress_dialogs:
            dialog = self.progress_dialogs[item.uid]
            dialog.update_progress(item)
        # Tutup dialog secara otomatis jika sudah selesai, error, atau dihentikan
            if item.status in [DownloadStatus.FINISHED, DownloadStatus.ERROR, DownloadStatus.STOPPED]:
                dialog.accept() # Menutup dialog
                self.progress_dialogs.pop(item.uid, None)

    def _on_dialog_pause_resume_request(self, uid):
        """Menangani permintaan pause/resume dari dialog progres."""
        item = self.manager.get_item_by_uid(uid)
        if not item: return

        if item.status == DownloadStatus.DOWNLOADING:
            self.manager.control_download(uid, 'pause')
        elif item.status == DownloadStatus.PAUSED:
            self.manager.control_download(uid, 'resume')

    def show_settings_dialog(self):
        dialog = SettingsDialog(self.settings, self)
        dialog.exec()
        
    def show_about_dialog(self):        
        title = "About Macan Download Manager Pro"        
        text = """
        <div style='color: white;'>
        <p><b>Macan Download Manager Pro</b> is a robust and efficient download management application built using Python and the PySide6 (Qt) framework. It is designed to provide users with a powerful, multi-threaded, and aesthetically pleasing tool for managing their file downloads.</p>
        <p><b>Key Features include:</b></p>
        <ul>
            <li><b>Multi-threaded Downloading:</b> Utilizes <i>requests</i> library within separate <i>QThread</i> workers for concurrent and efficient file retrieval.</li>
            <li><b>Download Resume Support:</b> Automatically handles partial downloads and resumes from the last known position using HTTP Range headers.</li>
            <li><b>Configurable Limits:</b> Allows users to set a global maximum number of concurrent downloads and a speed limit (throttling) in KB/s.</li>
            <li><b>Advanced Filtering & Search:</b> Features a side-bar for filtering downloads by status and a dedicated search bar to filter by file name.</li>
            <li><b>Custom UI with Dark Theme:</b> Provides a modern, dark-themed user interface with custom SVG icons for a better visual experience.</li>
            <li><b>Persistent Storage:</b> Saves the download list and user settings, ensuring continuity across sessions.</li>
            <li><b>System Integration:</b> Includes a system tray icon and drag-and-drop support for easily adding new download URLs.</li>
            <li><b>Download Management:</b> Supports actions like Start, Pause, Stop, Stop All, and Retry for individual or multiple selected downloads.</li>
        </ul>
        <p>Macan Download Manager Pro aims to be a reliable and professional solution for all your downloading needs.</p>
        <hr>
        <p><i>Copyright 2025 - Danx Exodus - Macan Angkasa</i></p>
        """
        QMessageBox.about(self, title, text)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.show_add_download_dialog(url.toString())
            break

    # --- FUNGSI BARU DAN YANG DIUBAH UNTUK NOTIFIKASI & TRAY ---

    @Slot(str)
    def show_download_complete_notification(self, filename):
        """Menampilkan notifikasi di system tray saat download selesai."""
        self.tray_icon.showMessage(
            "Download Selesai",
            f"File '{filename}' telah berhasil diunduh.",
            QSystemTrayIcon.Information,
            5000  # milliseconds
        )
        
    def quit_application(self):
        """Memicu proses penutupan aplikasi secara penuh."""
        self.is_exiting = True
        self.close()

    def show_and_raise(self):
        """Menampilkan dan membawa window ke depan."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    @Slot(QSystemTrayIcon.ActivationReason)
    def on_tray_icon_activated(self, reason):
        """Menangani klik pada tray icon (klik ganda akan menampilkan window)."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_raise()

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.windowIcon())
        self.tray_icon.setToolTip("Macan Download Manager Pro")
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show_and_raise)
        add_action = tray_menu.addAction("Add Download")
        add_action.triggered.connect(lambda: self.show_add_download_dialog())
        tray_menu.addSeparator()
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.quit_application)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        minimize_on_close = self.settings.value("minimize_to_tray", True, type=bool)
        if minimize_on_close and not self.is_exiting:
            self.hide()
            event.ignore()
            self.tray_icon.showMessage(
                "Macan Download Manager",
                "Running on background.",
                QSystemTrayIcon.Information,
                2000
            )
            return

        active_downloads_exist = any(item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.QUEUED, DownloadStatus.PAUSED] for item in self.manager.downloads)
        if active_downloads_exist:
            reply = QMessageBox.question(self, 'Confirm Exit',
                "There are active downloads. Are you sure you want to exit? They will be paused.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return

        print("Closing application, stopping threads...")
        # ==================== BAGIAN YANG DIPERBAIKI ====================
        # Iterasi hanya pada unduhan yang mungkin memiliki thread aktif untuk menghindari error
        for item in self.manager.downloads:
            # Hanya periksa item yang statusnya Downloading atau Paused
            if item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED]:
                # Pastikan objek thread masih ada dan sedang berjalan sebelum mencoba menghentikannya
                if item.thread and item.thread.isRunning():
                    item.worker.stop()
                    item.thread.quit()
                    if not item.thread.wait(1000): # Beri waktu 1 detik untuk thread berhenti
                        print(f"Warning: Thread for {item.filename} did not stop in time.")
        # ===============================================================
        
        self.manager.save_downloads()
        self.tray_icon.hide()
        print("Downloads saved. Exiting.")
        event.accept()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QDialog { background-color: #262626; color: #FFFFFF; }
            QDialog QLabel, QDialog QCheckBox { color: white; }
            QMessageBox { background-color: #2F2F2F; color: white; }
            QToolBar { background-color: #333333; border: none; padding: 5px; spacing: 5px; }
            QToolBar QToolButton { padding: 6px; margin: 2px; border-radius: 4px; }
            QToolBar QToolButton:hover { background-color: #454545; }
            QToolBar::separator { width: 1px; background-color: #454545; margin-left: 4px; margin-right: 4px; }
            QListWidget { background-color: #2F2F2F; border: none; font-size: 14px; }
            QListWidget::item { padding: 10px 15px; }
            QListWidget::item:selected { background-color: #4A4A4A; border-left: 3px solid #8E44AD; }
            QListWidget::item:hover { background-color: #404040; }
            QTableView { background-color: #262626; border: none; gridline-color: #454545; color: #E0E0E0; }
            QHeaderView::section { background-color: #333333; color: white; padding: 4px; border: 1px solid #454545; font-weight: bold; }
            QTableView::item { padding-left: 5px; }
            QTableView::item:selected { background-color: #555; }
            QProgressBar { border: 1px solid #454545; border-radius: 4px; text-align: center; color: white; }
            QProgressBar::chunk { background: QLinearGradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8E44AD, stop:1 #9B59B6); border-radius: 4px; }
            QLineEdit, QPushButton, QComboBox, QSpinBox { padding: 5px; background-color: #333; border: 1px solid #555; border-radius: 4px; }
            QToolBar QLineEdit { padding: 4px; background-color: #FFFFFF; color: #000; }
            QPushButton { background-color: #8E44AD; font-weight: bold; }
            QPushButton:hover { background-color: #9B59B6; }
            QStatusBar { color: white; font-weight: bold; }
            QMenu { background-color: #333; color: white; border: 1px solid #555; }
            QMenu::item:selected { background-color: #8E44AD; }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Cek apakah ada argumen "--tray"
    if "--tray" in sys.argv:
        print("Starting in tray mode...")
        # Jangan tampilkan window utama, karena sudah ada tray icon
    else:
        window.show()
        
    sys.exit(app.exec())