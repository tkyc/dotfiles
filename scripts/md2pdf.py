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
ML, MR, MT, MB = 58.0, 58.0, 60.0, 56.0     # page margins
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
TOP = -(MT + 8.0)

cur = []        # PDF content operators for the page being built
PAGES = []      # list of (ops, page_height)
y = TOP         # cursor; 0 is the top of the page, growing negative downward

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

def disc(cx, cy, rad, color):
    r, g, b = color
    k = 0.5523 * rad
    emit("%.3f %.3f %.3f rg" % (r, g, b))
    emit("%.2f %.2f m" % (cx + rad, cy))
    emit("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx + rad, cy + k, cx + k, cy + rad, cx, cy + rad))
    emit("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx - k, cy + rad, cx - rad, cy + k, cx - rad, cy))
    emit("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx - rad, cy - k, cx - k, cy - rad, cx, cy - rad))
    emit("%.2f %.2f %.2f %.2f %.2f %.2f c" % (cx + k, cy - rad, cx + rad, cy - k, cx + rad, cy))
    emit("f")

def finish_page(h):
    global cur, y
    PAGES.append((cur[:], h))
    cur.clear()
    y = TOP

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

def parse_inline(s):
    """Return a list of (text, style) runs. style in reg/bold/ital/mono/link/break."""
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
        elif m.group("b1") is not None:
            runs.append((m.group("b1"), "bold"))
        elif m.group("b2") is not None:
            runs.append((m.group("b2"), "bold"))
        elif m.group("i1") is not None:
            runs.append((m.group("i1"), "ital"))
        elif m.group("i2") is not None:
            runs.append((m.group("i2"), "ital"))
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
        xx = x_left + indent
        for wi, word in enumerate(line):
            if wi > 0:
                xx += space_w
            for frag, st in word:
                fw = text_w(frag, st, size)
                if st == "mono":
                    fillrect(xx - 1.0, y - 2.5, fw + 2.0, size + 1.5, CODE_BG)
                show(xx, y, frag, st, size, frag_color(st, color))
                xx += fw
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
def render_table(headers, rows):
    """headers: list of cells (or []); each cell is a list[str] of lines.
    rows: list of ('data', [cells]) or ('span', text). Cells may be multi-line (via <br>)."""
    global y
    ncol = len(headers) if headers else max((len(r[1]) for r in rows if r[0] == "data"), default=1)
    size = 9.5; padx = 7.0; base = 17.0; lh = 12.0
    widths = [0.0] * ncol

    def consider(cells):
        for i, c in enumerate(cells[:ncol]):
            widths[i] = max(widths[i], max((text_w(ln, "reg", size) for ln in c), default=0.0))
    if headers:
        consider(headers)
    for r in rows:
        if r[0] == "data":
            consider(r[1])
    widths = [w + 2 * padx for w in widths]
    total = sum(widths)
    if total > CW:
        scale = CW / total
        widths = [w * scale for w in widths]
        total = CW
    offs = []; acc = 0.0
    for w in widths:
        offs.append(acc); acc += w
    x0 = ML

    def row_height(cells):
        return base + (max((len(c) for c in cells), default=1) - 1) * lh

    def draw_cells(cells, bold=False, bg=None):
        global y
        rh = row_height(cells)
        if bg:
            fillrect(x0, y - rh + 4, total, rh, bg)
        for i in range(ncol):
            strokerect(x0 + offs[i], y - rh + 4, widths[i], rh, TBORDER)
            if i < len(cells):
                yy = y - 8
                for ln in cells[i]:
                    show(x0 + offs[i] + padx, yy, ln, "bold" if bold else "reg",
                         size, HEAD if bold else BODY)
                    yy -= lh
        y -= rh

    if headers:
        need(row_height(headers))
        draw_cells(headers, bold=True, bg=THEAD_BG)
    for r in rows:
        if r[0] == "span":
            if need(base) and headers:
                draw_cells(headers, bold=True, bg=THEAD_BG)
            strokerect(x0, y - base + 4, total, base, TBORDER)
            tw = text_w(r[1], "ital", size)
            show(x0 + (total - tw) / 2.0, y - base + 9, r[1], "ital", size, MUTED)
            y -= base
        else:
            if need(row_height(r[1])) and headers:
                draw_cells(headers, bold=True, bg=THEAD_BG)
            draw_cells(r[1])

# ---------------------------------------------------------------- other blocks
def draw_code_block(code_lines):
    global y
    size = 9.5; lh = 13.0; padx = 8.0; pady = 7.0
    bh = pady * 2 + lh * max(1, len(code_lines))
    need(bh)
    fillrect(ML, y - bh, CW, bh, CODE_BG)
    strokerect(ML, y - bh, CW, bh, (0.90, 0.91, 0.93), 0.6)
    yy = y - pady - lh + 3.5
    for ln in code_lines:
        show(ML + padx, yy, ln, "mono", size, CODE_TX)
        yy -= lh
    y -= bh + 6

def draw_blockquote(text):
    global y
    y0 = y
    draw_flow(parse_inline(text), ML + 16, CW - 16, 10.5, 15.5, MUTED)
    y1 = y
    fillrect(ML + 2, y1 + 2, 3.0, (y0 - y1), BAR)
    y -= 6

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)

def cell_lines(raw):
    """Split a table cell into display lines, honoring <br> (so it isn't just stripped)."""
    t = strip_tags(_BR_RE.sub(NUL, raw))
    return [seg.strip() for seg in t.split(NUL)]

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
            draw_code_block(code)
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            level = len(m.group(1)); txt = m.group(2).rstrip("#").strip()
            if level == 1:
                size, lead, sb, sa = 19.0, 24.0, 2.0, 8.0
            elif level == 2:
                size, lead, sb, sa = 15.0, 20.0, 20.0, 7.0
            else:
                size, lead, sb, sa = 12.5, 16.0, 14.0, 4.0
            y -= sb
            draw_flow(parse_inline(txt), ML, CW, size, lead, HEAD)
            if level <= 2:
                y += 2
                rule(ML, y, ML + CW, RULE, 0.9)
                y -= 6
            y -= sa
            i += 1
            continue

        # horizontal rule
        if re.match(r"^(\*\s*){3,}$", s) or re.match(r"^(-\s*){3,}$", s) or re.match(r"^(_\s*){3,}$", s):
            y -= 8
            rule(ML, y, ML + CW, RULE, 1.0)
            y -= 12
            i += 1
            continue

        # blockquote
        if s.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            draw_blockquote(" ".join(q.strip() for q in quote if q.strip()))
            continue

        # HTML table
        if s.startswith("<table"):
            headers = []; rows = []
            while i < n and "</table>" not in lines[i]:
                row = lines[i].strip()
                if "<th>" in row:
                    headers = [cell_lines(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", row)]
                elif "<td" in row:
                    if "colspan" in row:
                        cell = re.findall(r"<td[^>]*>(.*?)</td>", row)
                        rows.append(("span", " ".join(cell_lines(cell[0])) if cell else ""))
                    else:
                        cells = re.findall(r"<td[^>]*>(.*?)</td>", row)
                        rows.append(("data", [cell_lines(c) for c in cells]))
                i += 1
            i += 1  # skip </table>
            y -= 4
            render_table(headers, rows)
            y -= 6
            continue

        # GitHub pipe table
        if "|" in s and i + 1 < n and is_delim_row(lines[i + 1]):
            headers = [cell_lines(c) for c in s.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                cells = [cell_lines(c) for c in lines[i].strip().strip("|").split("|")]
                rows.append(("data", cells))
                i += 1
            y -= 4
            render_table(headers, rows)
            y -= 6
            continue

        # unordered list
        if re.match(r"^[-*+]\s+", s):
            while i < n and re.match(r"^[-*+]\s+", lines[i].strip()):
                item = re.sub(r"^[-*+]\s+", "", lines[i].strip())
                need(15.5)
                disc(ML + 8, y + 3.4, 1.7, BODY)
                draw_flow(parse_inline(item), ML + 20, CW - 20, 10.5, 15.5, BODY)
                y -= 3
                i += 1
            y -= 6
            continue

        # ordered list
        if re.match(r"^\d+\.\s+", s):
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                mm = re.match(r"^(\d+)\.\s+(.*)$", lines[i].strip())
                need(15.5)
                show(ML + 4, y, mm.group(1) + ".", "reg", 10.5, BODY)
                draw_flow(parse_inline(mm.group(2)), ML + 24, CW - 24, 10.5, 15.5, BODY)
                y -= 3
                i += 1
            y -= 6
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
        draw_flow(parse_inline(" ".join(para)), ML, CW, 10.5, 15.5, BODY)
        y -= 9

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
    global PAGE_W, CW, PAGINATE, PAGE_H, TOP, y, cur, PAGES

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
    TOP = -(MT + 8.0)
    y = TOP
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
