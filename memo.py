import os
import argparse
import json
import sqlite3
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QWidget, QListWidgetItem, QLabel,
                               QTextEdit, QPushButton, QLineEdit, QSplitter,  QCheckBox, QSizePolicy, QComboBox,
                               QToolButton, QMenu, QMessageBox, QInputDialog, QFileDialog, QFontDialog)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QRegularExpression, QEvent
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QTextBlockFormat, QAction, QActionGroup, QSyntaxHighlighter, QColor, QMouseEvent
from datetime import datetime
from memo_db import MemoDB
    
DEFAULT_DATE_FORMAT = "%y/%m/%d"

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, document, theme='light', base_font=None):
        super().__init__(document)
        self.theme = theme
        self.base_font = base_font if base_font else QFont()
        self._update_formats()

    def set_theme(self, theme):
        self.theme = theme
        self._update_formats()
        self.rehighlight()

    def set_base_font(self, font):
        self.base_font = font
        self._update_formats()
        self.rehighlight()

    def _update_formats(self):
        is_dark = self.theme == 'dark'

        self.highlightingRules = []

        header_format = QTextCharFormat()
        header_format.setFontWeight(QFont.Bold)
        header_format.setForeground(QColor("#4EA1DF") if is_dark else QColor("#0055A4"))
        self.highlightingRules.append((QRegularExpression("^#{1,6}\\s+.*"), header_format))

        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        self.highlightingRules.append((QRegularExpression("\\*\\*[^\\*]+\\*\\*"), bold_format))
        self.highlightingRules.append((QRegularExpression("__[^_]+__"), bold_format))

        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        self.highlightingRules.append((QRegularExpression("\\*[^\\*]+\\*"), italic_format))
        self.highlightingRules.append((QRegularExpression("_[^_]+_"), italic_format))

        strike_format = QTextCharFormat()
        strike_format.setFontStrikeOut(True)
        strike_format.setForeground(QColor("gray"))
        self.highlightingRules.append((QRegularExpression("~~[^~]+~~"), strike_format))

        code_format = QTextCharFormat()
        code_format.setFontFamilies(["Courier New", "Courier", "Monospace"])
        code_format.setBackground(QColor("#3A3A3A") if is_dark else QColor("#F0F0F0"))
        code_format.setForeground(QColor("#CE9178") if is_dark else QColor("#A31515"))
        self.highlightingRules.append((QRegularExpression("`[^`]+`"), code_format))

        checkbox_format = QTextCharFormat()
        checkbox_format.setForeground(QColor("#4CAF50"))
        checkbox_format.setFontWeight(QFont.Bold)
        self.highlightingRules.append((QRegularExpression("^\\s*[-*+]?\\s*\\[[ xX]\\]"), checkbox_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class StringTemplateInputDialog(QDialog):
    def __init__(self, parent=None, title="", label="", text="", help_text=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        main_layout = QVBoxLayout(self)

        # Label for the input field
        main_layout.addWidget(QLabel(label))

        # Input field
        self.input_line_edit = QLineEdit(self)
        self.input_line_edit.setText(text)
        main_layout.addWidget(self.input_line_edit)

        # Help text
        if help_text:
            help_label = QLabel(help_text)
            help_label.setTextFormat(Qt.RichText)
            help_label.setWordWrap(True)
            main_layout.addWidget(help_label)

        # OK/Cancel buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def getText(self):
        return self.input_line_edit.text()

class MemoListItemWidget(QWidget):
    """Custom widget for displaying a memo in the list."""
    delete_requested = Signal(int)
    importance_changed = Signal(int, bool)

    def __init__(self, memo_id, title, summary, is_important, parent=None):
        super().__init__(parent)
        self.memo_id = memo_id
        self.is_important = is_important

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.important_button = QPushButton()
        self.important_button.setFixedSize(24, 24)
        self.important_button.setStyleSheet("border: none; background-color: transparent; font-size: 16px;")
        self._update_importance_icon()
        self.important_button.clicked.connect(self.on_importance_toggled)
        layout.addWidget(self.important_button)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)

        self.title_label = QLabel(title)
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        self.summary_label = QLabel(summary)
        self.summary_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.summary_label)
        layout.addLayout(text_layout, 1)

        self.delete_button = QPushButton("☒")     #❌✖️✏↺↵↻↶⤺
        self.delete_button.setFixedSize(22, 24)
        self.delete_button.setStyleSheet("border: none; background-color: transparent;")
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.memo_id))
        layout.addWidget(self.delete_button)

    def _update_importance_icon(self):
        icon = "📌" if self.is_important else "◻︎" #○☒⟲❍◻︎◼︎
        self.important_button.setText(icon)

    def on_importance_toggled(self):
        self.is_important = not self.is_important
        self._update_importance_icon()
        self.importance_changed.emit(self.memo_id, self.is_important)

