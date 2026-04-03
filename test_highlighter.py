import sys
from PySide6.QtWidgets import QApplication, QTextEdit
from PySide6.QtGui import QTextCursor
from memo import MarkdownHighlighter

app = QApplication(sys.argv)
edit = QTextEdit()
edit.setPlainText("**bold** and *italic*")

highlighter = MarkdownHighlighter(edit.document(), 'light', edit.font())
highlighter.rehighlight()

# Let's inspect the formats
cursor = edit.textCursor()
cursor.setPosition(0)
cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)

# Inspect highlighter formats directly
block = edit.document().firstBlock()
for format_range in block.layout().formats():
    print(format_range.start, format_range.length, format_range.format.fontItalic(), format_range.format.fontWeight())
