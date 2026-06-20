import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = REPO_ROOT / ".venv"
REPORT_DIR = REPO_ROOT / "test_reports"
JUNIT_XML = REPORT_DIR / "results.xml"
COV_HTML = REPORT_DIR / "coverage"
LIBS_DIR = REPO_ROOT / "libs"

def _bootstrap_venv():
    if not VENV_DIR.exists():
        return

    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        return

    venv_python = VENV_DIR / "bin" / "python"
    if not venv_python.exists():
        return

    has_pip = (VENV_DIR / "bin" / "pip").exists()
    if not has_pip:
        print("Installing pip into .venv ...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--target",
             str(VENV_DIR / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"),
             "--upgrade", "pip"],
            capture_output=True, check=False,
            env={**os.environ, "PIP_BREAK_SYSTEM_PACKAGES": "1"},
        )

    os.environ.setdefault("PIP_REQUIRE_VIRTUALENV", "false")
    os.execv(str(venv_python), [str(venv_python), *sys.argv])


_bootstrap_venv()

def _ensure_installed(missing: list[str]):
    if not _importable("duck_leveldb"):
        missing.append(str(REPO_ROOT))

    if not missing:
        return

    print(f"Missing dependencies: {' '.join(missing)}")
    pip = _find_pip()
    env = {**os.environ, "PIP_BREAK_SYSTEM_PACKAGES": "1"}

    args = []
    for pkg in missing:
        if pkg.startswith("/") or pkg.startswith("."):
            args += ["-e", pkg]
        else:
            args.append(pkg)

    result = subprocess.run(
        [*pip, "install", *args],
        capture_output=True, text=True, env=env,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    os.execv(sys.executable, [sys.executable, *sys.argv])


REQUIRED = ["pytest"]
REQUIRED_COV = ["pytest-cov", "coverage"]
OPTIONAL = ["plyvel"]


def _find_pip():
    candidates = [
        [sys.executable, "-m", "pip"],
        [sys.executable, "-m", "pip3"],
        ["pip3"],
        ["pip"],
    ]
    for cmd in candidates:
        try:
            r = subprocess.run([*cmd, "--version"], capture_output=True, text=True)
            if r.returncode == 0:
                return cmd
        except FileNotFoundError:
            continue
    print("pip not found", file=sys.stderr)
    sys.exit(1)


def check_env(use_coverage: bool):
    missing = [p for p in REQUIRED if not _importable(p)]
    if use_coverage:
        missing += [p for p in REQUIRED_COV if not _importable(p)]

    _ensure_installed(missing)

    if not (LIBS_DIR / "leveldb.dll").exists():
        print(f"Warning: leveldb.dll not found in {LIBS_DIR}", file=sys.stderr)

    try:
        import duck_leveldb  # noqa: F401
    except ImportError as e:
        print(f"duck_leveldb import failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"duck_leveldb backend init failed: {e}", file=sys.stderr)
        sys.exit(1)

    available = [p for p in OPTIONAL if _importable(p)]
    if not available:
        print("plyvel not available, will use ctypes backend")


def _importable(name: str) -> bool:
    if name == "pytest-cov":
        name = "pytest_cov"
    try:
        __import__(name.replace("-", "_"))
        return True
    except ImportError:
        return False


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

    use_coverage = not args.no_cov

    print("Checking environment ...")
    check_env(use_coverage)

    clear_reports()

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
