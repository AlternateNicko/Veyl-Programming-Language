# VeylPL/Test/syntax.py
"""
Tests VeylPL syntax, built-in functions, and built-in methods (including
multi-use cases) by running each Test_code/Syntax case and comparing actual
stdout output against the expected output declared in its .json metadata.
"""
import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_harness import (
    load_veyl_module, run_eps_program, load_test_cases, TEST_CODE_ROOT,
)


def _output_similarity(actual, expected):
    """
    Partial-credit comparison between actual stdout and expected output.
    Exact match (modulo trailing whitespace) = 1.0. Otherwise uses
    difflib's SequenceMatcher ratio for a graded "how close" score rather
    than a strict binary pass/fail, since the spec calls for output
    accuracy to "decrease" on mismatch rather than simply fail.
    """
    a = actual.strip()
    e = str(expected).strip()
    if a == e:
        return 1.0
    return difflib.SequenceMatcher(None, a, e).ratio()


def run_syntax_tests(veyl_module=None):
    """
    Runs every Syntax test case. Returns:
        {"score": float, "results": [ {...} ]}

    Scoring per spec:
      - any error (Python exception OR an Veyl self.Errors flag set) = 0.0
      - otherwise, output similarity to "expected" (graded, see above)
      - "expected": None means the case is pure syntax-validity checking -
        score is 1.0 if it ran clean, 0.0 if anything errored
    """
    if veyl_module is None:
        veyl_module = load_veyl_module()

    cases = load_test_cases(TEST_CODE_ROOT / "Syntax")
    results = []

    for case in cases:
        meta = case["meta"]
        expected = meta.get("expected")
        run = run_eps_program(veyl_module, case["code"])

        had_veyl_error = bool(run["errors"]) and any(run["errors"].values())
        had_python_error = run["python_exception"] is not None

        entry = {
            "name": case["name"],
            "expected": expected,
            "actual_stdout": run["stdout"],
            "python_exception": run["python_exception"],
            "veyl_errors": {k: v for k, v in (run["errors"] or {}).items() if v},
        }

        if had_python_error or had_veyl_error:
            entry["score"] = 0.0
            entry["note"] = "python exception" if had_python_error else "unexpected veyl error raised"
        elif expected is None:
            entry["score"] = 1.0
            entry["note"] = "syntax-validity check only, ran clean"
        else:
            entry["score"] = _output_similarity(run["stdout"], expected)

        results.append(entry)

    scored = [r["score"] for r in results]
    overall = sum(scored) / len(scored) if scored else None
    return {"score": overall, "results": results}


def _print_report(report):
    print("=== Syntax Results ===")
    for r in report["results"]:
        print(f"  {r['name']:<20} score={r['score'] * 100:.1f}%")
        if r["score"] < 1.0:
            if r["python_exception"]:
                print(f"    !! Python exception: {r['python_exception'].splitlines()[-1]}")
            elif r["veyl_errors"]:
                print(f"    !! Veyl error(s): {list(r['veyl_errors'].keys())}")
            elif r["expected"] is not None:
                print(f"    expected: {r['expected']!r}")
                print(f"    actual  : {r['actual_stdout'].strip()!r}")
    overall = report["score"]
    print(f"\nOverall syntax score: {overall * 100:.1f}%" if overall is not None else "\nOverall syntax score: N/A (no test cases found)")


if __name__ == "__main__":
    report = run_syntax_tests()
    _print_report(report)