# VeylPL/Test/test_harness.py
"""
Shared infrastructure used by benchmark.py, syntax.py, error_test.py, and
unique.py. Handles loading a specific veyl.py version, running a .vey
program against it while capturing stdout/timing/errors, and loading
.vey + .json test case pairs from a Test_code subfolder.
"""
import importlib.util
import io
import json
import re
import sys
import time
import traceback
from contextlib import redirect_stdout
from pathlib import Path

# Root of the VeylPL project - Test/ is one level below this
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_CODE_ROOT = PROJECT_ROOT / "Test_code"
VERSIONS_ROOT = PROJECT_ROOT / "versions"

VERSION_FILENAME_RE = re.compile(r"^veyl_v(\d+)\.py$")


def discover_versions():
    """
    Finds every versions/veyl_vXXX.py file. Returns a list of dicts
    sorted oldest-to-newest by the numeric version tag in the filename:
        {"tag": "v105", "path": Path(...)}
    "tag" is just the filename's version marker (e.g. "v105") - the real,
    authoritative version string comes from self.version once the module
    is actually loaded and an VEY instance exists (see get_version_string).
    """
    versions = []
    for path in VERSIONS_ROOT.glob("veyl_v*.py"):
        match = VERSION_FILENAME_RE.match(path.name)
        if not match:
            continue
        versions.append({"tag": f"v{match.group(1)}", "path": path})
    versions.sort(key=lambda v: int(v["tag"][1:]))
    return versions


def load_veyl_module(veyl_path=None, module_name=None):
    """
    Loads a specific veyl.py file as a uniquely-named module and
    registers it as sys.modules["veyl"] so that built_in_libraries.py's
    lazy `from veyl import VEY` resolves to THIS version.

    veyl_path: path to the veyl.py / veyl_vXXX.py file to load.
                  Defaults to the project's current VeylPL/veyl.py.
    module_name:  unique internal name to register the module under.
                  Auto-generated from the filename if not given.

    IMPORTANT: this mutates sys.modules["veyl"] globally. Only run one
    version's tests at a time - loading a second version before the first
    finishes will corrupt in-flight VEY instances relying on the first.
    """
    if veyl_path is None:
        veyl_path = PROJECT_ROOT / "veyl.py"
    veyl_path = Path(veyl_path)

    if not veyl_path.exists():
        raise FileNotFoundError(f"veyl file not found at {veyl_path}")

    # built_in_libraries.py / error.py are shared/non-versioned - make sure
    # they're importable regardless of which folder the veyl file lives in
    for p in (str(veyl_path.parent), str(PROJECT_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)

    if module_name is None:
        module_name = veyl_path.stem  # e.g. "veyl_v105"

    spec = importlib.util.spec_from_file_location(module_name, veyl_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    sys.modules["veyl"] = module  # so built_in_libraries.py's lazy import finds THIS one
    spec.loader.exec_module(module)
    return module


def get_version_string(veyl_module):
    """
    Returns the real version string (e.g. "1.0.5") by instantiating a
    throwaway VEY and reading self.version - more reliable than parsing
    the filename, since self.version is what the language itself claims
    to be, independent of how the file happens to be named on disk.
    """
    return veyl_module.VEY("", {}).version


def run_vey_program(veyl_module, code, path=".", file_name="test", extension=".vey"):
    """
    Runs a block of veyl code against the given (already-loaded) veyl
    module. Captures stdout, wall-clock execution time, the final Errors
    dict, and any raw Python exception that escaped the interpreter
    entirely (a signal of a genuine interpreter bug, not an veyl-level
    language error).

    Returns a dict:
        {
            "stdout": str,          # everything printed via output()/print
            "elapsed": float,       # seconds
            "errors": dict | None,  # vey.Errors after running, if it got that far
            "python_exception": str | None,  # traceback text if the
                                              # interpreter itself crashed
        }
    """
    buffer = io.StringIO()
    result = {"stdout": "", "elapsed": None, "errors": None, "python_exception": None}
    vey = None
    start = time.perf_counter()
    try:
        with redirect_stdout(buffer):
            vey = veyl_module.VEY(code, {}, path, file_name, extension)
            vey.execute()
    except Exception:
        result["python_exception"] = traceback.format_exc()
    finally:
        result["elapsed"] = time.perf_counter() - start
        result["stdout"] = buffer.getvalue()
        if vey is not None:
            result["errors"] = dict(vey.Errors)
    return result


def load_test_cases(category_folder):
    """
    Loads every matching .vey + .json pair from a Test_code subfolder
    (e.g. Test_code/Benchmark). Each .json is expected to have a matching
    .vey file with the same stem. Skips any .json missing its .vey pair
    (and vice versa) and reports them rather than silently ignoring them.

    Returns a list of dicts:
        {"name": stem, "code": vey_source_text, "meta": parsed_json_dict}
    """
    folder = Path(category_folder)
    cases = []
    skipped = []
    for json_path in sorted(folder.glob("*.json")):
        vey_path = json_path.with_suffix(".vey")
        if not vey_path.exists():
            skipped.append(json_path.name)
            continue
        with open(json_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        with open(vey_path, "r", encoding="utf-8") as f:
            code = f.read()
        cases.append({"name": json_path.stem, "code": code, "meta": meta})
    if skipped:
        print(f"[test_harness] Warning: {len(skipped)} .json file(s) in {folder} had no matching .vey file: {skipped}")
    return cases


def closeness_score(actual, expected):
    """
    Shared scoring formula for anything measured as "how close is actual
    to expected" (currently just benchmark speed):
        score = max(0, 1 - abs(actual - expected) / abs(expected))
    Returns a 0.0-1.0 float (multiply by 100 for a percentage).
    """
    if expected == 0:
        return 1.0 if actual == 0 else 0.0
    return max(0.0, 1 - abs(actual - expected) / abs(expected))