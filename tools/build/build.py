"""Build the Trinidad and Tobago law repository from the retrieved laws.gov.tt catalogue and PDFs.

    python build.py ~/Documents/trinidad-and-tobago-law-build --today YYYY-MM-DD [--workers 4] [--limit N]
                    [--update-date pdf-created|retrieved] [--parse-only]

laws.gov.tt (the Digital Legislative Library of the Law Revision Commission) publishes every Chapter of the Laws of
Trinidad and Tobago as a series of dated consolidations: the 2006 Revised Edition as at 31 December 2004, 2007, 2009,
2012, (2013,) 2014 and 2016, and an unofficial update as at 31 December 2015. About 190 Chapters, and 26 Acts not yet
given a Chapter number, also have a later "Recent Update" with no date of its own.

1. Every consolidation PDF is parsed into units (parse_pdf.py): the Act's sections and schedules, and each piece of
   subsidiary legislation printed after it with its own regulations and schedules. Each parse is kept as PARSED/<id>.json.
2. Per Chapter, the consolidations are taken in date order. The first is a commit `Kind: consolidated` by the Law
   Revision Commission, holding the whole text as at that date. Each later one is compared with the one before, unit
   by unit (typesetting alone, i.e. whitespace, quotes and dashes, is not a change).
3. A changed unit is credited to an amending law only when its own margin notes newly name exactly one law, made no
   earlier than the year of the previous consolidation (`Kind: amendment`, `Evidence: margin note`). Every other
   change stays with the Law Revision Commission, `Kind: consolidation`, and lists the laws newly named in that
   Chapter's margins (`Newly-cited:`), which are candidates and not credited.
4. Commits are dated noon Trinidad time (UTC-4, no daylight saving) on the consolidation's as-at date. A change first
   shown in the consolidation as at 31 December 2009 was in force by that day, not necessarily from it; the
   `In-force-basis:` trailer says so. The Recent Updates carry no as-at date: by default they are dated by the PDF's
   creation date (`Date-source: pdf-created`); `--update-date retrieved` dates them by the day the catalogue was
   retrieved instead (`Date-source: retrieved`). The choice is open (see README).
5. One commit per (Chapter, consolidation, crediting law), in date order; written with git fast-import, so the same
   cache always gives the same hashes.
"""
import argparse
import calendar
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
CACHE = HERE / '.cache'
PDF = CACHE / 'pdf'
PARSED = CACHE / 'parsed'
PARSE_FORMAT = '1'  # bump with parse_pdf.PARSER_VERSION changes too (both are checked)

COMMITTER = 'Lexifina <trinidad-and-tobago@lexifina.com>'
LRC = ('Law Revision Commission (laws.gov.tt)', 'law-revision-commission@laws-gov-tt.invalid')
SITE = 'https://laws.gov.tt/ttdll-web/revision/'
EDITION = re.compile(r'^as at December 31st (\d{4})\b')
# The older Revised Editions ("as at June 1925 1925 Revised Edition", "as at December 1990 1980 Revised Edition"):
# the as-at month and year, and the edition. Dated the month's last day (the label gives no day).
OLD_EDITION = re.compile(r'^as at (January|June|December) (\d{4}) (\d{4}) Revised Edition$')
MONTHS = {'January': 1, 'June': 6, 'December': 12}
CHAP = re.compile(r'(\d{1,3})[:.](\d{2,3})')
TT_OFFSET = -4  # Atlantic Standard Time all year


# ---------------------------------------------------------------------------------------------------- parsing

def _parser_version(scan: bool = False) -> str:
    src = (HERE / 'parse_pdf.py').read_text('utf-8')
    m = re.search(r'^PARSER_VERSION = (\S+)', src, re.M)
    if not scan:
        return f'{PARSE_FORMAT}.{m.group(1)}'
    return f"{PARSE_FORMAT}.{m.group(1)}.scan{re.search(r'^SCAN_VERSION = (\S+)', src, re.M).group(1)}"


