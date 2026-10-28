#!/usr/bin/env python3
"""
md2pdf.py -- convert a Markdown file to a PDF, with no dependencies.

Pure Python 3 standard library only: no pip installs, and no external programs
(no Ghostscript / pandoc / browser). It writes the PDF bytes directly, using the
base-14 PDF fonts (Helvetica family + Courier), which need no embedding.

Style approximates markdownlivepreview.com: clean sans-serif body, bold headings
with an underline on the top two levels, grey rules, bordered tables with a
shaded header, fenced code boxes and blockquotes.

Usage:
    python3 md2pdf.py input.md [output.pdf]
    python3 md2pdf.py input.md --paginate --page-size a4
    python3 md2pdf.py input.md -o out.pdf --width 612

Options:
    --paginate            multi-page output (default: one continuous tall page)
    --page-size letter|a4 page size when paginating (default: letter)
    --width PT            page width in points (default: 612)

Supported Markdown: headings (#..######), paragraphs, bold (**/__),
italic (*/_), inline code (`code`), links ([text](url)), unordered lists
(*, -, +), ordered lists (1.), fenced code blocks (```), blockquotes (>),
horizontal rules (***, ---, ___), GitHub pipe tables and HTML <table>.
"""

import re
import html
import argparse

# ---------------------------------------------------------------- font metrics
# Adobe AFM advance widths (units per 1000), ASCII 32..126.
_HELV = ("278 278 355 556 556 889 667 191 333 333 389 584 278 333 278 278 556 "
         "556 556 556 556 556 556 556 556 556 278 278 584 584 584 556 1015 667 "
         "667 722 722 667 611 778 722 278 500 667 556 833 722 778 667 778 722 "
         "667 611 722 667 944 667 667 611 278 278 278 469 556 333 556 556 500 "
         "556 556 278 556 556 222 222 500 222 833 556 556 556 556 333 500 278 "
         "556 500 722 500 500 500 334 260 334 584")
_HELVB = ("278 333 474 556 556 889 722 238 333 333 389 584 278 333 278 278 556 "
          "556 556 556 556 556 556 556 556 556 333 333 584 584 584 611 975 722 "
          "722 722 722 667 611 778 722 278 556 722 611 833 722 778 667 778 722 "
          "667 611 722 667 944 667 667 611 333 278 333 584 556 333 556 611 556 "
          "611 556 333 611 611 278 278 556 278 889 611 611 611 611 389 556 333 "
          "611 556 778 556 556 500 389 280 389 584")

def _build(s):
    return {chr(32 + i): int(v) for i, v in enumerate(s.split())}

_W = {"reg": _build(_HELV), "bold": _build(_HELVB)}

# style -> PDF font resource name; F1..F5 are declared in every page's resources
STYLE2RES = {"reg": "F1", "bold": "F2", "ital": "F3", "mono": "F4",
             "bolditalic": "F5", "link": "F1"}

def char_w(ch, style):
    if style == "mono":
        return 600
    tbl = _W["bold"] if style in ("bold", "bolditalic") else _W["reg"]
    return tbl.get(ch, 556)

def text_w(s, style, size):
    return sum(char_w(c, style) for c in s) * size / 1000.0

# ---------------------------------------------------------------- style tokens
ML, MR, MT, MB = 58.0, 58.0, 56.0, 56.0     # page margins
GAP      = 10.0     # space between text blocks (paragraphs, lists)
BOX_GAP  = 13.0     # space around boxed blocks (tables, code). Text line boxes already
                    # carry half-leading above and below, so boxes get a bit more.
ASC, DESC = 0.718, 0.207                    # Helvetica ascent/descent, fraction of size
BODY     = (0.20, 0.22, 0.25)
HEAD     = (0.09, 0.11, 0.13)
RULE     = (0.86, 0.88, 0.90)
TBORDER  = (0.80, 0.82, 0.84)
THEAD_BG = (0.949, 0.957, 0.965)
MUTED    = (0.40, 0.43, 0.47)
LINK     = (0.13, 0.38, 0.72)
CODE_BG  = (0.945, 0.95, 0.96)
CODE_TX  = (0.16, 0.18, 0.22)
BAR      = (0.80, 0.82, 0.86)

# ---------------------------------------------------------------- render state
# Set in main(); declared here so the drawing functions can use them as globals.
PAGE_W = 612.0
CW = PAGE_W - ML - MR
PAGINATE = False
PAGE_H = 792.0
TOP = -MT

