#!/usr/bin/env python3
"""
docxview.py -- view a Word .docx file in the terminal, with no dependencies.

Pure Python 3 standard library only: a .docx is a zip of XML parts, so this
reads word/document.xml (plus styles, numbering, relationships and notes) with
zipfile + ElementTree and renders it as ANSI-styled text, paged through less.

Usage:
    python3 docxview.py file.docx
    python3 docxview.py file.docx --width 80
    python3 docxview.py file.docx --plain > file.txt

Options:
    -w, --width N   wrap width (default: terminal width, max 100)
    --plain         no colors / styling (also the default when piping)
    --color         force colors even when piping
    --no-pager      write straight to stdout instead of $PAGER / less

Rendered: title/subtitle and headings, bold, italic, underline, strikethrough,
highlight, monospace runs, hyperlinks (with their URL), bullet and numbered
lists (from numbering.xml, nested levels included), indentation, alignment,
quotes, tables (merged cells and nested tables included), line and page
breaks, tracked insertions (deletions are hidden), footnotes and endnotes,
headers and footers (per section, with first-page / even-page variants; PAGE
fields show as '#' since there are no pages here), text boxes, and
placeholders for images.
"""

import argparse
import io
import os
import posixpath
import re
import shlex
import shutil
import subprocess
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET

# ------------------------------------------------------------------ namespaces
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}

# "Strict" OOXML uses different namespace URIs for the same vocabulary.
STRICT = [
    (b"http://purl.oclc.org/ooxml/wordprocessingml/main", NS["w"].encode()),
    (b"http://purl.oclc.org/ooxml/officeDocument/relationships", NS["r"].encode()),
]

def q(name):
    """'w:p' -> '{namespace}p' (ElementTree's Clark notation)."""
    pre, local = name.split(":")
    return "{%s}%s" % (NS[pre], local)

def wattr(el, name):
    return None if el is None else el.get(q("w:" + name))

def is_page(instr):
    """A PAGE field instruction (the current page number)."""
    return (instr or "").split()[:1] == ["PAGE"]

def on(el):
    """A toggle property like <w:b/>: present and not switched off."""
    return el is not None and wattr(el, "val") not in ("0", "false", "off", "none")

W_P, W_TBL, W_R, W_T = q("w:p"), q("w:tbl"), q("w:r"), q("w:t")
W_TXBX = q("w:txbxContent")
# containers whose children are treated as if they sat in the parent
TRANSPARENT = {q("w:sdt"), q("w:sdtContent"), q("w:customXml"), q("w:smartTag")}
# inline content that is never shown
SKIP = {q("w:pPr"), q("w:rPr"), q("w:sdtPr"), q("w:sdtEndPr"), q("w:del"),
        q("w:moveFrom"), q("w:instrText"), q("w:delText")}

MONO = {"courier", "courier new", "consolas", "menlo", "monaco",
        "lucida console", "source code pro", "fira code", "jetbrains mono"}
BULLETS = ["•", "◦", "▪"]

# ------------------------------------------------------------------- styling
SGR = {"b": "1", "dim": "2", "i": "3", "u": "4", "hl": "7", "s": "9",
       "code": "33", "link": "34;4", "hd": "36", "tt": "35"}
ANSI = re.compile(r"\x1b\[[0-9;]*m")

def paint(text, attrs, color):
    codes = ";".join(SGR[a] for a in sorted(attrs or ()) if a in SGR)
    if not color or not codes:
        return text
    return "\x1b[%sm%s\x1b[0m" % (codes, text)

def cwidth(ch):
    if unicodedata.combining(ch) or unicodedata.category(ch) == "Cf":
        return 0
    return 2 if unicodedata.east_asian_width(ch) in "WF" else 1

def swidth(s):
    return sum(cwidth(c) for c in s)

def vwidth(line):
    """Visible width of a painted line."""
    return swidth(ANSI.sub("", line))

def pad(line, width):
    return line + " " * max(0, width - vwidth(line))

# ---------------------------------------------------------------- numbering
def roman(n):
    out = ""
    for v, s in ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"),
                 (90, "xc"), (50, "l"), (40, "xl"), (10, "x"), (9, "ix"),
                 (5, "v"), (4, "iv"), (1, "i")):
        while n >= v:
            out, n = out + s, n - v
    return out

