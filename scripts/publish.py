import argparse
import shutil
import subprocess
import sys
import toml
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / "pypi_config.toml"
DIST_DIR = REPO_ROOT / "dist"


def load_config(repo: str) -> dict:
    if not CONFIG_PATH.exists():
        print(f"Config file not found: {CONFIG_PATH}")
        print(f"Copy pypi_config.toml.example to pypi_config.toml and set your token.")
        sys.exit(1)

    cfg = toml.load(CONFIG_PATH)
    if repo not in cfg:
        print(f"Unknown repository: {repo}")
        print(f"Available: {', '.join(cfg.keys())}")
        sys.exit(1)

    entry = cfg[repo]
    if not entry.get("password"):
        print(f"Token for '{repo}' is empty. Set it in {CONFIG_PATH}")
        sys.exit(1)

    return entry


def build():
    print("Building package ...")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("Build failed")
        sys.exit(result.returncode)
    print("Build done.")


def upload(repo_config: dict):
    print("Uploading to PyPI ...")
    cmd = [
        sys.executable, "-m", "twine", "upload",
        "--repository-url", repo_config["repository"],
        "-u", repo_config["username"],
        "-p", repo_config["password"],
        str(DIST_DIR / "*"),
    ]
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        print("Upload failed")
        sys.exit(result.returncode)
    print("Upload done.")


def main():
    parser = argparse.ArgumentParser(description="Build and upload to PyPI")
    parser.add_argument(
        "--repo", default="pypi",
        choices=["pypi", "testpypi"],
        help="Target repository (default: pypi)",
    )
    parser.add_argument("--build-only", action="store_true", help="Build only, skip upload")
    args = parser.parse_args()

    repo_config = load_config(args.repo)

    build()

    if not args.build_only:
        upload(repo_config)


if __name__ == "__main__":
    main()
