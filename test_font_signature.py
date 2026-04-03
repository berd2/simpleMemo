import sys
from PySide6.QtWidgets import QApplication, QFontDialog
from PySide6.QtGui import QFont

app = QApplication(sys.argv)
ok, font = QFontDialog.getFont(QFont())
print("Returns:", type(ok), type(font))
