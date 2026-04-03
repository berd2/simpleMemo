import sys
from PySide6.QtWidgets import QApplication, QFontDialog
from PySide6.QtGui import QFont

app = QApplication(sys.argv)
res = QFontDialog.getFont(QFont())
print("Returns:", type(res), len(res), type(res[0]), type(res[1]))
