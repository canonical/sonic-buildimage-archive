#!/usr/bin/env python3
"""Compare two SONiC VS test runs side by side.

Parses per-directory results from worker logs and produces a detailed
comparison report showing which directories improved, regressed, or
stayed the same between two runs.

Usage:
    python3 compare_runs.py <dir_A> <workers_A> <label_A> <dir_B> <workers_B> <label_B>

Example:
    python3 compare_runs.py 92d92f40-07bd-4be4-a8ea-25a1b83b5551 7 "whomp ubuntu-sonic" \
                            4cdba686-whomp-official 7 "whomp official"
"""

import json
import sys
import os
import re
from collections import defaultdict

# Import from analyze_results
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_results import parse_worker_log, parse_worker_script

def load_test_counts():
    """Load AST-based test counts per directory from test_counts.json."""
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_counts.json')
    with open(json_path) as f:
        return json.load(f)

# VS-incompatible directories (excluded from adjusted comparison)
VS_INCOMPATIBLE = {
    'console', 'copp', 'dualtor', 'dualtor_mgmt', 'everflow',
    'kubesonic', 'nat', 'ospf', 'pfcwd', 'platform_tests/api',
    'platform_tests/daemon', 'platform_tests/mellanox', 'restapi',
    'sflow', 'vrf',
}


def load_run(result_dir, num_workers):
    """Load all worker results from a run directory. Returns dict of dir->results."""
    dirs = {}
    for w in range(1, num_workers + 1):
        logfile = os.path.join(result_dir, f'worker_{w}.log')
        if not os.path.exists(logfile):
            continue
        results = parse_worker_log(logfile)
        for r in results:
            d = r['directory']
            if r.get('incomplete'):
                if d not in dirs:
                    dirs[d] = {'status': 'incomplete', 'worker': w}
            elif r['result_line']:
                c = r['result_line']['counts']
                dirs[d] = {
                    'status': 'completed',
                    'worker': w,
                    'passed': c.get('passed', 0),
                    'failed': c.get('failed', 0),
                    'skipped': c.get('skipped', 0),
                    'error': c.get('error', 0),
                    'duration': r['result_line']['duration_str'],
                    'duration_secs': r['result_line']['duration_secs'],
                    'failed_tests': r.get('failed_tests', []),
                }

    # Check for untested dirs from worker scripts
    for w in range(1, num_workers + 1):
        script = os.path.join(result_dir, f'run_worker_{w}.sh')
        if not os.path.exists(script):
            continue
        assigned = parse_worker_script(script)
        for d in assigned:
            if d not in dirs:
                dirs[d] = {'status': 'untested', 'worker': w}

    return dirs


def classify(result):
    """Classify a directory result: pass/fail/skip/incomplete/untested."""
    if result['status'] in ('incomplete', 'untested'):
        return result['status']
    p = result.get('passed', 0)
    f = result.get('failed', 0)
    e = result.get('error', 0)
    if f == 0 and e == 0 and p > 0:
        return 'pass'
    if p == 0 and f == 0 and e == 0:
        return 'skip'
    return 'fail'


