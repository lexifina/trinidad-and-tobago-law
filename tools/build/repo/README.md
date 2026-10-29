# Laws of Trinidad and Tobago, consolidation by consolidation

The Laws of Trinidad and Tobago as a git repository: {{CHAPTERS}} Chapters, each with its subsidiary legislation, and {{ACTS}} Acts not yet given a Chapter number, from [laws.gov.tt](https://laws.gov.tt), the Digital Legislative Library of the Law Revision Commission (Office of the Attorney General and Ministry of Legal Affairs). There is one file per section, schedule and regulation, one paragraph per line.

**What kind of history this is.** laws.gov.tt keeps each Chapter as a series of dated consolidations of the 2006 Revised Edition: as at 31 December 2004, 2007, 2009, 2012, 2014 and 2016 (and 2013 for a few Chapters), plus an unofficial update as at 31 December 2015. Each is a commit here, dated by its as-at date. So this is a real history, but a coarse one: a change shows up at the first year-end consolidation that contains it, which can be up to three years after it took effect.

**Before 2004: the older Revised Editions.** For many Chapters laws.gov.tt also keeps the earlier official Revised Editions: 1925 (as at June 1925), 1940 (as at January 1941), 1950 (as at December 1950) and 1980 (as at December 1990), and one 1902 Ordinance. These are page scans with an OCR text layer the publisher added; the repository takes that text layer as published, OCR errors included (`Text-layer:` trailer), and each edition is a commit before the 2004 consolidation (`Kind: consolidation`). Scans with no text layer are not OCR'd here; they are listed in [`data/issues.csv`](data/issues.csv). Older editions used: {{OLD_EDITIONS}}; {{SCAN_ONLY}} scan-only editions left out. Because the older text is OCR, a difference between an older edition and the next version can be an OCR error rather than a change in the law; the commit message says so. There is no line-by-line history before each law's first version here; each section keeps the history printed in its margin.

The record runs from {{FIRST}} to {{LAST}} in {{COMMITS}} commits, built from {{VERSIONS}} versions ({{PDFS}} PDFs). Consolidations per year from 2004: {{EDITIONS}}. Recent Updates: {{UPDATES}}.

## A lawyer's questions as git commands

| Question | Command |
| --- | --- |
| What did section 5 of the Widows' and Orphans' Pensions Act (Chap. 23:54) say on 1 June 2010? | `python tools/in_force_on.py 2010-06-01 chapters/23-54 s-5` |
| The whole of a Chapter on a date | `python tools/in_force_on.py 2010-06-01 chapters/23-54` |
| Which consolidation, or which law, last changed each line? | `git blame chapters/23-54/s-5.md` |
| Every change to a section | `git log -p chapters/23-54/s-5.md` |
| Everything credited to one Act | `git log --author='Act No. 2 of 2015' --stat` |
| Changes no law is credited with | `git log --grep='Kind: consolidation'` |
| The list of laws, and every version used | [`laws.csv`](laws.csv), [`data/versions.csv`](data/versions.csv) |

Folders: `chapters/<chapter>-<number>/` (Chap. 23:54 is `chapters/23-54/`), and `acts/<year>-<number>/` for Acts listed only under Recent Updates. In each: `title.md` (the cover with its "Amended by" list, notes, the arrangement of sections and the long title), `s-<n>.md` per section, a file per schedule, `sl-01/`, `sl-02/`... per piece of subsidiary legislation in the order printed (with `r-<n>.md` per regulation, rule or paragraph), and `index.txt`, the files in printed order.

A section file reads `# 5. Method of computing pensions. [17 of 2007 30 of 2007 1 of 2009].`: the number, then the first margin note (the marginal heading, with the enacting and amending laws as printed). Part headings above it are `##` lines. Other margin notes (cross references such as `Ch. 23:57.`, more history) are `- Margin:` lines at the end.

## The dates

- **Consolidations:** dated by their as-at date, at noon Trinidad time (UTC-4). `In-force:` is that date. It is the day the text was in force, not the day each change took effect: `In-force-basis:` says so on every commit, and `Date-source: as-at`.
- **Older Revised Editions:** their labels give only a month ("as at June 1925"), so each is dated the month's last day (30 June 1925, 31 January 1941, 31 December 1950, 31 December 1990, 31 December 1902; `Date-source: as-at-month`). Git cannot store a date before 1970: commits before then are dated 1970-01-01, one second apart in history order, and `In-force:` holds the real day (`Date-note:` trailer). The 1990 commits are at noon Trinidad time like the rest.
- **Recent Updates (open decision).** laws.gov.tt lists about 190 Chapters and the Acts above under "Recent Updates" (L.R.O. 1/2023 and similar), unofficial and **with no as-at date**. How to date them has not been decided. This build ({{UPDATE_DATE}}) dates each one by **its PDF's creation date** (`Date-source: pdf-created`; here from {{UPDATE_FIRST}} to {{UPDATE_LAST}}), the closest thing to a date the publisher gives. Rebuilding with `--update-date retrieved` dates them all by the day the catalogue was retrieved ({{RETRIEVED}}) instead (`Date-source: retrieved`). Either way, a change first shown in an update was in force by that date, perhaps long before.
- `tools/in_force_on.py` reads `In-force:`, so "on a date" means "in the latest consolidation dated on or before it".

## What "author" means

A change between two consolidations is credited to a law **only when the margin notes of the changed unit newly name exactly one law**, made no earlier than the year of the consolidation before: for example section 5 gains `*2 of 2015` between 2014 and 2016, so the change is by `Act No. 2 of 2015 <act-2015-2@laws-gov-tt.invalid>` (`Kind: amendment`, `Evidence: margin note`). Legal Notices are `Legal Notice No. 51 of 1980`. The commit is still dated by the consolidation, not by the law's commencement.

Every other change, where the margin names no new law or more than one, stays with the **Law Revision Commission** (`Kind: consolidation`); the laws newly named anywhere in that Chapter are listed as `Newly-cited:` candidates, never credited. The first version of each law is by the Commission too: `Kind: consolidated` when it is a consolidation from 2004 on, `Kind: consolidation` when it is an older Revised Edition. The same rule credits changes between the older editions and into 2004 (a law made no earlier than the year of the edition before).

In this build: {{FIRST_VERSIONS}} first versions ({{CONSOLIDATED}} from 2004 on, {{EARLIEST}} from an older Revised Edition), {{AMENDMENT}} commits credited to {{AMENDING_LAWS}} laws ({{CREDITED_FILES}} files), and {{CONSOLIDATION}} uncredited consolidation commits ({{UNCREDITED_FILES}} files). Every law newly named in a margin, and where it first appears, is in [`data/newly-cited.csv`](data/newly-cited.csv).

## What it does not show

- The day each change took effect; a change appears at the first year-end consolidation (or update) that contains it.
- Text before each law's first version here (the earliest older Revised Edition on laws.gov.tt, else mostly 31 December 2004). The original Acts and Ordinances on laws.gov.tt are not used, nor older editions that are scans without a text layer, or whose own title is another law's (laws.gov.tt lists, for example, the Judicature Ordinance as an older edition of Judges Salaries and Pensions, and Poor Relief of Public Assistance; listed in `data/issues.csv`).
- Corrected OCR: the older editions' text is the publisher's OCR as published ("1neans" for "means" and the like).
- Running headers, and the cover's table of current authorised pages (print bookkeeping that changes with every reprint). Quotes and dashes are normalised to `'`, `"` and `-`, and the dot leaders of form blanks to `...`. Footnotes are kept as lines of the unit they fall in.
- Versions that could not be fetched or used ({{ISSUES}}, in [`data/issues.csv`](data/issues.csv)). A few downloads serve another Chapter's PDF (the 2009 "Prevention of Corruption Act" download is the Larceny Act), one is an HTML page, and a few lead to `none.pdf`; these versions are left out and listed in `data/issues.csv`.
- Savings and transitional rules made by the amending laws, which laws.gov.tt links from each Chapter's page.

All the PDFs are stamped "UNOFFICIAL VERSION". Only the Gazette and the official printed Revised Edition are authoritative; this repository is a research aid.

## How it is checked

- Every version's words were compared, letters and digits only, with the text of its PDF read independently (`tools/build/check_words.py`).
- `scripts/global-law/check_corpus.py` (dates in order, trailers, corpus.json), and a smoke test of blame, the log and the on-date tool.
- The build is deterministic: the same PDFs (sha256 in [`data/pdf-sha256.tsv`](data/pdf-sha256.tsv)) give the same commit hashes. See [`REPRODUCE.md`](REPRODUCE.md).

## How it is built

The build reads the catalogue (every Chapter's list of versions, and the Recent Updates list) and the PDFs. `parse_pdf.py` reads each PDF by its typography: the 8pt margin column, section numbers at the paragraph indent, centred headings, schedules, and the subsidiary legislation after "SUBSIDIARY LEGISLATION". It also repairs two kinds of broken text: control characters some fonts use for quotes and dashes, and capitals encoded as lower-case letters in the 2006-2014 headings ("ChapTer"), read back from each glyph's width. The scanned older editions have no fonts in their text layer, so there the margin column is found by position (the empty strip, or gutter, between the notes and the body), running headers by their content (a page number or chapter reference in the top rows), and an OCR-misread section number ("s." for 5) counts only when it is the number expected next. `build.py` compares consecutive consolidations unit by unit, credits changes as above and writes the history with `git fast-import`. No AI model takes part in building or checking it.

## Licence

The Copyright Act (Chap. 82:80), section 7(1)(b): "no protection shall extend under this Act to ... any official text of a legislative, administrative or legal nature, as well as any official translation thereof". Section 7(2) protects collections of such texts that are original by their selection or arrangement, so this repository takes the text, not the Commission's page layout. See [`SOURCES.md`](SOURCES.md) and [`LICENSE`](LICENSE).
