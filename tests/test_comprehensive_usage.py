"""
Comprehensive usage test for laziest-import.
Covers every public API and demonstrates real-world usage patterns.
"""

import tempfile
from pathlib import Path

from laziest_import import easter_egg, lz
from laziest_import._alias import get_config_dirs, get_config_paths, validate_aliases_importable
from laziest_import._analysis import detect_environment
from laziest_import._analysis._benchmark import (
    BenchmarkReport,
    BenchmarkResult,
    benchmark,
    benchmark_imports,
    print_benchmark_report,
)
from laziest_import._analysis._dependency import DependencyNode, DependencyTree
from laziest_import._analysis._environment import show_environment
from laziest_import._analysis._preanalyze import DependencyPreAnalyzer
from laziest_import._analysis._preferences import (
    apply_preferences,
    clear_preferences,
    load_preferences,
    save_preferences,
)
from laziest_import._analysis._profiler import ImportProfiler
from laziest_import._api._config import reset_import_stats

# "import directly" cases (migrated from deprecated API)
from laziest_import._cache._api import invalidate_package_cache, reset_cache_stats
from laziest_import._cache._incremental import get_incremental_config
from laziest_import._install import set_pip_extra_args, set_pip_index
from laziest_import._introspect import get_module_info, list_module_symbols, search_in_module
from laziest_import._state_setters import reset_all
from laziest_import._symbol import (
    clear_shard_cache,
    disable_sharding,
    enable_sharding,
    get_loaded_modules_context,
    get_module_priority,
    get_sharding_config,
    set_module_priority,
)


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def subsection(title):
    print(f"\n  --- {title} ---")


# =============================================================================
# 1. BASIC IMPORT AND SETUP
# =============================================================================
section("1. BASIC IMPORT AND SETUP")

print(f"Version: {lz.__version__}")
print(f"laziest-import loaded: {lz}")

# from laziest_import import * style
from laziest_import import help as lzhelp

print(f"Direct import of functions works: lzhelp={callable(lzhelp)}")


# =============================================================================
# 2. LAZY MODULE ACCESS VIA ALIASES
# =============================================================================
section("2. LAZY MODULE ACCESS VIA ALIASES")

lz.cache.clear()

# Standard library aliases
_have_numpy = True
try:
    np = lz.np
    print(f"np = {np}, type = {type(np).__name__}")
    _test_arr = np.array([1, 2, 3])
    print(f"  np.array([1,2,3]) = {_test_arr}")
except (ImportError, NameError):
    _have_numpy = False
    np = None
    print("np = (numpy not installed)")
if _have_numpy:
    del _test_arr

os_mod = lz.os
print(f"os = {os_mod}")
print(f"  os.getcwd() = {os_mod.getcwd()}")

sys_mod = lz.sys
print(f"sys = {sys_mod}")
print(f"  sys.version = {sys_mod.version[:30]}...")

math_mod = lz.math
print(f"math = {math_mod}")
print(f"  math.pi = {math_mod.pi}, math.sqrt(16) = {math_mod.sqrt(16)}")

json_mod = lz.json
print(f"json = {json_mod}")
print(f"  json.dumps({{'a':1}}) = {json_mod.dumps({'a': 1})}")

re_mod = lz.re
print(f"re = {re_mod}")
_digits_re = r"\d+"
print(f"  re.findall(r'\\d+', 'a1b2c3') = {re_mod.findall(_digits_re, 'a1b2c3')}")

time_mod = lz.time
print(f"time = {time_mod}")

random_mod = lz.random
print(f"random = {random_mod}")
print(f"  random.randint(1,10) = {random_mod.randint(1, 10)}")

# Popular third-party aliases (may not be installed)
for alias in ["pd", "plt", "tf", "torch"]:
    try:
        mod = getattr(lz, alias)
        if mod is not None:
            print(f"{alias} = {mod}")
        else:
            print(f"{alias} = (not installed)")
    except (AttributeError, ImportError):
        print(f"{alias} = (not installed)")


# =============================================================================
# 3. SUBMODULE ACCESS
# =============================================================================
section("3. SUBMODULE ACCESS")

lz.cache.clear()

os_path = lz.os.path
print(f"os.path = {os_path}")
print(f"  os.path.join('a', 'b') = {os_path.join('a', 'b')}")
print(f"  os.path.dirname('/a/b/c') = {os_path.dirname('/a/b/c')}")

