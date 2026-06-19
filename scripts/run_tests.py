import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "test_reports"
JUNIT_XML = REPORT_DIR / "results.xml"
COV_HTML = REPORT_DIR / "coverage"


def clear_reports():
    if REPORT_DIR.exists():
        shutil.rmtree(REPORT_DIR)
    REPORT_DIR.mkdir(parents=True)


def main():
    parser = argparse.ArgumentParser(description="Run tests and generate reports")
    parser.add_argument("--no-cov", action="store_true", help="Skip coverage report")
    parser.add_argument("--open", action="store_true", help="Open coverage HTML report")
    parser.add_argument(
        "-k", dest="keyword", help="Only run tests matching the given keyword expression"
    )
    args = parser.parse_args()

    clear_reports()

    use_coverage = not args.no_cov
    runner = [sys.executable, "-m", "pytest"]

    pytest_args = [
        str(REPO_ROOT / "tests"),
        "-v",
        "--tb=short",
        f"--junitxml={JUNIT_XML}",
    ]

    if use_coverage:
        pytest_args += [
            "--cov=duck_leveldb",
            f"--cov-report=html:{COV_HTML}",
            "--cov-report=term-missing",
        ]

    if args.keyword:
        pytest_args.extend(["-k", args.keyword])

    print("Running tests ...")
    result = subprocess.run([*runner, *pytest_args], cwd=str(REPO_ROOT))
    exit_code = result.returncode

    print(f"\nJUnit XML: {JUNIT_XML}")

    if use_coverage:
        print(f"Coverage HTML: {COV_HTML}")
        if args.open:
            index = COV_HTML / "index.html"
            if index.exists():
                import webbrowser
                webbrowser.open(str(index))

    if exit_code == 0:
        print("All tests passed!")
    else:
        print(f"Some tests failed (exit code: {exit_code})")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
