"""Parse one consolidated Chapter of the Laws of Trinidad and Tobago (a laws.gov.tt PDF) into units.

The Revised Edition PDFs share one layout (Malta's parser is the model):
- a running header at the top of every page ("LAWS OF TRINIDAD AND TOBAGO", the page number, "Chap. 5:34", the short
  title, "L.R.O. 1/2023") and the publisher's stamps ("UNOFFICIAL VERSION", "UPDATED TO 31ST DECEMBER 2016", the
  Ministry's name and web address, a large "UNOFFICIAL" watermark). They are dropped by their content.
- the body in 12pt; a section starts with its number ("12A.") at the paragraph indent;
- an 8pt margin column on the outer edge (left on even pages, right on odd), holding each section's marginal heading
  and its history: the enacting or amending laws ("[11 of 2014 15 of 2018]", "15 of 2018.", "LN 51/1980", "23/2009")
  and cross references ("Ch. 11:24.");
- front matter (cover page with the "Amended by" list, notes on subsidiary legislation and amendments), an
  arrangement of sections, then the Act, then its subsidiary legislation, each with its own arrangement and numbering.

Output: {'front': [lines], 'parts': [{'kind': 'act'|'sl', 'title': [lines], 'preamble': [lines], 'units': [...]}]}.
"""
import re
import sys
from dataclasses import dataclass, field

sys.modules.setdefault('pymupdf.layout', None)  # the optional ONNX layout model is not used (and fails to load here)
import pymupdf  # noqa: E402

PARSER_VERSION = 5
SCAN_VERSION = 11  # the scan reader below (older Revised Editions: page images with the publisher's OCR text layer)

SECTION = re.compile(r'^(\d{1,3}[A-Z]{0,3})\.\s+(?=\S)')
SECTION_ALONE = re.compile(r'^(\d{1,3}[A-Z]{0,3})\.$')
ENUM = re.compile(r'^\((?:\d{1,3}[A-Z]{0,2}|[a-z]{1,2}|[ivxl]{1,6}|[A-Z]{1,2})\)')
SCHEDULE = re.compile(r'^((?:[A-Z]+\s+){0,2}SCHEDULE(?:\s+[A-Z0-9]{1,5})?|(?:FORM|APPENDIX|ANNEX)(?:\s+[A-Z0-9]{1,5})?)'
                      r'(?:\s*\(.*\))?$')
TITLE_WORDS = re.compile(r'\b(REGULATIONS|RULES|ORDER|NOTICE|PROCLAMATION|BY-LAWS|BYE-LAWS|DIRECTIONS|DECLARATION|SCHEME|CODE)\b')
# The publisher's stamps and running headers, matched on text with spaces removed and upper-cased.
STAMP = re.compile(r'^(UNOFFICIAL(VERSION)?|LAWSOFTRINIDADANDTOBAGO|MINISTRYOFTHEATTORNEYGENERAL.*|'
                   r'OFFICEOFTHEATTORNEYGENERAL.*|MINISTRYOFLEGALAFFAIRS.*|WWW\..*|UPDATEDTO.*|L\.R\.O\.?[0-9/]*|\.\.|CURRENTAUTHORISEDPAGES)$')
# Characters the CID fonts map to control codes (checked against the printed page).
CHARMAP = {'\x07': '’', '\x1b': '“', '\x1a': '”', '\x1e': '—', '\x1f': '–', '\x1d': '’', '\x1c': '‘',
           '\xad': '', ' ': ' ', '�': '’'}
CHARMAP_RE = re.compile('[' + ''.join(CHARMAP) + ']')


@dataclass
class Line:
    page: int
    y: float
    x: float      # where the first visible character starts
    x1: float
    size: float
    bold: bool
    italic: bool
    text: str
    margin: bool = False
    centred: bool = False
    rel: float = 0.0   # x relative to the page's body left edge
    tx: float = 0.0    # where the words start after a lone number or enumerator, relative


@dataclass
class Unit:
    id: str
    kind: str
    page: int
    y: float
    heading: list = field(default_factory=list)
    lines: list = field(default_factory=list)
    notes: list = field(default_factory=list)


