# duck-leveldb

Cross-platform LevelDB 接口，双后端自动切换：plyvel（优先）→ ctypes + leveldb.dll（回退）。

## 关键文件

- `setup.py` — 入口，版本号在此修改
- `pyproject.toml` — 锁定 setuptools<71（否则生成 Metadata-Version 2.4，PyPI 不支持）
- `duck_leveldb/__init__.py` — 后端选择逻辑
- `libs/leveldb.dll` — ctypes 后端依赖，需要存在于该路径或 `LEVELDB_DLL` 环境变量

## 命令

```bash
# 测试（推荐通过脚本，自动清空旧报告）
python scripts/run_tests.py
python scripts/run_tests.py --no-cov
python scripts/run_tests.py -k iterator

# 打包（必须用 python -m build，setup.py sdist 会产生连字符文件名被 PyPI 拒绝）
python scripts/publish.py --build-only

# 发布（从 scripts/pypi_config.toml 读取 token，该文件已 gitignore）
python scripts/publish.py              # 默认发布到正式 PyPI
python scripts/publish.py --repo testpypi
```

## 注意事项

- **sdist 文件名**：PyPI 要求下划线（`duck_leveldb-...`）。只能用 `python -m build`，不能用 `setup.py sdist`
- **Metadata-Version**：PyPI 只支持 ≤2.3，`pyproject.toml` 已锁定 setuptools<71
- **Flaky 测试**：Windows 下 LevelDB 快速开/关会导致 `000002.dbtmp` 竞争，fixture 有 3 次重试 + 延迟
- **Token**：放在 `scripts/pypi_config.toml`（已 `.gitignore`），模板见 `scripts/pypi_config.toml.example`
- **leveldb.dll**：ctypes 后端编译要求，Windows 下需确保 libs/ 中存在或设置 `LEVELDB_DLL` 环境变量
