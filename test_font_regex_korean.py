import re
print(bool(re.search(r"(?<!\*)\*[^\*]+\*(?!\*)", "**글자**")))
print(bool(re.search(r"_[^_]+_", "__글자__")))
