#!/usr/bin/env python3
"""Analyze worker logs from SONiC LXD parallel test run.

Parses per-directory pytest results from each worker log and produces
a summary report with pass/fail/skip/error counts and durations.
"""

import re
import sys
import os
from collections import defaultdict

# Pattern to match directory section headers
DIR_PATTERN = re.compile(r'^=== Directory: (.+?) \((\d+) tests? from (\d+) files?\) ===$')

# Pattern to match pytest final result lines like:
#   ====== 9 failed, 60 passed, 12 skipped, 83 warnings in 9176.09s (2:32:56) ======
#   =================== 1 passed, 1 warning in 103.12s (0:01:43) ===================
#   ============== 2 failed, 8 skipped, 1 warning in 98.54s (0:01:38) ==============
#   === no tests ran in 0.47s (0:00:00) ===
RESULT_PATTERN = re.compile(
    r'^={2,}\s+(.*?)\s+in\s+[\d.]+s\s+\((\d+:\d+:\d+)\)\s*={2,}$'
)

# Patterns to extract counts from the result string
COUNT_PATTERNS = {
    'passed': re.compile(r'(\d+) passed'),
    'failed': re.compile(r'(\d+) failed'),
    'skipped': re.compile(r'(\d+) skipped'),
    'error': re.compile(r'(\d+) errors?'),
    'warnings': re.compile(r'(\d+) warnings?'),
    'deselected': re.compile(r'(\d+) deselected'),
    'xfailed': re.compile(r'(\d+) xfailed'),
    'no_tests': re.compile(r'no tests ran'),
}

# Pattern to match FAILED/ERROR lines in short test summary
FAILED_LINE = re.compile(r'^(FAILED|ERROR)\s+(.+?)(?:\s+-\s+.*)?$')

def parse_duration(dur_str):
    """Parse H:MM:SS to seconds."""
    parts = dur_str.split(':')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

def format_duration(secs):
    """Format seconds to H:MM:SS."""
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    return f"{h}:{m:02d}:{s:02d}"

def parse_worker_log(filepath):
    """Parse a single worker log file and extract per-directory results."""
    results = []
    current_dir = None
    current_dir_info = None
    last_result_line = None
    failed_tests = []
    in_summary = False

    with open(filepath) as f:
        lines = f.readlines()

    for line in lines:
        line = line.rstrip('\n')

        # Check for directory header
        m = DIR_PATTERN.match(line)
        if m:
            # Save previous directory result
            if current_dir and last_result_line:
                results.append({
                    'directory': current_dir,
                    'declared_tests': current_dir_info[0],
                    'declared_files': current_dir_info[1],
                    'result_line': last_result_line,
                    'failed_tests': failed_tests,
                })
            elif current_dir and not last_result_line:
                # Previous directory started but never finished
                results.append({
                    'directory': current_dir,
                    'declared_tests': current_dir_info[0],
                    'declared_files': current_dir_info[1],
                    'result_line': None,
                    'failed_tests': [],
                    'incomplete': True,
                })
            current_dir = m.group(1)
            current_dir_info = (int(m.group(2)), int(m.group(3)))
            last_result_line = None
            failed_tests = []
            in_summary = False
            continue

        # Track short test summary section
        if 'short test summary info' in line:
            in_summary = True
            continue

        if in_summary:
            fm = FAILED_LINE.match(line)
            if fm:
                failed_tests.append((fm.group(1), fm.group(2)))  # (type, test_name)
                continue
            # End of summary when we hit another === line
            if line.startswith('===') or line.startswith('---'):
                in_summary = False

        # Check for pytest result line
        rm = RESULT_PATTERN.match(line)
        if rm and current_dir:
            last_result_line = {
                'raw': rm.group(1),
                'duration_str': rm.group(2),
                'duration_secs': parse_duration(rm.group(2)),
                'counts': {},
            }
            for key, pat in COUNT_PATTERNS.items():
                cm = pat.search(rm.group(1))
                if key == 'no_tests' and cm:
                    last_result_line['counts']['no_tests'] = True
                elif cm:
                    last_result_line['counts'][key] = int(cm.group(1))

    # Don't forget the last directory
    if current_dir and last_result_line:
        results.append({
            'directory': current_dir,
            'declared_tests': current_dir_info[0],
            'declared_files': current_dir_info[1],
            'result_line': last_result_line,
            'failed_tests': failed_tests,
        })
    # Track incomplete directory (started but no result line)
    elif current_dir and not last_result_line:
        results.append({
            'directory': current_dir,
            'declared_tests': current_dir_info[0],
            'declared_files': current_dir_info[1],
            'result_line': None,
            'failed_tests': [],
            'incomplete': True,
        })

    return results