def fix(t: str) -> str:
    return CHARMAP_RE.sub(lambda m: CHARMAP[m.group(0)], t)


CAPS_N = re.compile(r'\b[A-Zn]*n[A-Zn]*\b')


def caps_n(m: re.Match) -> str:
    """Some typesettings print a capital N with a glyph that extracts as "n" ("ADMInISTRATIOn"): inside a word of
    capitals (two or more besides the n), it is a capital N."""
    w = m.group(0)
    return w.replace('n', 'N') if sum(1 for c in w if c.isupper()) >= 2 else w


def clean(t: str) -> str:
    return CAPS_N.sub(caps_n, re.sub(r'\s+', ' ', fix(t)).strip())


def is_stamp(t: str) -> bool:
    k = re.sub(r'\s+', '', t).upper()
    return bool(STAMP.match(k))


_TIMES: dict[str, object] = {}


def times_font(name: str):
    """The base-14 Times face with the metrics of a span's font, or None for other fonts."""
    base = name.split('+', 1)[-1]
    if not base.startswith('Times'):
        return None
    bold = 'Bold' in base
    italic = 'Italic' in base or 'Oblique' in base
    key = 'tibi' if bold and italic else 'tibo' if bold else 'tiit' if italic else 'tiro'
    if key not in _TIMES:
        _TIMES[key] = pymupdf.Font(key)
    return _TIMES[key]


_WIDTH: dict[tuple, float] = {}


def width(font, ch: str) -> float:
    """Advance width of ch at size 1 (cached)."""
    k = (id(font), ch)
    if k not in _WIDTH:
        _WIDTH[k] = font.text_length(ch, 1)
    return _WIDTH[k]


def fix_caps(span: dict) -> list[dict]:
    """The 2006-2014 typesetting prints headings in capitals but encodes some capital letters as lower-case
    characters ("ChapTer", "Laws oF Trinidad and ToBaGo", "widows’ and orphans’ pensions aCT"). Each glyph's
    advance width tells which letter was drawn: a letter that measures as a capital rather than as
    lower case is a capital (letters too alike in width follow the rest of their word)."""
    chars = span.get('chars', [])
    f = times_font(span.get('font', ''))
    if f is None:
        return chars
    size = span['size']
    out = [dict(c) for c in chars]
    word: list[dict] = []

    def settle():
        up = lo = 0
        unsure = []
        for c in word:
            ch = c['c']
            if not ch.islower():
                continue
            w = c['bbox'][2] - c['bbox'][0]
            a, b = width(f, ch) * size, width(f, ch.upper()) * size
            if abs(a - b) < 0.4:
                unsure.append(c)
            elif abs(w - b) < abs(w - a):
                up += 1
                c['c'] = ch.upper()
            else:
                lo += 1
        if up > lo:
            for c in unsure:
                c['c'] = c['c'].upper()
        word.clear()

    for c in out:
        if c['c'].isalpha():
            word.append(c)
        else:
            settle()
    settle()
    return out


def read_lines(path: str) -> tuple[list[Line], list[dict]]:
    doc = pymupdf.open(path)
    out: list[Line] = []
    pages = []
    for pno, page in enumerate(doc):
        pages.append({'w': page.rect.width, 'h': page.rect.height})
        for block in page.get_text('rawdict')['blocks']:
            for ln in block.get('lines', []):
                for s in ln['spans']:
                    s['chars'] = fix_caps(s)
                    if 'CIDFont' in s.get('font', ''):
                        # the post-2016 CID fonts print the ellipsis of form blanks ("……") with the code of "8":
                        # a digit is half an em wide, the ellipsis a whole em.
                        for c in s['chars']:
                            if c['c'] == '8' and c['bbox'][2] - c['bbox'][0] > 0.8 * s['size']:
                                c['c'] = '…'
                chars = [c for s in ln['spans'] for c in s.get('chars', [])]
                text = ''.join(c['c'] for c in chars)
                if not text.strip():
                    continue
                spans = [s for s in ln['spans'] if ''.join(c['c'] for c in s.get('chars', [])).strip()]
                size = max(s['size'] for s in spans)
                if size > 40:  # the "UNOFFICIAL" watermark
                    continue
                first = next(c for c in chars if c['c'].strip())
                font = spans[0]['font']
                l = Line(pno, round(ln['bbox'][1], 1), round(first['bbox'][0], 1), round(ln['bbox'][2], 1),
                         round(size, 1), 'Bold' in font or bool(spans[0]['flags'] & 16),
                         'Italic' in font or bool(spans[0]['flags'] & 2), text)
                if is_stamp(l.text) and (l.y < 135 or l.y > 640 or pno == 0):
                    continue
                out.append(l)
    return out, pages