cur = []        # PDF content operators for the page being built
PAGES = []      # list of (ops, page_height)
y = TOP         # cursor: top edge of the next block; 0 is the top of the page, growing negative downward
gap = 0.0       # bottom margin of the previous block, still to be applied

def emit(s):
    cur.append(s)

def esc(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

def show(x, yy, s, style, size, color):
    if not s:
        return
    r, g, b = color
    emit("%.3f %.3f %.3f rg" % (r, g, b))
    emit("BT /%s %.2f Tf %.2f %.2f Td (%s) Tj ET" %
         (STYLE2RES[style], size, x, yy, esc(s)))

def fillrect(x, yy, w, h, color):
    r, g, b = color
    emit("%.3f %.3f %.3f rg" % (r, g, b))
    emit("%.2f %.2f %.2f %.2f re f" % (x, yy, w, h))

def strokerect(x, yy, w, h, color, lw=0.7):
    r, g, b = color
    emit("%.3f %.3f %.3f RG" % (r, g, b))
    emit("%.2f w %.2f %.2f %.2f %.2f re S" % (lw, x, yy, w, h))

def rule(x1, yy, x2, color, lw=0.8):
    r, g, b = color
    emit("%.3f %.3f %.3f RG" % (r, g, b))
    emit("%.2f w %.2f %.2f m %.2f %.2f l S" % (lw, x1, yy, x2, yy))

def disc(cx, cy, rad, color, hollow=False):
    r, g, b = color
    k = 0.5523 * rad
    if hollow:
        emit("%.3f %.3f %.3f RG 0.7 w" % (r, g, b))
    else:
        emit("%.3f %.3f %.3f rg" % (r, g, b))
    emit("%.2f %.2f m" % (cx + rad, cy))
    emit("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx + rad, cy + k, cx + k, cy + rad, cx, cy + rad))
    emit("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx - k, cy + rad, cx - rad, cy + k, cx - rad, cy))
    emit("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx - rad, cy - k, cx - k, cy - rad, cx, cy - rad))
    emit("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx + k, cy - rad, cx + rad, cy - k, cx + rad, cy))
    emit("S" if hollow else "f")

def finish_page(h):
    global cur, y
    PAGES.append((cur[:], h))
    cur.clear()
    y = TOP

def block_start(mt):
    """Open a block: move down by the larger of the previous block's bottom margin and
    this block's top margin (margins collapse, as in CSS). No margin at the top of a page."""
    global y, gap
    if y < TOP:
        y -= max(gap, mt)
    gap = 0.0

def block_end(mb):
    global gap
    gap = mb

def baseline_off(size, leading):
    """Distance from the top of a line box down to the baseline, glyphs centered in the box."""
    return (leading - (ASC + DESC) * size) / 2.0 + ASC * size

def need(h):
    """In paginate mode, break to a new page if h points won't fit. Returns True if it broke."""
    global y
    if not PAGINATE:
        return False
    if y - h < -(PAGE_H - MB):
        finish_page(PAGE_H)
        return True
    return False

# ---------------------------------------------------------------- inline parser
BREAK = object()                       # sentinel word meaning "force a new line"
NUL = "\x00"                           # internal marker for a forced break
_BR_RE = re.compile(r"<\s*/?\s*br\s*/?\s*>", re.I)   # <br> <br/> <br /> </br>

_INLINE = re.compile(
    r"`(?P<code>[^`]+)`"
    r"|\[(?P<ltext>[^\]]+)\]\((?P<lurl>[^)]+)\)"
    r"|\*\*(?P<b1>.+?)\*\*"
    r"|(?<!\w)__(?P<b2>.+?)__(?!\w)"
    r"|\*(?P<i1>[^*]+?)\*"
    r"|(?<!\w)_(?P<i2>[^_]+?)_(?!\w)"
)

# style of an inner run once it is wrapped in bold / italic (code and links keep theirs)
_IN_BOLD = {"reg": "bold", "ital": "bolditalic"}
_IN_ITAL = {"reg": "ital", "bold": "bolditalic"}

def parse_inline(s):
    """Return a list of (text, style) runs. style in reg/bold/ital/bolditalic/mono/link/break."""
    s = s.replace("<em>", "*").replace("</em>", "*")
    s = s.replace("<strong>", "**").replace("</strong>", "**")
    s = _BR_RE.sub(NUL, s)             # <br> variants -> forced-break marker
    runs = []
    pos = 0
    for m in _INLINE.finditer(s):
        if m.start() > pos:
            runs.append((s[pos:m.start()], "reg"))
        if m.group("code") is not None:
            runs.append((m.group("code"), "mono"))
        elif m.group("ltext") is not None:
            runs.append((m.group("ltext"), "link"))
        else:
            # bold / italic: parse the inside too, so `code` and links in it keep their style
            inner = next(g for g in ("b1", "b2", "i1", "i2") if m.group(g) is not None)
            wrap = _IN_BOLD if inner[0] == "b" else _IN_ITAL
            runs.extend((t, wrap.get(st, st)) for t, st in parse_inline(m.group(inner)))
        pos = m.end()
    if pos < len(s):
        runs.append((s[pos:], "reg"))
    # split out forced breaks (a NUL may sit inside any run, e.g. inside bold)
    final = []
    for text, style in runs:
        if NUL in text:
            parts = text.split(NUL)
            for k, part in enumerate(parts):
                if part:
                    final.append((part, style))
                if k < len(parts) - 1:
                    final.append(("", "break"))
        else:
            final.append((text, style))
    return final

def words_from_runs(runs):
    """Group runs into words; each word is a list of (fragment, style) or the BREAK sentinel."""
    words = []
    cur_word = []
    for text, style in runs:
        if style == "break":
            if cur_word:
                words.append(cur_word); cur_word = []
            words.append(BREAK)
            continue
        for p in re.split(r"(\s+)", text):
            if p == "":
                continue
            if p.strip() == "":
                if cur_word:
                    words.append(cur_word); cur_word = []
            else:
                cur_word.append((p, style))
    if cur_word:
        words.append(cur_word)
    return words

def word_width(word, size):
    return sum(text_w(f, st, size) for f, st in word)

def frag_color(style, base):
    if style == "link":
        return LINK
    if style == "mono":
        return CODE_TX
    return base

def draw_flow(runs, x_left, max_w, size, leading, color, first_indent=0.0):
    global y
    words = words_from_runs(runs)
    space_w = text_w(" ", "reg", size)
    line = []; line_w = 0.0; indent = first_indent

    def flush():
        global y
        need(leading)
        draw_words(line, x_left + indent, y - baseline_off(size, leading), size, color)
        y -= leading

    for word in words:
        if word is BREAK:
            flush()                       # draw the partial line, then start a new one
            line = []; line_w = 0.0; indent = 0.0
            continue
        ww = word_width(word, size)
        add = ww if not line else (space_w + ww)
        if line and (indent + line_w + add) > max_w:
            flush()
            line = []; line_w = 0.0; indent = 0.0
            line.append(word); line_w = word_width(word, size)
        else:
            line.append(word); line_w += add
    if line:
        flush()

# ---------------------------------------------------------------- tables
_BOLDER = {"reg": "bold", "ital": "bolditalic"}

# Column widths are computed as (inner + 2*padx) and later reduced by 2*padx, so a
# word exactly as wide as its column can come back a hair too wide from float rounding.
FIT_EPS = 0.01

def split_long_word(word, max_w, size):
    """Break a word wider than max_w into character chunks that each fit."""
    if max_w <= 0 or word_width(word, size) <= max_w + FIT_EPS:
        return [word]
    pieces, piece, pw = [], [], 0.0
    for frag, st in word:
        buf = ""
        for ch in frag:
            cw = text_w(ch, st, size)
            if pw + cw > max_w + FIT_EPS and (piece or buf):
                if buf:
                    piece.append((buf, st)); buf = ""
                pieces.append(piece); piece, pw = [], 0.0
            buf += ch; pw += cw
        if buf:
            piece.append((buf, st))
    if piece:
        pieces.append(piece)
    return pieces

def wrap_words(words, max_w, size):
    """Wrap a cell's words (BREAK = forced newline) into lines that fit max_w."""
    space_w = text_w(" ", "reg", size)
    lines, line_w = [[]], 0.0
    for word in words:
        if word is BREAK:
            lines.append([]); line_w = 0.0
            continue
        for piece in split_long_word(word, max_w, size):
            pw = word_width(piece, size)
            if lines[-1] and line_w + space_w + pw > max_w + FIT_EPS:
                lines.append([]); line_w = 0.0
            if lines[-1]:
                line_w += space_w
            lines[-1].append(piece); line_w += pw
    return lines

def draw_words(line, x, yy, size, color):
    """Draw one wrapped line of styled words starting at x."""
    space_w = text_w(" ", "reg", size)
    xx = x
    for wi, word in enumerate(line):
        if wi > 0:
            xx += space_w
        for frag, st in word:
            fw = text_w(frag, st, size)
            if st == "mono":
                fillrect(xx - 1.0, yy - 2.5, fw + 2.0, size + 1.5, CODE_BG)
            show(xx, yy, frag, st, size, frag_color(st, color))
            xx += fw

def column_widths(cell_rows, ncol, size, padx):
    """Auto table layout: each column gets at least its longest word, and leftover
    space goes to columns in proportion to how much wider their text wants to be."""
    space_w = text_w(" ", "reg", size)
    nat = [0.0] * ncol      # widest line if nothing wrapped
    mn = [0.0] * ncol       # widest single word
    for cells in cell_rows:
        for i, words in enumerate(cells[:ncol]):
            line_w, first = 0.0, True
            for word in words:
                if word is BREAK:
                    nat[i] = max(nat[i], line_w); line_w, first = 0.0, True
                    continue
                ww = word_width(word, size)
                mn[i] = max(mn[i], ww)
                line_w += ww if first else space_w + ww
                first = False
            nat[i] = max(nat[i], line_w)
    avail = CW - 2 * padx * ncol
    if sum(nat) <= avail:
        inner = nat
    elif sum(mn) >= avail:
        tot = sum(mn)
        inner = [m * avail / tot for m in mn] if tot else [avail / ncol] * ncol
    else:
        extra = avail - sum(mn)
        flex = [n - m for n, m in zip(nat, mn)]
        tf = sum(flex)
        inner = [m + (extra * f / tf if tf else extra / ncol) for m, f in zip(mn, flex)]
    return [w + 2 * padx for w in inner]

def render_table(headers, rows):
    """headers: list of cells (or []); each cell is a list of words from cell_words().
    rows: list of ('data', [cells]) or ('span', text). Cell text wraps to its column,
    keeps inline styles (bold, italic, code, links) and honors <br> line breaks."""
    global y
    ncol = len(headers) if headers else max((len(r[1]) for r in rows if r[0] == "data"), default=1)
    size = 9.5; padx = 7.0; pady = 4.0; lh = 12.0
    off = pady + baseline_off(size, lh)     # row top -> first baseline
    headers = [[w if w is BREAK else [(f, _BOLDER.get(st, st)) for f, st in w] for w in c]
               for c in headers]
    widths = column_widths(([headers] if headers else []) + [r[1] for r in rows if r[0] == "data"],
                           ncol, size, padx)
    total = sum(widths)
    offs = []; acc = 0.0
    for w in widths:
        offs.append(acc); acc += w
    x0 = ML

    def wrap_row(cells):
        return [wrap_words(cells[i], widths[i] - 2 * padx, size) if i < len(cells) else [[]]
                for i in range(ncol)]

    def row_height(cells):
        return 2 * pady + max(len(c) for c in wrap_row(cells)) * lh

    def draw_cells(cells, bold=False, bg=None):
        global y
        wrapped = wrap_row(cells)
        rh = 2 * pady + max(len(c) for c in wrapped) * lh
        if bg:
            fillrect(x0, y - rh, total, rh, bg)
        for i in range(ncol):
            strokerect(x0 + offs[i], y - rh, widths[i], rh, TBORDER)
            yy = y - off
            for line in wrapped[i]:
                draw_words(line, x0 + offs[i] + padx, yy, size, HEAD if bold else BODY)
                yy -= lh
        y -= rh

    if headers:
        need(row_height(headers))
        draw_cells(headers, bold=True, bg=THEAD_BG)
    for r in rows:
        if r[0] == "span":
            rh = 2 * pady + lh
            if need(rh) and headers:
                draw_cells(headers, bold=True, bg=THEAD_BG)
            strokerect(x0, y - rh, total, rh, TBORDER)
            tw = text_w(r[1], "ital", size)
            show(x0 + (total - tw) / 2.0, y - off, r[1], "ital", size, MUTED)
            y -= rh
        else:
            if need(row_height(r[1])) and headers:
                draw_cells(headers, bold=True, bg=THEAD_BG)
            draw_cells(r[1])

# ---------------------------------------------------------------- other blocks
def draw_code_block(code_lines):
    global y
    size = 9.5; lh = 13.0; padx = 8.0; pady = 7.0
    code_lines = [ln.expandtabs(4).rstrip() for ln in code_lines]
    # Shrink the font so the longest line fits in the box (down to 7.5 pt), then wrap the rest.
    longest = max((len(ln) for ln in code_lines), default=0)
    fit = (CW - 2 * padx) / (0.6 * max(1, longest))        # Courier is 600/1000 em wide
    if fit < size:
        size = max(7.5, fit)
        lh = size * 13.0 / 9.5
    per_line = max(1, int((CW - 2 * padx) / (0.6 * size) + FIT_EPS))
    code_lines = [ln[k:k + per_line] for ln in code_lines
                  for k in range(0, max(1, len(ln)), per_line)]
    bh = pady * 2 + lh * max(1, len(code_lines))
    need(bh)
    fillrect(ML, y - bh, CW, bh, CODE_BG)
    strokerect(ML, y - bh, CW, bh, (0.90, 0.91, 0.93), 0.6)
    yy = y - pady - baseline_off(size, lh)
    for ln in code_lines:
        show(ML + padx, yy, ln, "mono", size, CODE_TX)
        yy -= lh
    y -= bh

def draw_blockquote(text):
    y0 = y
    draw_flow(parse_inline(text), ML + 16, CW - 16, 10.5, 15.5, MUTED)
    fillrect(ML + 2, y, 3.0, y0 - y, BAR)

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)

def cell_lines(raw):
    """Split a table cell into display lines, honoring <br> (so it isn't just stripped)."""
    t = strip_tags(_BR_RE.sub(NUL, raw))
    return [seg.strip() for seg in t.split(NUL)]

_HTML_INLINE = [("<strong>", "**"), ("</strong>", "**"), ("<b>", "**"), ("</b>", "**"),
                ("<em>", "*"), ("</em>", "*"), ("<i>", "*"), ("</i>", "*"),
                ("<code>", "`"), ("</code>", "`")]

def cell_words(raw):
    """Parse a table cell into styled words, keeping inline markup and <br> breaks."""
    s = _BR_RE.sub(NUL, raw)
    for tag, md in _HTML_INLINE:
        s = s.replace(tag, md)
    s = html.unescape(strip_tags(s)).strip()
    return words_from_runs(parse_inline(s))

# ---------------------------------------------------------------- block parser
def is_delim_row(s):
    s = s.strip()
    if "|" not in s and set(s) - set("-:| "):
        return False
    core = s.strip().strip("|")
    cells = [c.strip() for c in core.split("|")]
    if not cells or any(c == "" for c in cells):
        return False
    return all(re.match(r"^:?-+:?$", c) for c in cells)

_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")

def render_list(lines, i):
    """Draw the list that starts at lines[i] and return the index after it. A deeper
    indent starts a nested list. An indented line with no marker continues the item."""
    global y
    items = []                      # [indent, marker, text]
    first_ordered = None
    while i < len(lines):
        raw = lines[i].expandtabs(4)
        m = _LIST_RE.match(raw)
        if m:
            indent, marker = len(m.group(1)), m.group(2)
            ordered = marker[0].isdigit()
            # a top-level item of the other kind (1. vs -) starts a new list
            if items and indent <= items[0][0] and ordered != first_ordered:
                break
            if not items:
                first_ordered = ordered
            items.append([indent, marker, m.group(3).strip()])
        elif (items and raw.strip() and raw[:1].isspace()
              and not raw.strip().startswith(("```", "~~~", ">", "|", "<table"))):
            items[-1][2] += " " + raw.strip()
        else:
            break
        i += 1

    block_start(GAP)
    size, lead = 10.5, 15.5
    stack = []                      # indents of the open levels
    xs = [ML]                       # left edge of each level
    for k, (indent, marker, text) in enumerate(items):
        while stack and indent < stack[-1]:
            stack.pop()
        if not stack or indent > stack[-1]:
            stack.append(indent)
        level = len(stack) - 1
        x = xs[min(level, len(xs) - 1)]
        if k > 0:
            y -= 3
        need(lead)
        bl = y - baseline_off(size, lead)
        if marker[0].isdigit():
            show(x + 4, bl, marker, "reg", size, BODY)
            tx = x + 24
        else:
            disc(x + 8, bl + 3.4, 1.7, BODY, hollow=level % 2 == 1)
            tx = x + 20
        del xs[level + 1:]
        xs.append(tx)               # a nested level starts under this item's text
        draw_flow(parse_inline(text), tx, CW - (tx - ML), size, lead, BODY)
    block_end(GAP)
    return i

def render_markdown(text):
    global y
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i, n = 0, len(lines)

    while i < n:
        raw = lines[i]
        s = raw.strip()
        if s == "":
            i += 1
            continue

        # fenced code block
        if s.startswith("```") or s.startswith("~~~"):
            fence = s[:3]
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith(fence):
                code.append(lines[i])
                i += 1
            i += 1  # closing fence
            block_start(BOX_GAP)
            draw_code_block(code)
            block_end(BOX_GAP)
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            level = len(m.group(1)); txt = m.group(2).rstrip("#").strip()
            # sb/sa: space before/after. A heading sits closer to its own section.
            if level == 1:
                size, lead, sb, sa = 19.0, 24.0, 24.0, 10.0
            elif level == 2:
                size, lead, sb, sa = 15.0, 20.0, 22.0, 10.0
            else:
                size, lead, sb, sa = 12.5, 16.0, 18.0, 6.0
            block_start(sb)
            need(lead * 2)                  # keep the heading with the next line
            draw_flow(parse_inline(txt), ML, CW, size, lead, HEAD)
            if level <= 2:
                y -= 3
                rule(ML, y, ML + CW, RULE, 0.9)
            block_end(sa)
            i += 1
            continue

        # horizontal rule
        if re.match(r"^(\*\s*){3,}$", s) or re.match(r"^(-\s*){3,}$", s) or re.match(r"^(_\s*){3,}$", s):
            block_start(20.0)
            rule(ML, y, ML + CW, RULE, 1.0)
            block_end(20.0)
            i += 1
            continue

        # blockquote
        if s.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            block_start(BOX_GAP)
            draw_blockquote(" ".join(q.strip() for q in quote if q.strip()))
            block_end(BOX_GAP)
            continue

        # HTML table
        if s.startswith("<table"):
            headers = []; rows = []
            while i < n and "</table>" not in lines[i]:
                row = lines[i].strip()
                if "<th>" in row:
                    headers = [cell_words(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", row)]
                elif "<td" in row:
                    if "colspan" in row:
                        cell = re.findall(r"<td[^>]*>(.*?)</td>", row)
                        rows.append(("span", " ".join(cell_lines(cell[0])) if cell else ""))
                    else:
                        cells = re.findall(r"<td[^>]*>(.*?)</td>", row)
                        rows.append(("data", [cell_words(c) for c in cells]))
                i += 1
            i += 1  # skip </table>
            block_start(BOX_GAP)
            render_table(headers, rows)
            block_end(BOX_GAP)
            continue

        # GitHub pipe table
        if "|" in s and i + 1 < n and is_delim_row(lines[i + 1]):
            headers = [cell_words(c) for c in s.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                cells = [cell_words(c) for c in lines[i].strip().strip("|").split("|")]
                rows.append(("data", cells))
                i += 1
            block_start(BOX_GAP)
            render_table(headers, rows)
            block_end(BOX_GAP)
            continue

        # list (unordered or ordered, nested by indent)
        if _LIST_RE.match(raw):
            i = render_list(lines, i)
            continue

        # paragraph (join consecutive plain lines)
        para = []
        while i < n:
            raw = lines[i].rstrip("\n")
            c = raw.strip()
            if c == "":
                break
            if (re.match(r"^(#{1,6})\s", c) or c.startswith("```") or c.startswith("~~~")
                    or c.startswith(">") or c.startswith("<table")
                    or re.match(r"^(\*\s*){3,}$", c) or re.match(r"^(-\s*){3,}$", c) or re.match(r"^(_\s*){3,}$", c)
                    or re.match(r"^[-*+]\s+", c) or re.match(r"^\d+\.\s+", c)
                    or ("|" in c and i + 1 < n and is_delim_row(lines[i + 1]))):
                break
            # Markdown hard break: line ends with two+ spaces, or a backslash
            hard = bool(re.search(r"\S  +$", raw))
            if c.endswith("\\"):
                c = c[:-1].rstrip()
                hard = True
            para.append(c + (NUL if hard else ""))
            i += 1
        block_start(GAP)
        draw_flow(parse_inline(" ".join(para)), ML, CW, 10.5, 15.5, BODY)
        block_end(GAP)

# ---------------------------------------------------------------- PDF writer
def build_pdf(pages, page_w, path):
    fonts = [("F1", "Helvetica"), ("F2", "Helvetica-Bold"), ("F3", "Helvetica-Oblique"),
             ("F4", "Courier"), ("F5", "Helvetica-BoldOblique")]
    P = len(pages)
    NUM_CAT, NUM_PAGES = 1, 2
    font_start = 3
    font_nums = {res: font_start + k for k, (res, _) in enumerate(fonts)}
    nn = font_start + len(fonts)
    page_nums, content_nums = [], []
    for _ in range(P):
        page_nums.append(nn); nn += 1
        content_nums.append(nn); nn += 1
    maxnum = nn - 1

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}

    def write(num, body):
        offsets[num] = len(pdf)
        pdf.extend(("%d 0 obj\n" % num).encode("latin-1"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")

    write(NUM_CAT, b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join("%d 0 R" % pn for pn in page_nums)
    write(NUM_PAGES, ("<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, P)).encode("latin-1"))
    for res, base in fonts:
        write(font_nums[res],
              ("<< /Type /Font /Subtype /Type1 /BaseFont /%s /Encoding /WinAnsiEncoding >>" % base).encode("latin-1"))
    fontres = " ".join("/%s %d 0 R" % (res, font_nums[res]) for res, _ in fonts)

    for idx, (ops, h) in enumerate(pages):
        stream = ("1 0 0 1 0 %.2f cm\n" % h) + "\n".join(ops) + "\n"
        # cp1252 matches the fonts' WinAnsiEncoding, so smart quotes, en/em
        # dashes, ellipsis, bullet, etc. render correctly instead of as '?'.
        sb = stream.encode("cp1252", "replace")
        write(content_nums[idx],
              b"<< /Length %d >>\nstream\n" % len(sb) + sb + b"endstream")
        write(page_nums[idx],
              ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] "
               "/Resources << /Font << %s >> >> /Contents %d 0 R >>"
               % (page_w, h, fontres, content_nums[idx])).encode("latin-1"))

    xref_off = len(pdf)
    pdf.extend(("xref\n0 %d\n" % (maxnum + 1)).encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for num in range(1, maxnum + 1):
        pdf.extend(("%010d 00000 n \n" % offsets[num]).encode("latin-1"))
    pdf.extend(("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                % (maxnum + 1, xref_off)).encode("latin-1"))

    with open(path, "wb") as f:
        f.write(pdf)

# ---------------------------------------------------------------- main
def main():
    global PAGE_W, CW, PAGINATE, PAGE_H, TOP, y, gap, cur, PAGES

    ap = argparse.ArgumentParser(description="Convert Markdown to PDF (no dependencies).")
    ap.add_argument("input", help="input .md file")
    ap.add_argument("output", nargs="?", help="output .pdf (default: input with .pdf)")
    ap.add_argument("-o", "--out", dest="out_flag", help="output .pdf path")
    ap.add_argument("--paginate", action="store_true", help="multi-page output")
    ap.add_argument("--page-size", choices=["letter", "a4"], default="letter")
    ap.add_argument("--width", type=float, default=612.0, help="page width in points")
    args = ap.parse_args()

    out_path = args.out_flag or args.output
    if not out_path:
        out_path = re.sub(r"\.(md|markdown|txt)$", "", args.input, flags=re.I) + ".pdf"

    PAGE_W = args.width
    CW = PAGE_W - ML - MR
    PAGINATE = args.paginate
    PAGE_H = 842.0 if args.page_size == "a4" else 792.0
    TOP = -MT
    y = TOP
    gap = 0.0
    cur = []
    PAGES = []

    with open(args.input, encoding="utf-8") as f:
        text = f.read()

    render_markdown(text)

    if PAGINATE:
        finish_page(PAGE_H)
    else:
        H = (-y) + MB
        PAGES.append((cur[:], H))

    build_pdf(PAGES, PAGE_W, out_path)
    total = "%d page%s" % (len(PAGES), "" if len(PAGES) == 1 else "s")
    if not PAGINATE:
        total += ", %.0f pt tall" % PAGES[0][1]
    print("Wrote %s (%s)" % (out_path, total))

if __name__ == "__main__":
    main()
