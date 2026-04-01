#!/usr/bin/env python3
"""Analyze directories that are slow (>45min) or hung across all test runs.

Usage:
    python3 analyze_slow_dirs.py
"""

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_results import parse_worker_log, format_duration
from compare_runs import VS_INCOMPATIBLE

RUNS = [
    ('husband-ubuntu',  '8846ee2a-husband-ubuntu',  7),
    ('whomp-official',   '4cdba686-whomp-official',   7),
    ('blubi-ubuntu',     'a9488a21-blubi-ubuntu',    10),
    ('kroop-official',   'da1448fb-kroop-official',  15),
]

THRESHOLD_SECS = 2700  # 45 minutes


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Collect all dir results across runs
    dir_data = defaultdict(list)

    for name, dirp, nw in RUNS:
        for w in range(1, nw + 1):
            logfile = os.path.join(dirp, f'worker_{w}.log')
            if not os.path.exists(logfile):
                continue
            results = parse_worker_log(logfile)
            for r in results:
                d = r['directory']
                if r.get('incomplete'):
                    dir_data[d].append({
                        'run': name, 'status': 'HUNG',
                        'p': 0, 'f': 0, 'e': 0, 's': 0,
                        'dur': 999999, 'dur_str': 'HUNG',
                    })
                elif r.get('result_line'):
                    c = r['result_line']['counts']
                    dir_data[d].append({
                        'run': name, 'status': 'OK',
                        'p': c.get('passed', 0),
                        'f': c.get('failed', 0),
                        'e': c.get('error', 0),
                        's': c.get('skipped', 0),
                        'dur': r['result_line']['duration_secs'],
                        'dur_str': r['result_line']['duration_str'],
                    })

    def fmt_dur(secs):
        if secs >= 999999:
            return 'HUNG'
        return format_duration(secs)

    # === Section 1: Hung directories ===
    print('=' * 100)
    print('SECTION 1: HUNG DIRECTORIES (incomplete — no result line)')
    print('=' * 100)
    print()

    hung_dirs = {}
    for d, entries in sorted(dir_data.items()):
        hung = [e for e in entries if e['status'] == 'HUNG']
        if hung:
            hung_dirs[d] = hung

    if hung_dirs:
        print(f'{"Directory":<45} {"Hung":<6} {"In runs"}')
        print('-' * 90)
        for d in sorted(hung_dirs, key=lambda x: -len(hung_dirs[x])):
            entries = hung_dirs[d]
            runs_str = ', '.join(e['run'] for e in entries)
            vs = ' [VS_INCOMPAT]' if d in VS_INCOMPATIBLE else ''
            print(f'{d:<45} {len(entries)}x     {runs_str}{vs}')
    else:
        print('None found!')

    # === Section 2: Slow directories ===
    print()
    print('=' * 100)
    print(f'SECTION 2: SLOW DIRECTORIES (max duration > {THRESHOLD_SECS // 60} min, excluding hung)')
    print('=' * 100)
    print()

    slow_dirs = []
    for d, entries in sorted(dir_data.items()):
        ok = [e for e in entries if e['status'] == 'OK']
        if not ok:
            continue
        max_dur = max(e['dur'] for e in ok)
        if max_dur < THRESHOLD_SECS:
            continue
        avg_dur = sum(e['dur'] for e in ok) / len(ok)
        best_p = max(e['p'] for e in ok)
        any_pass_clean = any(e['p'] > 0 and e['f'] == 0 and e['e'] == 0 for e in ok)
        all_skip = all(e['p'] == 0 and e['f'] == 0 and e['e'] == 0 for e in ok)
        all_fail = all(e['f'] > 0 or e['e'] > 0 for e in ok) and not all_skip
        slow_dirs.append((d, ok, max_dur, avg_dur, best_p, any_pass_clean, all_skip, all_fail))

    slow_dirs.sort(key=lambda x: -x[2])

    print(f'{"Directory":<42} {"Runs":<5} {"Max":>8} {"Avg":>8} {"Best P":>7} {"Status":<12} {"Per-run details"}')
    print('-' * 150)
    for d, ok, max_dur, avg_dur, best_p, any_pass_clean, all_skip, all_fail in slow_dirs:
        status = 'ALL-SKIP' if all_skip else ('CLEAN-PASS' if any_pass_clean else ('ALL-FAIL' if all_fail else 'MIXED'))
        vs = ' [VS]' if d in VS_INCOMPATIBLE else ''
        details = '; '.join(f'{e["run"]}: {e["p"]}P/{e["f"]}F/{e["e"]}E {e["dur_str"]}' for e in ok)
        print(f'{d + vs:<42} {len(ok):<5} {fmt_dur(max_dur):>8} {fmt_dur(int(avg_dur)):>8} {best_p:>7} {status:<12} {details}')

    # === Section 3: All-skip directories ===
    print()
    print('=' * 100)
    print('SECTION 3: ALL-SKIP DIRECTORIES (0P/0F/0E in every completed run)')
    print('=' * 100)
    print()

    allskip_dirs = []
    for d, entries in sorted(dir_data.items()):
        ok = [e for e in entries if e['status'] == 'OK']
        if not ok:
            continue
        all_skip = all(e['p'] == 0 and e['f'] == 0 and e['e'] == 0 for e in ok)
        if all_skip:
            vs = ' [VS_INCOMPAT]' if d in VS_INCOMPATIBLE else ''
            runs_str = ', '.join(f'{e["run"]} ({e["dur_str"]})' for e in ok)
            allskip_dirs.append(d)
            print(f'  {d}{vs}: {len(ok)} runs all-skip — {runs_str}')

    if not allskip_dirs:
        print('None found!')

    # === Section 4: All directories summary (sorted by duration) ===
    print()
    print('=' * 100)
    print('SECTION 4: ALL DIRECTORIES BY MAX DURATION')
    print('=' * 100)
    print()

    all_dirs = []
    for d, entries in sorted(dir_data.items()):
        hung = [e for e in entries if e['status'] == 'HUNG']
        ok = [e for e in entries if e['status'] == 'OK']
        max_dur = max((e['dur'] for e in ok), default=0)
        total_p = sum(e['p'] for e in ok)
        total_fe = sum(e['f'] + e['e'] for e in ok)
        n_hung = len(hung)
        all_dirs.append((d, len(ok), n_hung, max_dur, total_p, total_fe))

    all_dirs.sort(key=lambda x: (-x[2], -x[3]))  # hung first, then by max duration

    print(f'{"#":<4} {"Directory":<45} {"Runs":<5} {"Hung":<5} {"Max Dur":>8} {"Total P":>8} {"Total F+E":>10} {"Notes"}')
    print('-' * 130)
    for i, (d, nok, nhung, maxd, tp, tfe) in enumerate(all_dirs, 1):
        vs = ' [VS]' if d in VS_INCOMPATIBLE else ''
        notes = []
        if nhung:
            notes.append(f'{nhung}x HUNG')
        if nok > 0 and tp == 0 and tfe == 0:
            notes.append('ALL-SKIP')
        if nok > 0 and tp == 0 and tfe > 0:
            notes.append('ZERO-PASS')
        notes_str = ', '.join(notes)
        print(f'{i:<4} {d + vs:<45} {nok:<5} {nhung:<5} {fmt_dur(maxd):>8} {tp:>8} {tfe:>10} {notes_str}')

    # === Section 5: Recommendations ===
    print()
    print('=' * 100)
    print('SECTION 5: EXCLUSION RECOMMENDATIONS')
    print('=' * 100)
    print()

    exclude_hung = []
    exclude_allskip = []
    exclude_allfail_slow = []
    add_timeout = []

    for d, entries in sorted(dir_data.items()):
        hung = [e for e in entries if e['status'] == 'HUNG']
        ok = [e for e in entries if e['status'] == 'OK']

        if hung and not ok:
            exclude_hung.append((d, len(hung)))
            continue

        if ok:
            all_skip = all(e['p'] == 0 and e['f'] == 0 and e['e'] == 0 for e in ok)
            all_fail = all((e['f'] > 0 or e['e'] > 0) and e['p'] == 0 for e in ok)
            max_dur = max(e['dur'] for e in ok)

            if all_skip:
                exclude_allskip.append(d)
            elif hung:
                add_timeout.append((d, len(hung), max_dur))
            elif max_dur >= 3600 and all_fail:
                exclude_allfail_slow.append((d, max_dur))
            elif max_dur >= 5400:  # > 1.5h
                add_timeout.append((d, 0, max_dur))

    print('### Should EXCLUDE from test list (waste of time):')
    if exclude_hung:
        print(f'\n  Always hung ({len(exclude_hung)}):')
        for d, n in exclude_hung:
            vs = ' [already VS_INCOMPAT]' if d in VS_INCOMPATIBLE else ''
            print(f'    - {d} ({n}x hung){vs}')

    if exclude_allskip:
        print(f'\n  Always all-skip ({len(exclude_allskip)}):')
        for d in exclude_allskip:
            vs = ' [already VS_INCOMPAT]' if d in VS_INCOMPATIBLE else ''
            print(f'    - {d}{vs}')

    if exclude_allfail_slow:
        print(f'\n  Always all-fail AND slow >1h ({len(exclude_allfail_slow)}):')
        for d, dur in exclude_allfail_slow:
            vs = ' [already VS_INCOMPAT]' if d in VS_INCOMPATIBLE else ''
            print(f'    - {d} (max {fmt_dur(dur)}){vs}')

    print(f'\n### Should ADD TIMEOUT (sometimes hung or very slow >1.5h):')
    if add_timeout:
        for d, n_hung, max_dur in add_timeout:
            vs = ' [already VS_INCOMPAT]' if d in VS_INCOMPATIBLE else ''
            hung_str = f', {n_hung}x hung' if n_hung else ''
            print(f'    - {d} (max {fmt_dur(max_dur)}{hung_str}){vs}')
    else:
        print('    None')

    print()
    total_exclude = len(exclude_hung) + len(exclude_allskip) + len(exclude_allfail_slow)
    print(f'Total dirs to EXCLUDE: {total_exclude}')
    print(f'  - Always hung: {len(exclude_hung)}')
    print(f'  - Always all-skip: {len(exclude_allskip)}')
    print(f'  - Always all-fail + slow: {len(exclude_allfail_slow)}')
    print(f'Total dirs needing TIMEOUT: {len(add_timeout)}')


if __name__ == '__main__':
    main()
