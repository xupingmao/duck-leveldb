import sys

try:
    import plyvel
    from duck_leveldb._plyvel_backend import LevelDB, Iterator
except ImportError:
    from duck_leveldb._ctypes_backend import LevelDB, Iterator