cc_abc = lz.collections.abc
print(f"collections.abc = {cc_abc}")
print(f"  collections.abc.MutableMapping = {cc_abc.MutableMapping}")

# Submodules via auto-import (e.g., itertools, collections.abc):
itertools_mod = lz.itertools
print(f"itertools = {itertools_mod}")
print(f"  itertools.chain([1,2],[3,4]) = {list(itertools_mod.chain([1, 2], [3, 4]))}")

# os.path is loaded automatically with os:
os_path = lz.os.path
print(f"os.path already loaded via os: {os_path}")


# =============================================================================
# 4. MODULE ATTRIBUTE ACCESS
# =============================================================================
section("4. MODULE ATTRIBUTE ACCESS")

lz.cache.clear()

# Direct attribute access without intermediate variable
pi_value = lz.math.pi
print(f"lz.math.pi = {pi_value}")

getcwd_result = lz.os.getcwd()
print(f"lz.os.getcwd() = {getcwd_result}")

dumps_result = lz.json.dumps({"hello": "world"})
print(f"lz.json.dumps({{'hello': 'world'}}) = {dumps_result}")


# =============================================================================
# 5. ALIAS MANAGEMENT
# =============================================================================
section("5. ALIAS MANAGEMENT")

# register_alias
lz.alias.register("my_math", "math")
print("Registered 'my_math' -> 'math'")
print(f"  lz.my_math.pi = {lz.my_math.pi}")

# register_aliases batch
lz.alias.register_many({"my_os": "os", "my_json": "json"})
print("Batch registered: my_os, my_json")

# unregister_alias
lz.alias.unregister("my_os")
print("Unregistered 'my_os'")

# list_loaded
print(f"Loaded modules: {lz.module.list_loaded()}")

# list_available
available = lz.module.list_available()
print(f"Available aliases (sample): {available[:10]}... ({len(available)} total)")

# get_module
lz.cache.clear()
_ = lz.math.pi  # trigger load
mod = lz.module.get("math")
print(f"get_module('math'): {mod}, pi = {mod.pi}")

# validate_aliases_importable
result = validate_aliases_importable({"numpy": "numpy", "os": "os", "fake_mod_xyz": "fake_mod_xyz"})
print(
    f"validate_aliases_importable: {list(result['importable'].keys())} importable, {list(result['not_importable'].keys())} not"
)


# =============================================================================
# 6. AUTO SEARCH
# =============================================================================
section("6. AUTO SEARCH")

lz.config.auto_search = True
print(f"auto_search enabled: {lz.config.auto_search}")

# Search for a module by name
found = lz.symbol.search("typing")
print(f"search_module('typing') = {found}")

found = lz.symbol.search("pathlib")
print(f"search_module('pathlib') = {found}")

# search_class
result = lz.symbol.search("defaultdict", symbol_type="class")
print(f"search_class('defaultdict') = {result}")

# Disable
lz.config.auto_search = False
print(f"auto_search disabled: {not lz.config.auto_search}")
lz.config.auto_search = True


# =============================================================================
# 7. CACHE MANAGEMENT
# =============================================================================
section("7. CACHE MANAGEMENT")

lz.cache.clear()

# File cache
lz.cache.files.enabled = True
print(f"file_cache enabled: {lz.cache.files.enabled}")

cache_info = lz.cache.files.info()
print(f"file_cache_info: {cache_info}")

lz.cache.files.force_save()
print("force_save_cache() done")

lz.cache.files.enabled = False
print(f"file_cache disabled: {not lz.cache.files.enabled}")

# Cache config
lz.cache.config.symbol_index_ttl = 3600
lz.cache.config.stdlib_cache_ttl = 7200
lz.cache.config.compression = True
config = lz.cache.config
print(f"cache_config: {config}")

# Cache stats
stats = lz.cache.stats
print(f"cache_stats hit_rate: {stats['hit_rate']:.2%}")

reset_cache_stats()
print("cache_stats reset")

invalidate_package_cache("math")
print("invalidate_package_cache('math') done")

# Cache directory
orig_dir = lz.cache.dir
print(f"original cache_dir: {orig_dir}")

with tempfile.TemporaryDirectory() as tmpdir:
    lz.cache.dir = tmpdir
    print(f"temp cache_dir set: {lz.cache.dir}")
    lz.cache.reset_dir()
print(f"cache_dir reset: {lz.cache.dir}")


# =============================================================================
# 8. VERSION INFORMATION
# =============================================================================
section("8. VERSION INFORMATION")

