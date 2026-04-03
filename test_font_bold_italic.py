import sys
from PySide6.QtWidgets import QApplication, QTextEdit
from PySide6.QtGui import QTextCursor, QTextCharFormat, QFont
from PySide6.QtCore import QRegularExpression

app = QApplication(sys.argv)
edit = QTextEdit()
edit.setPlainText("**글자**")

# simulate apply_title_style which clears and sets formats
cursor = edit.textCursor()
cursor.select(QTextCursor.Document)
fmt = QTextCharFormat()
fmt.setFontWeight(QFont.Normal)
# BUG: if we don't set italic to false here, does it carry over?
fmt.setFontItalic(False)
cursor.setCharFormat(fmt)

# Apply highlighter
from memo import MarkdownHighlighter
highlighter = MarkdownHighlighter(edit.document(), 'light', edit.font())
highlighter.rehighlight()

block = edit.document().firstBlock()
for format_range in block.layout().formats():
    print("start:", format_range.start, "len:", format_range.length, "italic:", format_range.format.fontItalic(), "weight:", format_range.format.fontWeight())
