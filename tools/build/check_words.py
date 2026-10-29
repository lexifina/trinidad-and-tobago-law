"""Letters-and-digits check: every version in the repository against the text of its PDF, read independently.

    python check_words.py <repo> [--pdf-dir DIR] [--limit N] [--workers 4]

For each row of data/versions.csv, the law's files at the last commit dated on or before that version are joined
and cut into words of letters and digits (case-folded; markup and the "Margin:" label dropped). The PDF is read
with PyMuPDF's plain `dict` text (not the parser's character boxes or layout rules), dropping only the publisher's
stamps, the large watermark and the running header band (for the scanned older editions, whose OCR text layer has no
fonts: the top rows holding a page number or chapter reference), and cut the same way. The two are compared as multisets:
The verdict counts letters and digits one by one (`missing` in the PDF but not the repository, `extra` the
reverse), because plain extraction runs letter-spaced words together; a version fails above 1%. The words that
differ are listed to show where.
"""
import argparse
import csv
import io
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
WORD = re.compile(r'[0-9a-z]+')
STAMP = re.compile(r'^(UNOFFICIAL(VERSION)?|LAWSOFTRINIDADANDTOBAGO|MINISTRYOF.*|OFFICEOFTHEATTORNEYGENERAL.*|WWW\..*|'
                   r'UPDATEDTO.*|L\.R\.O\.?[0-9/]*|CURRENTAUTHORISEDPAGES)$')
PAGES = re.compile(r'^(Current authorised pages|Pages Authorised\b.*|\(inclusive\).*|Pages|Authorised|by L\.R\.O\.?|'
                   r'\d+ ?- ?\d+( (\.\.|\d+/\d{4}))?( \d+ ?- ?\d+( (\.\.|\d+/\d{4}))?)*)$', re.I)
HEADER = re.compile(r'^\s*\d{1,4}\s*$|Chap\.\s*\d|No\.\s*\d+\s+of\s+\d{4}|\[Subsidiary\]')
# Scanned older editions (an OCR text layer, no fonts): the running header is the top row of a page that holds a page
# number or a chapter reference ("782  Ch. 39. No. 8.]  San Fernando Recreation Ground."), within the top 13%.
SCAN_HEADER = re.compile(r'^\[?\s*\d{1,4}\s*[\]J]?\.?$|\b(?:Ch|CAP|Cap|Chap)\s*\.\s*[\d:]|\bNo\.\s*\d+\s*\.?\s*[\]J]'
                         r'|^\d{1,4}\s+[A-Z]|[a-z.]\s+\d{1,4}$')
LIMIT = 0.01


def words(text: str) -> Counter:
    t = text.lower().replace('­', '')
    return Counter(WORD.findall(t))


def scan_words(doc) -> Counter:
    """A scanned edition's OCR text layer: every line except the publisher's stamps and the running-header rows."""
    out = Counter()
    for page in doc:
        rows: list[list] = []
        for b in page.get_text('dict')['blocks']:
            for ln in b.get('lines', []):
                text = ''.join(s['text'] for s in ln['spans'])
                if text.strip():
                    rows.append([ln['bbox'][1], text, ln['bbox'][0]])
        rows.sort(key=lambda r: r[0])
        grouped: list[list] = []
        for y, text, x in rows:
            if grouped and abs(grouped[-1][-1][0] - y) <= 4:
                grouped[-1].append((y, text, x))
            else:
                grouped.append([(y, text, x)])
        top = page.rect.height * 0.13
        for k, g in enumerate(grouped):
            # header rows: among the first three, each judged on its whole text
            text = re.sub(r'\s+', ' ', ' '.join(t for _, t, _ in sorted(g, key=lambda r: r[2]))).strip()
            if k < 3 and g[0][0] <= top and (SCAN_HEADER.search(text) or STAMP.match(re.sub(r'\s+', '', text).upper())):
                continue
            for _, t, _ in g:
                if STAMP.match(re.sub(r'\s+', '', t).upper()):
                    continue
                # the authorised-pages table is on the cover; elsewhere "21 - 25" is a table row (pension ages)
                if page.number == 0 and PAGES.match(re.sub(r'\s+', ' ', t.replace('–', '-')).strip()):
                    continue
                out += words(t)
    return out


def pdf_words(path: str, scan: bool = False) -> Counter:
    sys.modules.setdefault('pymupdf.layout', None)
    import pymupdf
    doc = pymupdf.open(path)
    if scan:
        return scan_words(doc)
    out = Counter()
    for page in doc:
        for b in page.get_text('dict')['blocks']:
            for ln in b.get('lines', []):
                spans = [s for s in ln['spans'] if s['text'].strip()]
                if not spans:
                    continue
                text = ''.join(s['text'] for s in spans)
                size = max(s['size'] for s in spans)
                y = ln['bbox'][1]
                key = re.sub(r'\s+', '', text).upper()
                if size > 40 or (STAMP.match(key) and (y < 135 or y > 640 or page.number == 0)):
                    continue
                italic = 'Italic' in spans[0]['font'] or bool(spans[0]['flags'] & 2)
                if size >= 9 and ((y < 120 and page.number > 0) or (y < 128 and (HEADER.search(text) or italic))):
                    continue  # the running header band (the body of a 2016 page can start at y=123)
                if PAGES.match(re.sub(r'\s+', ' ', text.replace('–', '-')).strip()):
                    continue  # the cover's table of authorised pages, left out by design
                out += words(text)
    return out


def repo_words(texts: list[str]) -> Counter:
    out = Counter()
    for t in texts:
        t = re.sub(r'^- Margin: ', '', t, flags=re.M)
        t = re.sub(r'^#+ ', '', t, flags=re.M)
        out += words(t)
    return out


