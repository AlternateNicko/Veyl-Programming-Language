# VeylPL/Test/error_test.py
"""
Tests VeylPL's error handling/error messages. Runs every Test_code/Error
case and checks that the EXPECTED veyl-level error actually got raised
through self.Errors, rather than a raw Python exception escaping the
interpreter (which would mean the language's own error handler failed to
catch something it should have).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_harness import (
    load_veyl_module, run_vey_program, load_test_cases, TEST_CODE_ROOT,
)

# error_metadata.py's own code->name mapping, used only to sanity-check that
# a test case's ["ErrorName", code] pair is internally consistent - this is
# validating the TEST DATA, not the interpreter, so it's reported separately
# from the score.
try:
    from error_metadata import code as ERROR_CODE_MAP
except ImportError:
    ERROR_CODE_MAP = None


def _check_metadata_consistency(error_name, error_code):
    """
    Returns None if consistent, or a warning string if the test case's
    declared error name doesn't match what error_metadata.py says that
    code actually represents.
    """
    if ERROR_CODE_MAP is None:
        return "error_metadata.py not importable, skipped consistency check"
    entry = ERROR_CODE_MAP.get(error_code)
    if entry is None:
        return f"error code {error_code} does not exist in error_metadata.py"
    if entry["error"] != error_name:
        return f"error code {error_code} is actually '{entry['error']}' in error_metadata.py, not '{error_name}'"
    return None


def run_error_tests(veyl_module=None):
    """
    Runs every Error test case. Returns:
        {"score": float, "results": [ {...} ]}

    Scoring:
      - Python exception escaping the interpreter = 0.0 (this is the
        specific failure mode the spec calls out: the language's own
        error handler should have caught this, not raw Python)
      - expected error name's flag is True in vey.Errors after running = 1.0
      - any other outcome (wrong error raised, or no error raised at all) = 0.0
    """
    if veyl_module is None:
        veyl_module = load_veyl_module()

    cases = load_test_cases(TEST_CODE_ROOT / "Error")
    results = []

    for case in cases:
        meta = case["meta"]
        expected_error = meta.get("error")  # ["ErrorName", code]
        run = run_vey_program(veyl_module, case["code"])

        entry = {
            "name": case["name"],
            "expected_error": expected_error,
            "python_exception": run["python_exception"],
            "veyl_errors": {k: v for k, v in (run["errors"] or {}).items() if v},
        }

        if expected_error is None:
            entry["score"] = None
            entry["note"] = "no expected error given, skipped from scoring"
            results.append(entry)
            continue

        error_name, error_code = expected_error[0], expected_error[1]
        consistency_warning = _check_metadata_consistency(error_name, error_code)
        if consistency_warning:
            entry["metadata_warning"] = consistency_warning

        if run["python_exception"] is not None:
            entry["score"] = 0.0
            entry["note"] = "Python exception escaped - veyl's own error handler did not catch this"
        elif run["errors"] and run["errors"].get(error_name) is True:
            entry["score"] = 1.0
            entry["note"] = "expected error correctly raised"
        else:
            entry["score"] = 0.0
            entry["note"] = "expected error was not raised (or a different error was)"

        results.append(entry)

    scored = [r["score"] for r in results if r["score"] is not None]
    overall = sum(scored) / len(scored) if scored else None
    return {"score": overall, "results": results}


def _print_report(report):
    print("=== Error Handling Results ===")
    for r in report["results"]:
        status = "SKIPPED" if r["score"] is None else f"{r['score'] * 100:.1f}%"
        print(f"  {r['name']:<20} expected={r['expected_error']}  score={status}")
        if r.get("metadata_warning"):
            print(f"    !! test data warning: {r['metadata_warning']}")
        if r["score"] == 0.0:
            if r["python_exception"]:
                print(f"    !! Python exception: {r['python_exception'].splitlines()[-1]}")
            else:
                print(f"    veyl errors seen: {r['veyl_errors']}")
    overall = report["score"]
    print(f"\nOverall error-handling score: {overall * 100:.1f}%" if overall is not None else "\nOverall error-handling score: N/A")


if __name__ == "__main__":
    report = run_error_tests()
    _print_report(report)