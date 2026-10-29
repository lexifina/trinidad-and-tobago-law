# Reproducing this repository

Everything here comes from laws.gov.tt and can be rebuilt from it. The same PDFs give the same commit hashes.

## What this build used

- Built on {{TODAY}} from {{LAWS}} laws ({{CHAPTERS}} Chapters, {{ACTS}} Acts) and {{VERSIONS}} versions ({{PDFS}} PDFs). Catalogue retrieved {{RETRIEVED}}.
- {{COMMITS}} commits: {{CONSOLIDATED}} consolidated (first versions), {{AMENDMENT}} amendment, {{CONSOLIDATION}} consolidation (uncredited), and this documentation commit.
- Recent Updates dated by: `{{UPDATE_DATE}}`.
- sha256 of every PDF: `data/pdf-sha256.tsv`; of the catalogue the build read (`catalogue.json`, every Chapter's list of versions and the Recent Updates list): `{{SHA_CATALOGUE}}`. Versions not used, and why: `data/issues.csv` ({{ISSUES}}).
- Build scripts (sha256), copied to `tools/build/`:
  - `parse_pdf.py` {{SHA_PARSE_PDF_PY}}
  - `build.py` {{SHA_BUILD_PY}}
  - `docs.py` {{SHA_DOCS_PY}}
  - `check_words.py` {{SHA_CHECK_WORDS_PY}}

## Steps

Python 3.11+ with `pymupdf`, and `git` on the path. How the files were retrieved is not part of this record. With the retrieved catalogue (`catalogue.json`) and PDFs (`pdf/<download>.pdf`, each matching its sha256 in `data/pdf-sha256.tsv`) in the folder build.py reads (`CACHE`):

```sh
cd tools/build
python build.py ../../../trinidad-and-tobago-law-rebuilt --today {{TODAY}} --update-date {{UPDATE_DATE}}
python check_words.py ../../../trinidad-and-tobago-law-rebuilt   # letters-and-digits check against the PDFs
```

`--today` dates the documentation commit and is required, so a rebuild never depends on the day it is run. `--update-date pdf-created|retrieved` chooses how the undated Recent Updates are dated (see README).

## Decisions

- **Which versions:** the dated year-end consolidations of 2004-2016 (labels "as at December 31st <year>"), then the Chapter's Recent Update if it has one; before them, the older Revised Editions (labels "as at June 1925 1925 Revised Edition", "as at January 1941 1940 ...", "as at December 1950 1950 ...", "as at December 1990 1980 ...", "as at December 1902 1902 ..."). The older ones are scans: their OCR text layer (made by the publisher) is used as published; a scan with no text layer is not OCR'd and is listed in `data/issues.csv`, and so is one that prints a readable title of its own with no word close to the law's name (equal, a shared five-letter start, or an OCR-alike spelling), because laws.gov.tt lists some other laws as older editions of a Chapter (the Judicature Ordinance under Judges Salaries and Pensions, Poor Relief under Public Assistance). Chapter numbers are not compared in the scans (OCR misreads them).
- **Units:** a section starts with its number ("12A.") at the paragraph indent and must follow the one before (12 -> 13, 12 -> 12A, gaps up to 40 for repeals). Inside a schedule, numbers are the schedule's own. Subsidiary legislation starts after "SUBSIDIARY LEGISLATION"; each instrument starts at a "1." after its arrangement table or one that cites its title.
- **Margin notes** belong to the unit that starts nearest at or above them on the page.
- **Text repairs:** CID control characters mapped to quotes and dashes; capitals encoded as lower case read back from glyph widths (base-14 Times metrics); whitespace, curly quotes, dashes, soft hyphens and the length of dot leaders normalised, so typesetting alone never makes a change. The cover's table of authorised pages is left out. A version is skipped (listed in `data/issues.csv`) when its download is not a PDF or prints another Chapter's number. In the scans the margin column is found by position (the gutter: an empty vertical strip between notes and body, found from words of three or more letters and digits), running headers are the top rows (13% of the page) that hold a page number or chapter reference, and an OCR-misread section number ("s." for 5) counts only as the number expected next. A file whose text differs only in spacing keeps the earlier text only between two versions of the same kind (scan to scan, typeset to typeset).
- **Crediting:** only a single law newly named in the changed unit's own margin notes, made no earlier than the year of the previous consolidation. Otherwise the Law Revision Commission, `Kind: consolidation`.
- **Dates:** noon Trinidad time (UTC-4, no daylight saving) on the as-at date (for the older editions, the last day of the as-at month; before 1970, 1970-01-01 one second apart, with the real day in `In-force:`); Recent Updates by PDF creation date or retrieval day (`--update-date`). On one date: first versions, then credited changes by law, then uncredited ones; laws in folder order.

## AI

The scripts, the README and these notes were written by Claude Code with Claude Opus 5.5 (`claude-opus-5-5`), working for Lexifina. No AI model writes or changes legal text, and none runs when the repository is built or checked: the build is the Python in `tools/build/`, run as recorded here.
