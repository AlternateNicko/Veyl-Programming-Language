# VeylPL/Test/benchmark.py
"""
Tests Veyl by execution speed. Loads every .vey/.json pair from
Test_code/Benchmark, runs each program, and scores how close the actual
execution time came to the "speed" value declared in its .json metadata.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_harness import (
    load_veyl_module, run_vey_program, load_test_cases,
    closeness_score, TEST_CODE_ROOT,
)


def run_benchmark_tests(veyl_module=None):
    """
    Runs every Benchmark test case. Returns:
        {
            "score": float,       # 0.0-1.0, mean across all test cases
            "results": [ {...} ]  # per-test detail for reporting/debugging
        }
    A test case is skipped from scoring (but still reported) if its
    "speed" field is None, per the spec ("None for optional").
    """
    if veyl_module is None:
        veyl_module = load_veyl_module()

    cases = load_test_cases(TEST_CODE_ROOT / "Benchmark")
    results = []

    for case in cases:
        meta = case["meta"]
        expected_speed = meta.get("speed")
        run = run_vey_program(veyl_module, case["code"])

        entry = {
            "name": case["name"],
            "expected_speed": expected_speed,
            "actual_speed": run["elapsed"],
            "python_exception": run["python_exception"],
        }

        if run["python_exception"] is not None:
            entry["score"] = 0.0
            entry["note"] = "Python exception escaped the interpreter - automatic 0"
        elif expected_speed is None:
            entry["score"] = None  # not scored, informational only
            entry["note"] = "no expected speed given, skipped from scoring"
        else:
            entry["score"] = closeness_score(run["elapsed"], expected_speed)

        results.append(entry)

    scored = [r["score"] for r in results if r["score"] is not None]
    overall = sum(scored) / len(scored) if scored else None

    return {"score": overall, "results": results}


def _print_report(report):
    print("=== Benchmark Results ===")
    for r in report["results"]:
        status = "SKIPPED" if r["score"] is None else f"{r['score'] * 100:.1f}%"
        print(f"  {r['name']:<20} expected={r['expected_speed']}  actual={r['actual_speed']:.4f}s  score={status}")
        if r["python_exception"]:
            print(f"    !! Python exception: {r['python_exception'].splitlines()[-1]}")
    overall = report["score"]
    print(f"\nOverall benchmark score: {overall * 100:.1f}%" if overall is not None else "\nOverall benchmark score: N/A (no scorable cases)")


if __name__ == "__main__":
    report = run_benchmark_tests()
    _print_report(report)