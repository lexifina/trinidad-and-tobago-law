# Reproducing this repository

Everything here comes from laws.gov.tt and can be rebuilt from it. The same PDFs give the same commit hashes.

## What this build used

- Built on {{TODAY}} from {{LAWS}} laws ({{CHAPTERS}} Chapters, {{ACTS}} Acts) and {{VERSIONS}} versions ({{PDFS}} PDFs). Catalogue retrieved {{RETRIEVED}}.
- {{COMMITS}} commits: {{CONSOLIDATED}} consolidated (first versions), {{AMENDMENT}} amendment, {{CONSOLIDATION}} consolidation (uncredited), and this documentation commit.
- Recent Updates dated by: `{{UPDATE_DATE}}`.
- sha256 of every PDF: `data/pdf-sha256.tsv`. Versions not used, and why: `data/issues.csv` ({{ISSUES}}).
- Build scripts (sha256), copied to `tools/build/`:
  - `fetch.py` {{SHA_FETCH_PY}}
  - `parse_pdf.py` {{SHA_PARSE_PDF_PY}}
  - `build.py` {{SHA_BUILD_PY}}
  - `docs.py` {{SHA_DOCS_PY}}
  - `check_words.py` {{SHA_CHECK_WORDS_PY}}

## Steps

Python 3.11+ with `pymupdf`, and `curl` and `git` on the path.

```sh
cd tools/build
python fetch.py catalogue    # .cache/catalogue.json: every Chapter page, the Recent Updates list
python fetch.py pdfs         # the current PDF of each Chapter (Recent Update, else as at 2016)
python fetch.py history      # every year-end consolidation, as at 31 December 2004 to 2016
python build.py ../../../trinidad-and-tobago-law-rebuilt --today {{TODAY}} --update-date {{UPDATE_DATE}}
python check_words.py ../../../trinidad-and-tobago-law-rebuilt   # letters-and-digits check against the PDFs
```

`--today` dates the documentation commit and is required, so a rebuild never depends on the day it is run. `--update-date pdf-created|retrieved` chooses how the undated Recent Updates are dated (see README).

## Fetch rate

laws.gov.tt has no robots.txt (404) and no Crawl-delay. Everything was fetched with one request at a time, cached on disk, so each page and PDF was fetched once: the catalogue (about 540 pages) and about 3,900 PDFs on 28-29 October 2026, at roughly one PDF per second. A rebuild from the cache makes no requests.

## Decisions

- **Which versions:** the dated year-end consolidations of 2004-2016 (labels "as at December 31st <year>"), then the Chapter's Recent Update if it has one. Earlier Revised Editions are not used.
- **Units:** a section starts with its number ("12A.") at the paragraph indent and must follow the one before (12 -> 13, 12 -> 12A, gaps up to 40 for repeals). Inside a schedule, numbers are the schedule's own. Subsidiary legislation starts after "SUBSIDIARY LEGISLATION"; each instrument starts at a "1." after its arrangement table or one that cites its title.
- **Margin notes** belong to the unit that starts nearest at or above them on the page.
- **Text repairs:** CID control characters mapped to quotes and dashes; capitals encoded as lower case read back from glyph widths (base-14 Times metrics); whitespace, curly quotes, dashes, soft hyphens and the length of dot leaders normalised, so typesetting alone never makes a change. The cover's table of authorised pages is left out. A version is skipped (listed in `data/issues.csv`) when its download is not a PDF or prints another Chapter's number.
- **Crediting:** only a single law newly named in the changed unit's own margin notes, made no earlier than the year of the previous consolidation. Otherwise the Law Revision Commission, `Kind: consolidation`.
- **Dates:** noon Trinidad time (UTC-4, no daylight saving) on the as-at date; Recent Updates by PDF creation date or retrieval day (`--update-date`). On one date: first versions, then credited changes by law, then uncredited ones; laws in folder order.
