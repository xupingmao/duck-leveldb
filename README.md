# duck-leveldb

Cross-platform LevelDB 接口，自动选择可用后端：**plyvel**（优先）→ **ctypes + leveldb.dll**（回退）。

Windows / Linux / macOS 均可使用，无需手动配置后端。

## 安装

```bash
pip install duck-leveldb
```

> Windows 下 ctypes 模式需要 `leveldb.dll`，已内置在包中。如果不想内置，可通过 `LEVELDB_DLL` 环境变量指定路径。

## 快速开始

```python
from duck_leveldb import LevelDB

with LevelDB("/tmp/my.db", create=True) as db:
    db.put(b"hello", b"world")
    print(db.get(b"hello"))  # b"world"

    db.delete(b"hello")
    print(db.get(b"hello"))  # None
```

## API

### LevelDB

| 方法 | 说明 |
|------|------|
| `LevelDB(path, create=True)` | 打开/创建数据库 |
| `.get(key) -> bytes \| None` | 读取 |
| `.put(key, value)` | 写入 |
| `.delete(key)` | 删除 |
| `.iterator() -> Iterator` | 创建迭代器 |
| `.close()` | 关闭 |
| 支持 `with` 上下文管理器 |

### Iterator

```python
with db.iterator() as it:
    # 正向遍历
    for k, v in it:
        print(k, v)

    # 反向遍历
    it.seek_to_last()
    while it.valid():
        print(it.key(), it.value())
        it.prev()

    # 定位到指定 key
    it.seek(b"target")
```

| 方法 | 说明 |
|------|------|
| `.seek_to_first()` | 跳转到第一个 key |
| `.seek_to_last()` | 跳转到最后一个 key |
| `.seek(key)` | 跳转到 >= key 的位置 |
| `.next()` / `.prev()` | 前进 / 后退 |
| `.valid() -> bool` | 当前位置是否有效 |
| `.key() -> bytes` | 当前 key |
| `.value() -> bytes` | 当前 value |
| `.close()` | 关闭 |
| 支持 `with` 上下文管理器，支持 `for k, v in iterator` |

## 后端

| 后端 | 条件 | 说明 |
|------|------|------|
| plyvel | `import plyvel` 成功 | 性能好，推荐 |
| ctypes | 回退 | 内置 `leveldb.dll`，Windows 即开即用 |

## 开发

```bash
# 测试
python scripts/run_tests.py

# 仅测试，跳过覆盖率
python scripts/run_tests.py --no-cov

# 按关键字筛选
python scripts/run_tests.py -k iterator

# 打包
python scripts/publish.py --build-only

# 发布到 PyPI
python scripts/publish.py

# 发布到 TestPyPI
python scripts/publish.py --repo testpypi
```

发布前需在 `scripts/pypi_config.toml` 中填入 PyPI token（参考 `scripts/pypi_config.toml.example`）。
