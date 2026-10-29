"""Print a law of Trinidad and Tobago, or one section of it, as the record shows it on a date.

    python tools/in_force_on.py 2010-06-01 chapters/23-54          # every file of Chap. 23:54 on that day
    python tools/in_force_on.py 2010-06-01 chapters/23-54 s-5      # section 5
    python tools/in_force_on.py 2010-06-01 chapters/23-54/sl-01    # one piece of subsidiary legislation

The record holds year-end consolidations (as at 31 December 2004, 2007, 2009, 2012, 2014, 2015, 2016), undated
Recent Updates and, before 2004 for many Chapters, the older Revised Editions (1902, 1925, 1940, 1950, 1980 as at
December 1990; dated the last day of the as-at month, their OCR text as published), so "on a date" means "in the latest consolidation dated on or before that day": a change that took
effect in, say, March 2008 appears from 31 December 2009, the first consolidation that shows it. Reads the
`In-force:` trailers. Standard library only.
"""
import subprocess
import sys


def git(*args: str) -> str:
    return subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8', check=True).stdout


def commit_on(day: str, path: str) -> tuple[str, str] | None:
    """The last commit dated on or before `day` that touched `path`: (hash, date)."""
    fmt = '%H%x1f%(trailers:key=In-force,valueonly,separator=)'
    for line in git('log', '--first-parent', f'--format={fmt}', 'main', '--', path).splitlines():
        h, d = (line.split('\x1f') + [''])[:2]
        d = d.strip()
        if d and d <= day:
            return h, d
    return None


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    day, law = sys.argv[1], sys.argv[2].strip('/')
    unit = sys.argv[3] if len(sys.argv) > 3 else None
    path = f'{law}/{unit}.md' if unit else law
    if '/' not in law and not unit:
        # a whole folder (chapters, acts): each law in it, with the consolidation the record shows on that day
        latest: dict[str, str] = {}
        fmt = '%x1e%(trailers:key=In-force,valueonly,separator=)'
        for rec in git('log', '--first-parent', f'--format={fmt}', '--name-only', 'main', '--', law).split('\x1e'):
            head, _, names = rec.partition('\n')
            d = head.strip()
            if not d or d > day:
                continue
            for n in names.split():
                key = '/'.join(n.split('/')[:2])
                latest.setdefault(key, d)
        if not latest:
            sys.exit(f'{law}: nothing on or before {day}')
        for key in sorted(latest):
            print(f'{key}\t{latest[key]}')
        return
    found = commit_on(day, path)
    if not found:
        sys.exit(f'{path}: no version on or before {day} (the record starts at the law\'s first version: an '
                 f'older Revised Edition, else mostly 31 December 2004)')
    h, d = found
    if unit:
        sys.stdout.write(git('show', f'{h}:{path}'))
        return
    chapter = '/'.join(law.split('/')[:2])
    names = [n for n in git('show', f'{h}:{chapter}/index.txt').split() if f'{chapter}/{n}'.startswith(law + '/')]
    print(f'<!-- {law} as consolidated at {d} -->')
    for n in names:
        sys.stdout.write(git('show', f'{h}:{chapter}/{n}') + '\n')


if __name__ == '__main__':
    main()