lz.cache.clear()
_ = lz.math.pi  # ensure loaded

ver = lz.version.of("math")
print(f"get_version('math') = {ver}")

# Trigger more loads
_ = lz.json.dumps({})
_ = lz.os.getcwd()

# Package versions
cv = lz.version.cache()
print(f"cache_version: {cv}")

pv = lz.version.of("math")
print(f"package_version('math'): {pv}")

all_v = lz.version.all_packages()
print(f"all_package_versions keys: {list(all_v.keys())}")

lz_v = lz.version.current
print(f"laziest_import_version: {lz_v}")


# =============================================================================
# 9. IMPORT STATISTICS
# =============================================================================
section("9. IMPORT STATISTICS")

lz.cache.clear()

stats = lz.config.import_stats
print(
    f"import_stats before: total={stats['total_imports']}, avg={stats['average_time'] * 1000:.4f}ms"
)

_ = lz.math.pi
_ = lz.math.sqrt(4)
_ = lz.json.dumps({})

stats = lz.config.import_stats
print(
    f"import_stats after: total={stats['total_imports']}, avg={stats['average_time'] * 1000:.4f}ms"
)
print(f"  module_times: {stats['module_times']}")
print(f"  module_access_counts: {stats['module_access_counts']}")

reset_import_stats()
stats = lz.config.import_stats
print(f"import_stats reset: total={stats['total_imports']}")


# =============================================================================
# 10. DEBUG MODE
# =============================================================================
section("10. DEBUG MODE")

print(f"debug_mode: {lz.config.debug}")
lz.config.debug = True
print(f"debug_mode enabled: {lz.config.debug}")
_ = lz.math.pi  # will log debug info
lz.config.debug = False
print(f"debug_mode disabled: {not lz.config.debug}")


# =============================================================================
# 11. IMPORT HOOKS
# =============================================================================
section("11. IMPORT HOOKS")

hook_log = []


def pre_hook(name):
    hook_log.append(f"pre:{name}")


def post_hook(name):
    hook_log.append(f"post:{name}")


lz.hooks.pre.add(pre_hook)
lz.hooks.post.add(post_hook)
print("hooks registered")

lz.cache.clear()
_ = lz.collections.Counter
print(f"hook_log: {hook_log}")

lz.hooks.pre.remove(pre_hook)
lz.hooks.post.remove(post_hook)
print("hooks removed")

lz.hooks.clear()
print("all hooks cleared")


# =============================================================================
# 12. ASYNC IMPORT
# =============================================================================
section("12. ASYNC IMPORT")

import asyncio


async def demo_async():
    mod = await lz.async_.get("math")
    print(f"async import 'math': {mod.pi}")

    mods = await lz.async_.fetch(["os", "json", "re"])
    print(f"async batch import: {list(mods.keys())}")


asyncio.run(demo_async())

# Retry config
lz.config.retry.enabled = True
lz.config.retry.max_retries = 3
lz.config.retry.retry_delay = 0.1
print(f"retry enabled: {lz.config.retry.enabled}")
lz.config.retry.enabled = False
print(f"retry disabled: {not lz.config.retry.enabled}")


# =============================================================================
# 13. SYMBOL SEARCH
# =============================================================================
section("13. SYMBOL SEARCH")

print(f"symbol_search enabled: {lz.symbol.config.enabled}")

lz.symbol.config.enable()
lz.symbol.config.interactive = False
print("symbol_search explicitly enabled")

# Search for symbols
symbols = lz.symbol.search("sqrt", max_results=5)
print(f"search_symbol('sqrt'): {len(symbols)} results")
for s in symbols[:3]:
    print(f"  {s.module_name}.{s.symbol_name} ({s.symbol_type})")

symbols2 = lz.symbol.search("DataFrame", max_results=5)
print(f"search_symbol('DataFrame'): {len(symbols2)} results")
for s in symbols2[:3]:
    print(f"  {s.module_name}.{s.symbol_name} ({s.symbol_type})")

# Symbol search config
sc = lz.symbol.config.snapshot()
print(f"symbol_search_config: {sc}")

# Symbol cache info
ci = lz.symbol.cache_info()
print(f"symbol_cache_info keys: {list(ci.keys())}")

# rebuild
lz.symbol.index.rebuild()
print("symbol_index rebuilt")

# clear
lz.cache.symbols.clear()
print("symbol_cache cleared")

# sharding
enable_sharding()
print("sharding enabled")

