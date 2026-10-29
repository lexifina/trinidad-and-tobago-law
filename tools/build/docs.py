"""README, REPRODUCE.md, SOURCES.md, LICENSE, corpus.json, laws.csv, data/ and tools for the Trinidad and Tobago law
repository (called by build.py)."""
import csv
import hashlib
import io
import json
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
REPO_FILES = HERE / 'repo'
CACHE = HERE / '.cache'
# Published with the record. The retrieval script and its notes stay private (the user's rule of 2026-10-29), and
# publish_gate (gitlaw_common, private) checks every file before it is written.
BUILD_FILES = ('parse_pdf.py', 'build.py', 'docs.py', 'check_words.py')
sys.path.insert(0, str(HERE.parent / 'gitlaw_common'))
try:
    from publish_gate import publish_gate
except ImportError:          # an outside reader rebuilding from the published tools: no private rule to apply
    if os.environ.get('GITLAW_PUBLIC_REBUILD') != '1':
        raise SystemExit('publish gate missing: run from lexifina/scripts, or set GITLAW_PUBLIC_REBUILD=1')

    def publish_gate(files): return files


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _csv(rows: list[list]) -> bytes:
    out = io.StringIO()
    w = csv.writer(out, lineterminator='\n')
    for r in rows:
        w.writerow(r)
    return out.getvalue().encode('utf-8')


def pdf_sums(ids: list[str]) -> str:
    """sha256 of every PDF the build read; remembered by (size, mtime) in pdf-sha256.json next to the PDFs' folder."""
    store = CACHE / 'pdf-sha256.json'
    try:
        known = json.loads(store.read_text('utf-8'))
    except (OSError, json.JSONDecodeError):
        known = {}
    def one(d: str) -> tuple[str, str]:
        p = CACHE / 'pdf' / f'{d}.pdf'
        st = os.stat(p)
        k = f'{st.st_size}:{int(st.st_mtime)}'
        if known.get(d, {}).get('k') == k:
            return d, known[d]['sha']
        return d, _sha(p)

    sums = dict(one(d) for d in ids)
    for d, h in sums.items():
        st = os.stat(CACHE / 'pdf' / f'{d}.pdf')
        known[d] = {'k': f'{st.st_size}:{int(st.st_mtime)}', 'sha': h}
    store.write_text(json.dumps(known, sort_keys=True), 'utf-8')
    return ''.join(f'{d}.pdf\t{sums[d]}\n' for d in sorted(ids, key=int))


