import re
text1 = "**글자**"
text2 = "*글자*"
print("Is italic text1:", bool(re.search(r"(?<!\*)\*(?!\*)[^\*]+\*(?!\*)", text1)))
print("Is italic text2:", bool(re.search(r"(?<!\*)\*(?!\*)[^\*]+\*(?!\*)", text2)))
