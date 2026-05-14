"""
Custom file picker dialog with cyberpunk JARVIS theme.
Replaces native QFileDialog with a styled version.
"""

from pathlib import Path
import os

from PyQt6.QtCore import Qt, QDir, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPen, QBrush, QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QLabel, QWidget, QScrollArea,
    QFileDialog, QApplication, QStyle,
)
from PyQt6.QtCore import QSize


# Color palette (matching JARVIS theme)
class C:
    BG        = "#00060a"
    PANEL     = "#010d14"
    PANEL2    = "#010f18"
    BORDER    = "#0d3347"
    BORDER_B  = "#1a5c7a"
    BORDER_A  = "#0f4060"
    PRI       = "#00d4ff"
    PRI_DIM   = "#007a99"
    PRI_GHO   = "#001f2e"
    ACC       = "#ff6b00"
    ACC2      = "#ffcc00"
    GREEN     = "#00ff88"
    GREEN_D   = "#00aa55"
    RED       = "#ff3355"
    MUTED_C   = "#ff3366"
    TEXT      = "#8ffcff"
    TEXT_DIM  = "#3a8a9a"
    TEXT_MED  = "#5ab8cc"
    WHITE     = "#d8f8ff"
    DARK      = "#000d14"
    BAR_BG    = "#011520"


def qcol(h: str, a: int = 255) -> QColor:
    c = QColor(h); c.setAlpha(a); return c


_ICONS = {
    "folder":  ("📁", "#ffcc00"),
    "file":    ("📄", "#5ab8cc"),
    "image":   ("🖼", "#00d4ff"),
    "video":   ("🎬", "#ff6b00"),
    "audio":   ("🎵", "#cc44ff"),
    "pdf":     ("📋", "#ff4444"),
    "code":    ("💻", "#ffcc00"),
    "archive": ("📦", "#ff8844"),
    "doc":     ("📝", "#4488ff"),
    "unknown": ("📎", "#888888"),
}

_EXT_CATS = {
    **dict.fromkeys(["jpg","jpeg","png","gif","webp","bmp","svg","ico","tiff"], "image"),
    **dict.fromkeys(["mp4","avi","mov","mkv","wmv","flv","webm","m4v"], "video"),
    **dict.fromkeys(["mp3","wav","ogg","m4a","aac","flac","wma","opus"], "audio"),
    **dict.fromkeys(["pdf"], "pdf"),
    **dict.fromkeys(["doc","docx","odt","rtf"], "doc"),
    **dict.fromkeys(["py","js","ts","jsx","tsx","html","css","java","c","cpp",
                     "cs","go","rs","rb","php","swift","kt","sh","sql","lua"], "code"),
    **dict.fromkeys(["zip","rar","tar","gz","7z","bz2","xz"], "archive"),
}


def _cat(path: Path) -> str:
    if path.is_dir():
        return "folder"
    return _EXT_CATS.get(path.suffix.lower().lstrip("."), "file")


def _fmt_sz(sz: int) -> str:
    if sz < 1024:    return f"{sz} B"
    if sz < 1048576: return f"{sz/1024:.1f} KB"
    if sz < 1073741824: return f"{sz/1048576:.1f} MB"
    return f"{sz/1073741824:.1f} GB"


def _icon(path: Path):
    cat = _cat(path)
    if cat == "folder":
        return _ICONS["folder"]
    return _ICONS.get(_EXT_CATS.get(path.suffix.lower().lstrip("."), "unknown"), _ICONS["unknown"])


class _FileItem(QListWidgetItem):
    def __init__(self, path: Path):
        super().__init__()
        self.path = path
        self.setText(f"  {path.name}")
        self.setFont(QFont("Courier New", 9))

        cat  = _cat(path)
        ico  = _icon(path)
        icon = ico[0]
        col  = ico[1]

        if cat == "folder":
            self.setForeground(qcol("#ffcc00"))
        else:
            self.setForeground(qcol(col))


