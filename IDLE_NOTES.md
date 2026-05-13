# laziest-import IDLE 适配指南

## 概述

Python 内置的 IDLE 编辑器对类型存根（`.pyi` 文件）的支持有限。本文档说明如何在 IDLE 中获得最佳的使用体验。

## IDLE 的限制

1. **无 `.pyi` 自动加载**：IDLE 不会自动读取 `.pyi` 文件来提供类型提示
2. **无模块级 `__getattr__` 补全**：`laziest_import` 使用模块级 `__getattr__` 动态提供属性，IDLE 无法识别这类动态属性
3. **无第三方库自动补全**：IDLE 对第三方库的补全能力很弱

## 推荐配置

### 方法一：使用 IDLE 作为编辑器 + 命令行运行

1. **配置 IDLE 打开 `.py` 文件**：
   - IDLE → Options → Configure IDLE → General → Default source window font size: 12
   - 确保文件关联为 `.py` 文件

2. **代码编写提示**：
   ```python
   # 在脚本顶部添加类型注释以获得更好的可读性
   import laziest_import as lz  # type: ignore[import]
   
   # 使用时参考文档字符串
   arr = lz.np.array([1, 2, 3])  # numpy
   df = lz.pd.DataFrame()        # pandas
   ```

3. **运行脚本**：
   - 在 IDLE 中：F5 运行
   - 或命令行：`python your_script.py`

### 方法二：配合 mypy 使用

```bash
# 安装 mypy
pip install mypy

# 对项目进行类型检查
mypy your_script.py --ignore-missing-imports
```

### 方法三：推荐迁移到 VS Code / PyCharm

为了获得完整的自动补全和类型检查体验，建议使用以下编辑器：

| 编辑器 | 类型存根支持 | 自动补全 | 免费 |
|--------|------------|---------|------|
| VS Code + Pylance | ✅ 完全支持 | ✅ | ✅ |
| PyCharm Community | ✅ 完全支持 | ✅ | ✅ |
| IDLE | ❌ 有限 | ❌ | ✅ |

## laziest-import 特定适配

### 动态属性说明

`laziest_import` 通过模块级 `__getattr__` 提供以下动态属性，IDLE 无法识别：

- **模块别名**：`lz.np`, `lz.os`, `lz.pd`, `lz.plt` 等
- **符号搜索**：`lz.search_symbol()`, `lz.enable_symbol_search()` 等
- **后台索引**：`lz.start_background_index_build()` 等
- **RC 配置**：`lz.load_rc_config()` 等

### 类型存根覆盖范围

当前 `__init__.pyi` 已为以下内容提供类型提示：

- ✅ 所有公共函数（200+ 个）
- ✅ 所有数据类（SearchResult, SymbolMatch, DependencyNode 等）
- ✅ 代理类（LazyModule, LazySymbol, LazySubmodule, LazyProxy）
- ✅ 配置字典结构
- ⚠️ 模块级 `__getattr__` 动态属性（IDLE 不支持）

### 使用 `# type: ignore` 注释

在 IDLE 中使用 laziest-import 时，可能需要添加类型忽略注释：

```python
import laziest_import as lz  # type: ignore[import,no-redef]

# 动态属性需要 type: ignore
arr = lz.np.array([1, 2, 3])  # type: ignore[attr-defined]
df = lz.pd.DataFrame()  # type: ignore[attr-defined]
```

## 验证环境

```python
# 测试脚本 test_idle_compat.py
import laziest_import as lz

# 1. 基础导入
print("Version:", lz.__version__)

# 2. 模块代理
import math
print("math.pi:", lz.math.pi)

# 3. 别名
print("Loaded:", lz.list_loaded())
print("Available:", lz.list_available()[:5])

# 4. 符号搜索
results = lz.search_symbol("array", max_results=3)
print("Symbol search results:", len(results))

# 5. 配置
print("Debug mode:", lz.is_debug_mode())
print("Auto search:", lz.is_auto_search_enabled())

print("\n✅ IDLE 兼容性测试通过！")
```

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| IDLE 无法补全 `lz.` 后的属性 | 正常，IDLE 不支持 `__getattr__` 动态属性 |
| 运行时报 `ModuleNotFoundError` | 确保模块已安装：`pip install laziest-import` |
| 类型存根未生效 | 确认 `__init__.pyi` 与 `__init__.py` 在同一目录下 |
| 自动搜索慢 | 运行 `lz.rebuild_module_cache()` 重建缓存 |

## 版本信息

- laziest-import 版本：0.1.0-pre2
- Python 版本要求：3.10+
- IDLE 版本：随 Python 3.13+ 自带