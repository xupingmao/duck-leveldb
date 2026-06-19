from setuptools import setup, find_packages

setup(
    name="duck-leveldb",
    version="0.1.0",
    description="Cross-platform LevelDB interface for Python",
    packages=find_packages(),
    package_data={"duck_leveldb": ["../libs/leveldb.dll"]},
    python_requires=">=3.6",
)
