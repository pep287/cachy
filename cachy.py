#!/usr/bin/env python3
# importzinhos
import os, re, json, threading, base64, urllib.request
from pathlib import Path
from datetime import timedelta
from urllib.parse import quote, urlparse, parse_qs

import yt_dlp
from yt_dlp.postprocessor import PostProcessor

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QProgressBar,
    QFileDialog, QMessageBox, QDialog, QDialogButtonBox,
    QSizePolicy, QFrame, QScrollArea,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette, QIcon
import sys



# tema do pyqt6

def make_qss(dark):
    if dark:
        bg      = "#111111"
        surface = "#1a1a1a"
        input_  = "#1e1e1e"
        border  = "#2e2e2e"
        border2 = "#3a3a3a"
        text    = "#e0e0e0"
        muted   = "#666666"
        section = "#888888"
        scroll  = "#2a2a2a"
        scroll_h= "#3a3a3a"
        combo_v = "#1e1e1e"
        msg_bg  = "#1a1a1a"
    else:
        bg      = "#f5f5f5"
        surface = "#ffffff"
        input_  = "#ffffff"
        border  = "#d0d0d0"
        border2 = "#bbbbbb"
        text    = "#1a1a1a"
        muted   = "#888888"
        section = "#555555"
        scroll  = "#e0e0e0"
        scroll_h= "#b0b0b0"
        combo_v = "#ffffff"
        msg_bg  = "#ffffff"

    return f"""
QWidget {{
    background-color: {bg};
    color: {text};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}}
QMainWindow, QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: {bg};
    border: none;
}}
QLineEdit {{
    background-color: {input_};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 8px 12px;
    color: {text};
    font-size: 13px;
    selection-background-color: #cc0000;
    selection-color: #ffffff;
}}
QLineEdit:focus {{
    border: 1px solid {border2};
}}
QPushButton {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 8px 16px;
    color: {text};
    font-size: 13px;
}}
QPushButton:hover {{
    border-color: {border2};
    background-color: {input_};
}}
QPushButton:pressed {{
    background-color: {border};
}}
QPushButton:disabled {{
    color: {muted};
    background-color: {surface};
}}
QPushButton#btn_fetch {{
    background-color: #cc0000;
    border: none;
    color: #ffffff;
    font-weight: bold;
}}
QPushButton#btn_fetch:hover {{
    background-color: #dd1111;
}}
QPushButton#btn_fetch:pressed {{
    background-color: #aa0000;
}}
QPushButton#btn_fetch:disabled {{
    background-color: #7a2222;
    color: #bbbbbb;
}}
QPushButton#btn_download {{
    background-color: #cc0000;
    border: none;
    color: #ffffff;
    font-size: 15px;
    font-weight: bold;
    border-radius: 10px;
    padding: 13px;
    letter-spacing: 1px;
}}
QPushButton#btn_download:hover {{
    background-color: #dd1111;
}}
QPushButton#btn_download:pressed {{
    background-color: #aa0000;
}}
QPushButton#btn_download:disabled {{
    background-color: #7a2222;
    color: #bbbbbb;
}}
QComboBox {{
    background-color: {input_};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 7px 12px;
    color: {text};
    min-width: 130px;
}}
QComboBox:hover {{
    border-color: {border2};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: right center;
    width: 24px;
    border: none;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {muted};
    width: 0;
    height: 0;
}}
QComboBox QAbstractItemView {{
    background-color: {combo_v};
    border: 1px solid {border};
    border-radius: 4px;
    selection-background-color: #cc0000;
    selection-color: #ffffff;
    color: {text};
    padding: 4px;
}}
QProgressBar {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: #cc0000;
    border-radius: 4px;
}}
QLabel {{
    color: {text};
    background: transparent;
}}
QLabel#lbl_muted {{
    color: {muted};
    font-size: 11px;
}}
QLabel#lbl_title {{
    font-size: 22px;
    font-weight: bold;
    color: {text};
}}
QLabel#lbl_section {{
    color: {section};
    font-size: 10px;
    font-weight: bold;
}}
QFrame#card {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 10px;
}}
QFrame#divider {{
    background-color: {border};
    max-height: 1px;
    border: none;
}}
QScrollBar:vertical {{
    background: {bg};
    width: 6px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {scroll_h};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QDialog, QMessageBox {{
    background-color: {surface};
}}
"""



# logger

class DownloadLogger:
    def __init__(self, error_list):
        self._errors = error_list

    def debug(self, msg): pass
    def warning(self, msg): pass

    def error(self, msg):
        if msg.startswith("ERROR: "):
            self._errors.append(msg[7:])