ss = lz.symbol.sharded("sin", max_results=3)
print(f"search_with_sharding('sin'): {len(ss)} results")

shard_config = get_sharding_config()
print(f"sharding_config: {shard_config}")

clear_shard_cache()
print("shard_cache cleared")

disable_sharding()
print("sharding disabled")


# =============================================================================
# 14. SYMBOL PREFERENCES & RESOLUTION
# =============================================================================
section("14. SYMBOL PREFERENCES & RESOLUTION")

lz.symbol.prefer("array", "numpy")
pref = lz.symbol.preference("array")
print(f"symbol preference for 'array': {pref}")

lz.symbol.clear_preference("array")
print("symbol preference for 'array' cleared")

set_module_priority("numpy", 100)
prio = get_module_priority("numpy")
print(f"module priority for 'numpy': {prio}")

conflicts = lz.symbol.conflicts("sqrt") or []
print(f"symbol conflicts for 'sqrt': {len(conflicts)} found")
for mod in conflicts[:3]:
    print(f"  {mod}")

lz.symbol.config.auto_resolution = True
print(f"auto_symbol_resolution enabled: {lz.symbol.config.auto_resolution}")

lz.symbol.config.auto_resolution = False
print(f"auto_symbol_resolution disabled: {not lz.symbol.config.auto_resolution}")

ctx = get_loaded_modules_context()
print(f"loaded_modules_context: {len(ctx)} modules")


# =============================================================================
# 15. INCREMENTAL INDEX
# =============================================================================
section("15. INCREMENTAL INDEX")

lz.background.enable(True)
print("incremental_index enabled")

lz.symbol.index.incremental()
print("incremental build done")

inc_config = get_incremental_config()
print(f"incremental_config: {inc_config}")


# =============================================================================
# 16. AUTO INSTALL
# =============================================================================
section("16. AUTO INSTALL")

print(f"auto_install enabled: {lz.install.enabled}")

lz.install.enable(interactive=False, allow_non_interactive=True)
print("auto_install enabled (non-interactive)")

ac = lz.install.auto
print(f"auto_install_config: {ac}")

set_pip_index("https://pypi.org/simple/")
print("pip_index set")

set_pip_extra_args(["--no-cache-dir"])
print("pip_extra_args set")

lz.install.disable()
print("auto_install disabled")


# =============================================================================
# 17. DEPENDENCY ANALYSIS
# =============================================================================
section("17. DEPENDENCY ANALYSIS")

analyzer = DependencyPreAnalyzer()
print(f"DependencyPreAnalyzer created: {analyzer}")

source = """
import os
import json
from collections import defaultdict
import math
"""
result = lz.analyze.code(source)
print("analyze_source:")
print(f"  predicted_imports: {result.predicted_imports}")
print(f"  used_symbols: {result.used_symbols}")

with tempfile.TemporaryDirectory() as tmpdir:
    pyfile = Path(tmpdir) / "test_analysis.py"
    pyfile.write_text(source)
    result2 = lz.analyze.file(str(pyfile))
    print(f"analyze_file: {result2.predicted_imports}")

    pyfile2 = Path(tmpdir) / "test_analysis2.py"
    pyfile2.write_text("import re")
    results3 = lz.analyze.dir(tmpdir, recursive=False)
    print(f"analyze_directory: {len(results3)} files analyzed")


# =============================================================================
# 18. IMPORT PROFILER
# =============================================================================
section("18. IMPORT PROFILER")

profiler = ImportProfiler()
print("ImportProfiler created")

lz.profile.start()
print("profiling started")

_ = lz.math.pi
_ = lz.json.dumps({})
_ = lz.os.getcwd()

lz.profile.stop()
print("profiling stopped")

report = lz.profile.report()
print(f"profile_report modules: {list(report.modules.keys())}")
for name, profile in report.modules.items():
    print(f"  {name}: {profile.load_time * 1000:.2f}ms")

# Print formatted
lz.profile.print_report()


# =============================================================================
# 19. ENVIRONMENT & CONFLICTS
# =============================================================================
section("19. ENVIRONMENT & CONFLICTS")

env = detect_environment()
print(f"detect_environment: python={env.python_version}")

show_environment()

lz.cache.clear()
_ = lz.math.pi

confs = lz.symbol.show_conflicts()
print("show_conflicts done")

summary = lz.symbol.conflict_summary()
print(f"conflicts_summary: {summary}")


