import os
import ctypes
from ctypes import byref, c_char_p, c_size_t, c_ubyte, c_void_p, POINTER
from pathlib import Path


def _find_dll():
    search_dirs = [
        os.path.join(os.path.dirname(__file__), "..", "libs"),
        os.path.dirname(__file__),
        os.environ.get("LEVELDB_DLL", ""),
    ]
    for d in search_dirs:
        if d and os.path.isdir(d):
            p = os.path.join(d, "leveldb.dll")
            if os.path.exists(p):
                return p
        elif d and os.path.isfile(d):
            return d
    raise RuntimeError(
        "leveldb.dll not found. Place it in duck_leveldb/libs/ "
        "or set LEVELDB_DLL env var."
    )


def _load_dll():
    dll = ctypes.CDLL(_find_dll())

    dll.leveldb_options_create.restype = c_void_p
    dll.leveldb_options_create.argtypes = []
    dll.leveldb_options_destroy.argtypes = [c_void_p]
    dll.leveldb_options_destroy.restype = None
    dll.leveldb_options_set_create_if_missing.argtypes = [c_void_p, c_ubyte]
    dll.leveldb_options_set_create_if_missing.restype = None

    dll.leveldb_open.restype = c_void_p
    dll.leveldb_open.argtypes = [c_void_p, c_char_p, POINTER(c_char_p)]
    dll.leveldb_close.argtypes = [c_void_p]
    dll.leveldb_close.restype = None

    dll.leveldb_readoptions_create.restype = c_void_p
    dll.leveldb_readoptions_create.argtypes = []
    dll.leveldb_readoptions_destroy.argtypes = [c_void_p]
    dll.leveldb_readoptions_destroy.restype = None

    dll.leveldb_writeoptions_create.restype = c_void_p
    dll.leveldb_writeoptions_create.argtypes = []
    dll.leveldb_writeoptions_destroy.argtypes = [c_void_p]
    dll.leveldb_writeoptions_destroy.restype = None

    dll.leveldb_get.restype = c_void_p
    dll.leveldb_get.argtypes = [
        c_void_p, c_void_p, c_char_p, c_size_t,
        POINTER(c_size_t), POINTER(c_char_p),
    ]

    dll.leveldb_put.restype = None
    dll.leveldb_put.argtypes = [
        c_void_p, c_void_p, c_char_p, c_size_t,
        c_char_p, c_size_t, POINTER(c_char_p),
    ]

    dll.leveldb_delete.restype = None
    dll.leveldb_delete.argtypes = [
        c_void_p, c_void_p, c_char_p, c_size_t, POINTER(c_char_p),
    ]

    dll.leveldb_free.argtypes = [c_void_p]
    dll.leveldb_free.restype = None

    dll.leveldb_create_iterator.restype = c_void_p
    dll.leveldb_create_iterator.argtypes = [c_void_p, c_void_p]

    dll.leveldb_iter_destroy.argtypes = [c_void_p]
    dll.leveldb_iter_destroy.restype = None
    dll.leveldb_iter_seek_to_first.argtypes = [c_void_p]
    dll.leveldb_iter_seek_to_first.restype = None
    dll.leveldb_iter_seek_to_last.argtypes = [c_void_p]
    dll.leveldb_iter_seek_to_last.restype = None
    dll.leveldb_iter_seek.argtypes = [c_void_p, c_char_p, c_size_t]
    dll.leveldb_iter_seek.restype = None
    dll.leveldb_iter_next.argtypes = [c_void_p]
    dll.leveldb_iter_next.restype = None
    dll.leveldb_iter_prev.argtypes = [c_void_p]
    dll.leveldb_iter_prev.restype = None
    dll.leveldb_iter_valid.argtypes = [c_void_p]
    dll.leveldb_iter_valid.restype = c_ubyte
    dll.leveldb_iter_key.argtypes = [c_void_p, POINTER(c_size_t)]
    dll.leveldb_iter_key.restype = c_void_p
    dll.leveldb_iter_value.argtypes = [c_void_p, POINTER(c_size_t)]
    dll.leveldb_iter_value.restype = c_void_p

    return dll


_dll = None


def _get_dll():
    global _dll
    if _dll is None:
        _dll = _load_dll()
    return _dll


