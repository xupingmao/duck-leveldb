import os
import sys


if sys.platform == "win32":
    try:
        import plyvel  # noqa: F401
        from duck_leveldb._plyvel_backend import LevelDB, Iterator
    except ImportError:
        from duck_leveldb._ctypes_backend import LevelDB, Iterator
else:
    import plyvel  # noqa: F401
    from duck_leveldb._plyvel_backend import LevelDB, Iterator