# =============================================================================
# 20. PREFERENCES
# =============================================================================
section("20. PREFERENCES")

save_preferences()
print("preferences saved")

load_preferences()
print("preferences loaded")

apply_preferences()
print("preferences applied")

clear_preferences()
print("preferences cleared")


# =============================================================================
# 21. DEPENDENCY TREE
# =============================================================================
section("21. DEPENDENCY TREE")

tree = lz.analyze.dep_tree("math", max_depth=2)
print("dependency_tree('math', max_depth=2):")
print(f"  root: {tree.root_module}, children: {len(tree.tree.children) if tree.tree else 0}")
print(f"  total_nodes: {tree.total_modules}")

# Print tree manually (avoid unicode encoding issues on some platforms)
print(f"\nDependency Tree: {tree.root_module}")
print("=" * 50)
print(f"Total modules: {tree.total_modules}")
print(f"  - Stdlib: {tree.stdlib_count}")
print(f"  - Third-party: {tree.third_party_count}")
print(f"  - Unavailable: {tree.unavailable_count}")
print(f"Max depth: {tree.max_depth}")
if tree.tree:
    print(f"  root children: {len(tree.tree.children)} nodes")

# Data classes
node = DependencyNode("test_node")
print(f"DependencyNode('test_node'): {node}")

dt = DependencyTree(root_module="test_node", tree=node)
print(f"DependencyTree created: root={dt.root_module}")


# =============================================================================
# 22. BENCHMARK
# =============================================================================
section("22. BENCHMARK")

result = benchmark(lambda: lz.math.pi, iterations=50, name="lz.math.pi")
print(
    f"benchmark 'lz.math.pi': {result.avg_time * 1000:.4f}ms mean, {result.std_dev * 1000:.4f}ms std"
)

result2 = benchmark_imports(["math", "json", "os"])
print(f"benchmark_imports: {len(result2.results)} results")

print_benchmark_report(BenchmarkReport(results=[result]))

br = BenchmarkResult(
    name="test",
    iterations=100,
    total_time=0.1,
    avg_time=0.001,
    min_time=0.0009,
    max_time=0.0011,
    std_dev=0.0001,
)
print(f"BenchmarkResult: mean={br.avg_time * 1000:.4f}ms")

brep = BenchmarkReport([br])
print(f"BenchmarkReport: {len(brep.results)} results")


# =============================================================================
# 23. INTROSPECTION
# =============================================================================
section("23. INTROSPECTION")

symbols = list_module_symbols("math")
print(f"list_module_symbols('math'): {len(symbols)} symbols")
print(f"  sample: {symbols[:5]}")

info = get_module_info("math")
print(f"get_module_info('math'): is_package={info['is_package']}, path={info['path']}")

found = search_in_module("math", "pi")
print(f"search_in_module('math', 'pi'): {found}")


# =============================================================================
# 24. WHICH FUNCTION
# =============================================================================
section("24. WHICH FUNCTION")

loc = lz.symbol.which("sqrt")
print(f"which('sqrt'): {loc}")

loc2 = lz.symbol.which("cos")
print(f"which('cos'): {loc2}")

# which with module hint
loc3 = lz.symbol.which("sin", module_hint="math")
print(f"which('sin', module_hint='math'): {loc3}")

# which_all
locs = lz.symbol.which_all("sin")
print(f"which_all('sin'): {len(locs)} results")
for loc in locs[:3]:
    print(f"  {loc}")


# =============================================================================
# 25. HELP & EASTER EGG
# =============================================================================
section("25. HELP & EASTER EGG")

help_text = lzhelp()
print(f"help() returned {len(help_text)} chars")

help_alias = lzhelp("alias")
print(f"help('alias') returned {len(help_alias)} chars")

help_cache = lzhelp("cache")
print(f"help('cache') returned {len(help_cache)} chars")

egg = easter_egg()
print(f"easter_egg: {egg}")

egg2 = easter_egg("author")
print(f"easter_egg('author'): {egg2}")

egg3 = easter_egg("unknown")
print(f"easter_egg('unknown'): {egg3}")


# =============================================================================
# 26. CONFIG PATHS
# =============================================================================
section("26. CONFIG PATHS")

paths = get_config_paths()
print(f"config_paths: {paths}")

dirs = get_config_dirs()
print(f"config_dirs: {dirs}")


# =============================================================================
# 27. IMPORT STATISTICS DATA CLASSES
# =============================================================================
section("27. IMPORT STATISTICS DATA CLASSES")