# ---------------------------------------------------------------------------------------------------- scans
# The 1902, 1925, 1940, 1950 and 1980 Revised Editions on laws.gov.tt are page images with an OCR text layer added by
# the publisher (Adobe Acrobat "Paper Capture"). The text layer carries no fonts, so the margin column is found by
# position: an empty vertical strip (the gutter) separates the margin column from the body, and the words of an OCR
# line beyond it are margin notes (the 1940 gutter is only ~6pt wide, and OCR often joins a note to a body line).

HEADER_SCAN = re.compile(r'^\[?\s*\d{1,4}\s*[\]J]?\.?$|\b(?:Ch|CAP|Cap|Chap)\s*\.\s*[\d:]|\bNo\.\s*\d+\s*\.?\s*[\]J]'
                         r'|^\d{1,4}\s+[A-Z]|[a-z.]\s+\d{1,4}$')
OCR_DIGITS = str.maketrans({'s': '5', 'S': '5', 'l': '1', 'I': '1', 'i': '1', 'O': '0', 'o': '0', 'B': '8'})
WORDCHARS = re.compile(r'[\W_]')
OCR_SECTION = re.compile(r'^([0-9SsIilOoB]{1,3})\.\s+(?=\S)')


def _pct(v: list[float], q: float) -> float:
    v = sorted(v)
    return v[min(len(v) - 1, int(len(v) * q))]


