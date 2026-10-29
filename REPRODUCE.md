# Reproducing this repository

Everything here comes from laws.gov.tt and can be rebuilt from it. The same PDFs give the same commit hashes.

## What this build used

- Built on 2026-10-29 from 559 laws (533 Chapters, 26 Acts) and 4659 versions (4659 PDFs). Catalogue retrieved 2026-10-28.
- 3109 commits: 202 consolidated (first versions), 999 amendment, 1550 consolidation (uncredited), and this documentation commit.
- Recent Updates dated by: `pdf-created`.
- sha256 of every PDF: `data/pdf-sha256.tsv`; of the catalogue the build read (`catalogue.json`, every Chapter's list of versions and the Recent Updates list): `2050999cfd10fa67d611bb6c67d0a2d39eb20716f66de086efd799825236f121`. Versions not used, and why: `data/issues.csv` (74).
- Build scripts (sha256), copied to `tools/build/`:
  - `parse_pdf.py` e3c383971262b1748507cfb12315a58002b4eab26d5103759755c122c57d29e6
  - `build.py` f95da2f2d82defa9edd4821d907c491780dc304aa86eb9b08a4d1b157edc613a
  - `docs.py` ab3e5e74a72c4f2ade5c7b9037289b53939228feffed190ffaa62dfe488f828f
  - `check_words.py` 1e0883878182dcb57ec607b8050539b8d529ba2ca70049d33066c1c086c997cf

## Steps

Python 3.11+ with `pymupdf`, and `git` on the path. How the files were retrieved is not part of this record. With the retrieved catalogue (`catalogue.json`) and PDFs (`pdf/<download>.pdf`, each matching its sha256 in `data/pdf-sha256.tsv`) in the folder build.py reads (`CACHE`):

```sh
cd tools/build
python build.py ../../../trinidad-and-tobago-law-rebuilt --today 2026-10-29 --update-date pdf-created
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