stats_obj = lz.config.import_stats
imports_count = stats_obj["total_imports"]
print(f"Total imports recorded: {imports_count}")

_ = lz.math.pi
_ = lz.math.sqrt(4)
_ = lz.json.dumps({})

stats_after = lz.config.import_stats
print(
    f"After 3 more: total={stats_after['total_imports']}, module_times={stats_after['module_times']}"
)


# =============================================================================
# 28. BACKGROUND INDEX BUILD
# =============================================================================
section("28. BACKGROUND INDEX BUILD")

lz.background.start()
print(f"background index building: {lz.background.is_building}")

# Wait briefly
import time

time.sleep(0.5)

lz.background.timeout = 30
print(f"background_timeout set: {lz.background.timeout}")

lz.background.wait(timeout=5)
print("wait_for_index completed")

# Preheat config
ph = lz.background.preheat
print(f"preheat_config: {ph}")


# =============================================================================
# 29. RC CONFIG
# =============================================================================
section("29. RC CONFIG")

rc_info = lz.rc.info()
print(f"rc_info: {list(rc_info.keys())}")

rc_val = lz.rc.get("default_search_mode")
print(f"get_rc_value('default_search_mode'): {rc_val}")

rc2 = lz.rc.reload()
print("reload_rc_config done")


# =============================================================================
# 30. MODULE RELOAD
# =============================================================================
section("30. MODULE RELOAD")

lz.cache.clear()
_ = lz.math.pi
ok = lz.module.reload("math")
print(f"reload_module('math'): {ok}")


# =============================================================================
# 31. REGISTER / EXPORT / VALIDATE ALIASES
# =============================================================================
section("31. ALIAS EXPORT & VALIDATION")

lz.alias.register("demo_alias", "os")
print("registered 'demo_alias' -> 'os'")

exported = lz.alias.export()
print(f"export_aliases returned {len(exported)} chars (JSON)")

exported_cat = lz.alias.export(include_categories=False)
print(f"export_aliases(include_categories=False) returned {len(exported_cat)} chars")

validation = lz.alias.validate()
print(f"validate_aliases: {len(validation)} entries")
for alias, info in list(validation.items())[:3]:
    print(f"  {alias}: {info}")

lz.alias.reload()
print("aliases reloaded")

lz.install.rebuild_cache()
print("module cache rebuilt")


# =============================================================================
# 32. CACHE COMPRESSION
# =============================================================================
section("32. CACHE COMPRESSION")

lz.cache.config.compression = True
print("cache compression enabled")

cfg = lz.cache.config
print(f"compression in config: {cfg.compression}")


# =============================================================================
# 33. RESET ALL
# =============================================================================
section("33. RESET ALL")

lz.cache.clear()
print("clear_cache done")

reset_all()
print("reset_all done (aliases reloaded, caches cleared)")


# =============================================================================
# 34. NEGATIVE CACHE (should be instant on repeated misses)
# =============================================================================
section("34. NEGATIVE CACHE PERFORMANCE")

import contextlib
import time

lz.cache.clear()
t0 = time.perf_counter()
for _ in range(100):
    with contextlib.suppress(AttributeError):
        _ = lz.this_module_does_not_exist_at_all_xyz.foo
t = time.perf_counter() - t0
print(f"100 failed lookups: {t * 1000:.2f}ms total ({t / 100 * 1000:.4f}ms each)")
assert t < 2.0, f"Negative cache too slow: {t:.2f}s"


# =============================================================================
# 35. ENSURE EVERYTHING STILL WORKS AFTER CLEAR
# =============================================================================
section("35. POST-CLEAR VERIFICATION")

lz.cache.clear()
assert lz.math.pi > 3.14, "math.pi still works"
assert lz.os.getcwd() is not None, "os.getcwd still works"
assert lz.json.dumps({"a": 1}) == '{"a": 1}', "json.dumps still works"

lz.alias.register("test_final", "math")
assert lz.test_final.pi > 3.14, "registered alias still works"
lz.alias.unregister("test_final")

print("All systems operational after cache clear!")


# =============================================================================
# SUMMARY
# =============================================================================
section("SUMMARY")

stats = lz.config.import_stats
print(f"Total imports: {stats['total_imports']}")
loaded = lz.module.list_loaded()
print(f"Modules loaded this session: {len(loaded)}")
print("All tests passed!")


if __name__ == "__main__":
    print("\n=== Comprehensive usage test completed successfully! ===")
