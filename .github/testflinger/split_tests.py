#!/usr/bin/env python3
"""split_tests.py — Distribute test files across N workers, balanced by actual test count.

Uses ast to parse each test file and count test functions (def test_*).
Detects @pytest.mark.parametrize to weight parametrized tests proportionally.
Groups tests by directory (each directory = one pytest invocation) to avoid
cross-directory conftest.py conflicts.
Assigns directories to workers using greedy load-balancing (largest-first).

Usage:
    python3 split_tests.py \\
        --test-list upstream_t0_tests.txt \\
        --tests-dir /data/sonic-mgmt/tests \\
        --workers 4 \\
        --output-dir /home/tor-ci
"""

import argparse
import ast
import os
import sys
from collections import defaultdict


def count_tests_in_file(filepath):
    """Count test functions in a Python file using ast.

    For each def test_*(), counts 1.  If the function has a
    @pytest.mark.parametrize decorator with a literal list, multiplies
    by the number of parameter sets.

    Returns at least 1 (even if parsing fails) so every file has weight.
    """
    try:
        with open(filepath) as f:
            tree = ast.parse(f.read(), filename=filepath)
    except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
        return 1

    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                params = 1
                for dec in node.decorator_list:
                    if _is_parametrize(dec):
                        params *= _count_parametrize_cases(dec)
                count += params

    return max(count, 1)


def _is_parametrize(decorator):
    """Check if a decorator is pytest.mark.parametrize(...)."""
    if isinstance(decorator, ast.Call):
        func = decorator.func
        # @pytest.mark.parametrize(...)
        if isinstance(func, ast.Attribute) and func.attr == "parametrize":
            return True
    return False


def _count_parametrize_cases(decorator):
    """Count parameter sets in a @pytest.mark.parametrize(...) call."""
    if not isinstance(decorator, ast.Call) or len(decorator.args) < 2:
        return 1
    arg = decorator.args[1]
    if isinstance(arg, (ast.List, ast.Tuple)):
        return max(len(arg.elts), 1)
    return 1


def main():
    parser = argparse.ArgumentParser(
        description="Distribute sonic-mgmt tests across parallel workers"
    )
    parser.add_argument(
        "--test-list",
        required=True,
        help="File with test paths (one per line, relative to tests dir)",
    )
    parser.add_argument(
        "--tests-dir",
        required=True,
        help="Root directory containing test files (e.g. /data/sonic-mgmt/tests)",
    )
    parser.add_argument(
        "--workers", type=int, required=True, help="Number of workers"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write run_worker_N.sh scripts",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Read test list and count actual tests per file
    # ------------------------------------------------------------------
    with open(args.test_list) as f:
        test_files = [line.strip() for line in f if line.strip()]

    if not test_files:
        print("ERROR: test list is empty", file=sys.stderr)
        sys.exit(1)

    # dir -> [(relative_path, test_count), ...]
    dir_tests = defaultdict(list)
    dir_weight = defaultdict(int)

    for tf in test_files:
        filepath = os.path.join(args.tests_dir, tf)
        count = count_tests_in_file(filepath)

        directory = tf.rsplit("/", 1)[0] if "/" in tf else "."
        dir_tests[directory].append((tf, count))
        dir_weight[directory] += count

    total_weight = sum(dir_weight.values())
    print(
        f"Scanned {len(test_files)} files in {len(dir_tests)} directories: "
        f"{total_weight} test functions detected"
    )

    # ------------------------------------------------------------------
    # 2. Greedy load-balance directories across workers
    # ------------------------------------------------------------------
    sorted_dirs = sorted(dir_weight, key=dir_weight.get, reverse=True)

    worker_load = [0] * args.workers
    worker_dirs = [[] for _ in range(args.workers)]

    for d in sorted_dirs:
        # assign to the least-loaded worker
        min_idx = min(range(args.workers), key=lambda i: worker_load[i])
        worker_load[min_idx] += dir_weight[d]
        worker_dirs[min_idx].append(d)

    # ------------------------------------------------------------------
    # 3. Generate per-worker shell scripts
    # ------------------------------------------------------------------
    os.makedirs(args.output_dir, exist_ok=True)

    run_tests_cmd = (
        "docker exec -w /data/sonic-mgmt/tests mgmt"
        " ./run_tests.sh -n vms-kvm-t0 -d vlab-01"
        " -f vtestbed.yaml -i ../ansible/veos_vtb -u"
    )

    for i in range(args.workers):
        gid = i + 1
        script_path = os.path.join(args.output_dir, f"run_worker_{gid}.sh")

        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("set -e\n\n")
            f.write("# Phase 1: Deploy topology\n")
            f.write("/home/tor-ci/deploy-testbed.sh\n\n")
            f.write(
                "# Phase 2: Run tests (one pytest invocation per directory)\n"
            )
            f.write("RC=0\n")

            for d in worker_dirs[i]:
                files = dir_tests[d]
                total = dir_weight[d]
                f.write(
                    f"\necho '=== Directory: {d}"
                    f" ({total} tests from {len(files)} files) ==='\n"
                )
                f.write(run_tests_cmd)
                for tf, _ in files:
                    f.write(f" -c {tf}")
                f.write(" || RC=$?\n")

            f.write("\nexit $RC\n")

        os.chmod(script_path, 0o755)

        ndirs = len(worker_dirs[i])
        nfiles = sum(len(dir_tests[d]) for d in worker_dirs[i])
        print(
            f"  Worker {gid}: {worker_load[i]:4d} tests, "
            f"{nfiles:3d} files, {ndirs:2d} dirs"
        )


if __name__ == "__main__":
    main()
