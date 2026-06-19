from pathlib import Path

from setuptools import setup, find_packages


HERE = Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name="duck_leveldb",
    version="1.0.0-20260620",
    description="Cross-platform LevelDB interface for Python",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={"duck_leveldb": ["../libs/leveldb.dll"]},
    python_requires=">=3.6",
)
