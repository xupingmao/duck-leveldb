import plyvel


class Iterator:
    def __init__(self, it):
        self._it = it
        self._it.seek_to_first()

    def seek_to_first(self):
        self._it.seek_to_first()

    def seek_to_last(self):
        self._it.seek_to_last()

    def seek(self, key: bytes):
        self._it.seek(key)

    def valid(self):
        return self._it.valid()

    def key(self):
        return self._it.key()

    def value(self):
        return self._it.value()

    def next(self):
        self._it.next()

    def prev(self):
        self._it.prev()

    def close(self):
        del self._it

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class LevelDB:
    def __init__(self, db_path: str, create: bool = True):
        self._db = plyvel.DB(db_path, create_if_missing=create)

    def close(self):
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def get(self, key: bytes):
        return self._db.get(key)

    def put(self, key: bytes, value: bytes):
        self._db.put(key, value)

    def delete(self, key: bytes):
        self._db.delete(key)

    def iterator(self):
        return Iterator(self._db.iterator())