class Iterator:
    def __init__(self, it_ptr):
        self._iter = it_ptr
        self._closed = False

    def close(self):
        if self._closed:
            return
        self._closed = True
        _get_dll().leveldb_iter_destroy(self._iter)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def seek_to_first(self):
        _get_dll().leveldb_iter_seek_to_first(self._iter)

    def seek_to_last(self):
        _get_dll().leveldb_iter_seek_to_last(self._iter)

    def seek(self, key: bytes):
        _get_dll().leveldb_iter_seek(self._iter, key, len(key))

    def next(self):
        _get_dll().leveldb_iter_next(self._iter)

    def prev(self):
        _get_dll().leveldb_iter_prev(self._iter)

    def valid(self):
        return bool(_get_dll().leveldb_iter_valid(self._iter))

    def key(self):
        klen = c_size_t()
        raw = _get_dll().leveldb_iter_key(self._iter, byref(klen))
        return ctypes.string_at(raw, klen.value)

    def value(self):
        vlen = c_size_t()
        raw = _get_dll().leveldb_iter_value(self._iter, byref(vlen))
        return ctypes.string_at(raw, vlen.value)

    def __iter__(self):
        self.seek_to_first()
        return self

    def __next__(self):
        if not self.valid():
            raise StopIteration
        k = self.key()
        v = self.value()
        self.next()
        return (k, v)


class LevelDB:
    def __init__(self, db_path: str, create: bool = True):
        dll = _get_dll()
        self._db_path = Path(db_path).resolve()
        self._db_path.mkdir(parents=True, exist_ok=True)
        self._options = dll.leveldb_options_create()
        if not self._options:
            raise MemoryError("leveldb_options_create failed")
        dll.leveldb_options_set_create_if_missing(self._options, c_ubyte(1 if create else 0))

        err = c_char_p()
        self._db = dll.leveldb_open(self._options, str(self._db_path).encode("utf-8"), byref(err))
        if err.value is not None:
            msg = err.value.decode("utf-8", errors="replace")
            dll.leveldb_free(err)
            raise RuntimeError(f"leveldb_open failed: {msg}")
        if not self._db:
            raise RuntimeError("leveldb_open returned NULL")

        self._read_options = dll.leveldb_readoptions_create()
        self._write_options = dll.leveldb_writeoptions_create()
        self._closed = False

    def close(self):
        if self._closed:
            return
        self._closed = True
        dll = _get_dll()
        dll.leveldb_readoptions_destroy(self._read_options)
        dll.leveldb_writeoptions_destroy(self._write_options)
        dll.leveldb_close(self._db)
        dll.leveldb_options_destroy(self._options)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def get(self, key: bytes):
        dll = _get_dll()
        vallen = c_size_t()
        err = c_char_p()
        raw = dll.leveldb_get(self._db, self._read_options, key, len(key), byref(vallen), byref(err))
        if err.value is not None:
            msg = err.value.decode("utf-8", errors="replace")
            dll.leveldb_free(err)
            raise RuntimeError(f"leveldb_get failed: {msg}")
        if not raw:
            return None
        val = ctypes.string_at(raw, vallen.value)
        dll.leveldb_free(raw)
        return val

    def put(self, key: bytes, value: bytes):
        dll = _get_dll()
        err = c_char_p()
        dll.leveldb_put(self._db, self._write_options, key, len(key), value, len(value), byref(err))
        if err.value is not None:
            msg = err.value.decode("utf-8", errors="replace")
            dll.leveldb_free(err)
            raise RuntimeError(f"leveldb_put failed: {msg}")

    def delete(self, key: bytes):
        dll = _get_dll()
        err = c_char_p()
        dll.leveldb_delete(self._db, self._write_options, key, len(key), byref(err))
        if err.value is not None:
            msg = err.value.decode("utf-8", errors="replace")
            dll.leveldb_free(err)
            raise RuntimeError(f"leveldb_delete failed: {msg}")

    def iterator(self):
        dll = _get_dll()
        it = dll.leveldb_create_iterator(self._db, self._read_options)
        if not it:
            raise MemoryError("leveldb_create_iterator failed")
        return Iterator(it)