def parse_one(d: str, scan: bool = False) -> str:
    """Parse one PDF. `scan`: an older Revised Edition (page images with the publisher's OCR text layer), read by
    parse_pdf's scan reader; every other PDF is read by its typography as before."""
    out = PARSED / f'{d}.json'
    ver = _parser_version(scan)
    if out.exists():
        try:
            if json.loads(out.read_text('utf-8')).get('parser') == ver:
                return d
        except json.JSONDecodeError:
            pass
    import warnings
    warnings.filterwarnings('ignore')
    import parse_pdf
    try:
        r = parse_pdf.parse(str(PDF / f'{d}.pdf'), scan) if scan else parse_pdf.parse(str(PDF / f'{d}.pdf'))
    except Exception as e:  # noqa: BLE001 - recorded, the version is skipped
        r = {'error': f'{type(e).__name__}: {e}', 'front': [], 'parts': []}
    try:
        meta = parse_pdf.pymupdf.open(str(PDF / f'{d}.pdf')).metadata or {}
    except Exception:  # noqa: BLE001
        meta = {}
    r['created'] = meta.get('creationDate') or ''
    if scan:
        r['producer'] = meta.get('producer') or ''
    r['parser'] = ver
    out.write_text(json.dumps(r, ensure_ascii=False), 'utf-8')
    return d


def parsed_ok(d: str, scan: bool = False) -> bool:
    try:
        return json.loads((PARSED / f'{d}.json').read_text('utf-8')).get('parser') == _parser_version(scan)
    except (OSError, json.JSONDecodeError):
        return False