def letters(n):
    out = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        out = chr(97 + r) + out
    return out

def fmt_num(n, fmt):
    if fmt == "lowerLetter":
        return letters(n)
    if fmt == "upperLetter":
        return letters(n).upper()
    if fmt == "lowerRoman":
        return roman(n)
    if fmt == "upperRoman":
        return roman(n).upper()
    if fmt == "decimalZero":
        return "%02d" % n
    return str(n)

class Numbering:
    """numbering.xml: list definitions plus running counters per list."""

    def __init__(self, root):
        self.abstract = {}   # abstractNumId -> {ilvl: (numFmt, lvlText, start)}
        self.nums = {}       # numId -> (abstractNumId, {ilvl: startOverride})
        self.counters = {}   # numId -> {ilvl: current value}
        if root is None:
            return
        for an in root.findall("w:abstractNum", NS):
            levels = {}
            for lvl in an.findall("w:lvl", NS):
                levels[int(wattr(lvl, "ilvl") or 0)] = (
                    wattr(lvl.find("w:numFmt", NS), "val") or "decimal",
                    wattr(lvl.find("w:lvlText", NS), "val") or "",
                    int(wattr(lvl.find("w:start", NS), "val") or 1))
            self.abstract[wattr(an, "abstractNumId")] = levels
        for num in root.findall("w:num", NS):
            overrides = {}
            for ov in num.findall("w:lvlOverride", NS):
                start = ov.find("w:startOverride", NS)
                if start is not None:
                    overrides[int(wattr(ov, "ilvl") or 0)] = int(wattr(start, "val"))
            abs_id = wattr(num.find("w:abstractNumId", NS), "val")
            self.nums[wattr(num, "numId")] = (abs_id, overrides)

    def label(self, num_id, ilvl):
        """Advance the counter for (list, level) and return its marker."""
        abs_id, overrides = self.nums.get(num_id, (None, {}))
        levels = self.abstract.get(abs_id, {})
        fmt, text, start = levels.get(ilvl, ("bullet", "", 1))
        counts = self.counters.setdefault(num_id, {})
        counts[ilvl] = counts.get(ilvl, overrides.get(ilvl, start) - 1) + 1
        for deeper in [k for k in counts if k > ilvl]:
            del counts[deeper]
        if fmt == "bullet":
            return BULLETS[ilvl % len(BULLETS)]
        if fmt == "none":
            return ""

        def sub(m):
            lv = int(m.group(1)) - 1
            f, _, st = levels.get(lv, ("decimal", "", 1))
            return fmt_num(counts.get(lv, overrides.get(lv, st)), f)
        return re.sub(r"%(\d)", sub, text)

# ------------------------------------------------------------------- styles
def apply_rpr(attrs, rpr):
    """Layer one <w:rPr> onto a set of run attributes."""
    if rpr is None:
        return
    for tag, flag in (("b", "b"), ("i", "i"), ("u", "u"), ("strike", "s"),
                      ("dstrike", "s"), ("caps", "caps"), ("vanish", "hidden")):
        el = rpr.find("w:" + tag, NS)
        if el is not None:
            (attrs.add if on(el) else attrs.discard)(flag)
    hl = rpr.find("w:highlight", NS)
    if hl is not None:
        (attrs.add if on(hl) else attrs.discard)("hl")
    fonts = rpr.find("w:rFonts", NS)
    face = (wattr(fonts, "ascii") or wattr(fonts, "hAnsi") or "").lower()
    if face:
        mono = face in MONO or "mono" in face
        (attrs.add if mono else attrs.discard)("code")