def gutters(ls: list[list], W: float) -> tuple[float, float, float, float]:
    """The body column's edges on one page: the empty strip (no more than one word crosses it) nearest the body in the
    left 40% of the text, and in the right 40%, with text beyond it. No such strip on a side: no margin column there.
    Only words of three or more letters and digits count (OCR specks are scattered over the page), and their extent
    is returned too: a speck outside it is not body text."""
    xs = [wd for ws in ls for wd in ws if len(WORDCHARS.sub('', wd[4])) >= 3]
    if len(xs) < 20:
        return -1e9, 1e9, -1e9, 1e9
    lo, hi = int(min(w[0] for w in xs)), int(max(w[2] for w in xs)) + 1
    cover = [0] * (hi - lo + 1)
    for w in xs:
        for x in range(int(w[0]) - lo, int(w[2]) - lo + 1):
            cover[x] += 1
    span = hi - lo

    def strips(empty: int) -> list[tuple]:
        runs = []
        start = None
        for i, c in enumerate(cover + [10 ** 9]):
            if c <= empty and start is None:
                start = i
            elif c > empty and start is not None:
                # (a strip may run to the right edge: a margin holding a single word is crossed by one word only)
                if start > 0 and i - start >= 3:
                    runs.append((start + lo, i + lo))
                start = None
        return runs

    # A strip crossed by at most one word; on a side without one, a strip crossed by at most a fifth of the words that
    # cross a typical column (a skewed scan lets a few line ends run into a narrow gutter).
    filled = sorted(c for c in cover if c)
    strict, loose = strips(1), strips(max(1, int(0.2 * filled[len(filled) // 2])))
    lefts = [r for r in strict if r[1] < lo + 0.4 * span] or [r for r in loose if r[1] < lo + 0.4 * span]
    rights = [r for r in strict if r[0] > hi - 0.4 * span] or [r for r in loose if r[0] > hi - 0.4 * span]
    left = max(r[1] for r in lefts) if lefts else -1e9
    right = min(r[0] for r in rights) if rights else 1e9
    return left, right, lo, hi


def read_scan_lines(path: str) -> tuple[list[Line], list[dict]]:
    doc = pymupdf.open(path)
    pages = []
    lines_by_page = []
    edges: dict[int, tuple] = {}
    for pno, page in enumerate(doc):
        W, H = page.rect.width, page.rect.height
        pages.append({'w': W, 'h': H})
        lines: dict[tuple, list] = {}
        for x0, y0, x1, y1, w, b, ln, _ in page.get_text('words'):
            w = fix(w)
            if w.strip():
                lines.setdefault((b, ln), []).append((x0, y0, x1, y1, w))
        ls = [sorted(ws) for _, ws in sorted(lines.items())]
        lines_by_page.append(ls)
        edges[pno] = gutters(ls, W)
    out: list[Line] = []
    for pno, ls in enumerate(lines_by_page):
        left, right, lo, hi = edges[pno]
        sides: dict[str, list] = {}
        for ws in ls:
            notes: dict[str, list] = {}
            for wd in ws:
                side = 'L' if wd[2] <= left + 1 or wd[2] < lo else 'R' if wd[0] >= right - 1 or wd[0] > hi else 'B'
                (sides.setdefault('B', []) if side == 'B' else notes.setdefault(side, [])).append(wd)
            # margin notes keep the OCR's own lines (their lines are set closer than the body's)
            for side, g in sorted(notes.items()):
                out.append(Line(pno, round(min(w[1] for w in g), 1), round(g[0][0], 1), round(max(w[2] for w in g), 1),
                                8.0, False, False, ' '.join(w[4] for w in g), margin=True))
        hs = sorted(w[3] - w[1] for ws in ls for w in ws)
        h = hs[len(hs) // 2] if hs else 10.0
        # The printed lines, rebuilt from the words by height on the page: the OCR sometimes splits one printed line
        # into fragments ("1. This Ordinance may be" | "cited as the Widows' and"), which must join left to right.
        for side, wds in sorted(sides.items()):
            rows: list[list] = []
            for wd in sorted(wds, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
                yc = (wd[1] + wd[3]) / 2
                if rows and yc - sum((w[1] + w[3]) / 2 for w in rows[-1]) / len(rows[-1]) <= 0.5 * h:
                    rows[-1].append(wd)
                else:
                    rows.append([wd])
            margin = side != 'B'
            for g in rows:
                g.sort()
                out.append(Line(pno, round(min(w[1] for w in g), 1), round(g[0][0], 1), round(max(w[2] for w in g), 1),
                                8.0 if margin else 12.0, False, False, ' '.join(w[4] for w in g), margin=margin))
    return drop_scan_headers(out, pages), pages


def drop_scan_headers(lines: list[Line], pages: list[dict]) -> list[Line]:
    """The running header of a scanned page ("782   Ch. 39. No. 8.]   San Fernando Recreation Ground.", "CAP. 140.]",
    "Chap. 41:02", "LAWS OF TRINIDAD AND TOBAGO") and the publisher's stamps: a row in the top 13% of the page holding
    a page number or a chapter reference, dropped whole (the short title beside it too)."""
    by_page: dict[int, list[Line]] = {}
    for l in lines:
        by_page.setdefault(l.page, []).append(l)
    keep = []
    for pno, ls in sorted(by_page.items()):
        top = pages[pno]['h'] * 0.13
        rows: list[list[Line]] = []
        for l in sorted(ls, key=lambda l: l.y):
            if rows and abs(rows[-1][-1].y - l.y) <= 4:
                rows[-1].append(l)
            else:
                rows.append([l])
        drop = set()
        # the first three rows, each judged on its whole text, left to right (a table's row of column numbers,
        # "1 2 3 4", is not a page number)
        for row in rows[:3]:
            text = ' '.join(clean(l.text) for l in sorted(row, key=lambda l: l.x))
            if row[0].y <= top and (HEADER_SCAN.search(text) or is_stamp(text)):
                drop.update(id(l) for l in row)
        keep += [l for l in ls if id(l) not in drop and not is_stamp(l.text)]
    return keep


def drop_headers(lines: list[Line]) -> list[Line]:
    """The running header: the lines above the first body line of a page that read like a header (a page number,
    "Chap. 5:34", the short title in italics)."""
    keep = []
    by_page: dict[int, list[Line]] = {}
    for l in lines:
        by_page.setdefault(l.page, []).append(l)
    for pno, ls in sorted(by_page.items()):
        for l in ls:
            t = clean(l.text)
            # Everything above y=120 is header (subsidiary legislation repeats "[Subsidiary] <title>" at y=112);
            # from 120 to 128 the body can already start (2016 pages), so only header-like lines go.
            if l.size >= 9 and pno > 0 and l.y < 120:
                continue
            if l.y < 128 and l.size >= 9 and (re.fullmatch(r'\d{1,4}', t) or re.search(r'Chap\.\s*\d', t)
                                              or re.search(r'\bNo\.\s*\d+\s+of\s+\d{4}', t)
                                              or '[Subsidiary]' in t
                                              or l.italic or l.y < 112 or re.fullmatch(r'[\d\s]*Chap\..*', t)):
                continue
            keep.append(l)
    return keep


def mark_margin(lines: list[Line]) -> None:
    by_page: dict[int, list[Line]] = {}
    for l in lines:
        by_page.setdefault(l.page, []).append(l)
    for ls in by_page.values():
        body = [l for l in ls if l.size >= 9]
        if not body:
            for l in ls:
                l.margin = l.size <= 8.6
            continue
        # The body's edges: the most common wrap points, not the extremes (a line can run into the margin).
        xs = sorted(l.x for l in body)
        x1s = sorted(l.x1 for l in body)
        left = xs[len(xs) // 10] if len(xs) >= 10 else xs[0]
        right = x1s[(len(x1s) * 9) // 10] if len(x1s) >= 10 else x1s[-1]
        for l in ls:
            l.margin = l.size <= 8.6 and (l.x1 <= left + 4 or l.x >= right - 4)


def merge_rows(lines: list[Line]) -> list[Line]:
    rows: list[Line] = []
    for ln in sorted(lines, key=lambda l: (l.page, l.y, l.x)):
        if rows and rows[-1].page == ln.page and abs(rows[-1].y - ln.y) <= 2.5:
            prev = rows[-1]
            lone = clean(prev.text)
            if prev.tx == 0 and (ENUM.fullmatch(lone) or SECTION_ALONE.fullmatch(lone)):
                prev.tx = ln.x
            prev.text = prev.text.rstrip() + ' ' + ln.text.lstrip()
            prev.x1 = max(prev.x1, ln.x1)
            continue
        rows.append(Line(ln.page, ln.y, ln.x, ln.x1, ln.size, ln.bold, ln.italic, ln.text))
    left: dict[int, float] = {}
    ends: dict[int, list[float]] = {}
    for r in rows:
        # the left edge of the body: rows in the header band (a header that escaped drop_headers) don't count
        if r.y >= 128:
            left[r.page] = min(left.get(r.page, 1e9), r.x)
        ends.setdefault(r.page, []).append(r.x1)
    for r in rows:
        left.setdefault(r.page, r.x)
    right = {p: sorted(v)[(len(v) * 9) // 10] for p, v in ends.items()}
    for r in rows:
        r.rel = r.x - left[r.page]
        r.tx = (r.tx - left[r.page]) if r.tx else r.rel
        mid = (left[r.page] + right[r.page]) / 2
        # A heading is centred (equal gaps to both edges) and touches neither; a justified line touches both. The
        # short last line of a paragraph can sit near the middle by chance: one that starts in lower case, or a
        # numbered section or paragraph with running text, is not a heading.
        t = clean(r.text)
        r.centred = (r.rel > 12 and right[r.page] - r.x1 > 12 and abs((r.x + r.x1) / 2 - mid) < 8
                     and not t[:1].islower()
                     and not ((SECTION.match(t) or ENUM.match(t)) and re.search(r'[a-z]{3}', t)))
    return rows


def paragraphs(rows: list[Line]) -> list[str]:
    out: list[str] = []
    prev = None
    for r in rows:
        t = clean(r.text)
        if not t:
            continue
        new = (prev is None or bool(ENUM.match(t)) or r.centred or prev.centred
               or (r.rel > 6 and abs(r.rel - prev.tx) > 6 and abs(r.rel - prev.rel) > 3)
               or (r.page == prev.page and r.y - prev.y > 20))
        if new or not out:
            out.append(t)
        else:
            last = out[-1]
            out[-1] = last + t if (last.endswith('-') and t[:1].islower()) else last + ' ' + t
        prev = r
    return out


def note_blocks(margin: list[Line]) -> list[list[Line]]:
    blocks: list[list[Line]] = []
    for ln in sorted(margin, key=lambda l: (l.page, l.y)):
        if blocks and blocks[-1][-1].page == ln.page and ln.y - blocks[-1][-1].y <= 10.5:
            blocks[-1].append(ln)
        else:
            blocks.append([ln])
    return blocks


def plausible_next(prev: str | None, cur: str) -> bool:
    """A section number that can follow `prev` (12 -> 13, 12 -> 12A, 12A -> 12B, 12 -> 15 after repeals)."""
    if prev is None:
        return cur == '1'
    pn, pa = re.match(r'(\d+)([A-Z]*)', prev).groups()
    cn, ca = re.match(r'(\d+)([A-Z]*)', cur).groups()
    pn, cn = int(pn), int(cn)
    if cn == pn:
        return ca > pa
    return pn < cn <= pn + 40


ARRANGEMENT = re.compile(r'^ARRANGEMENT\s+OF\b', re.I)
ARR_END = re.compile(r'^(CHAPTER\s+\d|AN\s+ACT\b|An\s+Act\b|\[.*\d{4}\.?\]$)')
SUBSIDIARY = re.compile(r'^SUBSIDIARY\s+LEGISLATION$', re.I)


def sec_num(t: str, scan: bool, want=None):
    """The section number a row starts with, or None. In a scan an OCR misreading of the digits ("s." for 5, "l." for
    1) counts only when it reads as the number expected next (`want`)."""
    m = SECTION.match(t)
    if m:
        return m.group(1), m.end()
    if scan and want:
        m = OCR_SECTION.match(t)
        if m and m.group(1).translate(OCR_DIGITS) in want:
            return m.group(1).translate(OCR_DIGITS), m.end()
    return None


def next_numbers(prev: str | None) -> set[str]:
    if prev is None:
        return {'1'}
    n = int(re.match(r'\d+', prev).group(0))
    return {str(n + 1)}


def first_sections(rows: list[Line], lo: int, hi: int, need_cited: bool, scan: bool = False,
                   first: tuple = ('1',)) -> list[int]:
    """Rows in [lo, hi) where a numbering starts again at "1.", outside arrangement tables. In subsidiary legislation
    (need_cited) a new instrument starts at a "1." right after an arrangement table or one that cites its title."""
    out = []
    in_arr = False
    arr_ended = False
    for k in range(lo, hi):
        r = rows[k]
        t = clean(r.text)
        if ARRANGEMENT.match(t):
            in_arr = True
            continue
        if in_arr and (ARR_END.match(t) or (r.centred and t.isupper() and TITLE_WORDS.search(t)
                                             and not t.startswith('ARRANGEMENT'))):
            in_arr = False
            arr_ended = True
        m = sec_num(t, scan, set(first))
        if not (m and m[0] in first and r.rel < 60 and not r.centred) or in_arr:
            continue
        if need_cited:
            near = ' '.join(clean(rows[j].text) for j in range(k, min(k + 3, hi)))
            if not (arr_ended or re.search(r'\bcited\b|\bcitation\b', near, re.I)):
                continue
        out.append(k)
        arr_ended = False
        if not need_cited:
            break
    return out


def title_back(rows: list[Line], start: int, floor: int) -> int:
    """Where the title block above a first section begins: back over an arrangement table (if there is one between
    floor and start) and the centred or upper-case title rows above it."""
    arr = None
    for k in range(start - 1, floor, -1):
        if ARRANGEMENT.match(clean(rows[k].text)):
            arr = k
            break
    k = (arr if arr is not None else start) - 1
    while k > floor:
        t = clean(rows[k].text)
        if not t or SECTION.match(t) or ENUM.match(t):
            break
        if not (rows[k].centred or t.upper() == t or ARR_END.match(t) or re.match(r'^\(?(LN|GN|Legal Notice)\b', t)
                or re.match(r'^(made|Made)\b', t)):
            break
        k -= 1
    return k + 1


def parse(path: str, scan: bool = False) -> dict:
    if scan:
        doc = pymupdf.open(path)
        per_page = [len(WORDCHARS.sub('', pg.get_text())) for pg in doc]
        n = sum(per_page)
        if n < 40 * doc.page_count:
            return {'error': f"scan only: no text layer ({n} letters and digits on {doc.page_count} pages); not OCR'd here",
                    'scan_only': True, 'front': [], 'parts': [], 'pages': doc.page_count, 'scan': True}
        blank = sum(1 for c in per_page if c < 20)
        lines, pages = read_scan_lines(path)
    else:
        lines, pages = read_lines(path)
        lines = drop_headers(lines)
        mark_margin(lines)
    body = [l for l in lines if not l.margin]
    margin = [l for l in lines if l.margin]
    rows = merge_rows(body)
    act = first_sections(rows, 0, len(rows), False, scan)
    if scan:
        # OCR can destroy the "1." of section 1 ("L _ his, _ct may be cited"): then the Act starts at a "2." or "3."
        # before the first "1." found (which may be a numbered form in a schedule)
        later = first_sections(rows, 0, act[0] if act else len(rows), False, scan, ('2', '3'))
        if later:
            act = later
    if not act:
        out = {'front': paragraphs(rows), 'parts': [], 'pages': len(pages), 'notes_front': [
            ' '.join(clean(l.text) for l in b) for b in note_blocks(margin)]}
        if scan:
            out.update(scan=True, pages_without_text=blank)
        return out
    a = act[0]
    sl_mark = next((k for k in range(a, len(rows)) if SUBSIDIARY.match(clean(rows[k].text))), None)
    sl_starts = first_sections(rows, sl_mark + 1, len(rows), True, scan) if sl_mark is not None else []
    # The Act's title block: back from section 1 to the repeated "CHAPTER n:nn" heading.
    ts = a
    for k in range(a - 1, -1, -1):
        t = clean(rows[k].text)
        if ARRANGEMENT.match(t) or SECTION.match(t):
            break
        ts = k
        if re.match(r'^CHAPTER\s+\d', t):
            break
    bounds = [('act', 0, ts, a)]
    floor = sl_mark if sl_mark is not None else a
    for s in sl_starts:
        bounds.append(('sl', None, title_back(rows, s, floor), s))
        floor = s
    parts = []
    for j, (kind, _, t0, s) in enumerate(bounds):
        end = bounds[j + 1][2] if j + 1 < len(bounds) else len(rows)
        if kind == 'act' and sl_mark is not None:
            end = min(end, sl_mark)
        title_rows = rows[t0:s]
        if kind == 'sl' and j == 1 and sl_mark is not None:
            title_rows = rows[sl_mark:s]
        parts.append(build_part(title_rows, rows[s:end], kind, scan))
        parts[-1]['anchor'] = (rows[t0].page, rows[t0].y) if t0 < len(rows) else (0, 0)
    if sl_mark is not None and not sl_starts:
        # subsidiary legislation without a recognisable start: keep it whole
        parts.append({'kind': 'sl', 'title': rows[sl_mark:], 'units': [], 'anchor': (rows[sl_mark].page, rows[sl_mark].y)})
    front = rows[:ts]
    front_notes = attach_notes(parts, margin)
    out_parts = []
    for p in parts:
        out_parts.append({'kind': p['kind'], 'title': paragraphs(p['title']), 'title_notes': p.get('notes', []),
                          'units': [{'id': u.id, 'kind': u.kind, 'heading': u.heading, 'lines': paragraphs(u.lines),
                                     'notes': u.notes} for u in p['units']]})
    out = {'front': paragraphs(front), 'notes_front': front_notes, 'parts': out_parts, 'pages': len(pages)}
    if scan:
        out.update(scan=True, pages_without_text=blank)
    return out


def build_part(title: list[Line], rows: list[Line], kind: str, scan: bool = False) -> dict:
    units: list[Unit] = []
    pending: list[str] = []
    seen: dict[str, int] = {}
    prev_num = None
    in_schedule = False
    indent = rows[0].rel if rows else 0
    for k, r in enumerate(rows):
        t = clean(r.text)
        alone = SECTION_ALONE.match(t)
        m = sec_num(t, scan, next_numbers(prev_num)) or ((alone.group(1), alone.end()) if alone else None)
        if m and not in_schedule and r.rel <= indent + 30 and not r.centred and (k == 0 or plausible_next(prev_num, m[0])):
            num = m[0]
            prev_num = num
            n = seen.get(num, 0)
            seen[num] = n + 1
            u = Unit(num if n == 0 else f'{num}~{n + 1}', 'section', r.page, r.y, heading=pending)
            pending = []
            rest = t[m[1]:] if not alone else ''
            if rest:
                u.lines.append(Line(r.page, r.y, r.x, r.x1, r.size, False, r.italic, rest, rel=r.tx, tx=r.tx))
            units.append(u)
            continue
        s = SCHEDULE.match(t)
        if s and (r.centred or r.rel > 20) and len(t) < 60 and units:
            in_schedule = True
            uid = re.sub(r'[^a-z0-9]+', '-', s.group(1).lower()).strip('-')
            n = seen.get(uid, 0)
            seen[uid] = n + 1
            u = Unit(uid if n == 0 else f'{uid}~{n + 1}', 'schedule', r.page, r.y, heading=pending + [t])
            pending = []
            units.append(u)
            continue
        if not units:
            pending.append(t)
            continue
        cur = units[-1]
        if cur.kind == 'section' and r.centred and len(t) < 120 and not ENUM.match(t) and t.upper() == t:
            pending.append(t)
            continue
        if pending:
            cur.lines.extend(Line(r.page, r.y, 0, 0, 12, False, False, h, centred=True) for h in pending)
            pending = []
        cur.lines.append(r)
    if pending and units:
        units[-1].lines.extend(Line(0, 0, 0, 0, 12, False, False, h, centred=True) for h in pending)
    return {'kind': kind, 'title': title, 'units': units}


def attach_notes(parts: list[dict], margin: list[Line]) -> list[str]:
    """Margin notes belong to the unit (or part title) that starts nearest at or above them; notes above everything
    belong to the front matter, which is returned."""
    anchors = []
    for p in parts:
        p.setdefault('notes', [])
        anchors.append((p['anchor'][0], p['anchor'][1], 0, p['notes']))
        for u in p['units']:
            anchors.append((u.page, u.y, 1, u.notes))
    anchors.sort(key=lambda a: (a[0], a[1], a[2]))
    front: list[str] = []
    for block in note_blocks(margin):
        b = block[0]
        target = front
        for page, y, _, notes in anchors:
            if (page, y) <= (b.page, b.y + 6):
                target = notes
            else:
                break
        target.append(' '.join(clean(l.text) for l in block))
    return front


if __name__ == '__main__':
    import json
    d = parse(sys.argv[1], '--scan' in sys.argv)
    n = [a for a in sys.argv[2:] if a.isdigit()]
    print(json.dumps(d, ensure_ascii=False, indent=1)[:int(n[0]) if n else None])