def parse_all(ids: list[str], workers: int, scans: set[str] = frozenset()) -> None:
    todo = [d for d in ids if not parsed_ok(d, d in scans)]
    print(f'parsing {len(todo)} of {len(ids)} PDFs', flush=True)
    if not todo:
        return
    # Plain worker processes, each parsing every n-th PDF (multiprocessing pools lose their pipe handles when
    # run detached on Windows). A PDF that crashes a worker is retried alone, then recorded as unreadable.
    n = max(1, min(workers, len(todo)))
    jobs = [(d, d in scans) for d in todo]
    procs = [subprocess.Popen([sys.executable, '-W', 'ignore', '-c',
                               f'import build; [build.parse_one(d, s) for d, s in {jobs[k::n]!r}]'],
                              cwd=HERE, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             for k in range(n)]
    for p in procs:
        p.wait()
    for d in [d for d in todo if not parsed_ok(d, d in scans)]:
        try:
            subprocess.run([sys.executable, '-W', 'ignore', '-c', f'import build; build.parse_one({d!r}, {d in scans})'],
                           cwd=HERE, stdin=subprocess.DEVNULL, capture_output=True, timeout=1800)
        except subprocess.TimeoutExpired:
            pass
        if not parsed_ok(d, d in scans):
            (PARSED / f'{d}.json').write_text(json.dumps({'parser': _parser_version(d in scans), 'error': 'parser crashed',
                                                          'front': [], 'parts': []}), 'utf-8')


# ---------------------------------------------------------------------------------------------------- laws

def chap_number(label: str) -> str | None:
    m = CHAP.search(label or '')
    return f'{int(m.group(1))}:{m.group(2)}' if m else None


def pdf_created(raw: str) -> str | None:
    m = re.match(r'^D:(\d{4})(\d{2})(\d{2})', raw or '')
    return f'{m.group(1)}-{m.group(2)}-{m.group(3)}' if m else None


def load_laws(limit: int | None) -> tuple[list[dict], dict]:
    cat = json.loads((CACHE / 'catalogue.json').read_text('utf-8'))
    upd: dict[str, dict] = {}
    numbered: list[dict] = []
    for r in sorted(cat['recent'].values(), key=lambda r: int(r['download'])):
        c = chap_number(r['ref'])
        if c:
            upd[c] = r
        else:
            numbered.append(r)
    laws = []
    for cid, it in cat['chapters'].items():
        c = chap_number(it['chapter_label']) or chap_number(it['heading'])
        eds: dict[int, dict] = {}
        for v in it['versions']:
            m = EDITION.match(v['label'])
            if m and 2004 <= int(m.group(1)) <= 2016:
                y = int(m.group(1))
                eds.setdefault(y, {'kind': 'edition', 'download': v['download'], 'type': 'act', 'label': v['label'],
                                   'date': f'{y}-12-31'})
        old: dict[int, dict] = {}
        for v in it['versions']:
            m = OLD_EDITION.match(v['label'])
            if m and int(m.group(2)) < 2004:
                y, month = int(m.group(2)), MONTHS[m.group(1)]
                old.setdefault(y, {'kind': 'old', 'download': v['download'], 'type': 'act', 'label': v['label'],
                                   'date': f'{y}-{month:02d}-{calendar.monthrange(y, month)[1]:02d}',
                                   'as_at': f'{m.group(1)} {y}', 'revised': m.group(3)})
        versions = [old[y] for y in sorted(old)] + [eds[y] for y in sorted(eds)]
        if c in upd:
            r = upd[c]
            versions.append({'kind': 'update', 'download': r['download'], 'type': 'amendment',
                             'label': f"Recent Update ({r['ref']})", 'date': None})
        a, b = c.split(':')
        laws.append({'kind': 'chapter', 'id': cid, 'key': c, 'label': f'Chap. {c}', 'name': it['name'],
                     'dir': f'chapters/{int(a):02d}-{b}', 'classification': it.get('classification', ''),
                     'year': it.get('year', ''), 'versions': versions,
                     'amendments_listed': [x['kind'] for x in it.get('amendments', [])]})
    for r in numbered:
        m = re.search(r'No\.?\s*(\d+)\s+of\s+(\d{4})', r['ref'])
        n, y = m.group(1), m.group(2)
        laws.append({'kind': 'act', 'id': r['download'], 'key': f'{n}/{y}', 'label': f'Act No. {n} of {y}',
                     'name': r['title'], 'dir': f'acts/{y}-{int(n):03d}', 'classification': '', 'year': y,
                     'versions': [{'kind': 'update', 'download': r['download'], 'type': 'amendment',
                                   'label': f"Recent Update ({r['ref']})", 'date': None}],
                     'amendments_listed': []})
    laws.sort(key=lambda l: l['dir'])
    return (laws[:limit] if limit else laws), cat


# ---------------------------------------------------------------------------------------------------- files

def norm(s: str) -> str:
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = s.replace('–', '-').replace('—', '-').replace('­', '')
    # dot leaders of form blanks ("To: ..........") vary in length with each typesetting: one "..." each
    s = re.sub(r'[.…](?:\s*[.…]){3,}', '...', s)
    return re.sub(r'\s+', ' ', s).strip()


def squash(s: str) -> str:
    return re.sub(r'\s+', '', s)


ACT_CITE = re.compile(r'(?<![\d/.])(\d{1,3})\s+of\s+(\d{4})\b')
LN_CITE = re.compile(r'\b(?:L\.?\s?N\.?|G\.?\s?N\.?)\s*(?:No\.?\s*)?(\d{1,4})\s*/\s*(\d{4})\b')


def cite_keys(notes: list[str]) -> set[tuple]:
    """Laws named in margin notes: ('act', year, n) for "15 of 2018", ('ln', year, n) for "LN 51/1980"."""
    keys = set()
    for n in notes:
        n = n.replace('*', '')
        for a, y in LN_CITE.findall(n):
            keys.add(('ln', int(y), int(a)))
        # "n of yyyy" is an Act unless the nearest law word before it is a Legal (or Government) Notice
        # ("LN Nos. 103 of 2009 and 183 of 2021 revoked").
        for m in ACT_CITE.finditer(n):
            before = n[:m.start()]
            word = LAW_WORD.findall(before)
            kind = 'ln' if word and not re.match(r'(?i)acts?\b|ordinances?\b', word[-1]) else 'act'
            keys.add((kind, int(m.group(2)), int(m.group(1))))
    return keys


LAW_WORD = re.compile(r'\b(?:L\.?\s?N\.?|G\.?\s?N\.?|Legal\s+Notices?|Government\s+Notices?|Acts?|Ordinances?)(?=[\s.,;:]|$)')


def law_name(k: tuple) -> tuple[str, str]:
    kind, y, n = k
    if kind == 'act':
        return f'Act No. {n} of {y}', f'act-{y}-{n}@laws-gov-tt.invalid'
    return f'Legal Notice No. {n} of {y}', f'ln-{y}-{n}@laws-gov-tt.invalid'


def safe(uid: str) -> str:
    """A file name for a unit id. A repeated id ("form-1~2", the second Form 1) becomes "form-1--2": a "~" plus a
    digit is a Windows 8.3 short name and can alias another file in a Windows checkout."""
    return re.sub(r'[^0-9A-Za-z.-]', '-', uid.replace('~', '--'))


def unit_text(u: dict, prefix: str) -> str:
    """A section: its Part headings as `##` lines, `# 12A.` with its marginal heading (the first margin note), one
    line per paragraph, then the other margin notes as `- Margin:` lines. A schedule: `# FIRST SCHEDULE`."""
    lines = []
    heads = [norm(h) for h in (u.get('heading') or []) if norm(h)]
    notes = [norm(n) for n in u['notes'] if norm(n)]
    if u['kind'] == 'section':
        lines += [f'## {h}' for h in heads]
        head = f"# {prefix}{u['id'].split('~')[0]}."
        if notes:
            head += ' ' + notes[0]
            notes = notes[1:]
        lines.append(head)
    else:
        lines += [f'## {h}' for h in heads[:-1]]
        lines.append(f"# {heads[-1] if heads else u['id']}")
    lines.extend(norm(l) for l in u['lines'] if norm(l))
    lines.extend(f'- Margin: {n}' for n in notes)
    return '\n'.join(lines) + '\n'


PAGE_TABLE = re.compile(r'^(Current authorised pages|Pages Authorised\b.*|\(inclusive\).*|'
                        r'\d+ ?- ?\d+( (\.\.|\d+/\d{4}))?( \d+ ?- ?\d+( (\.\.|\d+/\d{4}))?)*)$', re.I)


def version_files(law: dict, parsed: dict) -> dict[str, tuple[str, set]]:
    """path -> (text, laws named in that unit's margin notes)."""
    files: dict[str, tuple[str, set]] = {}
    d = law['dir']
    # The cover's table of current authorised pages ("Pages Authorised (inclusive) by L.R.O.", "1-61 1/2009") is
    # print bookkeeping that changes with every reprint, not law: left out.
    title = [norm(l) for l in parsed.get('front', []) if norm(l) and not PAGE_TABLE.match(norm(l))]
    title_notes = list(parsed.get('notes_front', []))
    parts = parsed.get('parts', [])
    acts = [p for p in parts if p['kind'] == 'act']
    if acts:
        # (a short Act with no arrangement table has its cover in the title block too)
        title += [''] + [norm(l) for l in acts[0]['title'] if norm(l) and not PAGE_TABLE.match(norm(l))]
        title_notes += acts[0].get('title_notes', [])
    body = title + [f'- Margin: {norm(n)}' for n in title_notes if norm(n)]
    if any(body):
        files[f'{d}/title.md'] = ('\n'.join(body).strip('\n') + '\n', set())
    for p in acts[:1]:
        for u in p['units']:
            stem = f"s-{u['id']}" if u['kind'] == 'section' else u['id']
            files[f'{d}/{safe(stem)}.md'] = (unit_text(u, ''), cite_keys(u['notes']))
    for k, p in enumerate([p for p in parts if p['kind'] == 'sl'], 1):
        sd = f'{d}/sl-{k:02d}'
        t = [norm(l) for l in p['title'] if norm(l)] + [f'- Margin: {norm(n)}' for n in p.get('title_notes', []) if norm(n)]
        if t:
            files[f'{sd}/title.md'] = ('\n'.join(t) + '\n', cite_keys(p.get('title_notes', [])))
        for u in p['units']:
            stem = f"r-{u['id']}" if u['kind'] == 'section' else u['id']
            files[f'{sd}/{safe(stem)}.md'] = (unit_text(u, ''), cite_keys(u['notes']))
    if files:
        # the files in document order (the dict's insertion order)
        files[f'{d}/index.txt'] = ('\n'.join(p[len(d) + 1:] for p in files) + '\n', set())
    return files


# ---------------------------------------------------------------------------------------------------- dates

def git_date(day: str) -> str:
    """Noon Trinidad time (UTC-4) on day."""
    dt = datetime.strptime(day, '%Y-%m-%d').replace(hour=12, tzinfo=timezone(timedelta(hours=TT_OFFSET)))
    return f'{int(dt.timestamp())} -0400'


def long_date(day: str) -> str:
    d = datetime.strptime(day, '%Y-%m-%d')
    return f'{d.day} {d.strftime("%B")} {d.year}'


# ---------------------------------------------------------------------------------------------------- history

def printed_chapter(parsed: dict) -> str | None:
    """The Chapter number the PDF prints for itself ("CHAPTER 11:12"), from the cover or the Act's title."""
    lines = list(parsed.get('front', [])[:40])
    for p in parsed.get('parts', [])[:1]:
        lines += p.get('title', [])[:6]
    for l in lines:
        m = re.match(r'^CHAPTER\s+(\d{1,3})[:.](\d{2,3})\b', l.strip(), re.I)
        if m:
            return f'{int(m.group(1))}:{m.group(2)}'
    return None


NAME_STOP = {'act', 'acts', 'ordinance', 'ordinances', 'chapter', 'and', 'the', 'for', 'with', 'from', 'under', 'into',
             'other', 'laws', 'law', 'miscellaneous', 'provisions'}


def title_lines(parsed: dict) -> list[str]:
    """The cover's first lines and each part's title block."""
    lines = list(parsed.get('front', [])[:12])
    for p in parsed.get('parts', [])[:3]:
        lines += p.get('title', [])[:8]
    return lines


def short_title(parsed: dict) -> str | None:
    """A readable title line of an older edition ("LANDLORD AND TENANT.", "COUNTY COUNCILS ACT"): a line of the title
    lines written in capitals, made of readable words, that is not a CHAPTER / AN ORDINANCE / AN ACT / LAWS OF line,
    a fragment of the "LAWS OF TRINIDAD AND TOBAGO" stamp or a schedule or rules heading. None when the OCR left none."""
    lines = list(parsed.get('front', [])[:12]) + [t for p in parsed.get('parts', [])[:1] for t in p.get('title', [])[:8]]
    for l in lines:  # the Act's own titles, not a subsidiary instrument's
        t = l.strip()
        if not t or t != t.upper() or SKIP_TITLE.match(t) or STAMPISH.search(t):
            continue
        toks = re.findall(r"\S+", t)
        words = [w for w in toks if re.fullmatch(r"[A-Z][A-Z'\-]+[.,;:)]*|\(?[A-Z][A-Z'\-]+\)?[.,;:]*|AND|OF|THE", w)]
        if len(words) >= 1 and len(words) >= 0.8 * len(toks) and sum(len(w) for w in words) >= 6:
            return t
    return None


SKIP_TITLE = re.compile(r"^(CHAPTER|CHAP|CAP|AN\s+(ORDINANCE|ACT)|ORDINANCE|ACT\b|LAWS\s+OF|THE\s+LAWS|ARRANGEMENT|SECTION|"
                        r"SUBSIDIARY|PAGES|AMENDED|INDEX|NOTE|PAGE\b|\[|\()")


STAMPISH = re.compile(r'TRINIDAD|TOBAGO|TOBABO|SCHEDULE|REGULATION|RULES|BYE-LAWS|ORDER')


def title_matches(name: str, title: str) -> bool:
    """A word of the title (four letters or more) is close to a word of the law's name: equal, one a prefix of the
    other ("PENSIONS" / "Pension"), or alike as OCR misreads them ("OORONERS" / "Coroners", ratio >= 0.8)."""
    import difflib
    have = {w for w in re.findall(r'[a-z]{4,}', title.lower()) if w not in NAME_STOP}
    want = {w for w in re.findall(r'[a-z]{4,}', name.lower()) if w not in NAME_STOP}
    if not want or not have:
        return True
    return any(a.startswith(b[:5]) or b.startswith(a[:5]) or difflib.SequenceMatcher(None, a, b).ratio() >= 0.8
               for a in have for b in sorted(want))


def plan(laws: list[dict], update_date: str, retrieved: str, today: str) -> tuple[list[dict], list[dict], list[list]]:
    commits: list[dict] = []
    issues: list[dict] = []
    ledger: list[list] = []
    for law in laws:
        prev_files = None
        prev_v = None
        law['built_versions'] = []
        for v in law['versions']:
            if not (PDF / f"{v['download']}.pdf").exists() or not parsed_ok(v['download'], v['kind'] == 'old'):
                issues.append({'law': law['label'], 'version': v['label'], 'download': v['download'], 'issue': 'not fetched'})
                continue
            with open(PDF / f"{v['download']}.pdf", 'rb') as fh:
                if fh.read(5) != b'%PDF-':
                    # the server answers some downloads with an HTML page (a repository directory listing)
                    issues.append({'law': law['label'], 'version': v['label'], 'download': v['download'],
                                   'issue': 'the download is not a PDF (an HTML page); skipped'})
                    continue
            parsed = json.loads((PARSED / f"{v['download']}.json").read_text('utf-8'))
            if parsed.get('error') or not (parsed.get('parts') or parsed.get('front')):
                issues.append({'law': law['label'], 'version': v['label'], 'download': v['download'],
                               'issue': parsed.get('error') or 'no text'})
                continue
            # A download can serve another Chapter's PDF (the 2009 "Prevention of Corruption" is the Larceny Act):
            # the Chapter number printed on the cover and above the Act must be this law's.
            printed = printed_chapter(parsed)
            if v['kind'] == 'old':
                # laws.gov.tt lists some other laws as older editions of a Chapter (the Judicature Ordinance for
                # Judges Salaries and Pensions, Poor Relief for Public Assistance): skipped when the edition's own
                # short title shares no word with the law's name. OCR misreads chapter numbers, so they are not used.
                # (judged on all the title lines; the readable line is only the evidence that a title was printed)
                title = short_title(parsed)
                if title and not title_matches(law['name'], ' '.join(title_lines(parsed))):
                    issues.append({'law': law['label'], 'version': v['label'], 'download': v['download'],
                                   'issue': f"the PDF's title is {title!r}, not {law['name']}: another (perhaps an "
                                            f"earlier) law; skipped"})
                    continue
            elif law['kind'] == 'chapter' and printed and printed != law['key']:
                issues.append({'law': law['label'], 'version': v['label'], 'download': v['download'],
                               'issue': f'the PDF is Chap. {printed}, not {law["label"]}; skipped'})
                continue
            v = dict(v)
            if v['kind'] == 'update':
                created = pdf_created(parsed.get('created', ''))
                if update_date == 'pdf-created' and created and '2017-01-01' <= created <= today:
                    v['date'], v['date_source'] = created, 'pdf-created'
                else:
                    v['date'], v['date_source'] = retrieved, 'retrieved'
                    if update_date == 'pdf-created':
                        issues.append({'law': law['label'], 'version': v['label'], 'download': v['download'],
                                       'issue': f"PDF creation date {created or 'missing'} unusable; dated by retrieval"})
                v['created'] = created or ''
            elif v['kind'] == 'old':
                v['date_source'] = 'as-at-month'
                v['producer'] = parsed.get('producer', '')
                v['pages_without_text'] = parsed.get('pages_without_text', 0)
                if v['pages_without_text']:
                    issues.append({'law': law['label'], 'version': v['label'], 'download': v['download'],
                                   'issue': f"{v['pages_without_text']} of {parsed.get('pages', '?')} pages have no text "
                                            f"layer (scan only; not OCR'd here); the version is used without them"})
            else:
                v['date_source'] = 'as-at'
            if prev_v and v['date'] <= prev_v['date']:
                issues.append({'law': law['label'], 'version': v['label'], 'download': v['download'],
                               'issue': f"dated {v['date']}, not after the version before ({prev_v['date']}); skipped"})
                continue
            files = version_files(law, parsed)
            if not files:
                issues.append({'law': law['label'], 'version': v['label'], 'download': v['download'], 'issue': 'no units'})
                continue
            law['built_versions'].append(v)
            # A file whose text differs only in spacing keeps the earlier text, within one kind of source: an OCR
            # text layer's spacing is never carried into the typeset consolidations (2004 onwards stay as printed).
            if prev_files is not None and (prev_v['kind'] == 'old') == (v['kind'] == 'old'):
                for p in files:
                    if p in prev_files and squash(files[p][0]) == squash(prev_files[p][0]):
                        files[p] = prev_files[p]
            for p, (_, keys) in files.items():
                old = prev_files.get(p, ('', set()))[1] if prev_files else set()
                for k in sorted(keys - old):
                    ledger.append([law['label'], p[len(law['dir']) + 1:], law_name(k)[0], v['date'], v['label']])
            if prev_files is None:
                commits.append({'date': v['date'], 'kind': 'earliest' if v['kind'] == 'old' else 'consolidated',
                                'author': None, 'law': law, 'version': v,
                                'changes': {p: t for p, (t, _) in files.items()}, 'newly': []})
                prev_files, prev_v = files, v
                continue
            changed = sorted(p for p in files if p not in prev_files or files[p][0] != prev_files[p][0])
            removed = sorted(p for p in prev_files if p not in files)
            if not changed and not removed:
                prev_files, prev_v = files, v
                continue
            floor = int(prev_v['date'][:4])
            all_new = set().union(*(files[p][1] for p in files)) - set().union(*(prev_files[p][1] for p in prev_files))
            buckets: dict = {}
            for p in changed + removed:
                new = {k for k in ((files[p][1] if p in files else set()) - (prev_files[p][1] if p in prev_files else set()))
                       if k[1] >= floor}
                who = next(iter(new)) if len(new) == 1 and p in files and not p.endswith('/index.txt') else None
                b = buckets.setdefault(who, {})
                b[p] = files[p][0] if p in files else None
            # index.txt follows the bucket that adds or removes units; else the consolidation
            for who in sorted(buckets, key=lambda k: (k is None, k or ())):
                commits.append({'date': v['date'], 'kind': 'amendment' if who else 'consolidation', 'author': who,
                                'law': law, 'version': v, 'prev': prev_v, 'changes': buckets[who],
                                'newly': sorted(k for k in all_new if k[1] >= floor)})
            prev_files, prev_v = files, v
    order = {'consolidated': 0, 'earliest': 0, 'amendment': 1, 'consolidation': 2}
    commits.sort(key=lambda c: (c['date'], c['law']['dir'], order[c['kind']], c['author'] or ()))
    return commits, issues, ledger


def message(c: dict) -> tuple[str, str]:
    law, v = c['law'], c['version']
    name = f"{law['label']} {law['name']}"
    n = len(c['changes'])
    if v['kind'] == 'edition':
        y = v['date'][:4]
        what = f'the consolidation as at 31 December {y}'
        if 'Unofficial' in v['label']:
            what += ' (an unofficial update)'
        basis = (f'consolidation as at {long_date(v["date"])}: the text in force on that day; a change first shown '
                 f'here took effect on or before it')
    elif v['kind'] == 'old':
        what = f"the {v['revised']} Revised Edition (as at {v['as_at']})"
        basis = (f"{v['revised']} Revised Edition as at {v['as_at']}; the label gives the month only, so it is dated "
                 f"the month's last day, {long_date(v['date'])}; a change first shown here took effect on or before it")
    else:
        what = 'the Recent Update (unofficial, undated)'
        if v['date_source'] == 'pdf-created':
            basis = (f'undated unofficial update; dated by its PDF creation date, {long_date(v["date"])}; a change '
                     f'first shown here took effect on or before it')
        else:
            basis = (f'undated unofficial update; dated by the day it was retrieved, {long_date(v["date"])}; a change '
                     f'first shown here took effect on or before it')
    trailers_common = [f"In-force: {v['date']}", f'In-force-basis: {basis}', f"Date-source: {v['date_source']}"]
    if v['kind'] == 'update' and v.get('created'):
        trailers_common.append(f"Pdf-created: {v['created']}")
    if v['kind'] == 'old':
        trailers_common.append("Text-layer: the publisher's OCR of the scanned pages"
                               + (f" ({v['producer']})" if v.get('producer') else '') + ', not corrected here')
        if v.get('pages_without_text'):
            trailers_common.append(f"Pages-without-text: {v['pages_without_text']}")
        if v['date'] < '1970-01-01':
            trailers_common.append('Date-note: git cannot store dates before 1970; the commit is dated 1970-01-01 '
                                   'and In-force is the real day')
    trailers_common += [f"Edition: {v['label']}", f"Law: {law['label']}",
                        f"Source: {SITE}download/{v['download']}?type={v['type']}"]
    ocr = ([f"The earlier text ({c['prev']['label']}) is an OCR text layer, so some differences are OCR errors,",
            'not changes in the law.'] if c.get('prev') and c['prev']['kind'] == 'old' else [])
    if c['kind'] == 'consolidated':
        an, ae = LRC
        subject = f"{name}: as consolidated in {what}"
        body = [f"The text of {law['label']} ({law['name']}) as laws.gov.tt publishes it in {what}, the earliest",
                'version used here. Who wrote each line before this date is not shown; each section keeps the history',
                'printed in its margin.']
        trailers = ['Kind: consolidated', f"Consolidated: {v['date']}"] + trailers_common
    elif c['kind'] == 'earliest':
        an, ae = LRC
        subject = f"{name}: as consolidated in {what}"
        body = [f"The text of {law['label']} ({law['name']}) as laws.gov.tt publishes it in {what}, the earliest",
                "version used here: the scanned pages' OCR text layer as published, errors included. Who wrote each",
                'line before this date is not shown; each section keeps the history printed in its margin.']
        trailers = ['Kind: consolidation', f"Consolidated: {v['date']}"] + trailers_common
    elif c['kind'] == 'consolidation':
        an, ae = LRC
        subject = f"{name}: changes in {what}"
        body = [f"{n} file(s) of {law['label']} differ between {c['prev']['label']} and {v['label']}.",
                'Their margin notes do not name exactly one new law for them, so no law is credited.', *ocr]
        trailers = ['Kind: consolidation'] + trailers_common
        for k in c['newly']:
            trailers.append(f'Newly-cited: {law_name(k)[0]}')
    else:
        an, ae = law_name(c['author'])
        subject = f"{an}: {name} ({what})"
        body = [f"Changes to {n} file(s) of {law['label']} ({law['name']}) whose margin notes newly name {an},",
                f"first shown in {what}. The date is that of the consolidation, not the law's commencement.", *ocr]
        trailers = ['Kind: amendment', 'Evidence: margin note'] + trailers_common
    return f'{an} <{ae}>', '\n'.join([subject, '', *body, '', *trailers]) + '\n'


def fast_import(repo: Path, commits: list[dict], docs: dict[str, bytes], today: str) -> None:
    buf = io.BytesIO()
    w = buf.write
    clamp = 0
    for c in commits:
        author, msg = message(c)
        if c['date'] < '1970-01-01':
            # git cannot store a date before 1970: 1970-01-01, one second apart in history order
            clamp += 1
            when = f'{clamp} +0000'
        else:
            when = git_date(c['date'])
        w(b'commit refs/heads/main\n')
        w(f'author {author} {when}\ncommitter {COMMITTER} {when}\n'.encode())
        m = msg.encode('utf-8')
        w(f'data {len(m)}\n'.encode() + m + b'\n')
        for path, text in sorted(c['changes'].items()):
            if text is None:
                w(f'D {path}\n'.encode())
            else:
                t = text.encode('utf-8')
                w(f'M 100644 inline {path}\ndata {len(t)}\n'.encode() + t + b'\n')
        w(b'\n')
    when = git_date(today)
    msg = (f'Documentation: README, REPRODUCE, SOURCES, tools, laws.csv and data\n\n'
           f'Built on {today} from the retrieved laws.gov.tt files.\n\nKind: documentation\n').encode()
    w(b'commit refs/heads/main\n')
    w(f'author {COMMITTER} {when}\ncommitter {COMMITTER} {when}\n'.encode())
    w(f'data {len(msg)}\n'.encode() + msg + b'\n')
    for path, data in sorted(docs.items()):
        w(f'M 100644 inline {path}\ndata {len(data)}\n'.encode() + data + b'\n')
    w(b'\n')
    r = subprocess.run(['git', '-C', str(repo), 'fast-import', '--quiet', '--force'], input=buf.getvalue(),
                       capture_output=True)
    if r.returncode:
        sys.exit(r.stderr.decode('utf-8', 'replace')[-3000:])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('repo', type=Path)
    ap.add_argument('--today', required=True)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--update-date', choices=('pdf-created', 'retrieved'), default='pdf-created',
                    help='how to date the undated Recent Updates (open decision; see README)')
    ap.add_argument('--parse-only', action='store_true')
    args = ap.parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.today):
        sys.exit('--today must be YYYY-MM-DD')
    PARSED.mkdir(parents=True, exist_ok=True)
    laws, cat = load_laws(args.limit)
    retrieved = cat['fetched_on']
    if retrieved > args.today:
        sys.exit(f'catalogue retrieved {retrieved}, after --today')
    ids = sorted({v['download'] for l in laws for v in l['versions'] if (PDF / f"{v['download']}.pdf").exists()}, key=int)
    print(f"{len(laws)} laws, {sum(len(l['versions']) for l in laws)} versions listed, {len(ids)} PDFs cached", flush=True)
    scans = {v['download'] for l in laws for v in l['versions'] if v['kind'] == 'old'}
    parse_all(ids, args.workers, scans)
    if args.parse_only:
        return
    commits, issues, ledger = plan(laws, args.update_date, retrieved, args.today)
    kinds = {}
    for c in commits:
        kinds[c['kind']] = kinds.get(c['kind'], 0) + 1
    print(f'{len(commits)} commits {kinds}; {len(issues)} issues', flush=True)

    import docs as docmod
    docs = docmod.render(laws, commits, issues, ledger, args.today, args.update_date, retrieved)

    repo = args.repo
    repo.mkdir(parents=True, exist_ok=True)
    if (repo / '.git').exists():
        import shutil
        import stat

        def onerr(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(repo / '.git', onerror=onerr)
        for child in repo.iterdir():
            shutil.rmtree(child, onerror=onerr) if child.is_dir() else child.unlink()
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
    subprocess.run(['git', '-C', str(repo), 'config', 'core.autocrlf', 'false'], check=True)
    subprocess.run(['git', '-C', str(repo), 'config', 'core.longpaths', 'true'], check=True)
    fast_import(repo, commits, docs, args.today)
    subprocess.run(['git', '-C', str(repo), 'checkout', '-q', '-f', 'main'], check=True)
    head = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    count = subprocess.run(['git', '-C', str(repo), 'rev-list', '--count', 'HEAD'], capture_output=True, text=True).stdout.strip()
    print(f'built {repo}: {count} commits, head {head}', flush=True)


if __name__ == '__main__':
    main()
