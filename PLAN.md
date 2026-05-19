# Laziest-import 改造计划

> **核心理念不变**
> ```python
> from laziest_import import *
> np.array([1, 2, 3])        # ✅ 随心导入，无需任何前缀
>
> import laziest_import as lz
> lz.plt.plot([1, 2, 3])     # ✅ 前缀式同样支持
> ```

---

## 阶段一：API 层合并（消除三层冗余）

### 问题

当前三个 API 层做同样的事，互相包装：

```
__init__.py (965行)
  ├── _public_api.py   (旧式过程 API, 201行)  — 真正实现
  ├── _deprecated.py   (弃用包装器, 929行)    — 加 FutureWarning
  └── _api.py          (新 OOP API, 2196行)   — 再包装 _public_api
```

`__all__` 导出的默认 API 反而是弃用的旧 API，对新用户极其困惑。

### 方案

```
__init__.py        (精简：只保留 __getattr__ + __dir__ + __all__ + init)
_api/
  __init__.py      (导出全部 namespace)
  _module.py       ModuleNamespace
  _alias.py        AliasNamespace
  _symbol.py       SymbolNamespace + SymbolIndexNamespace + SymbolConfigNamespace
  _cache.py        CacheNamespace + 子 namespace
  _config.py       ConfigNamespace + ConfigContext + dataclasses
  _hooks.py        HookNamespace + HookList
  _analyze.py      AnalyzeNamespace
  _profile.py      ProfileNamespace
  _install.py      InstallNamespace
  _async.py        AsyncNamespace
  _background.py   BackgroundNamespace
  _version.py      VersionNamespace
  _rcconfig.py     RCConfigNamespace
  _export.py       ExportNamespace
  _deprecated.py   (轻量包装，仅用于旧→新映射)
```

合并后：

```
__init__.py
  └── from ._api import lz, LazyImport, ModuleNamespace, ...
```

| 文件 | 当前 | 改造后 |
|------|------|--------|
| `_public_api.py` | 201 行 | ❌ 删除 |
| `_deprecated.py` | 929 行 | ➡ 精简为映射层 |
| `_api.py` | 2196 行单文件 | ➡ 拆为 `_api/` 包 |
| `__init__.py` | 965 行 | ➡ 精简 |

---

## 阶段二：`__init__.py` 瘦身

### 当前 `__init__.py` 承担过多职责

| 职责 | 下一站 |
|------|--------|
| Hooks (`add_pre_import_hook` 等) | `laziest_import/_hooks.py` |
| 分析便利函数 (`analyze_file` 等) | 通过 `lz.analyze.file()` 替代 |
| `help()` / `easter_egg()` | 保留或移 `_help.py` |
| `_SYMBOL_FUNCTIONS` 懒加载（硬编码25个函数名） | 消除，改为注册机制 |

### `__getattr__` 解析链简化

当前 10 步解析 → 简化为：

1. 守卫检查（初始化状态、负缓存）
2. 别名映射查找
3. 动态导入（模糊匹配 + 缩写 + 纠错）
4. 自动符号解析
5. 失败 → 显示建议

消除硬编码函数名列表，改为函数注册表。

---

## 阶段三：API 语义简化

### namespace 层级过深

```
# 当前
lz.cache.symbols.clear()        # 三层
lz.cache.stats.hit_rate         # 三层
lz.cache.files.info()           # 三层

# 目标
lz.cache.clear_symbols()        # 两层
lz.cache.stats                  # property 直接返回 dict
lz.cache.file_info()            # 两层
```

### 配置体系统一

| 当前问题 | 方案 |
|----------|------|
| `_api.py` 的 dataclass 与 `_config.py` 字典重复 | 统一用 dataclass，一个来源 |
| 部分配置是 dict，部分是 property | 全部 property + dataclass 双向同步 |

---

## 阶段四：别名系统全面升级

### 当前问题

**1. 三重数据源冗余**

`nn` 同时存在于三个文件，格式不一：

| 文件 | 值 | 格式 |
|------|-----|------|
| `aliases/n.json` | `"nn": "torch.nn"` | 简单 k-v |
| `mappings/abbreviations.json` | `"nn": "torch.nn"` | 分类 k-v |
| `mappings/submodules.json` | `"nn": ["torch", "torch.nn"]` | 数组 |