class Styles:
    """styles.xml, resolved through basedOn chains."""

    def __init__(self, root):
        self.by_id = {}
        self.default_para = None
        self._kind = {}
        self._attrs = {}
        if root is None:
            return
        for s in root.findall("w:style", NS):
            sid = wattr(s, "styleId")
            self.by_id[sid] = s
            if wattr(s, "type") == "paragraph" and wattr(s, "default") in ("1", "true"):
                self.default_para = sid

    def chain(self, sid):
        """The style and its ancestors, most specific first."""
        out = []
        while sid in self.by_id and sid not in out:
            out.append(sid)
            sid = wattr(self.by_id[sid].find("w:basedOn", NS), "val")
        return [self.by_id[s] for s in out]

    def find(self, sid, path):
        for s in self.chain(sid):
            el = s.find(path, NS)
            if el is not None:
                return el
        return None

    def kind(self, sid):
        """('heading', n) / ('title', 0) / ('subtitle', 0) / ('quote', 0) / ('p', 0)."""
        if sid not in self._kind:
            self._kind[sid] = ("p", 0)
            for s in self.chain(sid):
                name = (wattr(s.find("w:name", NS), "val") or "").lower()
                m = re.fullmatch(r"heading (\d)", name)
                outline = wattr(s.find("w:pPr/w:outlineLvl", NS), "val")
                if m:
                    self._kind[sid] = ("heading", int(m.group(1)))
                elif name in ("title", "subtitle"):
                    self._kind[sid] = (name, 0)
                elif "quote" in name:
                    self._kind[sid] = ("quote", 0)
                elif outline and int(outline) < 9:
                    self._kind[sid] = ("heading", int(outline) + 1)
                else:
                    continue
                break
        return self._kind[sid]

    def run_attrs(self, psid, rsid):
        """Run attributes inherited from the paragraph and character styles."""
        key = (psid, rsid)
        if key not in self._attrs:
            attrs = set()
            for sid in (psid, rsid):
                for s in reversed(self.chain(sid)):
                    apply_rpr(attrs, s.find("w:rPr", NS))
            self._attrs[key] = frozenset(attrs)
        return self._attrs[key]

# ------------------------------------------------------------------- blocks
class Para:
    def __init__(self, spans, kind="p", level=0, label=None, indent=0, align=None):
        self.spans = spans    # [(text, attrs)]
        self.kind = kind      # p / heading / title / subtitle / quote
        self.level = level    # heading level
        self.label = label    # list marker, or None when not a list item
        self.indent = indent  # columns
        self.align = align    # None / center / right

    def empty(self):
        return self.label is None and not "".join(t for t, _ in self.spans).strip()

class Table:
    def __init__(self, rows):
        self.rows = rows      # [[Cell]]

class Cell:
    def __init__(self, blocks, span=1, merged=False, header=False):
        self.blocks = blocks
        self.span = span      # grid columns covered
        self.merged = merged  # continuation of a vertically merged cell
        self.header = header

class Rule:
    def __init__(self, title=None):
        self.title = title

class Frame:
    """A header or footer: its content between labelled rules."""
    def __init__(self, title, blocks):
        self.title = title
        self.blocks = blocks

