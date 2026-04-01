#!/usr/bin/env python3
"""Fair per-directory comparison of two SONiC VS test runs.

Only compares directories where BOTH runs completed, eliminating
coverage bias. Pass rate = passed / AST total (for common dirs).

Usage:
    python3 compare_fair.py <dir_A> <workers_A> <label_A> <dir_B> <workers_B> <label_B>

Example:
    python3 compare_fair.py 8846ee2a-husband-ubuntu 7 "husband ubuntu-sonic" \
                            4cdba686-whomp-official 7 "whomp official"
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare_runs import load_run, classify, load_test_counts, VS_INCOMPATIBLE


def main():
    if len(sys.argv) != 7:
        print(f"Usage: {sys.argv[0]} <dir_A> <workers_A> <label_A> <dir_B> <workers_B> <label_B>")
        sys.exit(1)

    dir_a, nw_a, label_a = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    dir_b, nw_b, label_b = sys.argv[4], int(sys.argv[5]), sys.argv[6]

    test_counts = load_test_counts()
    run_a = load_run(dir_a, nw_a)
    run_b = load_run(dir_b, nw_b)

    all_dirs = sorted(set(run_a.keys()) | set(run_b.keys()))

    # Common completed dirs (excluding VS-incompatible)
    common = [d for d in all_dirs
              if d not in VS_INCOMPATIBLE
              and run_a.get(d, {}).get('status') == 'completed'
              and run_b.get(d, {}).get('status') == 'completed']

    # Coverage-only dirs
    a_only = [d for d in all_dirs
              if d not in VS_INCOMPATIBLE
              and run_a.get(d, {}).get('status') == 'completed'
              and run_b.get(d, {}).get('status') != 'completed']
    b_only = [d for d in all_dirs
              if d not in VS_INCOMPATIBLE
              and run_b.get(d, {}).get('status') == 'completed'
              and run_a.get(d, {}).get('status') != 'completed']

    ast_total = sum(test_counts.get(d, 0) for d in common)

    def totals(run, dirs):
        p = sum(run[d].get('passed', 0) for d in dirs)
        f = sum(run[d].get('failed', 0) for d in dirs)
        e = sum(run[d].get('error', 0) for d in dirs)
        s = sum(run[d].get('skipped', 0) for d in dirs)
        return p, f, e, s

    pa, fa, ea, sa = totals(run_a, common)
    pb, fb, eb, sb = totals(run_b, common)
    rate_a = pa / ast_total * 100 if ast_total else 0
    rate_b = pb / ast_total * 100 if ast_total else 0

    # Classify directories
    a_wins = []       # A all-pass, B has failures
    b_wins = []       # B all-pass, A has failures
    both_pass = []
    both_fail = []
    other = []

    rows = []
    for d in common:
        ai, bi = run_a[d], run_b[d]
        ca, cb = classify(ai), classify(bi)
        ap, af, ae = ai.get('passed', 0), ai.get('failed', 0), ai.get('error', 0)
        bp, bf_, be = bi.get('passed', 0), bi.get('failed', 0), bi.get('error', 0)
        ast = test_counts.get(d, '?')

        if ca == 'pass' and cb == 'pass':
            verdict = '🤝 Both pass'
            both_pass.append(d)
        elif ca == 'pass' and cb != 'pass':
            verdict = '🅰️ A wins'
            a_wins.append(d)
        elif cb == 'pass' and ca != 'pass':
            verdict = '🅱️ B wins'
            b_wins.append(d)
        elif ca == 'fail' and cb == 'fail':
            both_fail.append(d)
            delta_fe = (af + ae) - (bf_ + be)
            if delta_fe > 0:
                verdict = '🅱️ B better'
            elif delta_fe < 0:
                verdict = '🅰️ A better'
            else:
                delta_p = ap - bp
                if delta_p > 0:
                    verdict = '🅰️ A better'
                elif delta_p < 0:
                    verdict = '🅱️ B better'
                else:
                    verdict = '🤝 Tie'
        else:
            verdict = '—'
            other.append(d)

        rows.append((d, ca, ap, af, ae, cb, bp, bf_, be, ast, verdict))

    # Count both-fail sub-winners
    bf_a = sum(1 for d in both_fail
               if (run_a[d].get('failed', 0) + run_a[d].get('error', 0))
               < (run_b[d].get('failed', 0) + run_b[d].get('error', 0)))
    bf_b = sum(1 for d in both_fail
               if (run_a[d].get('failed', 0) + run_a[d].get('error', 0))
               > (run_b[d].get('failed', 0) + run_b[d].get('error', 0)))
    bf_tie = len(both_fail) - bf_a - bf_b

    total_a = len(a_wins) + bf_a
    total_b = len(b_wins) + bf_b
    total_tie = len(both_pass) + bf_tie + len(other)

    # === Generate Markdown ===
    o = []
    o.append('# SONiC VS 202405 — Per-Directory Fair Comparison')
    o.append('')
    o.append('> **Methodology**: Only directories where **both** runs completed are compared.')
    o.append('> This eliminates coverage bias and focuses on actual test quality.')
    o.append('> Pass rate = passed / AST total (for common dirs only).')
    o.append('')

    o.append('## Runs Compared')
    o.append('')
    o.append(f'| | **A: {label_a}** | **B: {label_b}** |')
    o.append('|--|--|--|')
    o.append(f'| Directory | `{dir_a}` | `{dir_b}` |')
    o.append(f'| Workers | {nw_a} | {nw_b} |')
    o.append(f'| Common completed dirs | {len(common)} | {len(common)} |')
    o.append(f'| AST total (common dirs) | {ast_total} | {ast_total} |')
    o.append('')

    o.append('## Summary')
    o.append('')
    o.append(f'| Metric | **A ({label_a})** | **B ({label_b})** | Δ (B−A) |')
    o.append('|--------|:-:|:-:|:-:|')
    for metric, va, vb in [
        ('✅ Passed', pa, pb),
        ('❌ Failed', fa, fb),
        ('⚠️ Errors', ea, eb),
        ('⏭️ Skipped', sa, sb),
    ]:
        d = vb - va
        ds = f'+{d}' if d > 0 else str(d) if d < 0 else '—'
        o.append(f'| {metric} | {va} | {vb} | {ds} |')
    diff_rate = rate_b - rate_a
    sign = '+' if diff_rate > 0 else ''
    o.append(f'| **Pass rate** | **{rate_a:.1f}%** | **{rate_b:.1f}%** | **{sign}{diff_rate:.1f}%** |')
    o.append('')

    o.append('## Directory Score Summary')
    o.append('')
    o.append('| Category | Count |')
    o.append('|----------|:-----:|')
    o.append(f'| 🅰️ A wins (A all-pass, B has failures) | {len(a_wins)} |')
    o.append(f'| 🅱️ B wins (B all-pass, A has failures) | {len(b_wins)} |')
    o.append(f'| 🤝 Both pass | {len(both_pass)} |')
    o.append(f'| Both fail — A fewer failures | {bf_a} |')
    o.append(f'| Both fail — B fewer failures | {bf_b} |')
    o.append(f'| Both fail — tie | {bf_tie} |')
    o.append(f'| Other | {len(other)} |')
    o.append(f'| **Total A advantage** | **{total_a}** |')
    o.append(f'| **Total B advantage** | **{total_b}** |')
    o.append(f'| **Ties / both pass** | **{total_tie}** |')
    o.append('')

    o.append('## Per-Directory Comparison')
    o.append('')
    o.append('| # | Directory | AST | A: P/F/E | B: P/F/E | Verdict |')
    o.append('|:-:|-----------|:---:|----------|----------|---------|')
    for i, (d, ca, ap, af, ae, cb, bp, bf_, be, ast, verdict) in enumerate(rows, 1):
        dn = d if d != '.' else '(root)'
        o.append(f'| {i} | `{dn}` | {ast} | {ap}/{af}/{ae} | {bp}/{bf_}/{be} | {verdict} |')
    o.append('')

    # B wins details
    if b_wins:
        o.append('## Official Wins — Details')
        o.append('')
        o.append('Directories where B passes 100% but A has failures:')
        o.append('')
        for d in b_wins:
            ai = run_a[d]
            dn = d if d != '.' else '(root)'
            o.append(f'### `{dn}`')
            o.append(f'- A: {ai.get("passed",0)}P / {ai.get("failed",0)}F / {ai.get("error",0)}E')
            o.append(f'- B: all pass ({run_b[d].get("passed",0)}P)')
            failing = ai.get('failed_tests', [])
            if failing:
                o.append('- A failures:')
                for typ, test in failing[:10]:
                    o.append(f'  - {"❌" if typ == "FAILED" else "⚠️"} `{test}`')
                if len(failing) > 10:
                    o.append(f'  - ... and {len(failing) - 10} more')
            o.append('')

    # A wins details
    if a_wins:
        o.append('## Ubuntu-sonic Wins — Details')
        o.append('')
        o.append('Directories where A passes 100% but B has failures:')
        o.append('')
        for d in a_wins:
            bi = run_b[d]
            dn = d if d != '.' else '(root)'
            o.append(f'### `{dn}`')
            o.append(f'- A: all pass ({run_a[d].get("passed",0)}P)')
            o.append(f'- B: {bi.get("passed",0)}P / {bi.get("failed",0)}F / {bi.get("error",0)}E')
            failing = bi.get('failed_tests', [])
            if failing:
                o.append('- B failures:')
                for typ, test in failing[:10]:
                    o.append(f'  - {"❌" if typ == "FAILED" else "⚠️"} `{test}`')
                if len(failing) > 10:
                    o.append(f'  - ... and {len(failing) - 10} more')
            o.append('')

    # Both-fail details
    if both_fail:
        o.append('## Both-Fail Directories — Detailed Comparison')
        o.append('')
        o.append('| Directory | A: P/F/E | B: P/F/E | Δ Passed | Δ Fail+Err | Better |')
        o.append('|-----------|----------|----------|:--------:|:----------:|--------|')
        for d in both_fail:
            ai, bi = run_a[d], run_b[d]
            ap, af, ae = ai.get('passed', 0), ai.get('failed', 0), ai.get('error', 0)
            bp, bf_, be = bi.get('passed', 0), bi.get('failed', 0), bi.get('error', 0)
            dp = bp - ap
            dfe = (bf_ + be) - (af + ae)
            dp_s = f'+{dp}' if dp > 0 else str(dp)
            dfe_s = f'+{dfe}' if dfe > 0 else str(dfe)
            if (af + ae) < (bf_ + be):
                better = '🅰️ A'
            elif (af + ae) > (bf_ + be):
                better = '🅱️ B'
            else:
                better = '🤝'
            dn = d if d != '.' else '(root)'
            o.append(f'| `{dn}` | {ap}/{af}/{ae} | {bp}/{bf_}/{be} | {dp_s} | {dfe_s} | {better} |')
        o.append('')

    # Coverage-only section
    if a_only or b_only:
        o.append('## Coverage-Only Directories (excluded from comparison)')
        o.append('')
        o.append('These directories were completed by only one run.')
        o.append('')
        for tag, dirs, run in [('A', a_only, run_a), ('B', b_only, run_b)]:
            if dirs:
                extra_p = sum(run[d].get('passed', 0) for d in dirs)
                o.append(f'### {tag} only ({len(dirs)} dirs, {extra_p} extra passed)')
                o.append('')
                for d in sorted(dirs):
                    ri = run[d]
                    dn = d if d != '.' else '(root)'
                    o.append(f'- `{dn}`: {ri.get("passed",0)}P/{ri.get("failed",0)}F/{ri.get("error",0)}E')
                o.append('')

    # Conclusion
    o.append('## Conclusion')
    o.append('')
    o.append(f'When comparing only the **{len(common)} directories** where both runs completed:')
    o.append('')
    winner = 'B' if rate_b > rate_a else 'A'
    winner_label = label_b if winner == 'B' else label_a
    loser_label = label_a if winner == 'B' else label_b
    o.append(f'- **{winner_label}** achieves **{max(rate_a, rate_b):.1f}%** pass rate '
             f'vs {loser_label} **{min(rate_a, rate_b):.1f}%** ({sign}{abs(diff_rate):.1f}%)')
    o.append(f'- Directory wins: A **{total_a}** vs B **{total_b}**, ties **{total_tie}**')
    if a_only:
        a_extra = sum(run_a[d].get('passed', 0) for d in a_only)
        o.append(f'- A completed **{len(a_only)} additional dirs** (not in B), '
                 f'contributing **{a_extra} extra passed** tests')
    if b_only:
        b_extra = sum(run_b[d].get('passed', 0) for d in b_only)
        o.append(f'- B completed **{len(b_only)} additional dirs** (not in A), '
                 f'contributing **{b_extra} extra passed** tests')
    o.append('')

    print('\n'.join(o))


if __name__ == '__main__':
    main()
