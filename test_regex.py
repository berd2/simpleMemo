from PySide6.QtCore import QRegularExpression
text = "**bold** and *italic*"

bold_re = QRegularExpression("\\*\\*[^\\*]+\\*\\*")
it_re = QRegularExpression("(?<!\\*)\\*[^\\*]+\\*(?!\\*)")

print("Bold match:**bold**", bold_re.match(text).hasMatch(), bold_re.match(text).captured(0))
print("Italic match:**bold**", it_re.match("**bold**").hasMatch())