def status_emoji(c):
    """Return status emoji from counts dict."""
    f = c.get('failed', 0)
    e = c.get('error', 0)
    p = c.get('passed', 0)
    if f > 0 or e > 0:
        return '❌'
    if c.get('no_tests') or p == 0:
        return '⏭️'
    return '✅'


def main():
    log_dir = sys.argv[1] if len(sys.argv) > 1 else '/tmp'
    num_workers = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    all_results = {}
    for i in range(1, num_workers + 1):
        path = os.path.join(log_dir, f'worker_{i}.log')
        if os.path.exists(path):
            all_results[i] = parse_worker_log(path)
        else:
            print(f"<!-- WARNING: {path} not found -->")

    # Collect per-worker stats
    grand_passed = 0
    grand_failed = 0
    grand_skipped = 0
    grand_error = 0
    grand_duration = 0
    grand_dirs = 0
    all_failed_tests = []
    all_error_tests = []

    worker_stats = {}
    for worker_id in sorted(all_results.keys()):
        results = all_results[worker_id]
        completed = [r for r in results if r.get('result_line')]
        incomplete = [r for r in results if r.get('incomplete')]
        w_passed = sum(r['result_line']['counts'].get('passed', 0) for r in completed)
        w_failed = sum(r['result_line']['counts'].get('failed', 0) for r in completed)
        w_skipped = sum(r['result_line']['counts'].get('skipped', 0) for r in completed)
        w_error = sum(r['result_line']['counts'].get('error', 0) for r in completed)
        w_duration = sum(r['result_line']['duration_secs'] for r in completed)
        grand_passed += w_passed
        grand_failed += w_failed
        grand_skipped += w_skipped
        grand_error += w_error
        grand_duration = max(grand_duration, w_duration)
        grand_dirs += len(completed)
        worker_stats[worker_id] = {
            'completed': completed, 'incomplete': incomplete,
            'passed': w_passed, 'failed': w_failed,
            'skipped': w_skipped, 'error': w_error,
            'duration': w_duration,
        }

    total_tests = grand_passed + grand_failed + grand_skipped + grand_error
    pass_rate = (grand_passed / total_tests * 100) if total_tests > 0 else 0
    exec_total = grand_passed + grand_failed + grand_error
    exec_rate = (grand_passed / exec_total * 100) if exec_total > 0 else 0

    # === VS-incompatible pre-computation ===
    vs_incompatible = {
        'platform_tests/api': 'expects real hardware (no platform API on VS)',
        'everflow': 'mirror session failures on VS',
        'vrf': 'VRF not supported on VS topology',
        'pfcwd': 'PFC watchdog requires real ASIC',
        'platform_tests/mellanox': 'vendor-specific (Mellanox only)',
        'platform_tests/daemon': 'all skipped (expects real daemons)',
        'platform_tests/broadcom': 'vendor-specific (Broadcom only)',
        'console': 'all skipped (needs console access)',
        'dualtor': 'all skipped (needs dual-tor topology)',
        'dualtor_mgmt': 'all skipped (needs dual-tor topology)',
        'nat': 'all skipped (NAT not enabled on VS)',
        'restapi': 'all skipped (REST API not enabled on VS)',
        'sflow': 'all skipped (sFlow not on VS)',
        'copp': 'CoPP policer errors on VS',
        'kubesonic': 'skipped (k8s not on VS)',
        'ospf': 'skipped (OSPF not configured)',
    }
    excluded_passed = excluded_failed = excluded_skipped = excluded_error = 0
    excluded_dirs = []
    for wid, results in all_results.items():
        for r in results:
            if r.get('incomplete') or not r.get('result_line'):
                continue
            if r['directory'] in vs_incompatible:
                c = r['result_line']['counts']
                excluded_passed += c.get('passed', 0)
                excluded_failed += c.get('failed', 0)
                excluded_skipped += c.get('skipped', 0)
                excluded_error += c.get('error', 0)
                excluded_dirs.append((r['directory'], wid, c))

    adj_passed = grand_passed - excluded_passed
    adj_failed = grand_failed - excluded_failed
    adj_error = grand_error - excluded_error
    adj_skipped = grand_skipped - excluded_skipped
    adj_total = adj_passed + adj_failed + adj_skipped + adj_error
    adj_executed = adj_passed + adj_failed + adj_error
    adj_rate = (adj_passed / adj_executed * 100) if adj_executed > 0 else 0

    # Incomplete dirs
    all_incomplete = []
    for wid, results in all_results.items():
        for r in results:
            if r.get('incomplete'):
                all_incomplete.append((wid, r['directory'], r['declared_tests']))

    # 100% passing dirs
    ok_dirs = []
    for wid, results in all_results.items():
        for r in results:
            if r.get('incomplete') or not r.get('result_line'):
                continue
            c = r['result_line']['counts']
            if c.get('passed', 0) > 0 and c.get('failed', 0) == 0 and c.get('error', 0) == 0:
                ok_dirs.append((r['directory'], c.get('passed', 0), c.get('skipped', 0),
                               r['result_line']['duration_str']))
    ok_dirs.sort()

    # ===== MARKDOWN OUTPUT =====
    P = print

    P("# SONiC VS Test Results — Parallel LXD Run")
    P()

    # --- Grand Summary ---
    P("## Summary")
    P()
    P("| Metric | Raw | Adjusted (excl. VS-incompatible) |")
    P("|--------|-----|----------------------------------|")
    P(f"| Workers | {len(all_results)} | — |")
    P(f"| Directories completed | {grand_dirs} | {grand_dirs - len(excluded_dirs)} |")
    P(f"| Directories incomplete | {len(all_incomplete)} | — |")
    P(f"| Total tests | {total_tests} | {adj_total} |")
    P(f"| ✅ Passed | {grand_passed} | {adj_passed} |")
    P(f"| ❌ Failed | {grand_failed} | {adj_failed} |")
    P(f"| ⏭️ Skipped | {grand_skipped} | {adj_skipped} |")
    P(f"| ⚠️ Errors | {grand_error} | {adj_error} |")
    P(f"| **Pass rate (of executed)** | **{exec_rate:.1f}%** ({grand_passed}/{exec_total}) "
      f"| **{adj_rate:.1f}%** ({adj_passed}/{adj_executed}) |")
    P(f"| Wall clock | {format_duration(grand_duration)} | — |")
    P()

    # --- Worker Overview ---
    P("## Worker Overview")
    P()
    P("| Worker | Dirs | Incomplete | ✅ | ❌ | ⏭️ | ⚠️ | Duration |")
    P("|--------|------|------------|-----|-----|-----|-----|----------|")
    for wid in sorted(worker_stats):
        ws = worker_stats[wid]
        inc = len(ws['incomplete'])
        inc_s = str(inc) if inc else '—'
        P(f"| W{wid} | {len(ws['completed'])} | {inc_s} | {ws['passed']} | {ws['failed']} "
          f"| {ws['skipped']} | {ws['error']} | {format_duration(ws['duration'])} |")
    P()

    # --- Per-Worker Detail ---
    P("## Per-Worker Results")
    for worker_id in sorted(all_results.keys()):
        results = all_results[worker_id]
        ws = worker_stats[worker_id]
        inc = len(ws['incomplete'])
        inc_s = f" ({inc} incomplete)" if inc else ""
        P()
        P(f"### Worker {worker_id} — {len(ws['completed'])} dirs{inc_s}, "
          f"✅{ws['passed']} ❌{ws['failed']} ⏭️{ws['skipped']} ⚠️{ws['error']}, "
          f"{format_duration(ws['duration'])}")
        P()
        P("| Status | Directory | Passed | Failed | Skipped | Error | Duration |")
        P("|--------|-----------|--------|--------|---------|-------|----------|")

        for r in results:
            if r.get('incomplete'):
                P(f"| 💀 | `{r['directory']}` | — | — | — | — | *(incomplete)* |")
                continue
            c = r['result_line']['counts']
            p = c.get('passed', 0)
            f = c.get('failed', 0)
            s = c.get('skipped', 0)
            e = c.get('error', 0)
            d = r['result_line']['duration_str']
            em = status_emoji(c)
            P(f"| {em} | `{r['directory']}` | {p} | {f} | {s} | {e} | {d} |")

        # Collect failure/error info
        for r in results:
            if r.get('incomplete'):
                continue
            for ft_type, ft_name in r.get('failed_tests', []):
                if ft_type == 'FAILED':
                    all_failed_tests.append((worker_id, r['directory'], ft_name))
                else:
                    all_error_tests.append((worker_id, r['directory'], ft_name))

    P()

    # --- 100% Passing ---
    P("## ✅ 100% Passing Directories")
    P()
    P(f"> **{len(ok_dirs)}** directories passed all tests with zero failures/errors.")
    P()
    P("| Directory | Passed | Skipped | Duration |")
    P("|-----------|--------|---------|----------|")
    for d, p, s, dur in ok_dirs:
        s_str = str(s) if s > 0 else '—'
        P(f"| `{d}` | {p} | {s_str} | {dur} |")
    P()

    # --- Incomplete ---
    if all_incomplete:
        P("## 💀 Incomplete Directories")
        P()
        P(f"> **{len(all_incomplete)}** directories started but the worker exited before pytest finished.")
        P()
        P("| Worker | Directory | Declared Tests |")
        P("|--------|-----------|----------------|")
        for wid, d, dt in sorted(all_incomplete, key=lambda x: x[1]):
            P(f"| W{wid} | `{d}` | {dt} |")
        P()

    # --- VS-Incompatible ---
    P("## ⏭️ VS-Incompatible Directories (excluded from adjusted rate)")
    P()
    excluded_total = excluded_passed + excluded_failed + excluded_skipped + excluded_error
    P(f"> **{len(excluded_dirs)}** directories ({excluded_total} tests) are not meaningful on the VS platform.")
    P()
    P("| Directory | Passed | Failed | Skipped | Error | Reason |")
    P("|-----------|--------|--------|---------|-------|--------|")
    for d, wid, c in sorted(excluded_dirs):
        reason = vs_incompatible.get(d, '')
        p = c.get('passed', 0)
        f = c.get('failed', 0)
        s = c.get('skipped', 0)
        e = c.get('error', 0)
        P(f"| `{d}` | {p} | {f} | {s} | {e} | {reason} |")
    P()

    # --- Slowest ---
    P("## 🐢 Slowest Directories (top 15)")
    P()
    all_dirs_sorted = []
    for wid, results in all_results.items():
        for r in results:
            if r.get('incomplete') or not r.get('result_line'):
                continue
            all_dirs_sorted.append((r['result_line']['duration_secs'], r['directory'], wid, r['result_line']['counts']))
    all_dirs_sorted.sort(reverse=True)
    P("| Duration | Worker | Directory | Passed | Failed | Error |")
    P("|----------|--------|-----------|--------|--------|-------|")
    for dur, d, wid, c in all_dirs_sorted[:15]:
        p = c.get('passed', 0)
        f = c.get('failed', 0)
        e = c.get('error', 0)
        P(f"| {format_duration(dur)} | W{wid} | `{d}` | {p} | {f} | {e} |")
    P()

    # --- All Failures & Errors ---
    if all_failed_tests or all_error_tests:
        P("## ❌ All Failures & Errors")
        P()
        P(f"> **{len(all_failed_tests)}** failures, **{len(all_error_tests)}** errors")
        P()

        by_dir = defaultdict(list)
        for wid, d, t in all_failed_tests:
            by_dir[d].append(('FAILED', wid, t))
        for wid, d, t in all_error_tests:
            by_dir[d].append(('ERROR', wid, t))

        for d in sorted(by_dir.keys()):
            P(f"<details><summary><code>{d}</code> ({len(by_dir[d])} items)</summary>")
            P()
            for typ, wid, t in by_dir[d]:
                t_short = t[:120] + '...' if len(t) > 120 else t
                icon = '❌' if typ == 'FAILED' else '⚠️'
                P(f"- {icon} W{wid} `{t_short}`")
            P()
            P("</details>")
            P()


if __name__ == '__main__':
    main()
