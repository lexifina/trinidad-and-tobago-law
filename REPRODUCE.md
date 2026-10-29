# Reproducing this repository

Everything here comes from laws.gov.tt and can be rebuilt from it. The same PDFs give the same commit hashes.

## What this build used

- Built on 2026-10-29 from 559 laws (533 Chapters, 26 Acts) and 3777 versions (3777 PDFs). Catalogue retrieved 2026-10-28.
- 1736 commits: 559 consolidated (first versions), 508 amendment, 668 consolidation (uncredited), and this documentation commit.
- Recent Updates dated by: `pdf-created`.
- sha256 of every PDF: `data/pdf-sha256.tsv`. Versions not used, and why: `data/issues.csv` (12).
- Build scripts (sha256), copied to `tools/build/`:
  - `fetch.py` ae421360932b494f98645822ee0f09f0fc58469d3baddaece94a2236c452719c
  - `parse_pdf.py` b6695c4b253cc467ef2eaa57250013a3790156178be2979bf265b225d0ad4c3a
  - `build.py` c93b4171d44352b54ad1ad9609f1b3b569469fb8ac821e46423efb938ffd9f66
  - `docs.py` 793e7a7ba80b9622aa24e6f97e8dc18fa9e3ae55b3e0fe121a1a7b73167d6759
  - `check_words.py` ed94e5e2ce7707b63896d4a911158ee8686759f3b0403593a90113186019c6af

## Steps

Python 3.11+ with `pymupdf`, and `curl` and `git` on the path.

```sh
cd tools/build
python fetch.py catalogue    # .cache/catalogue.json: every Chapter page, the Recent Updates list
python fetch.py pdfs         # the current PDF of each Chapter (Recent Update, else as at 2016)
python fetch.py history      # every year-end consolidation, as at 31 December 2004 to 2016
python build.py ../../../trinidad-and-tobago-law-rebuilt --today 2026-10-29 --update-date pdf-created
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