class CheckboxTextEdit(QTextEdit):
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            block = cursor.block()
            text = block.text()

            # Simple regex to find checkbox in the line
            regex = QRegularExpression(r"^(\s*[-*+]?\s*)\[([ xX])\]")
            match = regex.match(text)

            if match.hasMatch():
                # Check if the click is roughly within the checkbox bounds
                # We can approximate this by checking the column
                start_idx = match.capturedStart(2)

                # We add some tolerance
                if start_idx - 1 <= cursor.positionInBlock() <= start_idx + 1:
                    current_state = match.captured(2)
                    new_state = 'x' if current_state == ' ' else ' '

                    # Perform the replacement
                    cursor.setPosition(block.position() + start_idx)
                    cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
                    cursor.insertText(new_state)
                    return # Event handled

        super().mouseReleaseEvent(event)


class NotepadDialog(QDialog):
    STRING_TEMPLATE_HELP_TEXT = """
        <b>Variables:</b><br>
        - %D : date_format (e.g., 24/01/01)<br>
        - %t : time_format (hh:mm)<br>
        - %T : time_format (hh:mm:ss)<br>
        - %c : category (e.g., cat1)<br>
        - %C : [category] (e.g., [cat1])<br>
        - %% : %<br>
        <i>Example: "%C New Memo %D %t" -></i><br>
        <i>  "[cat1] New Memo 24/01/01 12:34"</i>
    """

    def __init__(self, base_dir=None, db_path='memo.db', show_full_menu=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Memo")
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)        
        self.setMinimumSize(500, 400)
        self.resize(700, 600)

        self.base_dir = base_dir
        self.show_full_menu = show_full_menu
        self.db_path = db_path
        self.memo_db = MemoDB(db_path)
        self.current_memo_id = None
        self.is_new_memo = False
        self._loading_memos = False
        self._ignore_category_change = False
        self._is_startup = True
        self.undo_stack = []
        self.current_theme = 'light'
        self.new_memo_template = {"mode": "date", "value": DEFAULT_DATE_FORMAT, "date_format": DEFAULT_DATE_FORMAT, "string_value": ""}
        self.date_format_options = [
            ("YY/MM/DD", "%y/%m/%d"),
            ("YY-MM-DD", "%y-%m-%d"),
            ("YY.MM.DD", "%y.%m.%d"),
            ("YYMMDD",   "%y%m%d"),
            ("YYYY/MM/DD", "%Y/%m/%d"),
            ("YYYY-MM-DD", "%Y-%m-%d"),
            ("YYYY.MM.DD", "%Y.%m.%d"),
            ("YYYYMMDD",   "%Y%m%d"),
            ("MM/DD", "%m/%d"),
            ("MM-DD", "%m-%d"),
            ("MM.DD", "%m.%d"),
            ("MMDD",  "%m%d"),
        ]
        self.date_format_actions = {}
        self._syncing_template_actions = False

        # --- UI Widgets ---
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.setPlaceholderText("카테고리 선택 또는 입력...")

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("메모 검색...")
        self.search_button = QPushButton("🔍")
        self.search_button.setFixedSize(28, 28)
        self.memo_list_widget = QListWidget()
        self.memo_list_widget.setSpacing(2)
        
        self.undo_button = QPushButton("⟲")
        self.undo_button.setToolTip("삭제 취소")
        self.undo_button.setFixedSize(28, 28)
        self.undo_button.setEnabled(False)
        
        self.up_button = QPushButton("🡡")
        self.up_button.setToolTip("메모를 위로 이동")
        self.up_button.setFixedSize(28, 28)
        self.down_button = QPushButton("🡣")
        self.down_button.setToolTip("메모를 아래로 이동")
        self.new_memo_button = QPushButton("🞧")
        self.new_memo_button.setToolTip("새 메모")
        self.new_memo_button.setFixedSize(40, 28)
        self.save_button = QPushButton("💾")
        self.save_button.setFixedSize(40, 28)
        self.save_button.setToolTip("메모 저장")
        self.down_button.setFixedSize(28, 28)
        
        self.timestamp_label = QLabel()
        self.menu_button = QToolButton()
        self.menu_button.setText("☰")
        self.menu_button.setFixedSize(28, 28)
        self.menu_button.setToolTip("메뉴")
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu = QMenu(self)
        self.theme_actions = {}
        self.new_memo_action_group = None
        self.string_template_action = None
        self._setup_menu()
        self.content_edit = CheckboxTextEdit()
        self.highlighter = MarkdownHighlighter(self.content_edit.document(), self.current_theme, self.content_edit.font())

        # --- Layout ---
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.undo_button)
        left_layout.addLayout(search_layout)

        # Category ComboBox below search
        left_layout.addWidget(self.category_combo)
        left_layout.addWidget(self.memo_list_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        editor_header = QHBoxLayout()
        editor_header.addWidget(self.up_button)
        editor_header.addWidget(self.down_button)
        editor_header.addWidget(self.new_memo_button)
        editor_header.addWidget(self.save_button)
        editor_header.addStretch()
        editor_header.addWidget(self.timestamp_label)
        editor_header.addWidget(self.menu_button)
        right_layout.addLayout(editor_header)
        right_layout.addWidget(self.content_edit)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([210, 590])
        main_layout.addWidget(splitter)

        # --- Connections ---
        self.search_button.clicked.connect(self.filter_memos)
        self.search_edit.returnPressed.connect(self.filter_memos)
        self.new_memo_button.clicked.connect(self.create_new_memo)
        self.up_button.clicked.connect(self.move_memo_up)
        self.down_button.clicked.connect(self.move_memo_down)
        self.undo_button.clicked.connect(self.undo_delete)
        self.is_dirty = False
        self.memo_list_widget.currentItemChanged.connect(self.on_memo_selected)
        self.save_button.clicked.connect(self.save_current_memo)
        self.content_edit.textChanged.connect(self.on_text_changed)
        self.content_edit.textChanged.connect(self._on_content_text_changed)
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        self.category_combo.lineEdit().returnPressed.connect(self.on_category_enter)
        self.menu_button.clicked.connect(self.show_menu_at_left)

        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.setInterval(2000) # 2 seconds
        self.auto_save_timer.timeout.connect(self.auto_save_trigger)
        self.content_edit.textChanged.connect(self.reset_auto_save_timer)

        last_memo_id, last_category, saved_theme, template, saved_font = self._load_state()
        self.current_memo_id = last_memo_id # Set the ID to be preserved
        self.new_memo_template = template
        self.apply_theme(saved_theme)
        if saved_font:
            self.apply_font(saved_font)
        self.highlighter.set_theme(saved_theme)
        self._sync_new_memo_menu_checks()

        self.load_categories(set_current_text=last_category)
        self.load_memos() # This will load memos for the category and try to select self.current_memo_id

        # If after loading, the list is empty, create an initial memo.
        if self.memo_list_widget.count() == 0:
            self.create_new_memo()

    def load_categories(self, set_current_text=None):
        self._ignore_category_change = True
        current_text = set_current_text if set_current_text is not None else self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("") # '(전체)'
        categories = self.memo_db.get_all_categories()
        for category in categories:
            if category: # a non-empty string
                self.category_combo.addItem(category)
        self.category_combo.setCurrentText(current_text)
        self._ignore_category_change = False

    def on_category_changed(self, text):
        if self._ignore_category_change:
            return
        self.load_memos()
        self._save_state()

    def on_category_enter(self):
        text = self.category_combo.currentText()
        if not text:
            return

        is_new = self.category_combo.findText(text) == -1
        if is_new:
            if self.is_dirty:
                self.save_current_memo()
                self.is_dirty = False

            now = datetime.now()
            content = f"\n({now.strftime('%m/%d')}) "
            title = content.split('\n')[0].strip()

            new_id = self.memo_db.add_memo(title, content, category=text)
            self.current_memo_id = new_id
            self.is_new_memo = False

            self.load_categories(set_current_text=text)
            self.load_memos()


    def load_memos(self):
        if self._loading_memos:
            return
        self._loading_memos = True

        current_id_to_preserve = self.current_memo_id if not self.is_new_memo else None
        search_term = self.search_edit.text()
        current_category = self.category_combo.currentText()

        self.memo_list_widget.blockSignals(True)
        self.memo_list_widget.clear()
        all_memos = self.memo_db.get_all_memos()

        if current_category:
            memos = [m for m in all_memos if m[5] == current_category]
        else:
            memos = all_memos
        sorted_memos = memos

        item_to_select = None
        for memo_id, db_title, created_at, content, is_important, category, sort_order in sorted_memos:
            if search_term and not (search_term.lower() in db_title.lower() or search_term.lower() in content.lower()):
                continue

            lines = content.split('\n')
            title = db_title.strip()
            title_line_index = -1
            if title:
                for i, line in enumerate(lines):
                    if line.strip() == title:
                        title_line_index = i
                        break
            if title_line_index == -1:
                for i, line in enumerate(lines):
                    if line.strip():
                        title = line.strip()
                        title_line_index = i
                        break
            if not title:
                title = "(제목 없음)"

            summary_parts = lines[title_line_index + 1:]
            summary = ' ↵ '.join(p.strip() for p in summary_parts if p.strip())[:50]

            item = QListWidgetItem(self.memo_list_widget)
            widget = MemoListItemWidget(memo_id, title, summary, is_important)
            
            widget.delete_requested.connect(self.delete_memo)
            widget.importance_changed.connect(self.toggle_importance)
            
            item.setSizeHint(widget.sizeHint())
            self.memo_list_widget.addItem(item)
            self.memo_list_widget.setItemWidget(item, widget)
            item.setData(Qt.UserRole, memo_id)

            if memo_id == current_id_to_preserve:
                item_to_select = item
        
        self.memo_list_widget.blockSignals(False)
        self._loading_memos = False
        if item_to_select:
            self.memo_list_widget.setCurrentItem(item_to_select)
        elif self.memo_list_widget.count() > 0:
            self.memo_list_widget.setCurrentRow(0)
        else:
            # if no memos, clear the content area
            self.current_memo_id = None
            self.content_edit.clear()
            self.timestamp_label.clear()

    def filter_memos(self):
        self.load_memos()

    def on_memo_selected(self, current_item, previous_item):
        if self._loading_memos or not current_item:
            if not current_item:
                self.timestamp_label.clear()
            return
        try:
            memo_id = current_item.data(Qt.UserRole)
        except RuntimeError:
            return
        if self.is_dirty:
            self.save_current_memo()
            self.is_dirty = False

        # if memo_id == self.current_memo_id and not self.is_new_memo and not self._is_startup:
        #     return
        self.current_memo_id = memo_id
        
        memo = self.memo_db.get_memo_by_id(self.current_memo_id)
        if memo:
            _, _, created_at, content, _, category, _ = memo
            self.content_edit.blockSignals(True)
            self.content_edit.setPlainText(content)
            self.apply_title_style()
            self.content_edit.blockSignals(False)
            self.is_dirty = False
            self.content_edit.moveCursor(QTextCursor.End)
            self.update_timestamp(created_at, category)

        # Reset the new memo flag after loading
        self.is_new_memo = False
        self._save_state()
        self._is_startup = False

    def reset_auto_save_timer(self):
        if not self.content_edit.signalsBlocked():
            self.auto_save_timer.start()

    def auto_save_trigger(self):
        if self.is_dirty:
            self.save_current_memo()

    def on_text_changed(self):
        if not self.content_edit.signalsBlocked():
            self.is_dirty = True

    def _on_content_text_changed(self):
        if not self.content_edit.signalsBlocked():
            self.apply_title_style()

    def create_new_memo(self):
        if self.is_dirty:
            self.save_current_memo()
            self.is_dirty = False
        current_category = self.category_combo.currentText()
        
        initial_text = self._generate_new_memo_initial_text(current_category)
        if not initial_text.strip():
            initial_text = datetime.now().strftime('%y/%m/%d')
        title = initial_text.split('\n')[0].strip() or datetime.now().strftime('%y/%m/%d')
        content = initial_text if initial_text.endswith('\n') else f"{initial_text}\n"
        new_id = self.memo_db.add_memo(title, content, category=current_category)

        self.current_memo_id = new_id
        self.is_new_memo = True # Flag that we are in the new memo state
        self.load_memos()

        # Select the new memo in the list
        for i in range(self.memo_list_widget.count()):
            item = self.memo_list_widget.item(i)
            if item.data(Qt.UserRole) == new_id:
                self.memo_list_widget.setCurrentItem(item)
                break
        self.content_edit.setFocus()

    def _setup_menu(self):
        self.menu.clear()
        self.theme_actions = {}
        self.date_format_actions = {}
        self.theme_action_group = None

        if self.show_full_menu:
            about_action = self.menu.addAction("About")
            about_action.triggered.connect(self.show_about_dialog)

            font_action = self.menu.addAction("Font")
            font_action.triggered.connect(self.show_font_dialog)

            theme_menu = self.menu.addMenu("Theme")
            self.theme_action_group = QActionGroup(self)
            self.theme_action_group.setExclusive(True)
            for label, key in (("Light", "light"), ("Dark", "dark")):
                action = QAction(label, self)
                action.setCheckable(True)
                action.triggered.connect(lambda checked, theme=key: self.apply_theme(theme))
                self.theme_action_group.addAction(action)
                theme_menu.addAction(action)
                self.theme_actions[key] = action

        load_action = self.menu.addAction("Load DB")
        load_action.triggered.connect(self.load_db_file)

        new_message_menu = self.menu.addMenu("New Memo message")
        date_menu = new_message_menu.addMenu("Date")
        self.new_memo_action_group = QActionGroup(self)
        self.new_memo_action_group.setExclusive(True)
        for label, fmt in self.date_format_options:
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, fmt=fmt: self._handle_date_template_action(checked, fmt))
            self.new_memo_action_group.addAction(action)
            date_menu.addAction(action)
            self.date_format_actions[fmt] = action

        string_action = new_message_menu.addAction("String")
        string_action.setCheckable(True)
        string_action.triggered.connect(self._handle_string_template_action)
        self.new_memo_action_group.addAction(string_action)
        self.string_template_action = string_action

        if self.show_full_menu:
            self.menu.addSeparator()
        help_action = self.menu.addAction("Help")
        help_action.triggered.connect(self.show_help_document)

    def show_about_dialog(self):
        QMessageBox.information(self, "About", "Simple Memo app\nberd2@naver.com")

    def show_help_document(self):
        doc_path = None
        candidates = [
            os.path.join(os.getcwd(), "memo.md"), # Look in current working directory
            os.path.join(self.base_dir, "memo.md") if self.base_dir else None,
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "memo.md")
        ]
        for path in candidates:
            if path and os.path.exists(path):
                doc_path = path
                break
        if not doc_path:
            QMessageBox.warning(self, "Help", "memo.md 파일을 찾을 수 없습니다.")
            return
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as exc:
            QMessageBox.warning(self, "Help", f"문서를 불러올 수 없습니다:\n{exc}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Help")
        layout = QVBoxLayout(dialog)
        text_view = QTextEdit(dialog)
        text_view.setReadOnly(True)
        text_view.setPlainText(content)
        layout.addWidget(text_view)
        dialog.resize(700, 600)
        dialog.exec()

    def load_db_file(self):
        initial_dir = os.path.dirname(self.db_path) if self.db_path else os.getcwd()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Memo DB",
            initial_dir,
            "Memo DB Files (*memo*db);;SQLite DB (*.db);;All Files (*.*)"
        )
        if not file_path:
            return
        valid, error_message = self._validate_db_schema(file_path)
        if not valid:
            QMessageBox.critical(self, "Invalid DB", f"선택한 파일을 열 수 없습니다:\n{error_message}")
            return
        self._switch_database(file_path)
        QMessageBox.information(self, "DB Loaded", f"새로운 DB를 불러왔습니다:\n{file_path}")

    def show_menu_at_left(self):
        if not self.menu:
            return
        button_rect = self.menu_button.rect()
        global_point = self.menu_button.mapToGlobal(button_rect.bottomRight())
        menu_width = self.menu.sizeHint().width()
        global_point.setX(global_point.x() - menu_width)
        self.menu.popup(global_point)

    def _validate_db_schema(self, path):
        try:
            conn = sqlite3.connect(path)
        except sqlite3.Error as exc:
            return False, str(exc)
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(memos)")
            columns = [row[1] for row in cursor.fetchall()]
        except sqlite3.Error as exc:
            conn.close()
            return False, str(exc)
        conn.close()
        required = {"id", "title", "created_at", "content", "is_important", "category", "sort_order"}
        if not required.issubset(set(columns)):
            return False, "memos 테이블 구조가 올바르지 않습니다."
        return True, ""

    def _switch_database(self, new_path):
        try:
            self.memo_db.close()
        except Exception:
            pass
        self.memo_db = MemoDB(new_path)
        self.db_path = new_path
        last_memo_id, last_category, saved_theme, template, saved_font = self._load_state()
        self.current_memo_id = last_memo_id
        self.new_memo_template = template
        self.apply_theme(saved_theme)
        if saved_font:
            self.apply_font(saved_font)
        self._sync_new_memo_menu_checks()
        self.load_categories(set_current_text=last_category)
        self.load_memos()
        if self.memo_list_widget.count() == 0:
            self.create_new_memo()

    def _set_new_memo_template(self, mode, value):
        if mode not in ("date", "string") or not isinstance(value, str):
            return
        template = dict(self.new_memo_template)
        if mode == "date":
            template["mode"] = "date"
            template["value"] = value
            template["date_format"] = value
        else:
            template["mode"] = "string"
            template["value"] = value
            template["string_value"] = value
            template.setdefault("date_format", template.get("date_format", DEFAULT_DATE_FORMAT))
        template.setdefault("string_value", template.get("value", ""))
        template.setdefault("date_format", template.get("date_format", DEFAULT_DATE_FORMAT))
        self.new_memo_template = template
        self.memo_db.save_state('new_memo_template', json.dumps(self.new_memo_template))
        self._sync_new_memo_menu_checks()

    def _handle_string_template_action(self, checked):
        if self._syncing_template_actions:
            return
        if not checked:
            return
        current_value = self.new_memo_template.get('string_value') or (self.new_memo_template.get('value') if self.new_memo_template.get('mode') == 'string' else "")
        
        dialog = StringTemplateInputDialog(
            parent=self,
            title="New Memo message",
            label="Enter text:",
            text=current_value,
            help_text=self.STRING_TEMPLATE_HELP_TEXT
        )
        if dialog.exec():
            text = dialog.getText()
            if text.strip():
                self._set_new_memo_template('string', text.strip())
            else:
                self._sync_new_memo_menu_checks()
        else:
            self._sync_new_memo_menu_checks()

    def _handle_date_template_action(self, checked, fmt):
        if self._syncing_template_actions:
            return
        if checked:
            self._set_new_memo_template('date', fmt)

    def _sync_new_memo_menu_checks(self):
        if not self.new_memo_action_group:
            return
        self._syncing_template_actions = True
        mode = self.new_memo_template.get('mode', 'date')
        value = self.new_memo_template.get('value', DEFAULT_DATE_FORMAT)
        date_format = self.new_memo_template.get('date_format', DEFAULT_DATE_FORMAT)
        for fmt, action in self.date_format_actions.items():
            target = value if mode == 'date' else date_format
            action.setChecked(fmt == target and mode == 'date')
        if self.string_template_action:
            self.string_template_action.setChecked(mode == 'string')
            if mode == 'string':
                self.string_template_action.setText("String… (custom)")
                self.string_template_action.setToolTip(self.new_memo_template.get('value', ''))
            else:
                self.string_template_action.setText("String…")
                self.string_template_action.setToolTip("Set a custom starting line for new memos")
        self._syncing_template_actions = False

    def _generate_new_memo_initial_text(self, category_text):
        mode = self.new_memo_template.get('mode', 'date')
        value = self.new_memo_template.get('value', DEFAULT_DATE_FORMAT)
        if mode == 'string' and value.strip():
            return self._render_string_template(value, category_text or "")
        fmt = value if value else DEFAULT_DATE_FORMAT
        try:
            return datetime.now().strftime(fmt)
        except ValueError:
            return datetime.now().strftime(DEFAULT_DATE_FORMAT)

    def _current_date_format(self):
        fmt = self.new_memo_template.get('date_format') or DEFAULT_DATE_FORMAT
        return fmt

    def _render_string_template(self, template, category_text):
        if not template:
            return ""
        now = datetime.now()
        try:
            date_str = now.strftime(self._current_date_format())
        except ValueError:
            date_str = now.strftime(DEFAULT_DATE_FORMAT)
        replacements = {
            'd': date_str,
            'D': date_str,
            't': now.strftime("%H:%M"),
            'T': now.strftime("%H:%M:%S"),
            'c': category_text or "",
            'C': f"[{category_text}]" if category_text else "",
        }
        result = []
        i = 0
        length = len(template)
        while i < length:
            char = template[i]
            if char == '%' and i + 1 < length:
                code = template[i + 1]
                if code == '%':
                    result.append('%')
                    i += 2
                    continue
                if code in replacements:
                    replacement = replacements[code]
                    i += 2
                    if not replacement and code in ('c', 'C') and i < length and template[i] == ' ':
                        i += 1
                    result.append(replacement)
                    continue
            result.append(char)
            i += 1
        return ''.join(result)

    def save_current_memo(self):
        content = self.content_edit.toPlainText()
        
        if not content.strip():
            if not self.is_new_memo and self.current_memo_id:
                self.is_dirty = False
                self.delete_memo(self.current_memo_id, to_undo_stack=False)
            return
        lines = content.split('\n')
        title = lines[0].strip()
        if not title:
             for line in lines:
                if line.strip():
                    title = line.strip()
                    break

        if self.current_memo_id:
            memo = self.memo_db.get_memo_by_id(self.current_memo_id)
            if memo and (memo[1] != title or memo[3] != content):
                self.memo_db.update_memo(self.current_memo_id, title, content)
                # self.load_memos() # This causes re-entrancy issues.
                # Instead, find the item and update it directly.
                for i in range(self.memo_list_widget.count()):
                    item = self.memo_list_widget.item(i)
                    if item.data(Qt.UserRole) == self.current_memo_id:
                        widget = self.memo_list_widget.itemWidget(item)
                        if widget:
                            widget.title_label.setText(title)
                            summary_parts = lines[1:]
                            summary = ' ↵ '.join(p.strip() for p in summary_parts if p.strip())[:50]
                            widget.summary_label.setText(summary)
                        break
            elif memo:
                self.update_timestamp(memo[2], memo[5])

        self.apply_title_style()
        self.is_dirty = False

    def delete_memo(self, memo_id, to_undo_stack=True):
        memo_to_delete = self.memo_db.get_memo_by_id(memo_id)
        if to_undo_stack and memo_to_delete:
            self.undo_stack.append(memo_to_delete)
            if len(self.undo_stack) > 3:
                self.undo_stack.pop(0)
            self.undo_button.setEnabled(True)

        self.memo_db.delete_memo(memo_id)
        original_category = memo_to_delete[5] if memo_to_delete else ""

        categories = self.memo_db.get_all_categories()
        if original_category and original_category not in categories:
            current_cat = self.category_combo.currentText()
            self.load_categories()
            if current_cat == original_category:
                self.category_combo.setCurrentIndex(0)
            else:
                self.load_memos()
        else:
            self.load_memos()
        if memo_id == self.current_memo_id:
            self.current_memo_id = None
            self.content_edit.clear()

    def undo_delete(self):
        if not self.undo_stack:
            return
        
        memo_to_restore = self.undo_stack.pop()
        self.memo_db.restore_memo(*memo_to_restore)
        
        if not self.undo_stack:
            self.undo_button.setEnabled(False)

        memo_id = memo_to_restore[0]
        category = memo_to_restore[5]
        self.load_categories(set_current_text=category)
        self.load_memos()
        # Select the restored memo
        for i in range(self.memo_list_widget.count()):
            item = self.memo_list_widget.item(i)
            if item.data(Qt.UserRole) == memo_id:
                self.memo_list_widget.setCurrentItem(item)
                break

    def toggle_importance(self, memo_id, is_important):
        self.memo_db.update_memo_importance(memo_id, is_important)
        QTimer.singleShot(0, self.load_memos)

    def move_memo_up(self):
        self._move_memo(-1)

    def move_memo_down(self):
        self._move_memo(1)

    def _move_memo(self, direction):
        current_item = self.memo_list_widget.currentItem()
        if not current_item:
            return

        current_row = self.memo_list_widget.row(current_item)
        new_row = current_row + direction

        if 0 <= new_row < self.memo_list_widget.count():
            item_to_swap = self.memo_list_widget.item(new_row)
            id1 = current_item.data(Qt.UserRole)
            id2 = item_to_swap.data(Qt.UserRole)
            memo1 = self.memo_db.get_memo_by_id(id1)
            memo2 = self.memo_db.get_memo_by_id(id2)

            # Do not swap between important and unimportant items
            if memo1 and memo2 and memo1[4] == memo2[4]:
                self.memo_db.swap_memo_order(id1, id2)
                self.load_memos()

    def update_timestamp(self, timestamp_int, category=""):
        if timestamp_int:
            dt = datetime.fromtimestamp(timestamp_int)
            
            # Get the selected date format from new_memo_template
            date_format_str = self.new_memo_template.get('date_format', DEFAULT_DATE_FORMAT)
            
            # Format date and time
            formatted_date = dt.strftime(date_format_str)
            formatted_time = dt.strftime("%H:%M")
            
            # Construct the label string
            if category and category.strip():
                self.timestamp_label.setText(f"[{category}] {formatted_date} {formatted_time}")
            else:
                self.timestamp_label.setText(f"{formatted_date} {formatted_time}")
        else:
            self.timestamp_label.clear()

    def apply_title_style(self):
        # Save the current cursor position
        original_cursor = self.content_edit.textCursor()
        original_pos = original_cursor.position()
        self.content_edit.blockSignals(True)
        cursor = self.content_edit.textCursor()
        cursor.beginEditBlock()

        # Reset formats for the entire document
        cursor.select(QTextCursor.Document)

        # Reset block format
        reset_block_fmt = QTextBlockFormat()
        reset_block_fmt.setBottomMargin(0)
        cursor.setBlockFormat(reset_block_fmt)

        # Reset character format
        normal_char_fmt = QTextCharFormat()
        normal_char_fmt.setFontWeight(QFont.Normal)
        normal_char_fmt.setFontPointSize(self.font().pointSize())
        cursor.setCharFormat(normal_char_fmt)

        # Apply special format to the first line (title)
        cursor.movePosition(QTextCursor.Start)

        # Block format for title (add space after)
        title_block_fmt = QTextBlockFormat()
        title_block_fmt.setBottomMargin(8)
        cursor.setBlockFormat(title_block_fmt)

        # Character format for title (bold, larger font)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        title_char_fmt = QTextCharFormat()
        title_char_fmt.setFontWeight(QFont.Bold)
        title_char_fmt.setFontPointSize(self.font().pointSize() + 2)
        cursor.setCharFormat(title_char_fmt)
        cursor.endEditBlock()

        # Restore original cursor position
        cursor.clearSelection()
        cursor.setPosition(original_pos)
        self.content_edit.setTextCursor(cursor)
        self.content_edit.blockSignals(False)

    def show_font_dialog(self):
        result = QFontDialog.getFont(self.content_edit.font(), self, "Select Font")
        if len(result) == 2:
            ok, font = result
            if isinstance(ok, bool) and not isinstance(font, bool):
                if ok:
                    self.apply_font(font)
            else:
                font, ok = result
                if ok:
                    self.apply_font(font)
        else:
            if result:
                self.apply_font(result[0])

    def apply_font(self, font):
        self.content_edit.setFont(font)
        if hasattr(self, 'highlighter'):
            self.highlighter.set_base_font(font)
        font_info = {
            "family": font.family(),
            "pointSize": font.pointSize(),
            "weight": font.weight(),
            "italic": font.italic()
        }
        self.memo_db.save_state('font', json.dumps(font_info))

    def apply_theme(self, theme):
        theme = (theme or "light").lower()
        if theme not in ("light", "dark"):
            theme = "light"

        self.current_theme = theme
        if hasattr(self, 'highlighter'):
            self.highlighter.set_theme(theme)

        if theme == "dark":
            self.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    color: #f0f0f0;
                }
                QListWidget, QTextEdit {
                    background-color: #2b2b2b;
                    color: #f0f0f0;
                }
                QPushButton, QToolButton, QLineEdit, QComboBox {
                    background-color: #333333;
                    color: #f0f0f0;
                    border: 1px solid #444444;
                }
            """)
        else:
            self.setStyleSheet("")
        if hasattr(self, "theme_actions"):
            for key, action in self.theme_actions.items():
                action.setChecked(key == self.current_theme)

        self.memo_db.save_state('theme', self.current_theme)

    def _load_state(self):
        last_memo_id_str = self.memo_db.load_state('last_memo_id')
        last_memo_id = int(last_memo_id_str) if last_memo_id_str is not None else None
        last_category = self.memo_db.load_state('last_category', "")
        saved_theme = self.memo_db.load_state('theme', 'light')

        saved_font = None
        font_raw = self.memo_db.load_state('font')
        if font_raw:
            try:
                font_info = json.loads(font_raw)
                f = QFont(font_info.get("family", ""))
                if "pointSize" in font_info: f.setPointSize(font_info["pointSize"])
                if "weight" in font_info: f.setWeight(font_info["weight"])
                if "italic" in font_info: f.setItalic(font_info["italic"])
                saved_font = f
            except (json.JSONDecodeError, TypeError):
                pass

        template_raw = self.memo_db.load_state('new_memo_template')
        template = {"mode": "date", "value": DEFAULT_DATE_FORMAT, "date_format": DEFAULT_DATE_FORMAT, "string_value": ""}
        if template_raw:
            try:
                candidate = json.loads(template_raw)
                mode = candidate.get('mode')
                value = candidate.get('value')
                if mode in ('date', 'string') and isinstance(value, str):
                    template.update(candidate)
            except (json.JSONDecodeError, TypeError):
                pass
        template.setdefault('date_format', template.get('value') if template.get('mode') == 'date' else DEFAULT_DATE_FORMAT)
        if 'string_value' not in template:
            template['string_value'] = template.get('value', '') if template.get('mode') == 'string' else ""
        return last_memo_id, last_category, saved_theme, template, saved_font

    def _save_state(self):
        if self.current_memo_id is not None:
            self.memo_db.save_state('last_memo_id', self.current_memo_id)
        self.memo_db.save_state('last_category', self.category_combo.currentText())
        self.memo_db.save_state('theme', self.current_theme)
        self.memo_db.save_state('new_memo_template', json.dumps(self.new_memo_template))

    def closeEvent(self, event):
        if self.is_dirty:
            self.save_current_memo()
        self._save_state()
        self.memo_db.close()
        super().closeEvent(event)

if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    parser = argparse.ArgumentParser(add_help=False, description="Simple memo app")
    parser.add_argument('-db', '--db', dest='db_path', default='memo.db', help="SQLite database file path")
    parser.add_argument('-scale', '--scale', dest='scale_factor', type=float, help="Override QT_SCALE_FACTOR (e.g., 1.1)")
    parser.add_argument('-h', '--help', dest='show_help', action='store_true', help="Show this help message and exit")
    args, qt_args = parser.parse_known_args()

    if args.show_help:
        parser.print_help()
        sys.exit(0)

    if args.scale_factor:
        os.environ["QT_SCALE_FACTOR"] = str(args.scale_factor)

    qt_argv = [sys.argv[0]] + qt_args
    app = QApplication(qt_argv)

    current_dir = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

    db_path = os.path.abspath(args.db_path) if args.db_path else os.path.abspath('memo.db')
    dialog = NotepadDialog(base_dir=parent_dir, db_path=db_path, show_full_menu=True)
    dialog.show()
    sys.exit(app.exec())
