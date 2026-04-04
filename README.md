# laziest-import

[![PyPI version](https://img.shields.io/pypi/v/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![Python](https://img.shields.io/pypi/pyversions/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![License](https://img.shields.io/github/license/ChidcGithub/Laziest-import.svg)](LICENSE)

**零配置懒加载导入库** — 一行导入，直接使用任意已安装模块。

```python
from laziest_import import *

arr = np.array([1, 2, 3])      # numpy
df = pd.DataFrame({'a': [1]})  # pandas
plt.plot([1, 2, 3])            # matplotlib
```

无需 `import numpy as np`，无需 `import pandas as pd`。

## 安装

```bash
pip install laziest-import
```

## 快速开始

<details>
<summary>点击展开示例</summary>

**方式一：通配符导入（推荐）**

```python
from laziest_import import *

# 常用库直接使用
arr = np.array([1, 2, 3])           # numpy
df = pd.DataFrame({'a': [1, 2]})    # pandas
plt.plot([1, 2, 3]); plt.show()     # matplotlib

# 标准库
print(os.getcwd())                  # os
data = json.dumps({'key': 'value'}) # json

# 子模块自动加载
result = np.linalg.svd(matrix)      # numpy.linalg
```

**方式二：命名空间前缀**

```python
import laziest_import as lz

arr = lz.np.array([1, 2, 3])
df = lz.pd.DataFrame({'a': [1, 2]})
```

</details>

## 核心特性

| 特性 | 说明 |
|------|------|
| **懒加载** | 首次访问时才导入，减少启动开销 |
| **子模块支持** | `np.linalg.svd()` 自动链式加载 |
| **自动发现** | 未注册名称自动搜索已安装模块 |
| **模糊匹配** | 拼写错误自动纠正（Levenshtein 算法） |
| **自动安装** | 可选：缺失模块自动 pip install |
| **1000+ 别名** | 预定义常用包别名 |

## 自动安装（新功能）

启用后，访问未安装的模块会自动安装：

```python
from laziest_import import *

# 启用自动安装（交互式确认）
enable_auto_install()

# 使用国内镜像加速
enable_auto_install(index="https://pypi.tuna.tsinghua.edu.cn/simple")

# 现在访问未安装的模块会提示安装
arr = np.array([1, 2, 3])  # 若 numpy 未安装，自动提示安装
```

<details>
<summary>自动安装 API</summary>

| 函数 | 说明 |
|------|------|
| `enable_auto_install(interactive=True, index=None)` | 启用自动安装 |
| `disable_auto_install()` | 禁用自动安装 |
| `is_auto_install_enabled()` | 检查状态 |
| `install_package(name)` | 手动安装包 |
| `set_pip_index(url)` | 设置镜像源 |

</details>

## 预定义别名

<details>
<summary>点击展开完整列表</summary>

| 分类 | 别名 |
|------|------|
| 数据科学 | `np`, `pd`, `plt`, `sns`, `scipy` |
| 机器学习 | `torch`, `tf`, `keras`, `sklearn`, `xgboost`, `lightgbm` |
| 深度学习 | `transformers`, `langchain`, `llama_index` |
| Web 框架 | `flask`, `django`, `fastapi`, `starlette` |
| HTTP 客户端 | `requests`, `httpx`, `aiohttp` |
| 数据库 | `sqlalchemy`, `pymongo`, `redis`, `duckdb` |
| 云服务 | `boto3` (AWS), `google.cloud`, `azure` |
| 图像处理 | `cv2`, `PIL.Image`, `skimage` |
| GUI | `PyQt6`, `tkinter`, `flet`, `nicegui` |
| DevOps | `docker`, `kubernetes`, `ansible` |
| NLP | `spacy`, `nltk`, `transformers` |
| 可视化 | `plotly`, `bokeh`, `streamlit`, `gradio` |

</details>

## 更多功能

<details>
<summary>文件级缓存</summary>

缓存已导入模块，加速后续运行：

```python
import laziest_import as lz

# 查看缓存状态
info = lz.get_file_cache_info()

# 自定义缓存目录
lz.set_cache_dir('./my_cache')

# 清除缓存
lz.clear_file_cache()
```

</details>

<details>
<summary>调试与统计</summary>

```python
import laziest_import as lz

# 启用调试模式
lz.enable_debug_mode()

# 获取导入统计
stats = lz.get_import_stats()
# {'total_imports': 3, 'total_time': 0.15, 'module_times': {...}}

# 重置统计
lz.reset_import_stats()
```

</details>

<details>
<summary>导入钩子</summary>

```python
import laziest_import as lz

def before_import(module_name):
    print(f"准备导入: {module_name}")

def after_import(module_name, module):
    print(f"已导入: {module_name}")

lz.add_pre_import_hook(before_import)
lz.add_post_import_hook(after_import)
```

</details>

<details>
<summary>异步导入</summary>

```python
import laziest_import as lz
import asyncio

async def main():
    # 并行导入多个模块
    modules = await lz.import_multiple_async(['numpy', 'pandas', 'torch'])
    np, pd = modules['numpy'], modules['pandas']

asyncio.run(main())
```

</details>

<details>
<summary>自定义别名</summary>

```python
from laziest_import import *

# 注册单个别名
register_alias("mylib", "my_awesome_library")

# 批量注册
register_aliases({
    "api": "my_api_client",
    "db": "my_database_lib",
})
```

</details>

## 完整 API 参考

<details>
<summary>点击展开</summary>

### 别名管理

| 函数 | 说明 |
|------|------|
| `register_alias(alias, module_name)` | 注册别名 |
| `register_aliases(dict)` | 批量注册 |
| `unregister_alias(alias)` | 移除别名 |
| `list_loaded()` | 已加载模块列表 |
| `list_available()` | 所有可用别名 |
| `get_module(alias)` | 获取模块对象 |
| `clear_cache()` | 清除缓存 |

### 自动搜索

| 函数 | 说明 |
|------|------|
| `enable_auto_search()` | 启用自动发现 |
| `disable_auto_search()` | 禁用自动发现 |
| `search_module(name)` | 搜索模块 |
| `search_class(class_name)` | 按类名搜索 |
| `rebuild_module_cache()` | 重建缓存 |

### 符号搜索

| 函数 | 说明 |
|------|------|
| `enable_symbol_search()` | 启用符号搜索 |
| `search_symbol(name)` | 搜索类/函数 |
| `rebuild_symbol_index()` | 重建索引 |

### 自动安装

| 函数 | 说明 |
|------|------|
| `enable_auto_install()` | 启用自动安装 |
| `disable_auto_install()` | 禁用自动安装 |
| `install_package(name)` | 手动安装 |
| `set_pip_index(url)` | 设置镜像源 |

### 其他

| 函数 | 说明 |
|------|------|
| `get_version(alias)` | 获取模块版本 |
| `reload_module(alias)` | 重载模块 |
| `enable_retry()` | 启用重试机制 |
| `enable_file_cache()` | 启用文件缓存 |

</details>

## 配置文件

自定义别名可配置于：

1. `~/.laziest_import/aliases.json` （用户全局）
2. `./.laziest_import.json` （项目级别）

```json
{
    "mylib": "my_awesome_library",
    "api": "my_api_client"
}
```

## 工作原理

1. **代理对象**：每个别名映射到 `LazyModule` 代理
2. **按需导入**：首次属性访问时通过 `__getattr__` 触发真实导入
3. **缓存机制**：已导入模块缓存于代理对象中
4. **链式代理**：`LazySubmodule` 处理子模块递归懒加载
5. **模糊搜索**：Levenshtein 距离算法容错匹配

## 要求

- Python 3.8+

## License

[MIT](LICENSE)