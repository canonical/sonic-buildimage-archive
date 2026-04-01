#!/usr/bin/env python3
"""
Scan sonic-mgmt/tests for all test files compatible with t0 topology.

Usage:
    python3 scan_t0_tests.py /path/to/sonic-mgmt/tests > upstream_t0_tests.txt

Reads pytest.mark.topology(...) markers from each test_*.py file and outputs
those matching t0-compatible topologies (t0, t0-*, any), one per line.
"""
import os
import re
import sys

SKIP_FOLDERS = {
    "ptftests", "acstests", "saitests", "scripts", "k8s", "sai_qualify",
    "__pycache__", ".pytest_cache", "common",
}

T0_TOPOS = {"t0", "t0-16", "t0-56", "t0-64", "t0-116", "t0-120", "any"}

SKIP_FILES = {"test_pretest.py", "test_posttest.py"}


def scan(tests_dir):
    results = []
    for root, dirs, files in os.walk(tests_dir):
        rel_root = os.path.relpath(root, tests_dir)
        top_folder = rel_root.split("/")[0]
        if top_folder in SKIP_FOLDERS:
            continue
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

        for fname in sorted(files):
            if not fname.startswith("test_") or not fname.endswith(".py"):
                continue
            if fname in SKIP_FILES:
                continue

            fpath = os.path.join(root, fname)
            try:
                with open(fpath) as f:
                    content = f.read()
            except OSError:
                continue

            markers = re.findall(r"pytest\.mark\.topology\(([^)]+)\)", content)
            if not markers:
                continue

            topos = set()
            for m in markers:
                topos.update(re.findall(r"""['"]([^'"]+)['"]""", m))

            if topos & T0_TOPOS:
                results.append(os.path.relpath(fpath, tests_dir))

    results.sort()
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <sonic-mgmt-tests-dir>", file=sys.stderr)
        sys.exit(1)

    tests_dir = sys.argv[1]
    if not os.path.isdir(tests_dir):
        print(f"Error: {tests_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    results = scan(tests_dir)
    print(f"# {len(results)} t0-compatible tests from {tests_dir}", file=sys.stderr)
    for r in results:
        print(r)