**2. 别名无语义分类**

只能按字母导出，不能按用途筛选。

**3. 模糊匹配无上下文感知**

输入 `nn` 时不考虑用户当前是否已加载 `torch`，全局计算 Levenshtein 距离。

**4. 无智能提示**

```
AttributeError: module 'laziest_import' has no attribute 'nummpy'
```

→ 应该提示 "您是不是想找: `numpy` (alias: `np`)？"

**5. 无自动别名生成**

```
lz.alias.suggest(installed=True)   # ❌ 不存在
```

### 方案

#### 4.1 数据统一

```
aliases/              ← 唯一来源，合并 abbreviations + submodules
mappings/
  package_rename.json  ← 保留
  priorities.json      ← 保留
  symbol_misspellings.json ← 保留
  abbreviations.json   ← ❌ 删除，合并进 aliases/
  submodules.json      ← ❌ 删除，合并进 aliases/
```

#### 4.2 别名 JSON 格式升级

```json
// aliases/n.json
{
  "_meta": {
    "category": "data_science",
    "description": "NumPy is the fundamental package for scientific computing"
  },
  "np": "numpy",
  ...
}
```

保留按字母分文件，便于快速查找。每个 alias 文件头部加 `_meta` 元数据。

#### 4.3 智能建议

```
lz.alias.suggest(package="polars")       → "pd" (已被 pandas 占用, 建议 "po")
lz.alias.suggest(installed=True)         → 扫描 pip list，批量建议
lz.alias.suggest(pattern="plot")          → "plt", "plotly", "bokeh"
```

AI 模式：扫描已安装包，自动匹配已知缩写规则生成建议。

#### 4.4 筛选搜索

```
lz.alias.list(category="ml")             → ["torch", "tf", "sklearn", ...]
lz.alias.list(category="data_science")   → ["np", "pd", "plt", "sns", ...]
lz.alias.search("torch*")                → 通配符匹配
lz.alias.search("plot")                  → 子串匹配
```

#### 4.5 智能错误提示

```python
lz.nump  # AttributeError
# → "Did you mean `numpy`? (alias: `np`, category: data_science)"
# → "Available similar: `numba` (→ numba), `nlp` (→ spacy)"
```

利用 Levenshtein 距离 + 分类信息，给出最佳建议。

#### 4.6 上下文感知模糊匹配

- 用户已加载 `torch` → `nn` 优先匹配 `torch.nn`
- 用户已加载 `sklearn` → `svm` 优先匹配 `sklearn.svm`
- 优先级：上下文 > 精确匹配 > 缩写 > 纠错 > Levenshtein

#### 4.7 别名冲突智能解决

```python
lz.alias.register("pd", "polars")
# → Warning: "`pd` is already registered to `pandas`. Override? [y/N]"
```

自动检测冲突，提供交互式解决。

---

## 阶段五：功能完善

| 项目 | 状态 | 说明 |
|------|------|------|
| `py.typed` | ⏳ | 添加 PEP 561 标记 |
| 负缓存淘汰 | ⏳ | `_NEGATIVE_CACHE` 加 TTL |
| `__all__` 清理 | ⏳ | 只导出当前 API + alias 名 |
| OOP API 测试 | ⏳ | 为所有 namespace 类写专项测试 |
| `__getattr__` 类型提示 | ⏳ | 返回 `LazyModule` 类型，IDE 可补全 |
| 错误信息优化 | ⏳ | 加载失败时给出具体建议 |
| 线程安全测试 | ⏳ | 并发压力测试 |
| 异步加载增强 | ⏳ | async lazy loading |
| 自动补全增强 | ⏳ | `__dir__` 按分类返回别名 |

---

## 状态图

```
当前 → 阶段一(API合并) → 阶段二(__init__瘦身) → 阶段三(语义简化) → 阶段四(别名升级) → 阶段五(完善)
  │                                                                                       │
  └── 保持 from laziest_import import * 和 lz.np.* 稳定工作 ──────────────────────────────┘
```

每个阶段完成后：
1. 运行完整测试（934+ 项）
2. 提交 + 打 tag
3. 发布 CI 清理（目标：0 CI 失败）