def check_one(job: tuple) -> dict:
    law, version, download, texts, pdf, scan = job
    a = pdf_words(pdf, scan)
    b = repo_words(texts)
    # The verdict is on letters and digits, counted one by one: plain extraction runs the words of letter-spaced
    # lines together ("caribbeancommunity"), so word counts alone overstate differences. Words are kept to show
    # what differs.
    ca, cb = Counter(), Counter()
    for w, n in a.items():
        for ch in w:
            ca[ch] += n
    for w, n in b.items():
        for ch in w:
            cb[ch] += n
    total = sum(ca.values()) or 1
    cm, ce = sum((ca - cb).values()), sum((cb - ca).values())
    missing = a - b
    extra = b - a
    return {'law': law, 'version': version, 'download': download, 'pdf_words': sum(a.values()),
            'pdf_chars': sum(ca.values()), 'missing_chars': cm, 'extra_chars': ce,
            'missing': sum(missing.values()), 'extra': sum(extra.values()),
            'rate': round(max(cm, ce) / total, 5),
            'top_missing': ' '.join(w for w, _ in missing.most_common(8)),
            'top_extra': ' '.join(w for w, _ in extra.most_common(8))}


def worker(k: int, n: int) -> None:
    import json
    tmp = HERE / '.cache' / 'check_words'
    jobs = json.loads((tmp / 'jobs.json').read_text('utf-8'))[k::n]
    (tmp / f'res-{k}.json').write_text(json.dumps([check_one(tuple(j)) for j in jobs]), 'utf-8')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('repo', type=Path)
    ap.add_argument('--pdf-dir', type=Path, default=HERE / '.cache' / 'pdf')
    ap.add_argument('--limit', type=int)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--out', type=Path, default=HERE / '.cache' / 'check_words.csv')
    args = ap.parse_args()
    git = lambda *a: subprocess.run(['git', '-C', str(args.repo), *a], capture_output=True,  # noqa: E731
                                    encoding='utf-8', errors='replace').stdout
    rows = list(csv.DictReader(io.StringIO(git('show', 'HEAD:data/versions.csv'))))
    laws = {r['law']: r['path'].rstrip('/') for r in csv.DictReader(io.StringIO(git('show', 'HEAD:laws.csv')))}
    # per law folder: [(date, commit)] in history order
    hist: dict[str, list] = {}
    log = git('log', '--first-parent', '--reverse', '--format=%x1e%H %(trailers:key=In-force,valueonly,separator=)',
              '--name-only', 'HEAD')
    for rec in log.split('\x1e'):
        head, _, names = rec.partition('\n')
        parts = head.split()
        if len(parts) < 2:
            continue
        for d in {'/'.join(n.split('/')[:2]) for n in names.split() if n.count('/') >= 2}:
            hist.setdefault(d, []).append((parts[1], parts[0]))
    cat = subprocess.Popen(['git', '-C', str(args.repo), 'cat-file', '--batch'], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE)

    def blob(spec: str) -> str:
        cat.stdin.write(spec.encode('utf-8') + b'\n')
        cat.stdin.flush()
        head = cat.stdout.readline().split()
        if len(head) < 3:
            return ''
        data = cat.stdout.read(int(head[2]))
        cat.stdout.read(1)
        return data.decode('utf-8', 'replace')

    jobs = []
    for r in rows[:args.limit] if args.limit else rows:
        d = laws[r['law']]
        commit = None
        for date, h in hist.get(d, []):
            if date <= r['date']:
                commit = h
        if not commit:
            continue
        names = blob(f'{commit}:{d}/index.txt').split()
        texts = [blob(f'{commit}:{d}/{n}') for n in names]
        jobs.append((r['law'], r['version'], r['download'], texts, str(args.pdf_dir / f"{r['download']}.pdf"),
                     r['date_source'] == 'as-at-month'))
    cat.stdin.close()
    cat.wait()
    # plain worker processes over a job file (multiprocessing pools break on Windows here)
    import json
    tmp = HERE / '.cache' / 'check_words'
    tmp.mkdir(exist_ok=True)
    (tmp / 'jobs.json').write_text(json.dumps(jobs), 'utf-8')
    n = args.workers
    procs = [subprocess.Popen([sys.executable, '-X', 'utf8', '-W', 'ignore', '-c',
                               f'import check_words; check_words.worker({k}, {n})'], cwd=HERE,
                              stdin=subprocess.DEVNULL) for k in range(n)]
    for p in procs:
        p.wait()
    res = []
    for k in range(n):
        res += json.loads((tmp / f'res-{k}.json').read_text('utf-8'))
    res.sort(key=lambda x: (x['law'], x['version']))
    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(res[0]))
        w.writeheader()
        w.writerows(res)
    bad = [x for x in res if x['rate'] > LIMIT]
    tot = sum(x['pdf_words'] for x in res)
    tc = sum(x['pdf_chars'] for x in res)
    mc, ec = sum(x['missing_chars'] for x in res), sum(x['extra_chars'] for x in res)
    print(f"{len(res)} versions, {tc} PDF letters and digits; missing {mc} ({mc / max(tc, 1):.4%}), "
          f"extra {ec} ({ec / max(tc, 1):.4%}); {len(bad)} versions over {LIMIT:.0%} (details in {args.out})")
    for x in sorted(bad, key=lambda x: -x['rate'])[:15]:
        print(f"  {x['law']} {x['version']} rate {x['rate']} missing: {x['top_missing']} | extra: {x['top_extra']}")
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
