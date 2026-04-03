import sys
from PySide6.QtWidgets import QApplication, QTextEdit
from PySide6.QtGui import QTextCursor, QTextCharFormat, QFont

app = QApplication(sys.argv)
edit = QTextEdit()
edit.setPlainText("Hello World")

font = QFont("Courier", 20)
edit.setFont(font)
edit.document().setDefaultFont(font)

cursor = edit.textCursor()
cursor.select(QTextCursor.Document)

fmt = QTextCharFormat()
fmt.setFontWeight(QFont.Normal)
cursor.setCharFormat(fmt)

# Let's check what the font is for the first character
cursor.setPosition(0)
cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
print("Font family after setCharFormat:", cursor.charFormat().font().family())

fmt2 = QTextCharFormat()
fmt2.setFontWeight(QFont.Normal)
fmt2.setFont(font)
cursor.select(QTextCursor.Document)
cursor.setCharFormat(fmt2)

cursor.setPosition(0)
cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
print("Font family after setCharFormat with setFont:", cursor.charFormat().font().family())
