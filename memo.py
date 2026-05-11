import os
import argparse
import json
import sqlite3
import sys
import tempfile
import re
from typing import Optional, List, Tuple, Dict, Any, Union
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QWidget, QListWidgetItem, QLabel,
                               QTextEdit, QPushButton, QLineEdit, QSplitter, QCheckBox, QSizePolicy, QComboBox,
                               QToolButton, QMenu, QMessageBox, QInputDialog, QFileDialog, QFontDialog, QApplication)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QRegularExpression, QEvent
from PySide6.QtGui import (QFont, QTextCursor, QTextCharFormat, QTextBlockFormat, QAction, QActionGroup,
                           QSyntaxHighlighter, QColor, QMouseEvent, QContextMenuEvent, QTextDocument)
from memo_db import MemoDB

DEFAULT_DATE_FORMAT = "%y/%m/%d"

def get_appdata_dir() -> Optional[str]:
    """Return a platform-specific application data directory for NemoBook."""
    app_dirname = "NemoBook"
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            return os.path.join(appdata, app_dirname)
        return os.path.join(os.path.expanduser("~"), app_dirname)
    else:
        # Linux/macOS
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            return os.path.join(xdg_config_home, app_dirname)
        return os.path.join(os.path.expanduser("~"), ".config", app_dirname)

class ThemeManager:
    """Manages themes and QSS stylesheets for the memo app."""
    def __init__(self):
        self.dark_themes = [
            "Default Dark", "Charcoal", "Obsidian", "Navy", 
            "Midnight Blue", "Brown", "Dark Chocolate", "Deep Brown",
        ]
        self.is_dark_theme = False
        self.themes = {
            "Default Light": self._get_light_theme_qss(),
            "Grey": self._get_grey_theme_qss(),
            "Mint": self._get_mint_theme_qss(),
            "Aqua": self._get_aqua_theme_qss(),
            "Ivory": self._get_ivory_theme_qss(),
            "Light Brown": self._get_light_brown_theme_qss(),
            "Default Dark": self._get_dark_theme_qss(),
            "Charcoal": self._get_charcoal_theme_qss(),
            "Obsidian": self._get_obsidian_theme_qss(),
            "Navy": self._get_navy_theme_qss(),
            "Midnight Blue": self._get_midnight_blue_theme_qss(),
            "Brown": self._get_brown_theme_qss(),
            "Dark Chocolate": self._get_dark_chocolate_theme_qss(),
            "Deep Brown": self._get_deep_brown_theme_qss(),
        }

    def update_theme_status(self, theme_name: str) -> None:
        self.is_dark_theme = theme_name in self.dark_themes

    def get_qss(self, theme_name: str) -> str:
        return self.themes.get(theme_name, self._get_light_theme_qss())

    def _get_light_theme_qss(self):
        return """
            QWidget { color: #222222; }
            QMainWindow, QDialog { background-color: #f0f0f0; }
            QListWidget, QTextEdit { background-color: #ffffff; color: #222222; border: 1px solid #ccc; padding: 10px; }
            QPushButton { background-color: #e1e1e1; border: 1px solid #adadad; padding: 5px; border-radius: 2px; }
            QPushButton:hover { background-color: #cacaca; }
            QComboBox, QLineEdit { border: 1px solid #adadad; padding: 2px; background-color: #ffffff; color: #222222; }
            QMenu { background-color: #ffffff; border: 1px solid #adadad; }
            QMenu::item:selected { background-color: #6fa8dc; color: #ffffff; }
        """

    def _get_dark_theme_qss(self):
        return """
            QWidget { background-color: #333; color: #eee; }
            QMainWindow, QDialog { background-color: #2b2b2b; }
            QListWidget, QTextEdit { background-color: #2b2b2b; color: #f0f0f0; border: 1px solid #444; padding: 10px; }
            QPushButton { background-color: #555; color: #eee; border: 1px solid #666; padding: 5px; border-radius: 2px; }
            QPushButton:hover { background-color: #666; }
            QComboBox, QLineEdit { border: 1px solid #666; padding: 2px; background-color: #555; color: #eee; }
            QMenu { background-color: #444; border: 1px solid #666; }
            QMenu::item:selected { background-color: #666; color: #eee; }
        """

    def _get_mint_theme_qss(self):
        return "QWidget { background-color: #e8f5e9; color: #1b5e20; } QPushButton { background-color: #66bb6a; color: white; } QTextEdit { background-color: white; padding: 10px; }"
    def _get_aqua_theme_qss(self):
        return "QWidget { background-color: #e0f7fa; color: #004d40; } QPushButton { background-color: #4db6ac; color: white; } QTextEdit { background-color: white; padding: 10px; }"
    def _get_grey_theme_qss(self):
        return "QWidget { background-color: #e0e0e0; color: #212121; } QPushButton { background-color: #cccccc; } QTextEdit { background-color: #eeeeee; padding: 10px; }"
    def _get_ivory_theme_qss(self):
        return "QWidget { background-color: #fffff0; color: #36454f; } QPushButton { background-color: #f0e68c; } QTextEdit { background-color: white; padding: 10px; }"
    def _get_light_brown_theme_qss(self):
        return "QWidget { background-color: #f5f5dc; color: #5d4037; } QPushButton { background-color: #cd853f; color: white; } QTextEdit { background-color: white; padding: 10px; }"
    def _get_charcoal_theme_qss(self):
        return "QWidget { background-color: #36454f; color: #f5f5f5; } QPushButton { background-color: #547280; } QTextEdit { background-color: #4a6572; padding: 10px; }"
    def _get_obsidian_theme_qss(self):
        return "QWidget { background-color: #212121; color: #f5f5f5; } QPushButton { background-color: #4a4a4a; } QTextEdit { background-color: #313131; padding: 10px; }"
    def _get_navy_theme_qss(self):
        return "QWidget { background-color: #2c3e50; color: #ecf0f1; } QPushButton { background-color: #546e7a; } QTextEdit { background-color: #465a65; padding: 10px; }"
    def _get_midnight_blue_theme_qss(self):
        return "QWidget { background-color: #1c2833; color: #d5dbe0; } QPushButton { background-color: #34495e; } QTextEdit { background-color: #2c3e50; padding: 10px; }"
    def _get_brown_theme_qss(self):
        return "QWidget { background-color: #5d4037; color: #efebe9; } QPushButton { background-color: #795548; } QTextEdit { background-color: #6d4c41; padding: 10px; }"
    def _get_dark_chocolate_theme_qss(self):
        return "QWidget { background-color: #3e2723; color: #d7ccc8; } QPushButton { background-color: #6d4c41; } QTextEdit { background-color: #5d4037; padding: 10px; }"
    def _get_deep_brown_theme_qss(self):
        return "QWidget { background-color: #32231F; color: #E0D6D3; } QPushButton { background-color: #4A3832; } QTextEdit { background-color: #42312A; padding: 10px; }"

