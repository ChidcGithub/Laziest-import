# laziest-import

[![PyPI version](https://img.shields.io/pypi/v/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![PyPI pre-release](https://img.shields.io/github/release/ChidcGithub/Laziest-import/all.svg?label=pre-release&color=orange)](https://github.com/ChidcGithub/Laziest-import/releases)
[![Python](https://img.shields.io/pypi/pyversions/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![License](https://img.shields.io/pypi/l/laziest-import.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![GitHub stars](https://img.shields.io/github/stars/ChidcGithub/Laziest-import.svg?style=social&label=Stars)](https://github.com/ChidcGithub/Laziest-import/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ChidcGithub/Laziest-import.svg?style=social&label=Forks)](https://github.com/ChidcGithub/Laziest-import/network/members)
[![GitHub issues](https://img.shields.io/github/issues/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import/pulls)
[![GitHub Actions](https://github.com/ChidcGithub/Laziest-import/workflows/Build%20and%20Publish/badge.svg)](https://github.com/ChidcGithub/Laziest-import/actions)
[![GitHub last commit](https://img.shields.io/github/last-commit/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import)
[![Type hints](https://img.shields.io/badge/type_hints-mypy-blue.svg)](https://mypy-lang.org/)
[![Code style](https://img.shields.io/badge/code_style-pep8-green.svg)](https://peps.python.org/pep-0008/)
[![Tests](https://img.shields.io/badge/tests-1065%20passed-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import/tree/main/tests)
[![Coverage](https://img.shields.io/badge/coverage-comprehensive-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import/tree/main/tests)
[![CodeFactor](https://img.shields.io/badge/code_quality-A-brightgreen.svg)](https://www.codefactor.io/repository/github/chidcgithub/laziest-import)
[![Maintainability](https://img.shields.io/badge/maintainability-excellent-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import)
[![Contributors](https://img.shields.io/badge/contributors-welcome-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import/graphs/contributors)
[![First Timers Only](https://img.shields.io/badge/first-timers_only-blue.svg)](https://github.com/ChidcGithub/Laziest-import/contribute)
[![Documentation Status](https://img.shields.io/badge/docs-complete-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import)
[![Made with Love](https://img.shields.io/badge/made_with-%E2%9D%A4-red.svg)](https://github.com/ChidcGithub/Laziest-import)
[![Pythonic](https://img.shields.io/badge/pythonic-yes-blue.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ChidcGithub/Laziest-import)
[![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/ChidcGithub/Laziest-import)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import/pulls)
[![License MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

[![中文版](https://img.shields.io/badge/%E4%B8%AD%E6%96%87-README_CN-blue.svg)](README_CN.md)
[![English](https://img.shields.io/badge/English-README-blue.svg)](README.md)

--- <div align="center">

## 零配置懒加载导入库

**一行代码即可导入和使用任何已安装的模块**

<p align="center">
<b>一个神奇的方式来导入 Python 模块 - 直接用就行！</b>
</p>

</div>

--- ## 目录

- [功能特性](#-核心功能)
- [快速开始](#-快速开始)
- [安装方法](#-安装方法)
- [终端演示](#-终端演示)
- [使用示例](#-使用示例)
- [配置说明](#-配置说明)
- [API 参考](#-api-参考)
- [常见问题](#-常见问题)
- [工作原理](#-工作原理)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

--- ## 核心功能

| 功能 | 徽章 | 描述 |
|---------|-------|-------------|
| 懒加载 | ![](https://img.shields.io/badge/feature-lazy_loading-green.svg) | 模块只在第一次访问时导入 |
| 后台索引 | ![](https://img.shields.io/badge/feature-background_index-blue.svg) | 符号索引在后台线程中构建 |
| 自动纠错 | ![](https://img.shields.io/badge/feature-auto_correction-purple.svg) | 拼写错误自动纠正（`nump` → `numpy`） |
| 符号搜索 | ![](https://img.shields.io/badge/feature-symbol_search-orange.svg) | 在所有模块中搜索符号 |
| 多层缓存 | ![](https://img.shields.io/badge/feature-multi_level_cache-green.svg) | 三层缓存系统提供高速访问 |
| 依赖分析 | ![](https://img.shields.io/badge/feature-dependency_analysis-blue.svg) | 分析模块依赖关系 |
| 性能基准 | ![](https://img.shields.io/badge/feature-benchmarking-purple.svg) | 基准测试导入和函数 |
| CLI 接口 | ![](https://img.shields.io/badge/feature-cli-lightgrey.svg) | `laziest-import freeze` / `init` / `fix` 命令 |
| 符号自动补全 | ![](https://img.shields.io/badge/feature-autocomplete-blue.svg) | 基于前缀的符号名补全 |
| 1065+ 测试 | ![](https://img.shields.io/badge/tests-1065%2B-brightgreen.svg) | 全面的测试覆盖 |
| 1000+ 别名 | ![](https://img.shields.io/badge/aliases-1000%2B-orange.svg) | 为常用包预定义的别名 |

--- ## 安装方法

```bash
# 稳定版本
pip install laziest-import

# 预发布版本（最新功能）
pip install --pre laziest-import

# 从源码安装（最新开发版）
pip install git+https://github.com/ChidcGithub/Laziest-import.git
```

--- ## 快速开始

### 方法 1：通配符导入（推荐）

```python
from laziest_import import *

# 数据科学
arr = np.array([1, 2, 3])           # numpy
df = pd.DataFrame({'a': [1, 2]})    # pandas
plt.plot([1, 2, 3]); plt.show()     # matplotlib

# 标准库
print(os.getcwd())                  # os
data = json.dumps({'key': 'value'}) # json
result = math.sqrt(16)              # math

# 子模块（自动加载）
svd_result = np.linalg.svd(matrix)  # numpy.linalg.svd()
```

### 方法 2：命名空间前缀

```python
import laziest_import as lz

arr = lz.np.array([1, 2, 3])
df = lz.pd.DataFrame({'a': [1, 2]})
```

### 方法 3：懒代理（自动纠错）

```python
from laziest_import import lazy

# 自动拼写纠错
arr = lazy.nump.array([1, 2, 3])    # nump -> numpy 
df = lazy.pnda.DataFrame()          # pnda -> pandas 
arr2 = lazy.nupi.array([4, 5, 6])   # nupi -> numpy 

# 子模块快捷方式
layer = lazy.nn.Linear(10, 5)       # nn -> torch.nn 
relu = lazy.F.relu(tensor)          # F -> torch.nn.functional 
```

--- ## 最新更新

### v1.0.0.6（当前）

- **全面的 Bug 修复**：修复 8 个关键 bug，包括 `module_access_counts` 重置、`LazySymbol` None 值无限重导入、hash/eq 契约违反、`_scan_path_modules` 仅返回第一个路径、`reset_all()` 错误模块引用、`get_symbol_help()` 损坏的属性访问等
- **线程安全**：为 `_ALIAS_MAP` 写入、负缓存、`invalidate_package_cache` 和 hook 移除添加了锁保护
- **Python 3.9 兼容性**：`Any | None` 联合语法替换为 `Optional[Any]`
- **版本比较修复**：预发布版本字符串现在正确比较数字后缀（如 `alpha10` vs `alpha2`）
- **配置系统修复**：环境变量现在具有最高优先级；`interactive` 覆盖参数在自动安装中被正确尊重
- **缓存修复**：清理限定为 `laziest_*.json` 前缀；`max_cache_size_mb=0` 视为无限制；部分缓存加载不再阻止完整重建
- **`which()` 改进**：模块提示不匹配时返回 `None` 而非静默错误回退
- **CI 修复**：GitHub Actions 工作流添加 `timeout-minutes` 防止 6 小时挂起

### 新功能

- **反射运算符**：`LazySymbol` 现支持 `__radd__`、`__rsub__`、`__rmul__`、`__rtruediv__` 等 12 个运算符
- **异步重试逻辑**：基于 `_RETRY_CONFIG` 实现实际重试
- **CLI `fix` 命令**：`laziest-import fix` 从检测到的别名使用生成标准 `import` 语句
- **符号自动补全**：`symbol_autocomplete(prefix)` 前缀补全
- **构建进度 API**：`get_progress()` 查询当前构建状态
- **`which_all` 实时搜索**：索引构建后仍执行实时搜索
- **终端演示**：`examples/terminal_demo.py` 交互式动画演示

### 代码质量

- 10+ 处宽泛的 `except Exception` 缩小为具体异常
- 测试文件中删除 `sys.path.insert(0, '.')`
- `is True or is False` 断言替换为 `isinstance(bool)`
- `_symbol/` 重定向文件中删除冗余 `x as x` 导入
- 重复的 `SymbolIndexCache` 数据类合并为单一定义
- `_is_stdlib_module` 提升为模块级常量集合
- README 统一版本号和测试计数

### v0.1.0

- **阶段五 — 假代码审计与修复**：所有占位符/假代码替换为真正的逻辑
- **修复 `assert True` 测试**：4 个测试替换为真正的断言
- **修复无声 `except Exception: pass`**：4 个测试、`HookList.__call__()`、`_benchmark.py` 预热/测量、`_state_setters.py` 缩小为 `except ImportError`
- **修复 48 个零断言冒烟测试**：添加了类型/值断言
- **修复 `_jupyter.py` `unload_ipython_extension()`**：无操作 `pass` 替换为 `unregister_magics()`
- **修复 `_cache/_api.py` `invalidate_package_cache()`**：添加了缺失的 `_STDLIB_SYMBOL_CACHE` 清理
- **修复 `_build_known_modules_cache()` 中的循环导入**：跳过扫描 CWD（`''`/`'.'` 路径）以防止重新导入工作目录中的脚本
- **1065 项测试**：全部通过，全面覆盖

### v0.1.0-rc2

- **OOP API 迁移**：23 个测试文件从模块级 API 迁移到 `lz` 单例
- **修复 `LazyImport.__getattr__`**：在昂贵查找之前进行负缓存检查
- **修复 `reset_all()`**：现在重新加载别名、更新 `__all__` 并重建符号索引
- **提高 `_build_symbol_index` 默认值**：`max_modules=500`，`timeout=60.0` 以实现完整的索引覆盖

### v0.1.0-rc1

- **阶段四 — 别名系统升级**：数据统一、JSON 格式升级、智能建议、过滤搜索、智能错误提示、上下文感知模糊匹配、冲突检测
- **数据统一**：108 个别名从 `mappings/abbreviations.json` 合并到 `aliases/*.json`；删除 `abbreviations.json` 和 `submodules.json`
- **JSON 格式升级**：所有 27 个别名字母文件增加 `_meta` 元数据（类别、描述）
- **AliasNamespace API**：`lz.alias.list(category=)`、`lz.alias.search(pattern, by_module=)`、`lz.alias.suggest(package=/installed=/pattern=)`
- **智能错误提示**：基于 Levenshtein 距离的拼写检测 — `lz.nummpy` 提示 `Did you mean numpy?`
- **上下文感知模糊匹配**：已加载模块在自动搜索中获得优先级加成
- **冲突检测**：`register_alias()` 在别名覆盖时发出警告
- **Bug 修复**：修复 `__repr__` 抛 `NameError`（严重）；修复别名搜索回退时错误导入模块（严重）；修复 opencv/cv2 无限循环；修复 sage/sagemath 指向不存在模块；修复 4 个环形别名链；修复 80+ 个连字符化别名值（使用 PyPI 名而非可导入模块名）；修复 70+ 个连字符化别名键（Python 语法不可达）；修复缩进错误导致 symbol-not-found 回退被隐藏；删除 48 行死代码；修复 `_suggest_for_package()` 返回重复项错误
- **1065+ 测试**：全面的测试覆盖


--- ## 终端演示

运行交互式终端演示，观看 laziest-import 的动画效果：

```bash
python examples/terminal_demo.py
```

<div align="center">
  <pre>
  /=======================================\
  |   laziest-import  Terminal Demo        |
  \=======================================/
  [1] 一行代码导入所有模块
     -> np.array([1,2,3])     = [1 2 3]
     -> math.sqrt(144)        = 12.0
     -> os.getcwd()           = /home/user
  [2] 子模块自动加载
     -> os.path.join('a','b') = a/b
  [3] 跨模块符号搜索
     -> math.sqrt  (function)
     -> numpy.sqrt (function)
  ...
  </pre>
</div>

--- ## 使用示例

### 符号搜索与定位

```python
import laziest_import as lz

# 在所有模块中搜索一个符号
results = lz.search_symbol('DataFrame')
for result in results:
print(f"{result.module_name}.{result.symbol_name}")

# 查找符号定义位置
loc = lz.which('sqrt')
print(f"找到位置：{loc}")  # numpy.sqrt

# 查找所有出现位置
locs = lz.which_all('sqrt')
for loc in locs:
print(f"{loc.module_name}.{loc.symbol_name}")
```

### 依赖树分析

```python
import laziest_import as lz

# 分析一个模块的依赖树
tree = lz.dependency_tree('numpy', max_depth=2)
print(f"总模块数：{tree.total_modules}")
print(f"标准库：{tree.stdlib_count}，第三方：{tree.third_party_count}")

# 打印格式化的树
lz.print_dependency_tree(tree)
```

### 性能基准测试

```python
import laziest_import as lz

# 基准测试一个函数
result = lz.benchmark(
lambda: sum(range(10000)),
name="sum_test",
iterations=100,
warmup=10
)
print(f"平均：{result.avg_time*1000:.4f}ms")
print(f"最小：{result.min_time*1000:.4f}ms")
print(f"最大：{result.max_time*1000:.4f}ms")

# 基准测试模块导入
report = lz.benchmark_imports(['numpy', 'pandas', 'matplotlib'])
lz.print_benchmark_report(report)
```

### 自动安装（可选）

```python
from laziest_import import *

# 启用自动安装
lz.enable_auto_install()

# 访问未安装的模块会触发安装
arr = np.array([1, 2, 3])  # 如果 numpy 缺失，提示安装
```

--- ## 配置说明

### 用户配置

```python
import laziest_import as lz

# 创建默认配置文件
lz.create_rc_file()

# 加载配置
config = lz.load_rc_config()

# 获取特定值
value = lz.get_rc_value('debug', default=False)

# 配置信息
info = lz.get_rc_info()
```

### 缓存配置

```python
import laziest_import as lz

# 设置自定义缓存目录
lz.set_cache_dir('./my_cache')

# 配置缓存设置
lz.set_cache_config(
symbol_index_ttl=3600,       # 符号索引 TTL：1 小时
stdlib_cache_ttl=2592000,    # 标准库缓存 TTL：30 天
max_cache_size_mb=200        # 最大缓存大小：200 MB
)

# 获取缓存统计
stats = lz.get_cache_stats()
print(f"命中率：{stats['hit_rate']:.1%}")

# 查看缓存状态
info = lz.get_file_cache_info()
print(f"缓存大小：{info['cache_size_mb']:.2f} MB")
```

--- ## API 参考

### 别名管理

| 函数 | 描述 |
|----------|-------------|
| `register_alias(alias, module_name)` | 注册一个别名 |
| `register_aliases(dict)` | 注册多个别名 |
| `unregister_alias(alias)` | 移除一个别名 |
| `list_loaded()` | 列出已加载的模块 |
| `list_available()` | 列出所有可用的别名 |
| `get_module(alias)` | 获取模块对象 |
| `clear_cache()` | 清除内存缓存 | ### 符号搜索

| 函数 | 描述 |
|----------|-------------|
| `enable_symbol_search()` | 启用符号搜索 |
| `disable_symbol_search()` | 禁用符号搜索 |
| `search_symbol(name)` | 搜索类/函数 |
| `rebuild_symbol_index()` | 重建符号索引 |
| `which(symbol)` | 查找符号位置 |
| `which_all(symbol)` | 查找所有符号位置 | ### 自动安装

| 函数 | 描述 |
|----------|-------------|
| `enable_auto_install()` | 启用自动安装 |
| `disable_auto_install()` | 禁用自动安装 |
| `install_package(name)` | 手动安装包 |
| `set_pip_index(url)` | 设置镜像 URL | ### 缓存管理

| 函数 | 描述 |
|----------|-------------|
| `get_cache_version()` | 获取缓存版本 |
| `set_cache_config(...)` | 配置缓存设置 |
| `get_cache_config()` | 获取缓存配置 |
| `get_cache_stats()` | 获取缓存统计 |
| `reset_cache_stats()` | 重置缓存统计 |
| `invalidate_package_cache(pkg)` | 失效包缓存 |
| `get_file_cache_info()` | 获取文件缓存信息 |
| `clear_file_cache()` | 清除文件缓存 |
| `set_cache_dir(path)` | 设置缓存目录 | ### 分析与性能分析

| 函数 | 描述 |
|----------|-------------|
| `analyze_file(path)` | 分析 Python 文件的导入 |
| `analyze_source(code)` | 分析源代码字符串 |
| `analyze_directory(path)` | 分析目录中的所有文件 |
| `start_profiling()` | 开始导入分析器 |
| `stop_profiling()` | 停止导入分析器 |
| `get_profile_report()` | 获取分析报告 |
| `print_profile_report()` | 打印格式化报告 |
| `dependency_tree(module)` | 分析模块依赖树 |
| `print_dependency_tree(tree)` | 打印依赖树 |
| `benchmark(func)` | 基准测试函数 |
| `benchmark_imports(modules)` | 基准测试模块导入 |
| `detect_environment()` | 检测 Python 环境 |
| `show_environment()` | 显示环境信息 |
| `find_symbol_conflicts()` | 查找符号冲突 |
| `show_conflicts()` | 显示冲突表格 | ### 偏好设置

| 函数 | 描述 |
|----------|-------------|
| `set_symbol_preference(name, module)` | 设置符号偏好 |
| `get_symbol_preference(name)` | 获取符号偏好 |
| `clear_symbol_preference(name)` | 清除符号偏好 |
| `save_preferences()` | 保存偏好到文件 |
| `load_preferences()` | 从文件加载偏好 |
| `apply_preferences(prefs)` | 应用已加载的偏好 |
| `clear_preferences()` | 清除所有偏好 | --- ## 常见问题

### 常见问题

**问：模块未找到（AttributeError）**
```
AttributeError: module 'laziest_import' has no attribute 'mymodule'
```
解决：模块未注册。使用 `lz.enable_auto_search()` 启用自动发现，或手动注册：
```python
lz.register_alias('mymodule', 'mypackage.mymodule')
```

**问：第一次导入较慢**
符号索引可能正在构建。使用以下命令检查状态：
```python
lz.is_index_building()  # True if building
lz.wait_for_index(30)  # 最多等待 30 秒
```

**问：拼写纠错不工作**
确保模块在别名列表中：
```python
lz.register_alias('nump', 'numpy')  # 添加拼写错误
arr = lz.nump.array([1, 2, 3])  # 现在可以工作
```

**问：符号冲突（多个模块中有相同名称）**
使用模块提示或偏好：
```python
lz.set_symbol_preference('DataFrame', 'pandas')  # 偏好 pandas
result = lz.DataFrame  # 获取 pandas.DataFrame
```

### 调试模式

启用详细日志记录：
```python
lz.enable_debug_mode()
import laziest_import as lz
arr = lz.np.array([1, 2, 3])  # 查看日志中的导入详情
```

### 缓存问题

如果遇到数据过期问题，请清除缓存：
```python
lz.clear_cache()       # 清除内存缓存
lz.clear_file_cache()  # 清除磁盘缓存
lz.rebuild_symbol_index()  # 重建符号索引
```

### 性能提示

1. **第一次运行**：约 2 秒构建索引
2. **缓存运行**：约 0.003 秒（快 700 倍！）
3. 使用 `lz.enable_background_build()` 避免第一次导入时阻塞
4. 对于 CI/CD，设置 `LAZY_BG_BUILD=1` 预构建缓存

--- ## 工作原理

### 架构

1. **代理对象**：每个别名映射到一个 `LazyModule` 代理
2. **按需导入**：真正的导入在第一次属性访问时通过 `__getattr__` 触发
3. **缓存**：导入的模块在代理对象中缓存
4. **链式代理**：`LazySubmodule` 处理递归懒加载
5. **模糊搜索**：用于容错匹配的 Levenshtein 距离算法

### 多层缓存架构

该库使用三层缓存系统以获得最佳性能：

| 缓存级别 | 描述 | 默认 TTL |
|-------------|-------------|-------------|
| **标准库缓存** | 标准库符号 | 7 天 |
| **第三方缓存** | 已安装的包符号 | 24 小时 |
| **内存缓存** | 当前会话的热缓存 | 会话期间 | 缓存文件存储在 `~/.laziest_import/cache/` 并自动：
- 根据 TTL 设置过期
- 超过大小限制时清理（默认：100 MB）
- Python 版本变更时失效

--- ## 预定义别名

### 数据科学
`np`、`pd`、`plt`、`sns`、`scipy`

### 机器学习
`torch`、`tf`、`keras`、`sklearn`、`xgboost`、`lightgbm`

### 深度学习
`transformers`、`langchain`、`llama_index`

### Web 框架
`flask`、`django`、`fastapi`、`starlette`

### HTTP 客户端
`requests`、`httpx`、`aiohttp`

### 数据库
`sqlalchemy`、`pymongo`、`redis`、`duckdb`

### 云服务
`boto3` (AWS)、`google.cloud`、`azure`

### 图像处理
`cv2`、`PIL.Image`、`skimage`

### GUI
`PyQt6`、`tkinter`、`flet`、`nicegui`

### DevOps
`docker`、`kubernetes`、`ansible`

### NLP
`spacy`、`nltk`、`transformers`

### 可视化
`plotly`、`bokeh`、`streamlit`、`gradio`

--- ## 贡献指南

我们喜欢贡献！查看我们的 [贡献指南](CONTRIBUTING.md) 获取更多信息。

### 如何贡献

1. Fork 这个仓库，从 `main` 创建你的分支
2. 阅读我们的 [行为准则](CODE_OF_CONDUCT.md)
3. 确保你的代码通过 lint 检查（`flake8`）
4. 为任何新功能添加测试
5. 确保测试套件通过（`pytest tests/`）
6. 提交你的更改
7. 推送到你的分支并打开 Pull Request！

### 开发设置

```bash
# 克隆仓库
git clone https://github.com/ChidcGithub/Laziest-import.git
cd Laziest-import

# 以开发模式安装
pip install -e ".[dev,test]"

# 运行测试
pytest tests/ -v

# 运行 lint 检查
flake8 laziest_import/
```

### 好的入门问题

在找一个开始的地方？查看：
- 好的入门问题：[标记为 "good first issue" 的问题](https://github.com/ChidcGithub/Laziest-import/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- 需要帮助：[标记为 "help wanted" 的问题](https://github.com/ChidcGithub/Laziest-import/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)

### 贡献方式

- 报告 Bug
- 提议新功能
- 改进文档
- 修复现有问题
- 添加更多测试
- 帮助翻译
- 设计改进

--- ## 贡献者

感谢这些了不起的人们：

<a href="https://github.com/ChidcGithub/Laziest-import/graphs/contributors">
<img src="https://contrib.rocks/image?repo=ChidcGithub/Laziest-import" />
</a>

使用 [contrib.rocks](https://contrib.rocks) 制作。

--- ## Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=ChidcGithub/Laziest-import&type=Date)](https://star-history.com/#ChidcGithub/Laziest-import&Date)

--- ## 联系我们

- 邮箱：(你的邮箱)
- GitHub：[ChidcGithub/Laziest-import](https://github.com/ChidcGithub/Laziest-import)
- 讨论：[GitHub Discussions](https://github.com/ChidcGithub/Laziest-import/discussions)
- 问题：[GitHub Issues](https://github.com/ChidcGithub/Laziest-import/issues)

--- ## 致谢

- 感谢所有帮助改进这个项目的贡献者！
- 受到 Python 社区对简洁、简单 API 的热爱的启发

--- ## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

--- ## 支持我们

如果你觉得这个项目有用，请考虑：

- 在 GitHub 上给这个仓库加星标
- 报告 Bug 或建议功能
- 与朋友和同事分享
- 如果你使用了，请在博客上写文章介绍
- 为项目做贡献

谢谢！
---

<div align="center">
<b>由 Chidc 和贡献者用心制作</b>
</div>