def render(laws: list[dict], commits: list[dict], issues: list[dict], ledger: list[list], today: str,
           update_date: str, retrieved: str) -> dict[str, bytes]:
    kinds = Counter(c['kind'] for c in commits)
    built = [l for l in laws if l.get('built_versions')]
    chapters = sum(1 for l in built if l['kind'] == 'chapter')
    acts = sum(1 for l in built if l['kind'] == 'act')
    versions = sum(len(l['built_versions']) for l in built)
    editions = Counter(v['date'][:4] for l in built for v in l['built_versions'] if v['kind'] == 'edition')
    old = Counter((v['date'], f"{v['revised']} Revised Edition as at {v['as_at']}")
                  for l in built for v in l['built_versions'] if v['kind'] == 'old')
    scan_only = sum(1 for i in issues if i['issue'].startswith('scan only'))
    updates = [v for l in built for v in l['built_versions'] if v['kind'] == 'update']
    upd_days = sorted(v['date'] for v in updates)
    dates = sorted(c['date'] for c in commits)
    authors = {c['author'] for c in commits if c['kind'] == 'amendment'}
    credited_files = sum(len(c['changes']) for c in commits if c['kind'] == 'amendment')
    uncredited_files = sum(len(c['changes']) for c in commits if c['kind'] == 'consolidation')
    ids = sorted({v['download'] for l in built for v in l['built_versions']}, key=int)

    laws_csv = _csv([['law', 'kind', 'name', 'classification', 'year', 'versions', 'first_version', 'last_version',
                      'last_version_label', 'path']] +
                    [[l['label'], l['kind'], l['name'], l['classification'], l['year'], len(l['built_versions']),
                      l['built_versions'][0]['date'], l['built_versions'][-1]['date'], l['built_versions'][-1]['label'],
                      l['dir'] + '/'] for l in built])
    versions_csv = _csv([['law', 'version', 'date', 'date_source', 'pdf_created', 'download', 'source']] +
                        [[l['label'], v['label'], v['date'], v['date_source'], v.get('created', ''), v['download'],
                          f"https://laws.gov.tt/ttdll-web/revision/download/{v['download']}?type={v['type']}"]
                         for l in built for v in l['built_versions']])
    ledger_csv = _csv([['law', 'file', 'cited_law', 'first_shown', 'version']] + sorted(ledger))
    issues_csv = _csv([['law', 'version', 'download', 'issue']] +
                      [[i['law'], i['version'], i['download'], i['issue']] for i in issues])

    stats = {
        'today': today, 'laws': len(built), 'chapters': chapters, 'acts': acts, 'versions': versions,
        'commits': len(commits) + 1, 'consolidated': kinds['consolidated'], 'amendment': kinds['amendment'],
        'consolidation': kinds['consolidation'], 'amending_laws': len(authors), 'credited_files': credited_files,
        'uncredited_files': uncredited_files, 'first': dates[0] if dates else '', 'last': dates[-1] if dates else '',
        'issues': len(issues), 'updates': len(updates), 'update_first': upd_days[0] if upd_days else '',
        'update_last': upd_days[-1] if upd_days else '', 'update_date': update_date, 'retrieved': retrieved,
        'pdfs': len(ids), 'ledger_rows': len(ledger),
        'editions': ', '.join(f'{y} ({n})' for y, n in sorted(editions.items())),
        'earliest': kinds['earliest'], 'first_versions': kinds['consolidated'] + kinds['earliest'],
        'old_versions': sum(old.values()), 'scan_only': scan_only,
        'old_editions': ', '.join(f'{name} ({n})' for (_, name), n in sorted(old.items())) or 'none',
    }
    sub = lambda t: _fill(t, stats)  # noqa: E731
    readme = sub((REPO_FILES / 'README.md').read_text('utf-8'))
    reproduce = sub((REPO_FILES / 'REPRODUCE.md').read_text('utf-8'))
    for name in BUILD_FILES:
        reproduce = reproduce.replace('{{SHA_' + name.upper().replace('.', '_') + '}}', _sha(HERE / name))
    reproduce = reproduce.replace('{{SHA_CATALOGUE}}', _sha(CACHE / 'catalogue.json'))
    sources = sub((REPO_FILES / 'SOURCES.md').read_text('utf-8'))

    corpus = {
        'corpus': 'tt/national/acts',
        'name': 'Laws of Trinidad and Tobago (Chapters, their subsidiary legislation, and Acts not yet given a Chapter)',
        'label': 'Trinidad and Tobago',
        'language': 'en',
        'history': 'in-force',
        'history_from': stats['first'],
        'record_to': stats['last'],
        'record_note': (f"Every Chapter on laws.gov.tt ({chapters}) and {acts} Acts not yet in a Chapter, as the "
                        f"year-end consolidations as at 31 December 2004-2016 and the undated Recent Updates show them "
                        f"(updates dated by {'PDF creation date' if update_date == 'pdf-created' else 'retrieval day'}), "
                        f"and before 2004, for {stats['old_versions']} versions, the older Revised Editions (1902, 1925, "
                        f"1940, 1950, 1980 as at 1990; scans, their OCR text layer as published, dated the last day of "
                        f"the as-at month); a change appears at the first consolidation that shows it, not on its "
                        f"commencement day. "
                        f"Catalogue retrieved {retrieved}; built {today}."),
        'checked_on': retrieved,
        'in_force_trailer': 'In-force',
        'baseline_trailer': 'Consolidated',
        'has_future_branch': False,
        'laws': {'chapters': chapters, 'acts': acts},
        'built': today,
        'dates': {'commit': 'as-at date of the consolidation that first shows the text (in force on or before it)',
                  'basis_trailer': 'In-force-basis', 'source_trailer': 'Date-source',
                  'undated_updates': update_date, 'time': '12:00 America/Port_of_Spain (UTC-4)',
                  'older_editions': 'dated the last day of the as-at month (the labels give no day)',
                  'before_1970': '1970-01-01, one second apart in history order; In-force holds the real day'},
        'author': {'amendment': 'the Act or Legal Notice newly named in the changed unit\'s margin notes',
                   'consolidated': 'Law Revision Commission (laws.gov.tt)',
                   'earliest_older_edition': 'Law Revision Commission (laws.gov.tt), Kind: consolidation',
                   'consolidation': 'Law Revision Commission (laws.gov.tt)', 'evidence_trailer': 'Evidence'},
        'scope': {
            'trailer': 'Applies',
            'when_absent': 'not extracted; savings and transitional rules are in the amending laws themselves',
            'default_reach': {
                'rule': 'repeal does not affect rights accrued or proceedings pending unless the law says so',
                'meaning': 'the savings rules of the Interpretation Act on the effect of repeal and amendment',
                'authority': 'Interpretation Act (Chap. 3:01), section 27',
                'decided_here': False,
            },
        },
        'citation': {'file': r'(.+)/s-0*([0-9]+[A-Z]*)\.md',
                     'cites': r'([Ss]ection|s\.) ?{n}([^0-9A-Za-z]|$)'},
        'tool': 'tools/in_force_on.py',
    }

    files = {
        'corpus.json': (json.dumps(corpus, indent=2, ensure_ascii=False) + '\n').encode('utf-8'),
        'README.md': readme.encode('utf-8'),
        'REPRODUCE.md': reproduce.encode('utf-8'),
        'SOURCES.md': sources.encode('utf-8'),
        'LICENSE': (REPO_FILES / 'LICENSE').read_bytes(),
        'laws.csv': laws_csv,
        'data/versions.csv': versions_csv,
        'data/newly-cited.csv': ledger_csv,
        'data/issues.csv': issues_csv,
        'data/stats.json': (json.dumps(stats, indent=1, sort_keys=True) + '\n').encode('utf-8'),
        'data/pdf-sha256.tsv': pdf_sums(ids).encode('utf-8'),
        'tools/in_force_on.py': (REPO_FILES / 'tools' / 'in_force_on.py').read_bytes(),
    }
    for name in BUILD_FILES:
        files[f'tools/build/{name}'] = (HERE / name).read_bytes()
    for name in ('README.md', 'REPRODUCE.md', 'SOURCES.md', 'LICENSE'):
        files[f'tools/build/repo/{name}'] = (REPO_FILES / name).read_bytes()
    return publish_gate(files)


def _fill(t: str, stats: dict) -> str:
    for k, v in stats.items():
        t = t.replace('{{' + k.upper() + '}}', str(v))
    return t