# injetor de metadados 🏳️‍🌈

class MetadataInjectorPP(PostProcessor):
    def __init__(self, downloader, meta):
        super().__init__(downloader)
        self.meta = meta or {}

    def run(self, info):
        if not self.meta:
            return [], info
        mapping = {
            'artist': 'artist', 'title': 'title', 'album': 'album',
            'track': 'track_number', 'genre': 'genre',
        }
        for our_key, yt_key in mapping.items():
            val = self.meta.get(our_key)
            if val:
                info[yt_key] = val
        # year vai pro upload_date no formato correto YYYYMMDD
        year = self.meta.get('year')
        if year and len(str(year)) == 4:
            info['upload_date'] = f"{year}0101"
        return [], info



# ain threadzinha amo python

class FetchWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            opts = {
                "quiet": True, "no_warnings": True,
                "extract_flat": True, "skip_download": True,
                "socket_timeout": 20,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class ThumbnailWorker(QObject):
    finished = pyqtSignal(bytes)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            resp = urllib.request.urlopen(self.url, timeout=10)
            self.finished.emit(resp.read())
        except Exception:
            pass


class MetadataWorker(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, title):
        super().__init__()
        self.title = title

    def run(self):
        result = CachyWindow.enrich_metadata_static(self.title)
        if result:
            self.finished.emit(result)


class DownloadWorker(QObject):
    progress = pyqtSignal(float, str, str)   # pct, info_str, status_str
    processing = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, opts, enriched_meta, is_playlist, playlist_count):
        super().__init__()
        self.url = url
        self.opts = opts
        self.enriched_meta = enriched_meta
        self.is_playlist = is_playlist
        self.playlist_count = playlist_count
        self.playlist_index = 0

    def run(self):
        self.opts['progress_hooks'] = [self._hook]
        try:
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                if self.enriched_meta:
                    ydl.add_post_processor(
                        MetadataInjectorPP(ydl, self.enriched_meta),
                        when='pre_process',
                    )
                ydl.download([self.url])
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = downloaded / total
                speed = d.get("speed", 0)
                eta = d.get("eta", 0)
                speed_str = fmt_speed(speed) if speed else "?"
                eta_str = str(timedelta(seconds=int(eta))) if eta else "?"
                info_str = f"{fmt_size(downloaded)} / {fmt_size(total)}  |  {speed_str}  |  ETA: {eta_str}"
                if self.is_playlist and self.playlist_count > 0:
                    status_str = f"Baixando... {self.playlist_index + 1}/{self.playlist_count}  •  {pct*100:.1f}%"
                else:
                    status_str = f"Baixando... {pct*100:.1f}%"
                self.progress.emit(pct, info_str, status_str)
        elif d["status"] == "finished":
            if self.is_playlist:
                self.playlist_index += 1
            self.processing.emit(self.playlist_index)
        elif d["status"] == "error":
            self.error.emit("Erro durante o download")



# HELPERS

def fmt_speed(s):
    if s >= 1_000_000: return f"{s/1_000_000:.1f} MB/s"
    if s >= 1_000: return f"{s/1_000:.0f} KB/s"
    return f"{s:.0f} B/s"

def fmt_size(s):
    if s >= 1_000_000_000: return f"{s/1_000_000_000:.2f} GB"
    if s >= 1_000_000: return f"{s/1_000_000:.1f} MB"
    if s >= 1_000: return f"{s/1_000:.0f} KB"
    return f"{s:.0f} B"



# preset da caixa de dialogo

class ChoiceDialog(QDialog):
    def __init__(self, parent, title, message, choices):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.choice = None
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        for key, label in choices:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._pick(k))
            layout.addWidget(btn)

    def _pick(self, key):
        self.choice = key
        self.accept()


class InputDialog(QDialog):
    def __init__(self, parent, title, placeholder):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        layout.addWidget(self.input)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def value(self):
        return self.input.text().strip()



# main window