# ------------------------------------------------------------------ reading
class Docx:
    def __init__(self, data):
        self.zip = zipfile.ZipFile(io.BytesIO(data))
        self.names = set(self.zip.namelist())
        main = next((t for kind, t in self.rels("").values()
                     if kind == "officeDocument"), "word/document.xml")
        self.main = main
        self.doc_rels = self.rels(main)
        self.part_rels = self.doc_rels   # rels of the part being read
        self.styles = Styles(self.part("styles"))
        self.numbering = Numbering(self.part("numbering"))
        self.notes = {"footnotes": None, "endnotes": None}  # parsed lazily
        self.note_refs = []      # [(label, kind, id)] in reading order
        self.page_break = False
        self.fields = []         # open complex fields: {instr, hide}
        settings = self.part("settings")
        self.even_odd = settings is not None and on(
            settings.find("w:evenAndOddHeaders", NS))

    def xml(self, name):
        if name not in self.names:
            return None
        data = self.zip.read(name)
        for strict, transitional in STRICT:
            data = data.replace(strict, transitional)
        return ET.fromstring(data)

    def rels(self, part):
        """{rId: (type, target)} for a part; internal targets become zip paths."""
        d, f = posixpath.split(part)
        root = self.xml(posixpath.join(d, "_rels", f + ".rels"))
        out = {}
        for rel in [] if root is None else root.findall("pr:Relationship", NS):
            target = rel.get("Target", "")
            if rel.get("TargetMode") != "External":
                target = (target[1:] if target.startswith("/")
                          else posixpath.normpath(posixpath.join(d, target)))
            out[rel.get("Id")] = (rel.get("Type", "").rsplit("/", 1)[-1], target)
        return out

    def part(self, kind):
        target = next((t for k, t in self.doc_rels.values() if k == kind), None)
        return self.xml(target) if target else None

    # -- block level
    def kids(self, el):
        for ch in el:
            if ch.tag in TRANSPARENT:
                yield from self.kids(ch)
            else:
                yield ch

    def blocks(self, elements):
        out = []
        for ch in elements:
            if ch.tag == W_P:
                out.extend(self.para(ch))
            elif ch.tag == W_TBL:
                out.append(self.table(ch))
        return out

    def body(self):
        root = self.xml(self.main)
        if root is None:
            raise ValueError("no main document part")
        body = root.find("w:body", NS)

        # a paragraph carrying a sectPr ends its section; the body's ends the last
        sections, current = [], []
        for ch in self.kids(body):
            if ch.tag == q("w:sectPr"):
                continue
            current.append(ch)
            sect = ch.find("w:pPr/w:sectPr", NS) if ch.tag == W_P else None
            if sect is not None:
                sections.append((current, sect))
                current = []
        sections.append((current, body.find("w:sectPr", NS)))

        plan, refs = [], {}
        for elements, sect in sections:
            refs = self.section_refs(sect, refs)
            title_pg = sect is not None and on(sect.find("w:titlePg", NS))
            plan.append((elements, self.variants(refs, "header", title_pg),
                         self.variants(refs, "footer", title_pg)))

        # show each header/footer once per run of sections that share it
        out, shown = [], None
        for n, (elements, header, footer) in enumerate(plan):
            if header != shown:
                out.extend(self.frames("Header", header))
                shown = header
            out.extend(self.blocks(elements))
            last = n == len(plan) - 1
            if last:
                out.extend(self.notes_blocks())
            if last or footer != plan[n + 1][2]:
                out.extend(self.frames("Footer", footer))
        return out

    def section_refs(self, sect, inherited):
        """{(kind, type): part} in force for a section; unset ones carry over."""
        refs = dict(inherited)
        for kind in ("header", "footer"):
            for ref in [] if sect is None else sect.findall("w:%sReference" % kind, NS):
                rel = self.doc_rels.get(ref.get(q("r:id")))
                if rel:
                    refs[(kind, wattr(ref, "type") or "default")] = rel[1]
        return refs

    def variants(self, refs, kind, title_pg):
        """((label suffix, part), ...) of the distinct headers/footers shown."""
        out = []
        for variant, label in (("default", ""), ("first", " (first page)"),
                               ("even", " (even pages)")):
            if (variant == "first" and not title_pg) or \
                    (variant == "even" and not self.even_odd):
                continue
            part = refs.get((kind, variant))
            if part and part not in [p for _, p in out]:
                out.append((label, part))
        # page order: the first page's comes before the rest
        return tuple(sorted(out, key=lambda v: v[0] != " (first page)"))

    def frames(self, title, variants):
        out = []
        for label, part in variants:
            root = self.xml(part)
            if root is None:
                continue
            saved = self.part_rels, self.fields
            self.part_rels, self.fields = self.rels(part), []
            blocks = self.blocks(self.kids(root))
            self.part_rels, self.fields = saved
            if blocks:
                out.append(Frame(title + label, blocks))
        return out

    def notes_blocks(self):
        out = []
        if self.note_refs:
            out.append(Rule("Notes"))
        for label, kind, nid in self.note_refs:
            note = self.note(kind, nid)
            blocks = self.blocks(self.kids(note)) if note is not None else []
            first = next((b for b in blocks if isinstance(b, Para)), None)
            if first is None:
                blocks.insert(0, first := Para([]))
            first.label = label
            out.extend(blocks)
        return out

    def note(self, kind, nid):
        if self.notes[kind] is None:
            root = self.part(kind)
            self.notes[kind] = {} if root is None else {
                wattr(n, "id"): n for n in root.findall("w:" + kind[:-1], NS)}
        return self.notes[kind].get(nid)

    def para(self, p):
        ppr = p.find("w:pPr", NS)
        sid = wattr(p.find("w:pPr/w:pStyle", NS), "val") or self.styles.default_para
        kind, level = self.styles.kind(sid)
        outline = wattr(p.find("w:pPr/w:outlineLvl", NS), "val")
        if outline and int(outline) < 9:
            kind, level = "heading", int(outline) + 1

        def prop(path):
            el = ppr.find(path, NS) if ppr is not None else None
            return el if el is not None else self.styles.find(sid, "w:pPr/" + path)

        label, ilvl = None, 0
        num_id = wattr(prop("w:numPr/w:numId"), "val")
        if num_id and num_id != "0":
            ilvl = int(wattr(prop("w:numPr/w:ilvl"), "val") or 0)
            label = self.numbering.label(num_id, ilvl)

        # indentation: twips -> columns, ~180 twips (1/8 inch) per column
        ind = prop("w:ind")
        left = int(wattr(ind, "left") or wattr(ind, "start") or
                   (720 * (ilvl + 1) if label is not None else 0))
        hanging = int(wattr(ind, "hanging") or (360 if label is not None else 0))
        indent = max(0, left - hanging if label is not None else left) // 180

        jc = wattr(prop("w:jc"), "val")
        align = {"center": "center", "right": "right", "end": "right"}.get(jc)

        out = []
        if on(prop("w:pageBreakBefore")):
            out.append(Rule())
        self.page_break = False
        spans = []
        self.inline(p, spans, sid, None)
        para = Para(spans, kind, level, label, indent, align)
        if not para.empty():
            out.append(para)
        if self.page_break:
            out.append(Rule())
        return out

    def table(self, tbl):
        rows = []
        for tr in self.kids(tbl):
            if tr.tag != q("w:tr"):
                continue
            header = tr.find("w:trPr/w:tblHeader", NS) is not None
            cells = []
            for tc in self.kids(tr):
                if tc.tag != q("w:tc"):
                    continue
                span = int(wattr(tc.find("w:tcPr/w:gridSpan", NS), "val") or 1)
                vm = tc.find("w:tcPr/w:vMerge", NS)
                merged = vm is not None and wattr(vm, "val") != "restart"
                blocks = [] if merged else self.blocks(self.kids(tc))
                cells.append(Cell(blocks, span, merged, header))
            if cells:
                rows.append(cells)
        return Table(rows)

    # -- inline level
    def inline(self, el, spans, sid, link):
        for ch in el:
            if ch.tag == W_R:
                self.run(ch, spans, sid, link)
            elif ch.tag == q("w:hyperlink"):
                rid = ch.get(q("r:id"))
                url = self.part_rels.get(rid, (None, None))[1] if rid else None
                start = len(spans)
                self.inline(ch, spans, sid, url or "#")
                shown = "".join(t for t, _ in spans[start:])
                plain = re.sub(r"^mailto:", "", url or "")
                if url and plain not in shown:
                    spans.append((" (%s)" % plain, {"dim"}))
            elif ch.tag == q("mc:AlternateContent"):
                self.inline(self.alternate(ch), spans, sid, link)
            elif ch.tag == q("w:fldSimple") and is_page(wattr(ch, "instr")):
                spans.append(("#", set()))
            elif ch.tag not in SKIP:
                self.inline(ch, spans, sid, link)

    def alternate(self, el):
        """Pick the first branch of an mc:AlternateContent."""
        choice = el.find("mc:Choice", NS)
        return choice if choice is not None else el.find("mc:Fallback", NS)

    def run(self, r, spans, sid, link):
        rsid = wattr(r.find("w:rPr/w:rStyle", NS), "val")
        attrs = set(self.styles.run_attrs(sid, rsid))
        apply_rpr(attrs, r.find("w:rPr", NS))
        if "hidden" in attrs:
            return
        if link:
            attrs.add("link")
        for ch in r:
            tag, text, a = ch.tag, None, attrs
            if ch.tag == q("mc:AlternateContent"):
                ch = next(iter(self.alternate(ch)), ch)
                tag = ch.tag
            if tag == q("w:fldChar"):
                text = self.field_char(wattr(ch, "fldCharType"))
            elif tag == q("w:instrText"):
                if self.fields:
                    self.fields[-1]["instr"] += ch.text or ""
            elif any(f["hide"] for f in self.fields):
                pass                     # stale cached page number
            elif tag == W_T:
                text = ch.text or ""
                if "caps" in attrs:
                    text = text.upper()
            elif tag in (q("w:tab"), q("w:ptab")):
                text = "\t"
            elif tag in (q("w:br"), q("w:cr")):
                if wattr(ch, "type") == "page":
                    self.page_break = True
                else:
                    text = "\n"
            elif tag == q("w:noBreakHyphen"):
                text = "-"
            elif tag == q("w:sym"):
                cp = int(wattr(ch, "char") or "2022", 16)
                text = "•" if 0xE000 <= cp <= 0xF8FF else chr(cp)
            elif tag in (q("w:drawing"), q("w:pict"), q("w:object")):
                text, a = self.picture(ch), {"dim"}
            elif tag in (q("w:footnoteReference"), q("w:endnoteReference")):
                kind = "footnotes" if "foot" in tag else "endnotes"
                label = "[%d]" % (len(self.note_refs) + 1)
                self.note_refs.append((label, kind, wattr(ch, "id")))
                text, a = label, {"dim"}
            if text:
                spans.append((text, a))

    def field_char(self, kind):
        """Track complex fields; a PAGE field's result is replaced with '#'."""
        if kind == "begin":
            self.fields.append({"instr": "", "hide": False})
            return None
        if not self.fields:
            return None
        field = self.fields[-1]
        page = is_page(field["instr"])
        if kind == "separate":
            field["hide"] = page
            return "#" if page else None
        if kind == "end":
            self.fields.pop()
            return "#" if page and not field["hide"] else None
        return None

    def picture(self, el):
        boxes = list(el.iter(W_TXBX))
        if boxes:
            paras = ("".join(t.text or "" for t in p.iter(W_T))
                     for box in boxes for p in box.iter(W_P))
            return "[text box: %s]" % " / ".join(t for t in paras if t.strip())
        doc_pr = el.find(".//wp:docPr", NS)
        desc = doc_pr is not None and (doc_pr.get("descr") or doc_pr.get("name"))
        if not desc:
            blip = el.find(".//a:blip", NS)
            rid = blip.get(q("r:embed")) if blip is not None else None
            desc = posixpath.basename(self.part_rels.get(rid, ("", ""))[1])
        return "[image: %s]" % desc if desc else "[image]"

