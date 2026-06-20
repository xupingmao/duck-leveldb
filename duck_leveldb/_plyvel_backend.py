import plyvel


class Iterator:
    def __init__(self, it):
        self._it = it
        self._closed = False
        self._current = None
        self.seek_to_first()

    def _read(self):
        try:
            self._current = next(self._it)
        except StopIteration:
            self._current = None

    def _prev_raw(self):
        try:
            self._it.prev()
            return True
        except StopIteration:
            return False

    def seek_to_first(self):
        self._it.seek_to_start()
        self._read()

    def seek_to_last(self):
        self._it.seek_to_stop()
        if not self._prev_raw():
            self._current = None
            return
        self._read()

    def seek(self, key: bytes):
        self._it.seek(key)
        self._read()

    def valid(self):
        return self._current is not None

    def key(self):
        return self._current[0] if self._current is not None else None

    def value(self):
        return self._current[1] if self._current is not None else None

    def next(self):
        self._read()

    def prev(self):
        if not self._prev_raw():
            self._current = None
            return
        if not self._prev_raw():
            self._current = None
            return
        self._read()

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._it.close()
        self._current = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self._current is None:
            raise StopIteration
        k, v = self._current
        self.next()
        return (k, v)


class LevelDB:
    def __init__(self, db_path: str, create: bool = True):
        try:
            self._db = plyvel.DB(db_path, create_if_missing=create)
        except Exception as e:
            raise RuntimeError(str(e)) from e

    def close(self):
        db = getattr(self, "_db", None)
        if db is not None:
            db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def get(self, key: bytes):
        return self._db.get(key)

    def put(self, key: bytes, value: bytes):
        self._db.put(key, value)

    def delete(self, key: bytes):
        self._db.delete(key)

    def iterator(self):
        return Iterator(self._db.iterator())
