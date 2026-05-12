import re

MARKERS = ["**", "__", "~~", "`", "*", "_"]

def toggle_format(block_text, rel_start, rel_end, marker):
    formats = []
    for m in MARKERS:
        escaped_m = re.escape(m)
        if m in ["*", "_"]:
            if m == "*":
                pattern = r'(?<!\*)(\*)(?!\*)(.*?)(?<!\*)(\*)(?!\*)'
            else:
                pattern = r'(?<!_)(_)(?!_)(.*?)(?<!_)(_)(?!_)'
        else:
            pattern = f'({escaped_m})(.*?)({escaped_m})'

        for match in re.finditer(pattern, block_text):
            formats.append({
                "marker": m,
                "start": match.start(1),
                "inner_start": match.start(2),
                "inner_end": match.end(2),
                "end": match.end(3) if len(match.groups()) >= 3 else match.end()
            })

    formats.sort(key=lambda x: (x["start"], -x["end"]))

    markers_to_remove = []
    markers_to_insert = []

    toggling_off = False

    for f in formats:
        if f["marker"] == marker:
            is_exact_outer = (f["start"] == rel_start and f["end"] == rel_end)
            is_exact_inner = (f["inner_start"] == rel_start and f["inner_end"] == rel_end)
            is_enclosing = (f["inner_start"] <= rel_start and f["inner_end"] >= rel_end)

            if is_exact_outer or is_exact_inner or is_enclosing:
                toggling_off = True
                break

    for f in formats:
        m_start_marker = (f["start"], f["inner_start"])
        m_end_marker = (f["inner_end"], f["end"])

        # 1. ENCLOSING
        if f["start"] <= rel_start and f["end"] >= rel_end:
            is_exact_outer = (f["start"] == rel_start and f["end"] == rel_end)
            is_exact_inner = (f["inner_start"] == rel_start and f["inner_end"] == rel_end)

            if is_exact_outer or is_exact_inner:
                markers_to_remove.append(m_start_marker)
                markers_to_remove.append(m_end_marker)
            elif f["inner_start"] <= rel_start and f["inner_end"] >= rel_end:
                if rel_start > f["inner_start"]:
                    markers_to_insert.append((rel_start, f["marker"], "end"))
                else: # ADDED THIS ELSE STATEMENT to remove the start marker
                    markers_to_remove.append(m_start_marker)

                if rel_end < f["inner_end"]:
                    markers_to_insert.append((rel_end, f["marker"], "start"))
                else:
                    markers_to_remove.append(m_end_marker)

            elif f["start"] == rel_start:
                markers_to_remove.append(m_start_marker)
                markers_to_insert.append((rel_end, f["marker"], "start"))
            elif f["end"] == rel_end:
                markers_to_remove.append(m_end_marker)
                markers_to_insert.append((rel_start, f["marker"], "end"))

        # 2. COMPLETELY INSIDE
        elif f["start"] >= rel_start and f["end"] <= rel_end:
            markers_to_remove.append(m_start_marker)
            markers_to_remove.append(m_end_marker)

        # 3. OVERLAPPING LEFT
        elif f["start"] < rel_start and f["end"] > rel_start and f["end"] <= rel_end:
            markers_to_remove.append(m_end_marker)
            markers_to_insert.append((rel_start, f["marker"], "end"))

        # 4. OVERLAPPING RIGHT
        elif f["start"] >= rel_start and f["start"] < rel_end and f["end"] > rel_end:
            markers_to_remove.append(m_start_marker)
            markers_to_insert.append((rel_end, f["marker"], "start"))

    if not toggling_off:
        markers_to_insert.append((rel_start, marker, "start"))
        markers_to_insert.append((rel_end, marker, "end"))

    res = ""
    idx = 0
    markers_to_insert.sort(key=lambda x: (x[0], 0 if x[2] == "end" else 1))

    remove_indices = set()
    for start, end in markers_to_remove:
        for i in range(start, end):
            remove_indices.add(i)

    while idx <= len(block_text):
        while markers_to_insert and markers_to_insert[0][0] == idx:
            res += markers_to_insert[0][1]
            markers_to_insert.pop(0)

        if idx < len(block_text):
            if idx not in remove_indices:
                res += block_text[idx]
        idx += 1

    return res

print(toggle_format("__under this__", 2, 7, "**"))
