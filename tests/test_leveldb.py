import time

import pytest

from duck_leveldb import LevelDB


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "leveldb"
    yield str(path)


@pytest.fixture
def db(db_path):
    for attempt in range(3):
        try:
            mgr = LevelDB(db_path, create=True)
        except RuntimeError:
            if attempt == 2:
                raise
            time.sleep(0.1 * (attempt + 1))
            continue
        with mgr as d:
            yield d
        return


class TestLevelDB:
    def test_put_and_get(self, db):
        db.put(b"key1", b"value1")
        assert db.get(b"key1") == b"value1"

    def test_get_missing_key(self, db):
        assert db.get(b"nonexistent") is None

    def test_put_overwrite(self, db):
        db.put(b"key", b"old")
        db.put(b"key", b"new")
        assert db.get(b"key") == b"new"

    def test_delete(self, db):
        db.put(b"key", b"value")
        db.delete(b"key")
        assert db.get(b"key") is None

    def test_delete_nonexistent(self, db):
        db.delete(b"nonexistent")

    def test_empty_key(self, db):
        db.put(b"", b"empty_key")
        assert db.get(b"") == b"empty_key"

    def test_empty_value(self, db):
        db.put(b"key", b"")
        assert db.get(b"key") == b""

    def test_binary_data(self, db):
        key = bytes(range(256))
        value = bytes(range(255, -1, -1))
        db.put(key, value)
        assert db.get(key) == value

    def test_multiple_keys(self, db):
        pairs = {f"k{i}".encode(): f"v{i}".encode() for i in range(100)}
        for k, v in pairs.items():
            db.put(k, v)
        for k, v in pairs.items():
            assert db.get(k) == v

    def test_context_manager_closes(self, db_path):
        with LevelDB(db_path, create=True) as db:
            db.put(b"ck", b"cv")
            assert db.get(b"ck") == b"cv"

    def test_double_close(self, db):
        db.put(b"x", b"y")
        db.close()
        db.close()

    def test_reopen(self, db_path):
        with LevelDB(db_path, create=True) as db:
            db.put(b"persist", b"me")
        with LevelDB(db_path, create=False) as db:
            assert db.get(b"persist") == b"me"


class TestIterator:
    def test_iterate_empty(self, db):
        it = db.iterator()
        assert list(it) == []

    def test_iterate_forward(self, db):
        db.put(b"a", b"1")
        db.put(b"b", b"2")
        db.put(b"c", b"3")
        it = db.iterator()
        assert list(it) == [(b"a", b"1"), (b"b", b"2"), (b"c", b"3")]

    def test_iterate_reverse(self, db):
        db.put(b"a", b"1")
        db.put(b"b", b"2")
        db.put(b"c", b"3")
        it = db.iterator()
        it.seek_to_last()
        assert it.valid()
        results = []
        while it.valid():
            results.append((it.key(), it.value()))
            it.prev()
        assert results == [(b"c", b"3"), (b"b", b"2"), (b"a", b"1")]

    def test_seek(self, db):
        db.put(b"a", b"1")
        db.put(b"b", b"2")
        db.put(b"d", b"4")
        it = db.iterator()
        it.seek(b"b")
        assert it.valid()
        assert it.key() == b"b"
        assert it.value() == b"2"
        it.next()
        assert it.key() == b"d"

    def test_seek_past_last(self, db):
        db.put(b"a", b"1")
        it = db.iterator()
        it.seek(b"z")
        assert not it.valid()

    def test_seek_before_first(self, db):
        db.put(b"b", b"2")
        it = db.iterator()
        it.seek(b"a")
        assert it.valid()
        assert it.key() == b"b"

    def test_seek_to_first(self, db):
        db.put(b"b", b"2")
        db.put(b"a", b"1")
        it = db.iterator()
        it.seek_to_first()
        assert it.valid()
        assert it.key() == b"a"

    def test_seek_to_last(self, db):
        db.put(b"a", b"1")
        db.put(b"c", b"3")
        it = db.iterator()
        it.seek_to_last()
        assert it.valid()
        assert it.key() == b"c"

    def test_iterator_context_manager(self, db):
        db.put(b"k", b"v")
        with db.iterator() as it:
            assert list(it) == [(b"k", b"v")]

    def test_iterator_double_close(self, db):
        it = db.iterator()
        it.close()
        it.close()

    def test_iterator_for_loop(self, db):
        db.put(b"x", b"10")
        db.put(b"y", b"20")
        results = []
        for k, v in db.iterator():
            results.append((k, v))
        assert results == [(b"x", b"10"), (b"y", b"20")]


class TestCreateWithoutCreate:
    def test_open_nonexistent_fails(self, tmp_path):
        path = str(tmp_path / "nonexistent_sub")
        with pytest.raises(RuntimeError):
            LevelDB(path, create=False)

    def test_reopen_existing_without_create(self, db_path):
        with LevelDB(db_path, create=True) as db:
            db.put(b"k", b"v")
        with LevelDB(db_path, create=False) as db:
            assert db.get(b"k") == b"v"
