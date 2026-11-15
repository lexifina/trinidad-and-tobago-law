# Trinidad and Tobago: law history in git

The law of Trinidad and Tobago as a git history: one file per section, schedule and regulation, a commit for each change a consolidation shows, dated by its as-at date, and the Act or Legal Notice that made the change as the commit's author where the margin notes name it. `git blame` names the law (or the Law Revision Commission) behind every line; `git log` lists every change to a section; picking a date gives the text of the latest consolidation on or before that day.

Part of [lexifina/global-law](https://github.com/lexifina/global-law), one git history for every country's law: this is Trinidad and Tobago's national law, which global-law reads at `trinidad-and-tobago/national/acts/`.

**What is in it now:** all 533 Chapters of the Laws of Trinidad and Tobago on laws.gov.tt and 26 Acts not yet given a Chapter number, with 575 pieces of subsidiary legislation between them: 4,659 versions, from the year-end consolidations of 2004 to 2016, 215 later Recent Updates and, for many Chapters, 882 versions from the older Revised Editions (1902 to 1980). There is no `PLAN.md`; [`laws.csv`](laws.csv) lists every law with its versions and folder, and [`data/versions.csv`](data/versions.csv) every version used.

Each Chapter is in `chapters/<chapter>-<number>/` and each Act not yet in a Chapter in `acts/<year>-<number>/`, with one file per section and schedule, `title.md` for the cover and long title, and `sl-01/`, `sl-02/` ... for its subsidiary legislation in printed order (`chapters/45-57/s-9.md` is section 9, Date of maternity leave, of the Maternity Protection Act, Chap. 45:57). The Constitution itself, enacted as the Schedule to the Act of Chap. 1:01, is [`acts/1976-004/`](acts/1976-004/).

The text is in English, as laws.gov.tt's PDFs print it; each section's first margin note is its heading, with the enacting and amending laws, and the other margin notes are `- Margin:` lines at its end.

## Questions as git commands

| Question | Command |
| --- | --- |
| Every change to section 9 of the Maternity Protection Act | `git log -p --word-diff -- chapters/45-57/s-9.md` |
| Which law wrote each line of section 9? | `git blame chapters/45-57/s-9.md` |
| Every version of the Act, with the as-at date of each | `git log --format="%h %(trailers:key=In-force,valueonly,separator=) %an" -- chapters/45-57` |
| Section 9 as it stood on 1 January 2010 | `python tools/in_force_on.py 2010-01-01 chapters/45-57 s-9` |

**Outside git**, we also host this record publicly, for free:

- **[Ask Claude about the law of Trinidad and Tobago](https://global-law.lexifina.com/v1/try_claude?country=trinidad-and-tobago)**: opens Claude with a first question ready.
- **[Ask ChatGPT](https://global-law.lexifina.com/v1/try_chatgpt?country=trinidad-and-tobago)**: the same question in ChatGPT.
- **[Search the law of Trinidad and Tobago on our site](https://lexifina.com/law?country=trinidad-and-tobago&q=maternity+leave)**: a search for "maternity leave", with each provision's text and its versions, no account needed.
- **[Developer REST API](https://global-law.lexifina.com/v1/search_law?query=maternity+leave&jurisdiction=trinidad-and-tobago)**: the same search as JSON, with no key. See the [documentation here](https://lexifina.com/api/global-law).

Both assistants read the record through the free Global law connector (MCP, `https://global-law.lexifina.com/mcp`); the first time, the chat gives you the link that adds it. Ask in English.

**Host it yourself easily.** All it takes is git and Python, and the tools run on your machine:

```sh
git clone --depth 1 https://github.com/lexifina/global-law && cd global-law
python3 tools/countries.py add trinidad-and-tobago/national/acts
python3 tools/law.py show 2026-01-01 trinidad-and-tobago/national/acts/chapters/45-57/s-9.md
```

Opened in Claude Code, Cursor, VS Code or Codex, the clone also starts a local MCP server with the same tools ([MCP.md](https://github.com/lexifina/global-law/blob/main/MCP.md)).

## Dates

Each commit is dated at noon, Trinidad time (UTC-4), on the as-at date of the consolidation that first shows its text, and carries it in its `In-force:` trailer. That is a day the text was in force, not the day a change took effect:

- the consolidations of the 2006 Revised Edition are as at 31 December 2004, 2007, 2009, 2012, 2014 and 2016 (2013 for a few Chapters, and an unofficial one as at 31 December 2015), so a change shows up at the first one that contains it, up to three years after it took effect;
- the Recent Updates are unofficial and give no as-at date, so each is dated by its PDF's creation date (2023-09-22 to 2026-04-23; `Date-source: pdf-created`);
- the older Revised Editions give only a month ("as at June 1925"), so each is dated the last day of it; git cannot store dates before 1970, so the 543 commits before then are dated 1970-01-01, one second apart, with the real day in `In-force:`. Ask for a date with `tools/in_force_on.py`, not `git log --before`.

A change is credited to a law only when the changed unit's margin notes newly name exactly one law (`Act No. 7 of 2012`, `Legal Notice No. 51 of 1980`): 999 commits, credited to 487 laws. Every first version and every other change is credited to the Law Revision Commission, and the laws newly named in that Chapter are listed as `Newly-cited:` candidates ([`data/newly-cited.csv`](data/newly-cited.csv)).

## How it is checked

- `tools/build/check_words.py` compares the letters and digits of every version with the text of its PDF, read independently.
- `tools/build/build.py` writes the history from the PDFs in one pass, and the same PDFs give the same commit hashes; [`REPRODUCE.md`](REPRODUCE.md) gives the steps, the sha256 of every PDF ([`data/pdf-sha256.tsv`](data/pdf-sha256.tsv)) and of the build scripts.
- History is append-only: no merge commits, and no commit dated before the one under it.

## What it does not show

- **The day each change took effect**: only the consolidation that first shows it.
- **Text before each law's first version here** (its earliest older Revised Edition, else mostly 31 December 2004). The original Acts and Ordinances, and the amending Acts and Legal Notices themselves with their savings and transitional rules, are not used.
- **Corrected OCR.** The older editions are scans, and their text is the publisher's OCR layer as published ("1neans" for "means"); a difference from the next version can be an OCR error.
- **43 versions left out** (13 scans with no text layer, 16 older editions that print another law's title, 8 downloads that serve another Chapter's PDF, 3 HTML pages, 3 not fetched), and the scanned pages with no text layer in 31 others; [`data/issues.csv`](data/issues.csv) lists all 74.
- **Running headers and the cover's table of authorised pages.** Quotes and dashes are normalised.
- **Case law, bills and the Gazette.** Not part of this record.

## Sources

| Source | Kind | Past versions | Notes |
| --- | --- | --- | --- |
| [laws.gov.tt](https://laws.gov.tt/ttdll-web/revision/list), the Digital Legislative Library of the Law Revision Commission | Consolidated laws: the 2006 Revised Edition's consolidations, the Recent Updates and the older Revised Editions | yes, consolidations as at 31 December 2004 to 2016, and the Revised Editions of 1902, 1925, 1940, 1950 and 1980 | Every PDF is stamped "UNOFFICIAL VERSION"; only the Gazette and the official printed Revised Edition are authoritative. See [`SOURCES.md`](SOURCES.md) |

## Licence

See [`LICENSE`](LICENSE). Under the Copyright Act (Chap. 82:80), section 7(1)(b), no copyright protection extends to "any official text of a legislative, administrative or legal nature"; the texts keep their wording, in Lexifina's own arrangement rather than the Revised Edition's page layout (section 7(2) protects original collections). Lexifina's tools, file arrangement, commit messages and documentation are CC0 1.0.

No AI model wrote or changed legal text, and none runs when the repository is built or checked; the scripts were written by an AI model (see [`REPRODUCE.md`](REPRODUCE.md)).

## More

From [lexifina/global-law](https://github.com/lexifina/global-law):

- [FEATURES.md](https://github.com/lexifina/global-law/blob/main/FEATURES.md): every feature, and what every corpus must support (`git blame`, `law.py`, the MCP tools)
- [FAQ.md](https://github.com/lexifina/global-law/blob/main/FAQ.md): questions and answers · [CONTRIBUTING.md](https://github.com/lexifina/global-law/blob/main/CONTRIBUTING.md): proposing changes · [MCP.md](https://github.com/lexifina/global-law/blob/main/MCP.md): the MCP server · [REPRODUCE.md](https://github.com/lexifina/global-law/blob/main/REPRODUCE.md): how it was built · [CHANGELOG.md](https://github.com/lexifina/global-law/blob/main/CHANGELOG.md)
- [FRESHNESS.md](https://github.com/lexifina/global-law/blob/main/FRESHNESS.md): how current each corpus is · [Monitoring](https://github.com/lexifina/global-law/tree/main/monitoring): whether updates are running · [WATCHING.md](https://github.com/lexifina/global-law/blob/main/WATCHING.md): how each official source is watched for changes
- [performance/](https://github.com/lexifina/global-law/tree/main/performance): how fast the tools are, measured
- [visualisations/](https://github.com/lexifina/global-law/tree/main/visualisations): charts and bridges across the world's law
- [Vulnerabilities](https://github.com/lexifina/global-law/tree/main/vulnerabilities): mistakes in legislation as published