class FilePickerDialog(QDialog):
    """
    Custom file picker styled as JARVIS cyberpunk dark UI.
    Shows directory contents with file icons, supports typing to filter.
    """

    def __init__(self, start_dir=None, parent=None, title="Select a File"):
        super().__init__(parent)
        self.selected_file = None
        self._history = []

        base = start_dir or str(Path.home())
        self._dir = Path(base).resolve()

        self.setWindowTitle(title)
        self.setMinimumSize(620, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background: {C.BG};
                border: 1px solid {C.BORDER_B};
                border-radius: 6px;
            }}
        """)

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(48)
        hdr.setStyleSheet(f"background: {C.DARK}; border-bottom: 1px solid {C.BORDER_B};")
        hl  = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 0, 14, 0)

        self._title_lbl = QLabel("SELECT FILE")
        self._title_lbl.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        self._title_lbl.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        hl.addWidget(self._title_lbl)
        hl.addStretch()

        self._path_lbl = QLabel(str(self._dir))
        self._path_lbl.setFont(QFont("Courier New", 8))
        self._path_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        self._path_lbl.setMaximumWidth(400)
        hl.addWidget(self._path_lbl, stretch=0)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setFont(QFont("Courier New", 10))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C.TEXT_DIM};
                border: 1px solid {C.BORDER}; border-radius: 3px;
            }}
            QPushButton:hover {{ color: {C.RED}; border-color: {C.RED}; }}
        """)
        close_btn.clicked.connect(self.reject)
        hl.addWidget(close_btn)
        lay.addWidget(hdr)

        # Path bar (clickable segments)
        path_bar = QWidget()
        path_bar.setFixedHeight(32)
        path_bar.setStyleSheet(f"background: {C.PANEL2}; border-bottom: 1px solid {C.BORDER};")
        pbl = QHBoxLayout(path_bar)
        pbl.setContentsMargins(8, 0, 8, 0)
        pbl.setSpacing(2)

        self._path_bar = path_bar
        self._path_segments = []
        self._update_path_bar()
        lay.addWidget(path_bar)

        # Search/filter input
        inp_w = QWidget()
        inp_w.setFixedHeight(38)
        inp_w.setStyleSheet(f"background: {C.PANEL}; border-bottom: 1px solid {C.BORDER};")
        il = QHBoxLayout(inp_w)
        il.setContentsMargins(10, 0, 10, 0)
        il.setSpacing(6)

        self._filter_input = QLineEdit()
        self._filter_input.setFont(QFont("Courier New", 9))
        self._filter_input.setPlaceholderText("Type to filter…")
        self._filter_input.setStyleSheet(f"""
            QLineEdit {{
                background: {C.DARK};
                color: {C.TEXT};
                border: 1px solid {C.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QLineEdit:focus {{ border: 1px solid {C.PRI}; }}
            QLineEdit::placeholder {{ color: {C.TEXT_DIM}; }}
        """)
        self._filter_input.textChanged.connect(self._on_filter)
        il.addWidget(self._filter_input)

        up_btn = QPushButton("↑")
        up_btn.setFixedSize(32, 28)
        up_btn.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
        up_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PANEL2}; color: {C.TEXT_MED};
                border: 1px solid {C.BORDER}; border-radius: 4px;
            }}
            QPushButton:hover {{ border-color: {C.PRI}; color: {C.PRI}; }}
        """)
        up_btn.clicked.connect(self._go_up)
        il.addWidget(up_btn)
        lay.addWidget(inp_w)

        # File list
        self._list = QListWidget()
        self._list.setFont(QFont("Courier New", 9))
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: {C.BG};
                color: {C.TEXT};
                border: none;
                outline: none;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background: {C.PRI_GHO};
                color: {C.PRI};
            }}
            QListWidget::item:hover {{
                background: {C.PANEL2};
            }}
            QScrollBar:vertical {{
                background: {C.BG};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {C.BORDER_B};
                border-radius: 4px;
            }}
        """)
        self._list.itemDoubleClicked.connect(self._on_item_double_click)
        lay.addWidget(self._list)

        # Footer
        ftr = QWidget()
        ftr.setFixedHeight(50)
        ftr.setStyleSheet(f"background: {C.DARK}; border-top: 1px solid {C.BORDER_B};")
        fl = QHBoxLayout(ftr)
        fl.setContentsMargins(14, 0, 14, 0)

        self._sel_lbl = QLabel("")
        self._sel_lbl.setFont(QFont("Courier New", 8))
        self._sel_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        fl.addWidget(self._sel_lbl)
        fl.addStretch()

        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setFixedSize(90, 32)
        cancel_btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C.TEXT_DIM};
                border: 1px solid {C.BORDER}; border-radius: 4px;
            }}
            QPushButton:hover {{ color: {C.WHITE}; border-color: {C.TEXT_MED}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        fl.addWidget(cancel_btn)

        open_btn = QPushButton("▸  OPEN")
        open_btn.setFixedSize(100, 32)
        open_btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PANEL2}; color: {C.PRI};
                border: 1px solid {C.PRI_DIM}; border-radius: 4px;
            }}
            QPushButton:hover {{ background: {C.PRI_GHO}; border-color: {C.PRI}; }}
        """)
        open_btn.clicked.connect(self._on_open)
        fl.addWidget(open_btn)
        lay.addWidget(ftr)

    def _update_path_bar(self):
        # Clear existing widgets from layout
        for w in self._path_segments:
            w.deleteLater()
        self._path_segments.clear()

        # Clear the layout
        pbl = self._path_segments
        if not hasattr(self, '_path_bar'):
            return
        layout = self._path_bar.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        parts = str(self._dir).split("/")
        path_so_far = ""
        for i, part in enumerate(parts):
            if i == 0:
                part = "/" if part == "" else part
                path_so_far = "/"
            else:
                path_so_far += part + "/"

            btn = QPushButton(part)
            btn.setFont(QFont("Courier New", 7))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {C.TEXT_MED};
                    border: none; padding: 2px 4px;
                }}
                QPushButton:hover {{ color: {C.PRI}; }}
            """)
            seg_path = path_so_far.rstrip("/") or "/"
            btn.clicked.connect(lambda _, p=seg_path: self._navigate_to(Path(p)))
            self._path_bar.layout().addWidget(btn)
            self._path_segments.append(btn)

    def _refresh(self):
        self._list.clear()
        try:
            entries = sorted(
                self._dir.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower())
            )
        except PermissionError:
            return

        for entry in entries:
            item = _FileItem(entry)
            self._list.addItem(item)

        self._path_lbl.setText(str(self._dir))
        self._title_lbl.setText(f"SELECT FILE — {self._dir.name.upper()}"[:40])

    def _on_filter(self, text: str):
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setHidden(text.lower() not in item.path.name.lower() if text else False)

    def _on_item_double_click(self, item: _FileItem):
        p = item.path
        if p.is_dir():
            self._history.append(self._dir)
            self._dir = p
            self._refresh()
        else:
            self.selected_file = str(p)
            self.accept()

    def _go_up(self):
        parent = self._dir.parent
        if parent != self._dir:
            self._history.append(self._dir)
            self._dir = parent
            self._refresh()

    def _navigate_to(self, path: Path):
        if path.is_dir():
            self._history.append(self._dir)
            self._dir = path
            self._refresh()
        else:
            self.selected_file = str(path)
            self.accept()

    def _on_open(self):
        cur = self._list.currentItem()
        if cur and cur.path.is_file():
            self.selected_file = str(cur.path)
            self.accept()
        elif cur and cur.path.is_dir():
            self._history.append(self._dir)
            self._dir = cur.path
            self._refresh()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Backspace:
            self._go_up()
        elif event.key() == Qt.Key.Key_Return:
            self._on_open()
        else:
            super().keyPressEvent(event)


def get_open_file_name(parent=None, title="Select a File for JARVIS",
                       start_dir=None, filters=None):
    """
    Show custom JARVIS file picker instead of native QFileDialog.
    Returns file path string or None if cancelled.
    """
    dlg = FilePickerDialog(start_dir=start_dir, parent=parent, title=title)
    dlg._filter_input.setFocus()
    if dlg.exec() == QDialog.Accepted and dlg.selected_file:
        return dlg.selected_file
    return None