class CachyWindow(QMainWindow):
    # vamo atualizar a ui atraves de thread pq SIM EU ADORO PYHTON E ESSAS FRESCURA
    sig_display_info   = pyqtSignal(dict)
    sig_fetch_error    = pyqtSignal(str)
    sig_thumb          = pyqtSignal(bytes)
    sig_meta           = pyqtSignal(dict)
    sig_progress       = pyqtSignal(float, str, str)
    sig_processing     = pyqtSignal(int)
    sig_dl_finished    = pyqtSignal()
    sig_dl_error       = pyqtSignal(str)
    sig_playlist_count = pyqtSignal(int)

    VIDEO_QS = ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p"]
    AUDIO_QS = ["best", "320k", "256k", "192k", "128k", "96k", "64k"]

    def __init__(self):
        super().__init__()
        self.download_path = str(Path.home() / "Downloads")
        self.video_info = None
        self.enriched_meta = None
        self.downloading = False
        self.is_playlist = False
        self.playlist_items = None
        self.download_url = None
        self.playlist_subfolder = None
        self.playlist_index = 0
        self.playlist_count = 0
        self.download_errors = []
        self._threads = []

        self._connect_signals()
        self._build_ui()

    def _connect_signals(self):
        self.sig_display_info.connect(self.display_info)
        self.sig_fetch_error.connect(self.fetch_error)
        self.sig_thumb.connect(self.set_thumbnail)
        self.sig_meta.connect(self.set_metadata)
        self.sig_progress.connect(self.update_progress)
        self.sig_processing.connect(self.on_processing)
        self.sig_dl_finished.connect(self.download_finished)
        self.sig_dl_error.connect(self.download_error)
        self.sig_playlist_count.connect(self._set_playlist_count)

    # ----------------------------------------------------------
    # UI
    # ----------------------------------------------------------
    def _build_ui(self):
        self.setWindowTitle("Cachy")
        self.setMinimumSize(700, 640)
        self.resize(820, 720)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setCentralWidget(scroll)

        container = QWidget()
        container.setMinimumWidth(640)
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(0)

        # --- Cabeçalho ---
        header = QHBoxLayout()
        title_lbl = QLabel("Cachy")
        title_lbl.setObjectName("lbl_title")
        header.addWidget(title_lbl)
        header.addStretch()
        self.theme_btn = QPushButton("Tema")
        self.theme_btn.setFixedWidth(90)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self._dark_mode = True
        header.addWidget(self.theme_btn)
        root.addLayout(header)
        root.addSpacing(20)

        # --- URL ---
        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole a URL do YouTube aqui...")
        self.url_input.returnPressed.connect(self.fetch_info)
        url_row.addWidget(self.url_input)

        self.paste_btn = QPushButton("Colar")
        self.paste_btn.setFixedWidth(80)
        self.paste_btn.clicked.connect(self.paste_url)
        url_row.addWidget(self.paste_btn)

        self.fetch_btn = QPushButton("Buscar")
        self.fetch_btn.setObjectName("btn_fetch")
        self.fetch_btn.setFixedWidth(90)
        self.fetch_btn.clicked.connect(self.fetch_info)
        url_row.addWidget(self.fetch_btn)
        root.addLayout(url_row)
        root.addSpacing(16)

        # --- Card de informações ---
        self.info_card = QFrame()
        self.info_card.setObjectName("card")
        self.info_card.setVisible(False)
        card_layout = QHBoxLayout(self.info_card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(14)

        self.thumb_lbl = QLabel()
        self.thumb_lbl.setFixedSize(160, 90)
        self.thumb_lbl.setStyleSheet("background:#2a2a2a; border-radius:6px;")
        self.thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.thumb_lbl)

        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        self.lbl_vtitle = QLabel("Nenhum vídeo carregado")
        self.lbl_vtitle.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_vtitle.setWordWrap(True)
        self.lbl_vuploader = QLabel("")
        self.lbl_vuploader.setObjectName("lbl_muted")
        self.lbl_vmeta = QLabel("")
        self.lbl_vmeta.setObjectName("lbl_muted")
        self.lbl_vduration = QLabel("")
        self.lbl_vduration.setObjectName("lbl_muted")
        info_col.addWidget(self.lbl_vtitle)
        info_col.addWidget(self.lbl_vuploader)
        info_col.addWidget(self.lbl_vmeta)
        info_col.addWidget(self.lbl_vduration)
        info_col.addStretch()
        card_layout.addLayout(info_col)
        root.addWidget(self.info_card)
        root.addSpacing(16)

        # --- Configurações ---
        settings_row = QHBoxLayout()
        settings_row.setSpacing(20)

        def setting_group(label_text, widget):
            col = QVBoxLayout()
            col.setSpacing(6)
            lbl = QLabel(label_text.upper())
            lbl.setObjectName("lbl_section")
            col.addWidget(lbl)
            col.addWidget(widget)
            return col

        self.format_dd = QComboBox()
        for key, text in [
            ("mp4","mp4  (vídeo)"), ("webm","webm (vídeo)"), ("mkv","mkv  (vídeo)"),
            ("mp3","mp3  (áudio)"), ("m4a","m4a  (áudio)"),
            ("opus","opus (áudio)"), ("wav","wav  (áudio)"),
        ]:
            self.format_dd.addItem(text, key)
        self.format_dd.currentIndexChanged.connect(self.on_format_change)
        settings_row.addLayout(setting_group("Formato", self.format_dd))

        self.quality_dd = QComboBox()
        for q in self.VIDEO_QS:
            self.quality_dd.addItem(q)
        self.quality_dd.setCurrentText("720p")
        settings_row.addLayout(setting_group("Qualidade", self.quality_dd))

        self.subs_dd = QComboBox()
        for s in ["nenhuma", "auto (geradas)", "manuais", "todas"]:
            self.subs_dd.addItem(s)
        settings_row.addLayout(setting_group("Legendas", self.subs_dd))

        settings_row.addStretch()
        root.addLayout(settings_row)
        root.addSpacing(16)

        # --- Divider ---
        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        div.setFixedHeight(1)
        root.addWidget(div)
        root.addSpacing(14)

        # --- Pasta de destino ---
        path_row = QHBoxLayout()
        path_lbl_fixed = QLabel("Salvar em:")
        path_lbl_fixed.setObjectName("lbl_muted")
        path_row.addWidget(path_lbl_fixed)
        self.path_lbl = QLabel(self.download_path)
        self.path_lbl.setObjectName("lbl_muted")
        self.path_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        path_row.addWidget(self.path_lbl)
        browse_btn = QPushButton("Procurar")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self.browse_path)
        path_row.addWidget(browse_btn)
        root.addLayout(path_row)
        root.addSpacing(12)

        # --- Barra de progresso ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        root.addWidget(self.progress_bar)
        root.addSpacing(6)

        self.progress_lbl = QLabel("")
        self.progress_lbl.setObjectName("lbl_muted")
        root.addWidget(self.progress_lbl)
        root.addSpacing(12)

        # --- Botão de download ---
        self.download_btn = QPushButton("BAIXAR")
        self.download_btn.setObjectName("btn_download")
        self.download_btn.setFixedHeight(50)
        self.download_btn.clicked.connect(self.start_download)
        root.addWidget(self.download_btn)
        root.addSpacing(8)

        # --- Status ---
        self.status_lbl = QLabel("Pronto")
        self.status_lbl.setObjectName("lbl_muted")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status_lbl)
        root.addStretch()

    
    # Tema escuro e claro 🏳️‍🌈

    def toggle_theme(self):
        self._dark_mode = not self._dark_mode
        QApplication.instance().setStyleSheet(make_qss(self._dark_mode))
        self.theme_btn.setText('Claro' if self._dark_mode else 'Escuro')

    
    # funcao de colar direto da clipboard do OS e pra pegar a pasta de download
    
    def paste_url(self):
        clip = QApplication.clipboard().text().strip()
        if clip and ("youtube.com" in clip or "youtu.be" in clip):
            self.url_input.setText(clip)

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "Escolher pasta de download", self.download_path
        )
        if path:
            self.download_path = path
            self.path_lbl.setText(path)

    
    # funcao pra ver o formato do q vc vai baixar duhhhhhhhhhh
   
    def on_format_change(self):
        fmt = self.format_dd.currentData()
        is_audio = fmt in ("mp3", "m4a", "opus", "wav")
        cur = self.quality_dd.currentText()
        self.quality_dd.blockSignals(True)
        self.quality_dd.clear()
        if is_audio:
            for q in self.AUDIO_QS:
                self.quality_dd.addItem(q)
            self.quality_dd.setCurrentText("192k" if cur not in self.AUDIO_QS else cur)
        else:
            for q in self.VIDEO_QS:
                self.quality_dd.addItem(q)
            self.quality_dd.setCurrentText("720p" if cur not in self.VIDEO_QS else cur)
        self.quality_dd.blockSignals(False)

    # puxar as info do link
 
    def _parse_youtube_url(self, url):
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if "youtube.com" not in host and "youtu.be" not in host:
                return None, False, None
            qs = parse_qs(parsed.query)
            list_id = qs.get("list", [None])[0]
            if not list_id:
                return None, False, None
            is_mix = "start_radio=1" in url or list_id.startswith("RD")
            video_id = qs.get("v", [None])[0]
            return list_id, is_mix, video_id
        except Exception:
            return None, False, None

    def fetch_info(self):
        url = self.url_input.text().strip()
        if not url:
            self._show_msg("Cole uma URL do YouTube primeiro.")
            return
        self.enriched_meta = None
        self.video_info = None
        self.is_playlist = False
        self.playlist_items = None
        self.download_url = url

        self.fetch_btn.setText("Buscando...")
        self.fetch_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.info_card.setVisible(False)
        self.status_lbl.setText("Analisando URL...")
        self.progress_bar.setValue(0)
        self.progress_lbl.setText("")

        list_id, is_mix, video_id = self._parse_youtube_url(url)
        if list_id:
            self._ask_playlist(url, list_id, is_mix, video_id)
            return
        self._start_fetch(url)

    def _start_fetch(self, url):
        worker = FetchWorker(url)
        thread = QThread()
        worker.moveToThread(thread)
        worker.finished.connect(self.sig_display_info)
        worker.error.connect(self.sig_fetch_error)
        thread.started.connect(worker.run)
        thread.start()
        self._threads.append((thread, worker))

        self._fetch_timer = QTimer()
        self._fetch_timer.setSingleShot(True)
        self._fetch_timer.timeout.connect(self._fetch_timeout)
        self._fetch_timer.start(40000)

    def _fetch_timeout(self):
        if not self.fetch_btn.isEnabled():
            self.fetch_btn.setText("Buscar")
            self.fetch_btn.setEnabled(True)
            self.download_btn.setEnabled(True)
            self.status_lbl.setText("Tempo limite. Verifique a URL ou sua internet.")
            self.progress_bar.setValue(0)

   
    # mostrar as info do video de forma bonitinha
 
    def display_info(self, info):
        if hasattr(self, '_fetch_timer'):
            self._fetch_timer.stop()
        self.fetch_btn.setText("Buscar")
        self.fetch_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.video_info = info

        title = info.get("title", "Sem título")
        uploader = info.get("uploader", info.get("channel", "Desconhecido"))
        dur = info.get("duration", 0)
        views = info.get("view_count", 0)
        likes = info.get("like_count", 0)

        dur_str = str(timedelta(seconds=int(dur))) if dur else "?"
        views_str = f"{views:,}" if views else "?"
        likes_str = f"{likes:,}" if likes else "?"

        self.lbl_vtitle.setText(title)
        self.lbl_vuploader.setText(uploader)
        self.lbl_vmeta.setText(f"{views_str} visualizações  •  {likes_str} likes")
        self.lbl_vduration.setText(dur_str)
        self.info_card.setVisible(True)
        self.status_lbl.setText("Vídeo carregado")

        thumb_url = info.get("thumbnail")
        if thumb_url:
            tw = ThumbnailWorker(thumb_url)
            tt = QThread()
            tw.moveToThread(tt)
            tw.finished.connect(self.sig_thumb)
            tt.started.connect(tw.run)
            tt.start()
            self._threads.append((tt, tw))

        mw = MetadataWorker(title)
        mt = QThread()
        mw.moveToThread(mt)
        mw.finished.connect(self.sig_meta)
        mt.started.connect(mw.run)
        mt.start()
        self._threads.append((mt, mw))

    def set_thumbnail(self, data):
        px = QPixmap()
        px.loadFromData(data)
        self.thumb_lbl.setPixmap(
            px.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                      Qt.TransformationMode.SmoothTransformation)
        )

    def set_metadata(self, meta):
        self.enriched_meta = meta
        parts = [meta.get('artist', '?'), '—', meta.get('title', '?')]
        if meta.get('album'):
            parts.append(f"• {meta['album']}")
        self.lbl_vtitle.setText(' '.join(parts))

    def _show_playlist_info(self, title, desc):
        self.lbl_vtitle.setText(f"{title}")
        self.lbl_vuploader.setText("")
        self.lbl_vmeta.setText(f"Playlist — {desc}")
        self.lbl_vduration.setText("")
        self.thumb_lbl.clear()
        self.info_card.setVisible(True)
        self.status_lbl.setText("Playlist carregada")

    def fetch_error(self, msg):
        if hasattr(self, '_fetch_timer'):
            self._fetch_timer.stop()
        self.fetch_btn.setText("Buscar")
        self.fetch_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.lbl_vtitle.setText("Erro ao carregar vídeo")
        self.info_card.setVisible(True)

        friendly = msg
        if "Unsupported URL" in msg: friendly = "URL não suportada."
        elif "HTTP Error" in msg: friendly = "Erro de conexão. Verifique sua internet."
        elif "Private video" in msg: friendly = "Este vídeo é privado."
        elif "copyright" in msg.lower(): friendly = "Vídeo indisponível por direitos autorais."
        elif "age" in msg.lower(): friendly = "Vídeo com restrição de idade."

        self.status_lbl.setText("Erro ao obter informações")
        self._show_msg(friendly)

    
    # outra funcao q fiz por conta do youtube ser uma merda com playlist/mix
   
    def _ask_playlist(self, url, list_id, is_mix, video_id):
        self.is_playlist = True
        self.fetch_btn.setText("Buscar")
        self.fetch_btn.setEnabled(True)
        self.download_btn.setEnabled(True)

        if is_mix:
            choices = []
            if video_id:
                choices.append(("single", "Baixar esta música"))
            choices.append(("cancel", "Cancelar"))
            dlg = ChoiceDialog(self, "Mix não suportado",
                               "Mixes do YouTube não podem ser baixados.\nDeseja baixar apenas a música atual?",
                               choices)
            dlg.exec()
            if dlg.choice == "single" and video_id:
                clean_url = f"https://youtube.com/watch?v={video_id}"
                self.is_playlist = False
                self.download_url = clean_url
                self.status_lbl.setText("Obtendo informações...")
                self._start_fetch(clean_url)
            else:
                self.fetch_btn.setEnabled(True)
                self.download_btn.setEnabled(True)
                self.progress_bar.setValue(0)
                self.status_lbl.setText("Pronto")
            return

        label = "Playlist"
        has_video_id = bool(video_id)
        choices = [
            ("first", "Primeiro vídeo" if has_video_id else "Apenas o primeiro"),
            ("all", "Todas"),
        ]
        dlg = ChoiceDialog(self, f"{label} detectada", "O que deseja baixar?", choices)
        dlg.exec()
        self._on_playlist_choice(url, list_id, is_mix, video_id, dlg.choice or "cancel", label)

    def _on_playlist_choice(self, url, list_id, is_mix, video_id, choice, label):
        if choice == "cancel":
            self.fetch_btn.setEnabled(True)
            self.download_btn.setEnabled(True)
            self.status_lbl.setText("Pronto")
            return

        if choice == "first" and video_id:
            self.playlist_items = None
            self.download_url = f"https://youtube.com/watch?v={video_id}"
            self.status_lbl.setText("Obtendo informações...")
            self._start_fetch(self.download_url)
            return

        if choice == "first":
            self.playlist_items = "1"
        else:
            self.playlist_items = None

        self.download_url = f"https://youtube.com/playlist?list={list_id}"
        self.progress_bar.setValue(0)
        self.status_lbl.setText("Pronto")
        desc = "todas"
        self._show_playlist_info(label, desc)

    # funcao pra puxar os meta dado (pqp q treco chato)
   
    @staticmethod
    def clean_title(title):
        t = re.sub(r'\s*\(.*?(?:of+icial|video|music|lyric|audio|4K|HD|HQ|remaster).*?\)', '', title, flags=re.IGNORECASE)
        t = re.sub(r'\s*\[.*?(?:of+icial|video|music|lyric|audio|4K|HD|HQ|remaster).*?\]', '', t, flags=re.IGNORECASE)
        t = re.sub(r'\s*\|.*', '', t)
        return t.strip()

    @staticmethod
    def parse_artist_title(title):
        m = re.match(r'^(.+?)\s*[-–—|]\s*(.+)$', title)
        return (m.group(1).strip(), m.group(2).strip()) if m else (None, title)

    @staticmethod
    def search_deezer(artist, song):
        try:
            q = quote(f'artist:"{artist}" track:"{song}"')
            resp = urllib.request.urlopen(f'https://api.deezer.com/search?q={q}&limit=3', timeout=8)
            data = json.loads(resp.read())
            for t in data.get('data', []):
                return {
                    'artist': t.get('artist', {}).get('name', artist),
                    'title': t.get('title', song),
                    'album': t.get('album', {}).get('title', ''),
                    'track': str(t.get('track_position', '')),
                    'genre': (t.get('genres', {}).get('data', [{}])[0].get('name', '') if t.get('genres', {}).get('data') else ''),
                    'year': (t.get('release_date', '')[:4] if t.get('release_date') else ''),
                }
        except Exception:
            return None

    @staticmethod
    def search_itunes(artist, song):
        try:
            q = quote(f'{artist} {song}')
            resp = urllib.request.urlopen(f'https://itunes.apple.com/search?term={q}&limit=3&entity=song', timeout=8)
            data = json.loads(resp.read())
            for r in data.get('results', []):
                return {
                    'artist': r.get('artistName', artist),
                    'title': r.get('trackName', song),
                    'album': r.get('collectionName', ''),
                    'track': str(r.get('trackNumber', '')),
                    'genre': r.get('primaryGenreName', ''),
                    'year': (r.get('releaseDate', '')[:4] if r.get('releaseDate') else ''),
                }
        except Exception:
            return None

    @staticmethod
    def enrich_metadata_static(title):
        cleaned = CachyWindow.clean_title(title)
        artist, song = CachyWindow.parse_artist_title(cleaned)
        if not artist:
            return None
        return CachyWindow.search_deezer(artist, song) or CachyWindow.search_itunes(artist, song)

    
    # Funcao de Download
    
    def build_ydl_opts(self):
        fmt = self.format_dd.currentData()
        quality = self.quality_dd.currentText()
        audio_only = fmt in ("mp3", "m4a", "opus", "wav")
        subs = self.subs_dd.currentText()
        dl_path = self.download_path
        if self.playlist_subfolder:
            dl_path = os.path.join(dl_path, self.playlist_subfolder)
        outtmpl = os.path.join(dl_path, "%(title)s.%(ext)s")
        pps = []

        if audio_only:
            outtmpl = os.path.join(dl_path, "%(title)s [%(id)s].%(ext)s")
            fmt_str = "bestaudio/best"
            audio_q = "0" if quality == "best" else quality
            pps.append({"key": "FFmpegExtractAudio", "preferredcodec": fmt, "preferredquality": audio_q})
            pps.append({"key": "EmbedThumbnail"})
        else:
            qmap = {
                "best": "bestvideo+bestaudio/best",
                "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
                "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
                "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            }
            fmt_str = qmap.get(quality, "bestvideo+bestaudio/best")
            merge = fmt if fmt in ("mkv", "webm") else "mp4"
            pps.append({"key": "FFmpegVideoConvertor", "preferedformat": merge})

        subs_opts = {"writesubtitles": False, "writeautomaticsub": False, "subtitleslangs": [], "embedsubs": False}
        if subs == "auto (geradas)":
            subs_opts.update({"writeautomaticsub": True, "subtitleslangs": ["pt", "pt-BR", "en"], "embedsubs": True})
        elif subs == "manuais":
            subs_opts.update({"writesubtitles": True, "subtitleslangs": ["pt", "pt-BR", "en"], "embedsubs": True})
        elif subs == "todas":
            subs_opts.update({"writesubtitles": True, "writeautomaticsub": True, "embedsubs": True})

        pps.append({"key": "FFmpegMetadata"})

        opts = {
            "format": fmt_str, "outtmpl": outtmpl, "postprocessors": pps,
            "quiet": True, "no_warnings": True, "writethumbnail": audio_only,
            **subs_opts,
        }
        if self.is_playlist:
            opts["ignoreerrors"] = True
            opts["logger"] = DownloadLogger(self.download_errors)
        if self.playlist_items:
            opts["playlist_items"] = self.playlist_items
        return opts

    def start_download(self):
        if self.downloading:
            return
        url = self.download_url or self.url_input.text().strip()
        if not url:
            self._show_msg("Cole uma URL do YouTube primeiro.")
            return
        if not self.video_info and not self.is_playlist:
            self._show_msg("Carregue as informações do vídeo primeiro.")
            return

        if self.is_playlist:
            self._ask_folder_and_download(url)
        else:
            self._begin_download(url)

    def _ask_folder_and_download(self, url):
        dlg = ChoiceDialog(self, "Pasta para playlist",
                           "Deseja criar uma pasta separada para os arquivos?",
                           [("playlist_name", "Usar nome da playlist"),
                            ("custom", "Nome personalizado"),
                            ("none", "Não criar")])
        dlg.exec()
        choice = dlg.choice or "none"
        if choice == "playlist_name":
            self.playlist_subfolder = True
            self._begin_download(url)
        elif choice == "custom":
            inp = InputDialog(self, "Nome da pasta", "Nome da pasta")
            if inp.exec() and inp.value():
                self.playlist_subfolder = inp.value()
                self._begin_download(url)
        else:
            self._begin_download(url)

    def _begin_download(self, url):
        self.downloading = True
        self.playlist_index = 0
        self.playlist_count = 0
        self.download_errors.clear()
        self.download_btn.setText("BAIXANDO...")
        self.download_btn.setEnabled(False)
        self.fetch_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_lbl.setText("Iniciando...")
        self.status_lbl.setText("Baixando...")

        opts = self.build_ydl_opts()

        if self.is_playlist:
            threading.Thread(target=self._extract_and_download, args=(url, opts), daemon=True).start()
        else:
            self._run_download_worker(url, opts)

    def _extract_and_download(self, url, opts):
        try:
            ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True, "socket_timeout": 20}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            entries = info.get("entries") or []
            count = len(entries)
            self.sig_playlist_count.emit(count)
            if self.playlist_subfolder is True:
                title = info.get("title") or "playlist"
                self.playlist_subfolder = re.sub(r'[\\/:*?"<>|]', '_', title).strip() or "playlist"
        except Exception:
            pass
        self._run_download_worker(url, opts)

    def _set_playlist_count(self, count):
        self.playlist_count = count
        if count > 0:
            self.status_lbl.setText(f"Baixando... 1/{count}")

    def _run_download_worker(self, url, opts):
        worker = DownloadWorker(url, opts, self.enriched_meta, self.is_playlist, self.playlist_count)
        thread = QThread()
        worker.moveToThread(thread)
        worker.progress.connect(self.sig_progress)
        worker.processing.connect(self.sig_processing)
        worker.finished.connect(self.sig_dl_finished)
        worker.error.connect(self.sig_dl_error)
        thread.started.connect(worker.run)
        thread.start()
        self._threads.append((thread, worker))

    
    # barra de progresso
    
    def update_progress(self, pct, info_str, status_str):
        self.progress_bar.setValue(int(pct * 1000))
        self.progress_lbl.setText(info_str)
        self.status_lbl.setText(status_str)

    def on_processing(self, index):
        self.playlist_index = index
        self.progress_bar.setValue(1000)
        self.progress_lbl.setText("Processando...")
        if self.is_playlist and self.playlist_count > 0:
            self.status_lbl.setText(f"Processando... {index}/{self.playlist_count}")
        else:
            self.status_lbl.setText("Processando...")

    
    # terminou yipiii 🎇🎇
   
    def download_finished(self):
        success = self.playlist_index if self.is_playlist else 1
        errors = self.download_errors
        self.progress_lbl.setText("Download concluído!")
        self.download_btn.setText("BAIXAR")
        self.download_btn.setEnabled(True)
        self.fetch_btn.setEnabled(True)
        self.downloading = False
        self.playlist_subfolder = None

        if self.is_playlist and errors:
            reasons = {}
            for err in errors:
                r = self._categorize_error(err)
                reasons[r] = reasons.get(r, 0) + 1
            fail_summary = ", ".join(f"{n}x {r}" for r, n in reasons.items())
            msg = f"{success} vídeo(s) baixado(s)\nFalhas: {fail_summary}"
            self.status_lbl.setText(f"{success} ok, {len(errors)} falha(s)")
            QMessageBox.warning(self, "Concluído com falhas", msg)
        else:
            self.status_lbl.setText("Download finalizado com sucesso!")
            QMessageBox.information(self, "Sucesso", f"Download concluído!\nSalvo em: {self.download_path}")

        self._notify("Cachy", self.status_lbl.text())

    def _categorize_error(self, msg):
        if "private video" in msg.lower(): return "Vídeo privado"
        if "video unavailable" in msg.lower(): return "Vídeo indisponível"
        if "copyright" in msg.lower(): return "Direitos autorais"
        if "age" in msg.lower(): return "Restrição de idade"
        if "membership" in msg.lower(): return "Membro"
        return "Outro erro"

    def download_error(self, msg):
        if "ffmpeg" in msg.lower() and "not found" in msg.lower():
            msg = "FFmpeg não encontrado."
        elif "private video" in msg.lower():
            msg = "Vídeo privado — não é possível baixar sem cookies."
        self.status_lbl.setText(f"Erro: {msg[:80]}")
        self.progress_lbl.setText("")
        self.download_btn.setText("BAIXAR")
        self.download_btn.setEnabled(True)
        self.fetch_btn.setEnabled(True)
        self.downloading = False
        self.playlist_subfolder = None
        self.progress_bar.setValue(0)
        self._notify("Cachy — Erro", msg)
        QMessageBox.critical(self, "Erro", msg)

    def _show_msg(self, msg):
        QMessageBox.information(self, "Cachy", msg)

    def _notify(self, title, msg):
        import subprocess
        try:
            if sys.platform == "linux":
                subprocess.run(["notify-send", title, msg], stderr=subprocess.DEVNULL)
            elif sys.platform == "darwin":
                subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "{title}"'])
            elif sys.platform == "win32":
                subprocess.run(["powershell", "-Command", f'New-BurntToastNotification -Text "{title}", "{msg}"'])
        except Exception:
            pass



# entry point

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(make_qss(True))
    window = CachyWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()