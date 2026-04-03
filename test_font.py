import sys
from PySide6.QtWidgets import QApplication, QFontDialog
app = QApplication(sys.argv)
ret = QFontDialog.getFont()
print(type(ret), len(ret), type(ret[0]), type(ret[1]))