# ---------------------------------------------------------------- rendering
TOKEN = re.compile(r"\n|[ \t]+|[^ \t\n]+")

def wrap(spans, width):
    """Greedy word wrap of styled spans -> lines of [(text, attrs)] segments."""
    items = []   # None = hard break, tuple = whitespace, list = word segments
    for text, attrs in spans:
        for tok in TOKEN.findall(text.replace("\t", "    ")):
            if tok == "\n":
                items.append(None)
            elif tok[0] == " ":
                items.append((tok, attrs))
            elif items and isinstance(items[-1], list):
                items[-1].append((tok, attrs))   # word continues across runs
            else:
                items.append([(tok, attrs)])

    lines, line, lw = [], [], 0
    width = max(1, width)

    def flush():
        while line and not line[-1][0].strip():
            line.pop()
        lines.append(line[:])
        line.clear()
        return 0

    for it in items:
        if it is None:
            lw = flush()
        elif isinstance(it, tuple):
            if line:
                line.append(it)
                lw += len(it[0])
        else:
            ww = sum(swidth(t) for t, _ in it)
            if lw + ww > width and line:
                lw = flush()
            if ww <= width:
                line.extend(it)
                lw += ww
                continue
            for t, attrs in it:          # longer than a line: split anywhere
                for c in t:
                    if lw + cwidth(c) > width and line:
                        lw = flush()
                    line.append((c, attrs))
                    lw += cwidth(c)
    if line or not lines:
        flush()
    return lines

