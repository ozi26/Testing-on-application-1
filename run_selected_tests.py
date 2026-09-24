#!/usr/bin/env python3
# =============================================================================
# RUN SELECTED TESTS (Multi-Language Version)
# Reads analyzer_result.json and runs the affected tests using the
# appropriate test runner for each language.
# =============================================================================

import json
import sys
from pathlib import Path

# Make the project importable
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from analyzer.test_runners import group_tests_by_runner, run_tests_for_group


def main():
    # -------------------------------------------------------------------------
    # Step 1: Read the analyzer results
    # -------------------------------------------------------------------------
    result_file = Path("analyzer_result.json")
    
    if not result_file.exists():
        print("ERROR: analyzer_result.json not found!")
        print("Run the analyzer first: python scripts/run_analyzer.py")
        sys.exit(1)
    
    with open(result_file, "r", encoding="utf-8") as f:
        result = json.load(f)
    
    if not result.get("has_affected_tests", False):
        print("=" * 60)
        print("NO AFFECTED TESTS — Skipping test execution")
        print("=" * 60)
        sys.exit(0)
    
    affected_tests = result["affected_tests"]
    
    # -------------------------------------------------------------------------
    # Step 2: Group tests by their required runner
    # -------------------------------------------------------------------------
    groups = group_tests_by_runner(affected_tests)
    
    print("=" * 60)
    print(f"Running {len(affected_tests)} affected test file(s)")
    print(f"Grouped into {len(groups)} test runner(s)")
    print("=" * 60)
    
    for runner_name, (_, files) in groups.items():
        print(f"\n{runner_name}:")
        for f in files:
            print(f"  - {f}")
    
    # -------------------------------------------------------------------------
    # Step 3: Run each group with its test runner
    # -------------------------------------------------------------------------
    overall_exit_code = 0
    
    for runner_name, (runner, files) in groups.items():
        print(f"\n{'=' * 60}")
        print(f"Executing: {runner_name}")
        print(f"{'=' * 60}")
        
        code = run_tests_for_group(runner, files)
        overall_exit_code = max(overall_exit_code, code)
    
    # -------------------------------------------------------------------------
    # Step 4: Exit with the worst exit code (0 = all passed)
    # -------------------------------------------------------------------------
    if overall_exit_code == 0:
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print(f"SOME TESTS FAILED (exit code {overall_exit_code})")
        print("=" * 60)
    
    sys.exit(overall_exit_code)


if __name__ == "__main__":
    main()