class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown syntax highlighter with dynamic header sizing."""
    def __init__(self, document: QTextDocument, theme: str = 'light', base_font: Optional[QFont] = None):
        super().__init__(document)
        self.theme = theme
        self.base_font = base_font if base_font else QFont()
        self._update_formats()

    def set_theme(self, theme: str) -> None:
        self.theme = theme
        self._update_formats()
        self.rehighlight()

    def set_base_font(self, font: QFont) -> None:
        self.base_font = font
        self._update_formats()
        self.rehighlight()

    def _update_formats(self) -> None:
        is_dark = self.theme.lower() in ["dark", "default dark", "charcoal", "obsidian", "navy", "midnight blue", "brown", "dark chocolate", "deep brown"]
        self.highlightingRules = []
        self.marker_format = QTextCharFormat()
        self.marker_format.setForeground(QColor("transparent"))
        self.marker_format.setFontPointSize(1)
        self.header_color = QColor("#4EA1DF") if is_dark else QColor("#0055A4")
        self.header_pattern = QRegularExpression("^(#{1,6})(\\s+)(.*)")
        bold_fmt = QTextCharFormat()
        bold_fmt.setFontWeight(QFont.Bold)
        self.highlightingRules.append((QRegularExpression("(\\*\\*)([^\\*]+)(\\*\\*)"), bold_fmt))
        underline_fmt = QTextCharFormat()
        underline_fmt.setFontUnderline(True)
        self.highlightingRules.append((QRegularExpression("(__)([^_]+)(__)"), underline_fmt))
        italic_fmt = QTextCharFormat()
        italic_fmt.setFontItalic(True)
        self.highlightingRules.append((QRegularExpression("(?<!\\*)(\\*)(?!\\*)([^\\*]+)(?<!\\*)(\\*)(?!\\*)"), italic_fmt))
        self.highlightingRules.append((QRegularExpression("(?<!_)(_)(?!_)([^_]+)(?<!_)(_)(?!_)"), italic_fmt))
        strike_fmt = QTextCharFormat()
        strike_fmt.setFontStrikeOut(True)
        strike_fmt.setForeground(QColor("gray"))
        self.highlightingRules.append((QRegularExpression("(~~)([^~]+)(~~)"), strike_fmt))
        code_fmt = QTextCharFormat()
        code_fmt.setFontFamilies(["Courier New", "Courier", "Monospace"])
        code_fmt.setBackground(QColor("#3A3A3A") if is_dark else QColor("#F0F0F0"))
        code_fmt.setForeground(QColor("#CE9178") if is_dark else QColor("#A31515"))
        self.highlightingRules.append((QRegularExpression("(`)([^`]+)(`)"), code_fmt))
        checkbox_fmt = QTextCharFormat()
        checkbox_fmt.setForeground(QColor("#4CAF50"))
        checkbox_fmt.setFontWeight(QFont.Bold)
        self.highlightingRules.append((QRegularExpression("^\\s*[-*+]?\\s*\\[[ xX]\\]"), checkbox_fmt))
        base_size = self.base_font.pointSize() if self.base_font.pointSize() > 0 else 10
        self.title_format = QTextCharFormat()
        self.title_format.setFontWeight(QFont.Bold)
        self.title_format.setFontPointSize(base_size + 2)

    def highlightBlock(self, text: str) -> None:
        if self.currentBlock().blockNumber() == 0:
            self.setFormat(0, len(text), self.title_format)
            return
        for pattern, fmt in self.highlightingRules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                if match.lastCapturedIndex() == 3:
                    self.setFormat(match.capturedStart(1), match.capturedLength(1), self.marker_format)
                    self.setFormat(match.capturedStart(3), match.capturedLength(3), self.marker_format)
                    self.setFormat(match.capturedStart(2), match.capturedLength(2), fmt)
                else:
                    self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
        header_match = self.header_pattern.match(text)
        if header_match.hasMatch():
            level = len(header_match.captured(1))
            header_fmt = QTextCharFormat()
            header_fmt.setFontWeight(QFont.Bold)
            header_fmt.setForeground(self.header_color)
            base_size = self.base_font.pointSize() if self.base_font.pointSize() > 0 else 10
            size_offset = max(0, 8 - ((level - 1) * 2))
            header_fmt.setFontPointSize(base_size + size_offset)
            self.setFormat(header_match.capturedStart(1), header_match.capturedLength(1) + header_match.capturedLength(2), self.marker_format)
            self.setFormat(header_match.capturedStart(3), header_match.capturedLength(3), header_fmt)

class CheckboxTextEdit(QTextEdit):
    """QTextEdit with checkbox toggle support and markdown insertion."""
    def createMimeDataFromSelection(self):
        from PySide6.QtCore import QMimeData
        mime = super().createMimeDataFromSelection()
        cursor = self.textCursor()
        selected_text = cursor.selectedText().replace('\u2029', '\n')
        temp = QTextEdit()
        temp.setMarkdown(selected_text)
        mime.setHtml(temp.toHtml())
        return mime

    def insertFromMimeData(self, source):
        if source.hasHtml():
            from PySide6.QtGui import QTextDocument
            temp_doc = QTextDocument()
            temp_doc.setHtml(source.html())

            # Using QTextDocument.toMarkdown() escapes Markdown characters by default.
            markdown_text = temp_doc.toMarkdown(QTextDocument.MarkdownDialectCommonMark)
            markdown_text = markdown_text.replace('\\*', '*').replace('\\#', '#').replace('\\-', '-').replace('\\_', '_').replace('\\~', '~').replace('\\`', '`')

            if markdown_text.endswith('\n\n'):
                markdown_text = markdown_text[:-2]
            elif markdown_text.endswith('\n'):
                markdown_text = markdown_text[:-1]

            self.textCursor().insertText(markdown_text)
        else:
            super().insertFromMimeData(source)

    def insert_markdown(self, prefix: str, suffix: str = "") -> None:
        cursor = self.textCursor()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.removeSelectedText()
            cursor.insertText(f"{prefix}{text}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
            if suffix:
                cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, len(suffix))
                self.setTextCursor(cursor)
        cursor.endEditBlock()
        self.setFocus()

    def toggle_heading(self) -> None:
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.StartOfBlock)
        cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        text = cursor.selectedText()
        match = QRegularExpression("^(#{1,6})\\s+(.*)").match(text)
        if match.hasMatch():
            level = len(match.captured(1))
            if level >= 4: cursor.insertText(match.captured(2))
            else: cursor.insertText(f"{'#' * (level + 1)} {match.captured(2)}")
        else: cursor.insertText(f"# {text}")
        cursor.endEditBlock()
        self.setFocus()

    def toggle_list(self) -> None:
        cursor = self.textCursor()
        cursor.beginEditBlock()

        start_pos = cursor.selectionStart()
        end_pos = cursor.selectionEnd()

        temp_cursor = self.textCursor()
        temp_cursor.setPosition(start_pos)
        start_block = temp_cursor.blockNumber()

        temp_cursor.setPosition(end_pos)
        end_block = temp_cursor.blockNumber()

        if end_pos > start_pos and temp_cursor.positionInBlock() == 0:
            end_block -= 1

        for i in range(start_block, end_block + 1):
            temp_cursor = self.textCursor()
            temp_cursor.setPosition(self.document().findBlockByNumber(i).position())
            temp_cursor.movePosition(QTextCursor.StartOfBlock)
            temp_cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            text = temp_cursor.selectedText()

            # Toggle bullet point ( • )
            match = QRegularExpression("^(\\s*)•\\s+(.*)").match(text)
            if match.hasMatch():
                prefix = match.captured(1)
                if prefix == " ":
                    prefix = ""
                temp_cursor.insertText(f"{prefix}{match.captured(2)}")
            else:
                space_match = QRegularExpression("^(\\s*)(.*)").match(text)
                if space_match.hasMatch() and space_match.captured(2):
                    prefix = space_match.captured(1)
                    if not prefix:
                        prefix = " "
                    temp_cursor.insertText(f"{prefix}• {space_match.captured(2)}")
                elif text:
                    temp_cursor.insertText(f" • {text}")
                else:
                    temp_cursor.insertText(" • ")

        cursor.endEditBlock()
        self.setFocus()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()

            match = QRegularExpression("^(\\s*•\\s+)").match(text)
            if match.hasMatch() and cursor.positionInBlock() >= len(match.captured(1)):
                if text == match.captured(1):
                    cursor.movePosition(QTextCursor.StartOfBlock)
                    cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()
                    super().keyPressEvent(event)
                    return

                prefix = match.captured(1)
                super().keyPressEvent(event)
                self.insertPlainText(prefix)
                return

        super().keyPressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        menu = self.createStandardContextMenu(event.pos())
        menu.addSeparator()
        menu.addAction("**Bold**").triggered.connect(lambda: self.insert_markdown("**", "**"))
        menu.addAction("*Italic*").triggered.connect(lambda: self.insert_markdown("*", "*"))
        menu.addAction("__Underline__").triggered.connect(lambda: self.insert_markdown("__", "__"))
        menu.addAction("~~Strike~~").triggered.connect(lambda: self.insert_markdown("~~", "~~"))
        menu.addAction("`Code`").triggered.connect(lambda: self.insert_markdown("`", "`"))
        menu.addAction("Heading (#)").triggered.connect(self.toggle_heading)
        menu.exec(event.globalPos())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            cursor = self.cursorForPosition(event.position().toPoint())
            block = cursor.block()
            text = block.text()
            regex = QRegularExpression(r"^(\s*[-*+]?\s*)\[([ xX])\]")
            match = regex.match(text)
            if match.hasMatch():
                start_idx = match.capturedStart(2)
                if start_idx - 1 <= cursor.positionInBlock() <= start_idx + 1:
                    new_state = 'x' if match.captured(2) == ' ' else ' '
                    cursor.setPosition(block.position() + start_idx)
                    cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
                    cursor.insertText(new_state)
                    return
        super().mouseReleaseEvent(event)

class MemoListItemWidget(QWidget):
    """Custom widget for memo list items with theme support."""
    delete_requested = Signal(int)
    importance_changed = Signal(int, bool)
    def __init__(self, memo_id: int, title: str, summary: str, is_important: bool, parent=None, theme_manager=None):
        super().__init__(parent)
        self.memo_id = memo_id
        self.is_important = is_important
        self.theme_manager = theme_manager
        layout = QHBoxLayout(self); layout.setContentsMargins(5, 5, 5, 5); layout.setSpacing(10)
        self.important_button = QPushButton(); self.important_button.setFixedSize(24, 24)
        self.important_button.setStyleSheet("border: none; background-color: transparent; font-size: 16px;")
        self._update_importance_icon()
        self.important_button.clicked.connect(self.on_importance_toggled)
        layout.addWidget(self.important_button)
        text_layout = QVBoxLayout(); text_layout.setSpacing(0)
        self.title_label = QLabel(title); font = self.title_label.font(); font.setBold(True); self.title_label.setFont(font)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.summary_label = QLabel(summary); self.summary_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        text_layout.addWidget(self.title_label); text_layout.addWidget(self.summary_label)
        layout.addLayout(text_layout, 1)
        self.delete_button = QPushButton("☒"); self.delete_button.setFixedSize(22, 24); self.delete_button.setStyleSheet("border: none; background-color: transparent;")
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.memo_id))
        layout.addWidget(self.delete_button)
        self._update_style(False)

    def _update_importance_icon(self) -> None:
        self.important_button.setText("📌" if self.is_important else "◻︎")
    def on_importance_toggled(self) -> None:
        self.is_important = not self.is_important; self._update_importance_icon(); self.importance_changed.emit(self.memo_id, self.is_important)
    def _update_style(self, is_selected: bool) -> None:
        if not self.theme_manager: return
        is_dark = self.theme_manager.is_dark_theme
        bg_color = ("#00508C" if is_selected else "transparent") if is_dark else ("#A0D8F0" if is_selected else "transparent")
        text_color = ("#FFFFFF" if is_selected else "#F0F0F0") if is_dark else ("#000000")
        self.setStyleSheet(f"background-color: {bg_color};")
        self.title_label.setStyleSheet(f"color: {text_color};")
        self.summary_label.setStyleSheet(f"color: {text_color};")

class HelpDialog(QDialog):
    def __init__(self, parent=None, title="Help", markdown_file="memo.md"):
        super().__init__(parent)
        self.setWindowTitle(title); self.resize(700, 600)
        layout = QVBoxLayout(self)
        self.browser = QTextEdit(); self.browser.setReadOnly(True)
        if os.path.exists(markdown_file):
            with open(markdown_file, "r", encoding="utf-8") as f: self.browser.setMarkdown(f.read())
        else: self.browser.setText(f"Help file not found: {markdown_file}")
        layout.addWidget(self.browser)
        btn = QPushButton("Close"); btn.clicked.connect(self.accept); layout.addWidget(btn)

class NotepadDialog(QDialog):
    STRING_TEMPLATE_HELP_TEXT = """<b>Variables:</b><br>- %D : date_format<br>- %t : time (hh:mm)<br>- %T : time (hh:mm:ss)<br>- %c : category<br>- %C : [category]<br>- %% : %"""
    def __init__(self, base_dir=None, db_path='memo.db', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Memo"); self.setWindowFlag(Qt.WindowMinimizeButtonHint, True); self.setMinimumSize(500, 400); self.resize(700, 600)
        self.base_dir = base_dir; self.db_path = self._get_safe_db_path(db_path)
        self.memo_db = MemoDB(self.db_path); self.current_memo_id = None; self.is_new_memo = False; self._loading_memos = False; self._ignore_category_change = False
        self.undo_stack: List[Tuple[Any, ...]] = []; self.current_theme = 'Default Light'; self.current_line_height = 150.0; self._last_block_count = -1
        self.theme_manager = ThemeManager(); self.new_memo_template = {"mode": "date", "value": DEFAULT_DATE_FORMAT, "date_format": DEFAULT_DATE_FORMAT, "string_value": ""}
        self.date_format_options = [("YY/MM/DD", "%y/%m/%d"), ("YY-MM-DD", "%y-%m-%d"), ("YY.MM.DD", "%y.%m.%d"), ("YYMMDD", "%y%m%d"), ("YYYY/MM/DD", "%Y/%m/%d"), ("YYYY-MM-DD", "%Y-%m-%d"), ("YYYY.MM.DD", "%Y.%m.%d"), ("YYYYMMDD", "%Y%m%d"), ("MM/DD", "%m/%d"), ("MM-DD", "%m-%d"), ("MM.DD", "%m.%d"), ("MMDD", "%m%d")]
        self.date_format_actions: Dict[str, QAction] = {}; self.line_height_actions: Dict[float, QAction] = {}; self.theme_actions: Dict[str, QAction] = {}; self._syncing_template_actions = False
        
        # UI Widgets
        self.category_combo = QComboBox(); self.category_combo.setEditable(True); self.category_combo.setPlaceholderText("카테고리 선택/입력...")
        self.search_edit = QLineEdit(); self.search_edit.setPlaceholderText("메모 검색..."); self.search_button = QPushButton("🔍"); self.search_button.setFixedSize(28, 28)
        self.memo_list_widget = QListWidget(); self.memo_list_widget.setSpacing(2)
        self.undo_button = QPushButton("⟲"); self.undo_button.setToolTip("삭제 취소"); self.undo_button.setFixedSize(28, 28); self.undo_button.setEnabled(False)
        self.up_button = QPushButton("🡡"); self.up_button.setToolTip("위로"); self.up_button.setFixedSize(28, 28)
        self.down_button = QPushButton("🡣"); self.down_button.setToolTip("아래로"); self.down_button.setFixedSize(28, 28)
        self.new_memo_button = QPushButton("🞧"); self.new_memo_button.setToolTip("새 메모"); self.new_memo_button.setFixedSize(40, 28)
        self.save_button = QPushButton("💾"); self.save_button.setToolTip("저장"); self.save_button.setFixedSize(40, 28)
        self.btn_bold = QPushButton("B"); self.btn_bold.setFixedSize(28, 28); f_b = self.btn_bold.font(); f_b.setBold(True); self.btn_bold.setFont(f_b)
        self.btn_italic = QPushButton("I"); self.btn_italic.setFixedSize(28, 28); f_i = self.btn_italic.font(); f_i.setItalic(True); self.btn_italic.setFont(f_i)
        self.btn_underline = QPushButton("U"); self.btn_underline.setFixedSize(28, 28); f_u = self.btn_underline.font(); f_u.setUnderline(True); self.btn_underline.setFont(f_u)
        self.btn_strike = QPushButton("S"); self.btn_strike.setFixedSize(28, 28); f_s = self.btn_strike.font(); f_s.setStrikeOut(True); self.btn_strike.setFont(f_s)
        self.btn_code = QPushButton("<>"); self.btn_code.setFixedSize(28, 28)
        self.btn_heading = QPushButton("H"); self.btn_heading.setFixedSize(28, 28)
        self.btn_list = QPushButton("•"); self.btn_list.setFixedSize(28, 28)
        self.timestamp_label = QLabel(); self.timestamp_label.hide(); self.menu_button = QToolButton(); self.menu_button.setText("☰"); self.menu_button.setFixedSize(28, 28); self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu = QMenu(self); self.content_edit = CheckboxTextEdit(); self.highlighter = MarkdownHighlighter(self.content_edit.document())

        self._init_layout(); self._init_connections()
        l_id, l_cat, s_thm, s_lh, tmpl, s_fnt = self._load_state()
        self.current_memo_id = l_id; self.new_memo_template = tmpl; self.apply_line_height(s_lh); self.apply_theme(s_thm)
        if s_fnt: self.apply_font(s_fnt)
        self._setup_menu(); self._sync_new_memo_menu_checks(); self.load_categories(set_current_text=l_cat); self.load_memos()
        if self.memo_list_widget.count() == 0: self.create_new_memo()

    def _init_layout(self):
        main_layout = QHBoxLayout(self); splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget(); left_layout = QVBoxLayout(left_widget); left_layout.setContentsMargins(0, 0, 0, 0)
        s_layout = QHBoxLayout(); s_layout.addWidget(self.search_edit); s_layout.addWidget(self.search_button); s_layout.addWidget(self.undo_button); left_layout.addLayout(s_layout)
        left_layout.addWidget(self.category_combo); left_layout.addWidget(self.memo_list_widget)
        right_widget = QWidget(); right_layout = QVBoxLayout(right_widget); right_layout.setContentsMargins(0, 0, 0, 0)
        e_header = QHBoxLayout(); e_header.addWidget(self.up_button); e_header.addWidget(self.down_button); e_header.addWidget(self.new_memo_button); e_header.addWidget(self.save_button); e_header.addSpacing(8)
        f_layout = QHBoxLayout(); f_layout.setSpacing(2); f_layout.addWidget(self.btn_bold); f_layout.addWidget(self.btn_italic); f_layout.addWidget(self.btn_underline); f_layout.addWidget(self.btn_strike); f_layout.addWidget(self.btn_code); f_layout.addWidget(self.btn_heading); f_layout.addWidget(self.btn_list); e_header.addLayout(f_layout); e_header.addStretch(); e_header.addWidget(self.menu_button)
        right_layout.addLayout(e_header); right_layout.addWidget(self.content_edit)
        splitter.addWidget(left_widget); splitter.addWidget(right_widget); splitter.setSizes([210, 590]); main_layout.addWidget(splitter)

    def _init_connections(self):
        self.search_button.clicked.connect(self.filter_memos); self.search_edit.returnPressed.connect(self.filter_memos)
        self.new_memo_button.clicked.connect(self.create_new_memo); self.up_button.clicked.connect(self.move_memo_up); self.down_button.clicked.connect(self.move_memo_down); self.undo_button.clicked.connect(self.undo_delete)
        self.memo_list_widget.currentItemChanged.connect(self.on_memo_selected); self.save_button.clicked.connect(self.save_current_memo)
        self.btn_bold.clicked.connect(lambda: self.content_edit.insert_markdown("**", "**")); self.btn_italic.clicked.connect(lambda: self.content_edit.insert_markdown("*", "*")); self.btn_underline.clicked.connect(lambda: self.content_edit.insert_markdown("__", "__")); self.btn_strike.clicked.connect(lambda: self.content_edit.insert_markdown("~~", "~~")); self.btn_code.clicked.connect(lambda: self.content_edit.insert_markdown("`", "`")); self.btn_heading.clicked.connect(self.content_edit.toggle_heading); self.btn_list.clicked.connect(self.content_edit.toggle_list)
        self.content_edit.textChanged.connect(self.on_text_changed); self.content_edit.textChanged.connect(self._on_content_text_changed)
        self.category_combo.lineEdit().returnPressed.connect(self.on_category_enter); self.menu_button.clicked.connect(self.show_menu_at_left)
        self.auto_save_timer = QTimer(self); self.auto_save_timer.setSingleShot(True); self.auto_save_timer.setInterval(2000); self.auto_save_timer.timeout.connect(self.save_current_memo); self.content_edit.textChanged.connect(lambda: self.auto_save_timer.start())

    def _setup_menu(self):
        self.menu.clear()
        self.menu.addAction("About").triggered.connect(lambda: QMessageBox.information(self, "About", "Simple Memo app\nberd2@naver.com"))
        self.menu.addAction("Font").triggered.connect(self.show_font_dialog)
        t_menu = self.menu.addMenu("Theme"); tg = QActionGroup(self); tg.setExclusive(True)
        for t in self.theme_manager.themes.keys():
            a = QAction(t, self); a.setCheckable(True); a.triggered.connect(lambda checked, th=t: self.apply_theme(th)); tg.addAction(a); t_menu.addAction(a); self.theme_actions[t] = a
        lh_menu = self.menu.addMenu("Line Spacing"); lhg = QActionGroup(self); lhg.setExclusive(True)
        for label, val in [("100%", 100.0), ("120%", 120.0), ("150%", 150.0), ("200%", 200.0)]:
            a = QAction(label, self); a.setCheckable(True); a.triggered.connect(lambda checked, v=val: self.apply_line_height(v)); lhg.addAction(a); lh_menu.addAction(a); self.line_height_actions[val] = a
        self.menu.addAction("Load DB").triggered.connect(self.load_db_file)
        m_menu = self.menu.addMenu("New Memo message"); d_menu = m_menu.addMenu("Date"); dg = QActionGroup(self); dg.setExclusive(True)
        for l, f in self.date_format_options:
            a = QAction(l, self); a.setCheckable(True); a.triggered.connect(lambda checked, fmt=f: self._handle_date_template_action(checked, fmt)); dg.addAction(a); d_menu.addAction(a); self.date_format_actions[f] = a
        self.string_template_action = m_menu.addAction("String"); self.string_template_action.setCheckable(True); self.string_template_action.triggered.connect(self._handle_string_template_action)
        self.menu.addSeparator(); self.menu.addAction("Help").triggered.connect(lambda: HelpDialog(self).exec())

    def show_menu_at_left(self):
        pos = self.menu_button.mapToGlobal(self.menu_button.rect().bottomRight()); pos.setX(pos.x() - self.menu.sizeHint().width()); self.menu.popup(pos)
    def _get_safe_db_path(self, db_path: str) -> str:
        is_frozen = getattr(sys, "frozen", False) or "__compiled__" in globals()
        if "Program Files" in os.getcwd(): is_frozen = True
        if is_frozen:
            ad = get_appdata_dir()
            if ad:
                try:
                    os.makedirs(ad, exist_ok=True); sp = os.path.join(ad, os.path.basename(db_path))
                    if os.path.exists(os.path.basename(db_path)) and not os.path.exists(sp):
                        import shutil; shutil.copy2(os.path.basename(db_path), sp)
                    return sp
                except: pass
            td = os.path.join(tempfile.gettempdir(), "NemoBook"); os.makedirs(td, exist_ok=True); return os.path.join(td, os.path.basename(db_path))
        return os.path.abspath(db_path)

    def load_categories(self, set_current_text=None):
        self._ignore_category_change = True; cur = set_current_text or self.category_combo.currentText(); self.category_combo.clear(); self.category_combo.addItem("")
        for c in self.memo_db.get_all_categories():
            if c: self.category_combo.addItem(c)
        self.category_combo.setCurrentText(cur); self._ignore_category_change = False

    def on_category_enter(self):
        txt = self.category_combo.currentText()
        if txt and self.category_combo.findText(txt) == -1:
            if self.is_dirty: self.save_current_memo()
            now = datetime.now(); nid = self.memo_db.add_memo(now.strftime('%y/%m/%d'), f"\n({now.strftime('%m/%d')}) ", category=txt)
            self.current_memo_id = nid; self.load_categories(set_current_text=txt); self.load_memos()

    def load_memos(self):
        if self._loading_memos: return
        self._loading_memos = True; cid = self.current_memo_id if not self.is_new_memo else None; term = self.search_edit.text().lower(); cat = self.category_combo.currentText()
        self.memo_list_widget.blockSignals(True); self.memo_list_widget.clear(); sel_item = None
        for mid, t, ca, con, imp, c, so in self.memo_db.get_all_memos():
            if cat and c != cat: continue
            if term and term not in t.lower() and term not in con.lower(): continue
            summary = ' ↵ '.join(p.strip() for p in con.split('\n')[1:] if p.strip())[:50]
            item = QListWidgetItem(self.memo_list_widget); widget = MemoListItemWidget(mid, t or "(No Title)", summary, imp, theme_manager=self.theme_manager)
            widget.delete_requested.connect(self.delete_memo); widget.importance_changed.connect(self.toggle_importance)
            item.setSizeHint(widget.sizeHint()); self.memo_list_widget.addItem(item); self.memo_list_widget.setItemWidget(item, widget); item.setData(Qt.UserRole, mid)
            if mid == cid: sel_item = item
        self.memo_list_widget.blockSignals(False); self._loading_memos = False
        if sel_item: self.memo_list_widget.setCurrentItem(sel_item)
        elif self.memo_list_widget.count() > 0: self.memo_list_widget.setCurrentRow(0)
        else: self.current_memo_id = None; self.content_edit.clear(); self.timestamp_label.clear()

    def filter_memos(self): self.load_memos()
    def on_memo_selected(self, cur, prev):
        if self._loading_memos: return
        if prev:
            w = self.memo_list_widget.itemWidget(prev)
            if isinstance(w, MemoListItemWidget): w._update_style(False)
        if not cur: self.timestamp_label.clear(); return
        mid = cur.data(Qt.UserRole); w = self.memo_list_widget.itemWidget(cur)
        if isinstance(w, MemoListItemWidget): w._update_style(True)
        if self.is_dirty and self.content_edit.toPlainText().strip(): self.save_current_memo()
        self.current_memo_id = mid; memo = self.memo_db.get_memo_by_id(mid)
        if memo:
            self.content_edit.blockSignals(True); self.content_edit.setPlainText(memo[3]); self.content_edit.blockSignals(False); self._apply_block_formats()
            self.update_timestamp(memo[2], memo[5]); self.is_dirty = False; self.content_edit.moveCursor(QTextCursor.End)
        self.is_new_memo = False; self._save_state()

    def create_new_memo(self):
        if self.is_dirty: self.save_current_memo()
        cat = self.category_combo.currentText(); init = self._generate_new_memo_initial_text(cat)
        title = init.split('\n')[0].strip() or datetime.now().strftime('%y/%m/%d')
        nid = self.memo_db.add_memo(title, init, category=cat); self.current_memo_id = nid; self.is_new_memo = True; self.load_memos()
        for i in range(self.memo_list_widget.count()):
            it = self.memo_list_widget.item(i)
            if it.data(Qt.UserRole) == nid: self.memo_list_widget.setCurrentItem(it); break
        self.content_edit.setFocus()

    def save_current_memo(self):
        if not self.is_dirty: return
        con = self.content_edit.toPlainText()
        if not con.strip():
            if not self.is_new_memo and self.current_memo_id: self.delete_memo(self.current_memo_id, False)
            return
        t = con.split('\n')[0].strip() or "(No Title)"
        if self.current_memo_id:
            self.memo_db.update_memo(self.current_memo_id, t, con)
            for i in range(self.memo_list_widget.count()):
                it = self.memo_list_widget.item(i)
                if it.data(Qt.UserRole) == self.current_memo_id:
                    w = self.memo_list_widget.itemWidget(it)
                    if isinstance(w, MemoListItemWidget):
                        w.title_label.setText(t); w.summary_label.setText(' ↵ '.join(p.strip() for p in con.split('\n')[1:] if p.strip())[:50])
                    break
        self._apply_block_formats(); self.is_dirty = False

    def delete_memo(self, mid, to_undo=True):
        m = self.memo_db.get_memo_by_id(mid)
        if to_undo and m:
            self.undo_stack.append(m)
            if len(self.undo_stack) > 10: self.undo_stack.pop(0)
            self.undo_button.setEnabled(True)
        self.memo_db.delete_memo(mid); self.load_memos()

    def undo_delete(self):
        if self.undo_stack: self.memo_db.restore_memo(*self.undo_stack.pop()); self.undo_button.setEnabled(len(self.undo_stack) > 0); self.load_memos()
    def toggle_importance(self, mid, imp): self.memo_db.update_memo_importance(mid, imp); QTimer.singleShot(0, self.load_memos)
    def move_memo_up(self): self._move_memo(-1)
    def move_memo_down(self): self._move_memo(1)
    def _move_memo(self, d):
        it = self.memo_list_widget.currentItem()
        if it:
            r = self.memo_list_widget.row(it)
            if 0 <= r+d < self.memo_list_widget.count():
                id1, id2 = it.data(Qt.UserRole), self.memo_list_widget.item(r+d).data(Qt.UserRole)
                m1, m2 = self.memo_db.get_memo_by_id(id1), self.memo_db.get_memo_by_id(id2)
                if m1 and m2 and m1[4] == m2[4]: self.memo_db.swap_memo_order(id1, id2); self.load_memos()

    def update_timestamp(self, ts, cat=""):
        if ts:
            dt = datetime.fromtimestamp(ts); df = self.new_memo_template.get('date_format', DEFAULT_DATE_FORMAT)
            self.timestamp_label.setText(f"[{cat}] {dt.strftime(df)} {dt.strftime('%H:%M')}" if cat else f"{dt.strftime(df)} {dt.strftime('%H:%M')}")
        else: self.timestamp_label.clear()

    def _apply_block_formats(self):
        self.content_edit.blockSignals(True); cur = self.content_edit.textCursor(); p = cur.position(); cur.beginEditBlock()
        cur.movePosition(QTextCursor.Start); f = QTextBlockFormat(); f.setBottomMargin(8); f.setLineHeight(self.current_line_height, QTextBlockFormat.ProportionalHeight.value); cur.setBlockFormat(f)
        while cur.movePosition(QTextCursor.NextBlock):
            f = QTextBlockFormat(); f.setLineHeight(self.current_line_height, QTextBlockFormat.ProportionalHeight.value); cur.setBlockFormat(f)
        cur.endEditBlock(); cur.setPosition(p); self.content_edit.setTextCursor(cur); self.content_edit.blockSignals(False)

    def show_font_dialog(self):
        ok, fnt = QFontDialog.getFont(self.content_edit.font(), self, "Select Font")
        if ok: self.apply_font(fnt)
    def apply_font(self, fnt):
        self.content_edit.setFont(fnt); self.content_edit.document().setDefaultFont(fnt); self.highlighter.set_base_font(fnt); self._apply_block_formats()
        self.memo_db.save_state('font', json.dumps({"family": fnt.family(), "pointSize": fnt.pointSize(), "weight": fnt.weight(), "italic": fnt.italic()}))
    def apply_line_height(self, lh):
        self.current_line_height = float(lh); self._apply_block_formats(); self.memo_db.save_state('line_height', str(lh))
    def apply_theme(self, th):
        self.setStyleSheet(self.theme_manager.get_qss(th)); self.theme_manager.update_theme_status(th); self.highlighter.set_theme(th); self.current_theme = th; self.memo_db.save_state('theme', th)
        for k, a in self.theme_actions.items(): a.setChecked(k == th)
        for i in range(self.memo_list_widget.count()):
            it = self.memo_list_widget.item(i); w = self.memo_list_widget.itemWidget(it)
            if isinstance(w, MemoListItemWidget): w._update_style(it.isSelected())

    def load_db_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Memo DB", os.path.dirname(self.db_path), "Memo DB Files (*memo*db);;All Files (*.*)")
        if p: self.memo_db.close(); self.memo_db = MemoDB(p); self.db_path = p; self.load_categories(); self.load_memos()
    def _handle_date_template_action(self, chk, fmt):
        if chk: self._set_new_memo_template('date', fmt)
    def _handle_string_template_action(self):
        val = self.new_memo_template.get('string_value', "")
        dialog = QInputDialog.getText(self, "New Memo message", "Enter text:", QLineEdit.Normal, val)
        if dialog[1]: self._set_new_memo_template('string', dialog[0].strip())
        self._sync_new_memo_menu_checks()
    def _set_new_memo_template(self, mode, val):
        self.new_memo_template.update({"mode": mode, "value": val})
        if mode == 'string': self.new_memo_template['string_value'] = val
        else: self.new_memo_template['date_format'] = val
        self.memo_db.save_state('new_memo_template', json.dumps(self.new_memo_template)); self._sync_new_memo_menu_checks()
    def _sync_new_memo_menu_checks(self):
        m = self.new_memo_template.get('mode', 'date'); v = self.new_memo_template.get('value', DEFAULT_DATE_FORMAT)
        for f, a in self.date_format_actions.items(): a.setChecked(m == 'date' and f == v)
        if self.string_template_action: self.string_template_action.setChecked(m == 'string')
    def _generate_new_memo_initial_text(self, cat):
        m = self.new_memo_template.get('mode', 'date'); v = self.new_memo_template.get('value', DEFAULT_DATE_FORMAT)
        if m == 'string':
            now = datetime.now(); df = self.new_memo_template.get('date_format', DEFAULT_DATE_FORMAT)
            reps = {'D': now.strftime(df), 't': now.strftime("%H:%M"), 'T': now.strftime("%H:%M:%S"), 'c': cat or "", 'C': f"[{cat}]" if cat else ""}
            res, i = [], 0
            while i < len(v):
                if v[i] == '%' and i+1 < len(v):
                    code = v[i+1]
                    if code == '%': res.append('%'); i += 2; continue
                    if code in reps: res.append(reps[code]); i += 2; continue
                res.append(v[i]); i += 1
            return "".join(res)
        return datetime.now().strftime(v or DEFAULT_DATE_FORMAT)

    def _load_state(self):
        mid = self.memo_db.load_state('last_memo_id'); cat = self.memo_db.load_state('last_category', ""); thm = self.memo_db.load_state('theme', 'Default Light')
        try: lh = float(self.memo_db.load_state('line_height', '150.0'))
        except: lh = 150.0
        fnt = None; f_raw = self.memo_db.load_state('font')
        if f_raw:
            try:
                d = json.loads(f_raw); f = QFont(d.get("family", ""))
                if "pointSize" in d: f.setPointSize(d["pointSize"])
                if "weight" in d: f.setWeight(d["weight"])
                if "italic" in d: f.setItalic(d["italic"])
                fnt = f
            except: pass
        t_raw = self.memo_db.load_state('new_memo_template'); tmpl = {"mode": "date", "value": DEFAULT_DATE_FORMAT, "date_format": DEFAULT_DATE_FORMAT, "string_value": ""}
        if t_raw:
            try: tmpl.update(json.loads(t_raw))
            except: pass
        return int(mid) if mid else None, cat, thm, lh, tmpl, fnt
    def _save_state(self):
        if self.current_memo_id: self.memo_db.save_state('last_memo_id', str(self.current_memo_id))
        self.memo_db.save_state('last_category', self.category_combo.currentText()); self.memo_db.save_state('theme', self.current_theme); self.memo_db.save_state('line_height', str(self.current_line_height)); self.memo_db.save_state('new_memo_template', json.dumps(self.new_memo_template))
    def on_category_changed(self, text):
        if not self._ignore_category_change: self.load_memos(); self._save_state()
    def on_text_changed(self): self.is_dirty = True
    def _on_content_text_changed(self):
        if not self.content_edit.signalsBlocked():
            cnt = self.content_edit.document().blockCount()
            if cnt != self._last_block_count: self._last_block_count = cnt; self._apply_block_formats()
    def closeEvent(self, event):
        if self.is_dirty: self.save_current_memo()
        self._save_state(); self.memo_db.close(); super().closeEvent(event)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Standalone Memo App")
    parser.add_argument('-db', default='memo.db', help="Database path")
    args = parser.parse_args()
    app = QApplication(sys.argv); d = NotepadDialog(db_path=args.db); d.show(); sys.exit(app.exec())
