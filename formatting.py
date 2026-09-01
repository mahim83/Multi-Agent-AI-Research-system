"""Turn the writer's raw markdown into markdown Streamlit can actually render.

The model likes two things Streamlit's renderer will not accept: HTML line
breaks inside table cells (`<br>`), which come out as literal text because
`st.markdown` escapes raw HTML, and wide comparison tables whose cells hold
whole paragraphs, which are unreadable even once the breaks work.

The writer prompt asks it not to do either. This is the net for when it does
anyway, so the report renders the same in Streamlit, in the downloaded `.md`
and in the terminal.
"""

import re

BR = re.compile(r"<\s*br\s*/?\s*>", re.IGNORECASE)
BULLET_CHAR = re.compile(r"^(\s*)[\u2022\u00b7\u25aa\u25b8\u2023]\s*")
LIST_ITEM = re.compile(r"^\s*(?:[-*+\u2022\u00b7\u25aa\u25b8\u2023]|\d+[.)])\s")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
DASHES = re.compile(r"^:?-+:?$")

# Tags the model reaches for that markdown has its own syntax for.
INLINE_MARKUP = [
    (re.compile(r"</?\s*(?:b|strong)\s*>", re.IGNORECASE), "**"),
    (re.compile(r"</?\s*(?:i|em)\s*>", re.IGNORECASE), "*"),
]
# Tags that carry no meaning once the layout is markdown.
NOISE_TAGS = re.compile(
    r"</?\s*(?:span|div|p|u|small|font|center|sub|sup)(?:\s[^>]*)?>", re.IGNORECASE
)

# A table whose cells stay this short still reads fine as a table; anything
# wider gets unrolled into sections.
MAX_CELL_CHARS = 120
# A leading cell this short is a row number or label, not content.
SHORT_CELL_CHARS = 24
# Past this, a cell is a paragraph rather than a statement, so it stays a field.
MAX_HEADING_CHARS = 200


def normalize_report(text):
    """Clean up one model-written markdown document."""
    if not text:
        return ""

    lines = str(text).replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    in_fence = False

    while i < len(lines):
        line = lines[i]

        # Code fences are left exactly as they are: HTML inside one is content.
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line.rstrip())
            i += 1
            continue
        if in_fence:
            out.append(line)
            i += 1
            continue

        block = _table_block(lines, i)
        if block:
            out.append("")
            out.extend(_rewrite_table(block))
            out.append("")
            i += len(block)
            continue

        cleaned = _clean(line)
        # Trailing whitespace goes, except the two spaces that are a line break.
        out.append(cleaned if cleaned.endswith("  ") else cleaned.rstrip())
        i += 1

    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def _clean(text):
    """Expand `<br>`, fix bullet characters and drop leftover HTML tags."""
    if BR.search(text):
        indent = text[: len(text) - len(text.lstrip())]
        parts = [p.strip() for p in BR.split(text) if p.strip()]
        broken = []
        for position, part in enumerate(parts):
            following = parts[position + 1] if position + 1 < len(parts) else ""
            # A bare newline is not a line break in markdown, so a continuing
            # sentence needs the two trailing spaces that make one. A list item
            # already starts its own line and does not.
            hard_break = following and not LIST_ITEM.match(following)
            broken.append(indent + part + ("  " if hard_break else ""))
        text = "\n".join(broken)

    text = "\n".join(BULLET_CHAR.sub(r"\1- ", part) for part in text.split("\n"))
    for pattern, replacement in INLINE_MARKUP:
        text = pattern.sub(replacement, text)
    return NOISE_TAGS.sub("", text)


def _is_row(line):
    stripped = line.strip()
    return stripped.startswith("|") and stripped.count("|") >= 2


def _cells(line):
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [c.strip().replace("\\|", "|") for c in CELL_SPLIT.split(stripped)]


def _table_block(lines, i):
    """Return the table starting at `i` (header, separator, rows), or None."""
    if not _is_row(lines[i]) or i + 1 >= len(lines) or not _is_row(lines[i + 1]):
        return None
    separator = _cells(lines[i + 1])
    if not separator or not all(DASHES.fullmatch(c) for c in separator):
        return None

    end = i + 2
    while end < len(lines) and _is_row(lines[end]):
        end += 1
    return lines[i:end]


def _rewrite_table(block):
    """Keep a narrow table as a table; unroll a wide one into sections."""
    rows = [_cells(line) for line in block[2:]]
    widest = max((len(cell) for row in rows for cell in row), default=0)
    if widest <= MAX_CELL_CHARS and not any(BR.search(line) for line in block):
        return [_clean(line).rstrip() for line in block]

    headers = _cells(block[0])
    out = []
    for position, row in enumerate(rows, start=1):
        out.extend(_unroll(headers, row, position))
    return out


def _unroll(headers, row, position):
    """Rewrite one table row as a heading plus a labelled block per column."""
    width = max(len(headers), len(row))
    headers = list(headers) + [""] * (width - len(headers))
    cells = [_clean(c) for c in row] + [""] * (width - len(row))

    # Leading short cells are the row's number or label, so they belong in the
    # heading rather than in a field of their own.
    index = 0
    labels = []
    while index < len(cells) - 1 and len(cells[index]) <= SHORT_CELL_CHARS:
        if cells[index]:
            labels.append(cells[index])
        index += 1

    title = BR.sub(" ", cells[index]) if index < len(cells) else ""
    title = " ".join(title.split())
    if title and len(title) <= MAX_HEADING_CHARS:
        index += 1
    else:
        title = ""  # too long to be a heading; leave it as a field below

    label = " ".join(labels) or str(position)
    out = [f"### {label}. {title}" if title else f"### {label}", ""]

    for header, cell in zip(headers[index:], cells[index:]):
        if not cell:
            continue
        if header and "\n" not in cell and len(cell) <= 80:
            out.append(f"**{header}:** {cell}")
        else:
            if header:
                out.extend([f"**{header}**", ""])
            out.append(cell)
        out.append("")

    return out