def main():
    if len(sys.argv) != 7:
        print(f"Usage: {sys.argv[0]} <dir_A> <workers_A> <label_A> <dir_B> <workers_B> <label_B>")
        sys.exit(1)

    dir_a, nw_a, label_a = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    dir_b, nw_b, label_b = sys.argv[4], int(sys.argv[5]), sys.argv[6]

    test_counts = load_test_counts()
    run_a = load_run(dir_a, nw_a)
    run_b = load_run(dir_b, nw_b)

    all_dirs = sorted(set(run_a.keys()) | set(run_b.keys()) | set(test_counts.keys()))

    # Separate VS-incompatible
    vs_compat_dirs = [d for d in all_dirs if d not in VS_INCOMPATIBLE]
    vs_incompat_dirs = [d for d in all_dirs if d in VS_INCOMPATIBLE]

    # Classify each dir in both runs
    def get_info(run, d):
        if d not in run:
            return {'status': 'not_run'}
        return run[d]

    # === Report ===
    print(f"# SONiC VS 202405 — Comparison Report")
    print()
    print(f"## Runs Compared")
    print()
    print(f"| | **A: {label_a}** | **B: {label_b}** |")
    print(f"|--|--|--|")
    print(f"| Directory | `{dir_a}` | `{dir_b}` |")
    print(f"| Workers | {nw_a} | {nw_b} |")

    # AST total for VS-compatible dirs
    ast_total = sum(test_counts.get(d, 0) for d in vs_compat_dirs
                    if d in test_counts)

    # Compute totals (adjusted = excluding VS-incompatible)
    for label, run, tag in [("A", run_a, label_a), ("B", run_b, label_b)]:
        completed = sum(1 for d in vs_compat_dirs if get_info(run, d)['status'] == 'completed')
        incomplete = sum(1 for d in vs_compat_dirs if get_info(run, d)['status'] == 'incomplete')
        untested = sum(1 for d in vs_compat_dirs if get_info(run, d)['status'] in ('untested', 'not_run'))
        passed = sum(get_info(run, d).get('passed', 0) for d in vs_compat_dirs if get_info(run, d)['status'] == 'completed')
        failed = sum(get_info(run, d).get('failed', 0) for d in vs_compat_dirs if get_info(run, d)['status'] == 'completed')
        error = sum(get_info(run, d).get('error', 0) for d in vs_compat_dirs if get_info(run, d)['status'] == 'completed')
        skipped = sum(get_info(run, d).get('skipped', 0) for d in vs_compat_dirs if get_info(run, d)['status'] == 'completed')
        rate = f"{passed/ast_total*100:.1f}%" if ast_total > 0 else "N/A"
        if label == "A":
            stats_a = (completed, incomplete, untested, passed, failed, error, skipped, ast_total, rate)
        else:
            stats_b = (completed, incomplete, untested, passed, failed, error, skipped, ast_total, rate)

    print()
    print(f"## Summary (adjusted, excl. VS-incompatible, AST total = {ast_total})")
    print()
    print(f"| Metric | **A: {label_a}** | **B: {label_b}** | Δ |")
    print(f"|--------|--|--|--|")
    for i, metric in enumerate(["Dirs completed", "Dirs incomplete", "Dirs untested/not-run",
                                 "✅ Passed", "❌ Failed", "⚠️ Errors", "⏭️ Skipped",
                                 "AST Total (denominator)", "**Pass rate (passed/AST total)**"]):
        va, vb = stats_a[i], stats_b[i]
        if isinstance(va, int):
            diff = vb - va
            delta = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "—"
        else:
            delta = ""
        print(f"| {metric} | {va} | {vb} | {delta} |")

    # === Side-by-side per-directory comparison ===
    print()
    print("## Per-Directory Comparison (VS-compatible only)")
    print()
    print("Legend: ✅=all pass, ❌=has failures/errors, ⏭️=all skipped, 💀=incomplete, 🚫=untested, ·=not in run")
    print()
    print(f"| Directory | A: Status | A: P/F/E | B: Status | B: P/F/E | Verdict |")
    print(f"|-----------|-----------|----------|-----------|----------|---------|")

    # Track categories
    better_in_a = []
    better_in_b = []
    same_both = []
    only_a = []
    only_b = []

    for d in vs_compat_dirs:
        info_a = get_info(run_a, d)
        info_b = get_info(run_b, d)

        def fmt_status(info):
            s = info['status']
            if s == 'not_run': return '·'
            if s == 'untested': return '🚫'
            if s == 'incomplete': return '💀'
            c = classify(info)
            if c == 'pass': return '✅'
            if c == 'skip': return '⏭️'
            return '❌'

        def fmt_counts(info):
            if info['status'] in ('not_run', 'untested', 'incomplete'):
                return '—'
            p = info.get('passed', 0)
            f = info.get('failed', 0)
            e = info.get('error', 0)
            return f"{p}/{f}/{e}"

        sa = fmt_status(info_a)
        sb = fmt_status(info_b)
        ca = fmt_counts(info_a)
        cb = fmt_counts(info_b)

        # Determine verdict
        ca_class = classify(info_a) if info_a['status'] != 'not_run' else 'not_run'
        cb_class = classify(info_b) if info_b['status'] != 'not_run' else 'not_run'

        rank = {'pass': 4, 'skip': 3, 'fail': 2, 'incomplete': 1, 'untested': 0, 'not_run': 0}

        if ca_class == 'not_run' and cb_class == 'not_run':
            continue  # skip if neither run tested it

        verdict = ''
        if ca_class == cb_class == 'pass':
            verdict = '✅ Both pass'
            same_both.append(d)
        elif ca_class == cb_class == 'fail':
            # Compare who has more passes
            pa = info_a.get('passed', 0)
            pb = info_b.get('passed', 0)
            fa = info_a.get('failed', 0) + info_a.get('error', 0)
            fb = info_b.get('failed', 0) + info_b.get('error', 0)
            if pa > pb or fa < fb:
                verdict = '🟢 A better'
                better_in_a.append(d)
            elif pb > pa or fb < fa:
                verdict = '🔵 B better'
                better_in_b.append(d)
            else:
                verdict = '🟡 Both fail'
                same_both.append(d)
        elif ca_class == cb_class:
            verdict = f'≈ Same ({ca_class})'
            same_both.append(d)
        elif rank.get(ca_class, 0) > rank.get(cb_class, 0):
            verdict = '🟢 A better'
            better_in_a.append(d)
        elif rank.get(cb_class, 0) > rank.get(ca_class, 0):
            verdict = '🔵 B better'
            better_in_b.append(d)
        elif ca_class == 'not_run':
            verdict = '(A: not tested)'
            only_b.append(d)
        elif cb_class == 'not_run':
            verdict = '(B: not tested)'
            only_a.append(d)

        print(f"| `{d}` | {sa} | {ca} | {sb} | {cb} | {verdict} |")

    # === Detailed diff for directories that differ ===
    print()
    print("## Score Summary")
    print()
    print(f"| Category | Count | Directories |")
    print(f"|----------|-------|-------------|")
    print(f"| 🟢 **A better** ({label_a}) | {len(better_in_a)} | {', '.join(f'`{d}`' for d in better_in_a[:20])}{'...' if len(better_in_a) > 20 else ''} |")
    print(f"| 🔵 **B better** ({label_b}) | {len(better_in_b)} | {', '.join(f'`{d}`' for d in better_in_b[:20])}{'...' if len(better_in_b) > 20 else ''} |")
    print(f"| ✅ Both pass / same | {len(same_both)} | {', '.join(f'`{d}`' for d in same_both[:20])}{'...' if len(same_both) > 20 else ''} |")
    print(f"| Only in A | {len(only_a)} | {', '.join(f'`{d}`' for d in only_a[:10])} |")
    print(f"| Only in B | {len(only_b)} | {', '.join(f'`{d}`' for d in only_b[:10])} |")

    # === Key differences deep dive ===
    # Show specific test-level diffs for dirs that passed in one, failed in other
    flip_dirs = []
    for d in vs_compat_dirs:
        info_a = get_info(run_a, d)
        info_b = get_info(run_b, d)
        ca_class = classify(info_a) if info_a['status'] != 'not_run' else 'not_run'
        cb_class = classify(info_b) if info_b['status'] != 'not_run' else 'not_run'
        if (ca_class == 'pass' and cb_class == 'fail') or (ca_class == 'fail' and cb_class == 'pass'):
            flip_dirs.append(d)

    if flip_dirs:
        print()
        print("## Key Flips (pass↔fail between runs)")
        print()
        for d in flip_dirs:
            info_a = get_info(run_a, d)
            info_b = get_info(run_b, d)
            ca_class = classify(info_a) if info_a['status'] != 'not_run' else 'not_run'
            cb_class = classify(info_b) if info_b['status'] != 'not_run' else 'not_run'

            winner = "A" if ca_class == 'pass' else "B"
            loser_info = info_b if winner == "A" else info_a
            loser_label = label_b if winner == "A" else label_a

            print(f"### `{d}` — ✅ in {'A' if winner == 'A' else 'B'}, ❌ in {'B' if winner == 'A' else 'A'}")
            print()
            p_a = info_a.get('passed', 0) if info_a['status'] == 'completed' else '—'
            f_a = info_a.get('failed', 0) if info_a['status'] == 'completed' else '—'
            e_a = info_a.get('error', 0) if info_a['status'] == 'completed' else '—'
            p_b = info_b.get('passed', 0) if info_b['status'] == 'completed' else '—'
            f_b = info_b.get('failed', 0) if info_b['status'] == 'completed' else '—'
            e_b = info_b.get('error', 0) if info_b['status'] == 'completed' else '—'
            print(f"| | A ({label_a}) | B ({label_b}) |")
            print(f"|--|--|--|")
            print(f"| Passed | {p_a} | {p_b} |")
            print(f"| Failed | {f_a} | {f_b} |")
            print(f"| Errors | {e_a} | {e_b} |")
            print()

            # Show failing tests from the losing side
            failing = loser_info.get('failed_tests', [])
            if failing:
                print(f"Failures in {loser_label}:")
                for typ, test in failing[:15]:
                    print(f"- {'❌' if typ == 'FAILED' else '⚠️'} `{test}`")
                if len(failing) > 15:
                    print(f"- ... and {len(failing) - 15} more")
                print()

    # === Both-fail deep dive ===
    both_fail_dirs = [d for d in vs_compat_dirs
                      if classify(get_info(run_a, d)) == 'fail' and classify(get_info(run_b, d)) == 'fail'
                      and get_info(run_a, d)['status'] == 'completed' and get_info(run_b, d)['status'] == 'completed']
    if both_fail_dirs:
        print()
        print("## Both-Fail Directories — Detailed Comparison")
        print()
        print(f"| Directory | A: P/F/E | B: P/F/E | Δ Passed | Δ Failed |")
        print(f"|-----------|----------|----------|----------|----------|")
        for d in both_fail_dirs:
            ia, ib = run_a[d], run_b[d]
            pa, fa, ea = ia.get('passed',0), ia.get('failed',0), ia.get('error',0)
            pb, fb, eb = ib.get('passed',0), ib.get('failed',0), ib.get('error',0)
            dp = pb - pa
            df = fb - fa
            dp_s = f"+{dp}" if dp > 0 else str(dp)
            df_s = f"+{df}" if df > 0 else str(df)
            print(f"| `{d}` | {pa}/{fa}/{ea} | {pb}/{fb}/{eb} | {dp_s} | {df_s} |")

    # === Coverage-only directories ===
    a_only = [d for d in vs_compat_dirs
              if get_info(run_a, d)['status'] == 'completed'
              and get_info(run_b, d)['status'] != 'completed']
    b_only = [d for d in vs_compat_dirs
              if get_info(run_b, d)['status'] == 'completed'
              and get_info(run_a, d)['status'] != 'completed']

    if a_only or b_only:
        print()
        print("## Coverage-Only Directories")
        print()
        print("These directories were completed by only one run.")
        print()
        for tag, label, dirs, run in [("A", label_a, a_only, run_a), ("B", label_b, b_only, run_b)]:
            if not dirs:
                continue
            extra_p = sum(run[d].get('passed', 0) for d in dirs)
            # Sort by passed descending
            dirs_sorted = sorted(dirs, key=lambda d: run[d].get('passed', 0), reverse=True)
            print(f"### {tag} only — {label} ({len(dirs)} dirs, {extra_p} extra passed)")
            print()
            print(f"| Directory | P/F/E | Note |")
            print(f"|-----------|-------|------|")
            for d in dirs_sorted:
                info = run[d]
                p, f, e = info.get('passed', 0), info.get('failed', 0), info.get('error', 0)
                note = "✅ all pass" if f == 0 and e == 0 and p > 0 else ""
                print(f"| `{d}` | {p}/{f}/{e} | {note} |")
            print()


if __name__ == '__main__':
    main()
