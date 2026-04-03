import re
text = "**bold**"
print(bool(re.search(r"(?<!\*)\*[^\*]+\*(?!\*)", text)))
print(bool(re.search(r"(?<!_)_[^_]+_(?!_)", "__bold__")))
