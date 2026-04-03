import sys
from PySide6.QtWidgets import QApplication, QTextEdit
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QRegularExpression

app = QApplication(sys.argv)
edit = QTextEdit()
edit.setPlainText("**bold** and *italic*")

rules = []

bold_format = QTextCharFormat()
bold_format.setFontWeight(QFont.Bold)
rules.append((QRegularExpression("\\*\\*[^\\*]+\\*\\*"), bold_format))

italic_format = QTextCharFormat()
italic_format.setFontItalic(True)
rules.append((QRegularExpression("(?<!\\*)\\*[^\\*]+\\*(?!\\*)"), italic_format))

def highlightBlock(text):
    for pattern, format in rules:
        iterator = pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            print(f"Match: '{match.captured(0)}' at {match.capturedStart()} with {pattern.pattern()}")

highlightBlock("**bold** and *italic*")
