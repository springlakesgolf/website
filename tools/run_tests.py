"""Run every website test in one go.

Run: python3 tools/run_tests.py            (all tests)
     python3 tools/run_tests.py dining     (only test files whose path contains "dining")

Finds every tools/**/test_*.py (run with python3 -m unittest) and every tools/**/*.test.js
(run with node --test), runs each one from the repo root, prints one line per file and
exits 1 if any file fails, if node is missing while JS tests exist, or if no tests are found.
A failing file's output is printed in full so the broken test is easy to see.
"""
import shutil, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKIP = {"node_modules", ".claude", ".git", "dist"}


def find_tests():
    def keep(p):
        return not (set(p.relative_to(REPO).parts) & SKIP)
    py = sorted(p for p in (REPO/"tools").rglob("test_*.py") if keep(p))
    js = sorted(p for p in (REPO/"tools").rglob("*.test.js") if keep(p))
    return py, js


def run(cmd):
    start = time.time()
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr, time.time() - start


def main(argv):
    py, js = find_tests()
    if argv:
        py = [p for p in py if any(a in str(p.relative_to(REPO)) for a in argv)]
        js = [p for p in js if any(a in str(p.relative_to(REPO)) for a in argv)]
    if not py and not js:
        print("No tests found.")
        return 1

    jobs = [(p, [sys.executable, "-m", "unittest", str(p.relative_to(REPO))]) for p in py]
    node = shutil.which("node")
    failed = []
    if js and not node:
        print("FAIL  node is not installed, so the JS tests cannot run:")
        for p in js:
            print("      " + str(p.relative_to(REPO)))
        failed += js
    elif js:
        jobs += [(p, [node, "--test", str(p.relative_to(REPO))]) for p in js]

    for p, cmd in jobs:
        code, out, secs = run(cmd)
        name = str(p.relative_to(REPO))
        if code == 0:
            print(f"ok    {name}  ({secs:.1f}s)")
        else:
            failed.append(p)
            print(f"FAIL  {name}  ({secs:.1f}s, exit {code})")
            print("      " + out.strip().replace("\n", "\n      "))

    total = len(py) + len(js)
    print()
    if failed:
        print(f"{len(failed)} of {total} test files failed:")
        for p in failed:
            print("  " + str(p.relative_to(REPO)))
        return 1
    print(f"All {total} test files passed ({len(py)} Python, {len(js)} JS).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