def paint_line(segs, extra, color):
    out, run, cur = [], "", None
    for text, attrs in segs:
        attrs = set(attrs) | extra
        if attrs != cur and run:
            out.append(paint(run, cur, color))
            run = ""
        run, cur = run + text, attrs
    if run:
        out.append(paint(run, cur, color))
    return "".join(out)

def render_para(b, width, color):
    extra = set()
    if b.kind == "heading":
        extra = {"b", "hd"} if b.level <= 3 else {"b"}
    elif b.kind == "title":
        extra = {"b", "tt"}
    elif b.kind == "subtitle":
        extra = {"i", "dim"}
    elif b.kind == "quote":
        extra = {"i"}

    indent = min(b.indent, width // 3)
    first = rest = " " * indent
    if b.label is not None:
        marker = b.label + " " if b.label else ""
        first += paint(marker, {"dim"} if b.label in BULLETS else set(), color)
        rest += " " * swidth(marker)
    if b.kind == "quote":
        bar = paint("│ ", {"dim"}, color)
        first, rest = bar + first, bar + rest

    lines = []
    for n, segs in enumerate(wrap(b.spans, width - vwidth(first))):
        lines.append((first if n == 0 else rest) + paint_line(segs, extra, color))

    if b.align and b.kind != "quote":
        for n, line in enumerate(lines):
            gap = width - vwidth(line)
            lines[n] = " " * (gap // 2 if b.align == "center" else gap) + line
    if b.kind == "heading" and b.level <= 2:
        rule = "═" if b.level == 1 else "─"
        lines.append(paint(rule * max(map(vwidth, lines)), {"hd"}, color))
    return lines

def fit_columns(natural, avail):
    """Water-filling: narrow columns keep their natural width, wide ones share."""
    widths = [0] * len(natural)
    todo = set(range(len(natural)))
    while todo:
        share = avail // len(todo)
        small = [c for c in todo if natural[c] <= share]
        if not small:
            extra = avail - share * len(todo)
            for n, c in enumerate(sorted(todo)):
                widths[c] = share + (1 if n < extra else 0)
            break
        for c in small:
            widths[c] = natural[c]
            avail -= natural[c]
            todo.remove(c)
    return [max(1, w) for w in widths]

BOX = {  # (up, down, left, right) -> junction
    (0, 0, 1, 1): "─", (1, 1, 0, 0): "│", (0, 1, 0, 1): "┌", (0, 1, 1, 0): "┐",
    (1, 0, 0, 1): "└", (1, 0, 1, 0): "┘", (1, 1, 0, 1): "├", (1, 1, 1, 0): "┤",
    (0, 1, 1, 1): "┬", (1, 0, 1, 1): "┴", (1, 1, 1, 1): "┼", (0, 0, 0, 0): " ",
    (1, 0, 0, 0): "│", (0, 1, 0, 0): "│", (0, 0, 1, 0): "─", (0, 0, 0, 1): "─",
}

def render_table(t, width, color):
    ncols = max(sum(c.span for c in row) for row in t.rows)
    rows = [row + [Cell([]) for _ in range(ncols - sum(c.span for c in row))]
            for row in t.rows]
    starts = []   # per row: grid column -> cell starting there
    for row in rows:
        col, at = 0, {}
        for cell in row:
            at[col] = cell
            col += cell.span
        starts.append(at)

    avail = max(ncols, width - 3 * ncols - 1)
    natural = [0] * ncols
    for at in starts:
        for col, cell in at.items():
            if cell.span == 1 and cell.blocks:
                lines = render_blocks(cell.blocks, avail, False, compact=True)
                natural[col] = max(natural[col], max(map(vwidth, lines)))
    widths = fit_columns(natural, avail)

    def cell_at(r, col):
        return max((c for c in starts[r] if c <= col), default=0)

    def border(above, below):
        horiz = []
        for col in range(ncols):
            cell = starts[below][cell_at(below, col)] if below is not None else None
            horiz.append(not (cell and cell.merged))
        out = ""
        for j in range(ncols + 1):
            up = above is not None and (j in starts[above] or j == ncols)
            down = below is not None and (j in starts[below] or j == ncols)
            left = j > 0 and horiz[j - 1]
            right = j < ncols and horiz[j]
            out += BOX[(int(up), int(down), int(left), int(right))]
            if j < ncols:
                out += ("─" if horiz[j] else " ") * (widths[j] + 2)
        return paint(out, {"dim"}, color)

    bar = paint("│", {"dim"}, color)
    out = [border(None, 0)]
    for r, at in enumerate(starts):
        cols = []
        for col, cell in sorted(at.items()):
            w = sum(widths[col:col + cell.span]) + 3 * (cell.span - 1)
            lines = render_blocks(cell.blocks, w, color, compact=True) if cell.blocks else []
            if cell.header:
                lines = [paint(ANSI.sub("", l), {"b"}, color) for l in lines]
            cols.append((w, lines))
        for n in range(max(len(lines) for _, lines in cols) or 1):
            out.append(bar + bar.join(
                " " + pad(lines[n] if n < len(lines) else "", w) + " "
                for w, lines in cols) + bar)
        out.append(border(r, r + 1 if r + 1 < len(starts) else None))
    return out

def rule(title, width, color):
    label = " %s " % title if title else ""
    return paint("┄" * 2 + label + "┄" * max(0, width - 2 - swidth(label)),
                 {"dim"}, color)

def render_blocks(blocks, width, color, compact=False):
    out, prev = [], None
    for b in blocks:
        if isinstance(b, Para):
            lines = render_para(b, width, color)
        elif isinstance(b, Table):
            lines = render_table(b, width, color) if b.rows else []
        elif isinstance(b, Frame):
            lines = ([rule(b.title, width, color)] +
                     render_blocks(b.blocks, width, color, compact=True) +
                     [rule(None, width, color)])
        else:
            lines = [rule(b.title, width, color)]
        list_run = (isinstance(prev, Para) and isinstance(b, Para)
                    and prev.label is not None and b.label is not None)
        if out and not compact and not list_run:
            out.append("")
        out.extend(lines)
        prev = b
    return out

# --------------------------------------------------------------------- main
def page(text):
    cmd = shlex.split(os.environ.get("PAGER") or "less")
    env = dict(os.environ)
    if posixpath.basename(cmd[0]) == "less":
        cmd.append("-R")
        env.setdefault("LESS", "FX")   # quit if it fits on one screen
    try:
        subprocess.run(cmd, input=text.encode(), env=env)
    except OSError:
        sys.stdout.write(text)

def main():
    ap = argparse.ArgumentParser(description="View a .docx file in the terminal.")
    ap.add_argument("file", help="the .docx to view ('-' for stdin)")
    ap.add_argument("-w", "--width", type=int, help="wrap width")
    ap.add_argument("--plain", action="store_true", help="no colors / styling")
    ap.add_argument("--color", action="store_true", help="colors even when piping")
    ap.add_argument("--no-pager", action="store_true", help="don't page the output")
    args = ap.parse_args()

    try:
        with (sys.stdin.buffer if args.file == "-" else open(args.file, "rb")) as f:
            data = f.read()
    except OSError as e:
        sys.exit("docxview: %s" % e)

    tty = sys.stdout.isatty()
    color = not args.plain and (args.color or (tty and "NO_COLOR" not in os.environ))
    width = args.width or min(shutil.get_terminal_size((80, 24)).columns - 1, 100)

    try:
        doc = Docx(data)
        text = "\n".join(render_blocks(doc.body(), width, color)) + "\n"
    except zipfile.BadZipFile:
        hint = " (old binary .doc files aren't supported)" \
            if data.startswith(b"\xd0\xcf\x11\xe0") else ""
        sys.exit("docxview: %s: not a .docx file%s" % (args.file, hint))
    except (ET.ParseError, ValueError, KeyError) as e:
        sys.exit("docxview: %s: malformed .docx (%s)" % (args.file, e))

    try:
        if tty and not args.no_pager:
            page(text)
        else:
            sys.stdout.write(text)
    except (BrokenPipeError, KeyboardInterrupt):
        pass

if __name__ == "__main__":
    main()
