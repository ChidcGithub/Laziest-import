"""
Comprehensive usage test for laziest-import.
Covers every public API and demonstrates real-world usage patterns.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import laziest_import as lz


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
from laziest_import import clear_cache, list_loaded, help as lzhelp

print(f"Direct import of functions works: clear_cache={callable(clear_cache)}")


# =============================================================================
# 2. LAZY MODULE ACCESS VIA ALIASES
# =============================================================================
section("2. LAZY MODULE ACCESS VIA ALIASES")

lz.clear_cache()

# Standard library aliases
np = lz.np
print(f"np = {np}, type = {type(np).__name__}")
print(f"  np.array([1,2,3]) = {np.array([1, 2, 3])}")

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
print(f"  re.findall(r'\\d+', 'a1b2c3') = {re_mod.findall(r'\\d+', 'a1b2c3')}")

time_mod = lz.time
print(f"time = {time_mod}")

random_mod = lz.random
print(f"random = {random_mod}")
print(f"  random.randint(1,10) = {random_mod.randint(1, 10)}")

# Popular third-party aliases (may not be installed)
for alias in ["pd", "plt", "tf", "torch"]:
    try:
        mod = getattr(lz, alias)
        print(f"{alias} = {mod}")
    except AttributeError:
        print(f"{alias} = (not installed)")


# =============================================================================
# 3. SUBMODULE ACCESS
# =============================================================================
section("3. SUBMODULE ACCESS")

lz.clear_cache()

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

lz.clear_cache()

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
lz.register_alias("my_math", "math")
print(f"Registered 'my_math' -> 'math'")
print(f"  lz.my_math.pi = {lz.my_math.pi}")

# register_aliases batch
lz.register_aliases({"my_os": "os", "my_json": "json"})
print(f"Batch registered: my_os, my_json")

# unregister_alias
lz.unregister_alias("my_os")
print(f"Unregistered 'my_os'")

# list_loaded
print(f"Loaded modules: {lz.list_loaded()}")

# list_available
available = lz.list_available()
print(f"Available aliases (sample): {available[:10]}... ({len(available)} total)")

# get_module
lz.clear_cache()
_ = lz.math.pi  # trigger load
mod = lz.get_module("math")
print(f"get_module('math'): {mod}, pi = {mod.pi}")

# validate_aliases_importable
result = lz.validate_aliases_importable(
    {"numpy": "numpy", "os": "os", "fake_mod_xyz": "fake_mod_xyz"}
)
print(
    f"validate_aliases_importable: {result['importable'].keys()} importable, {result['not_importable'].keys()} not"
)


# =============================================================================
# 6. AUTO SEARCH
# =============================================================================
section("6. AUTO SEARCH")

lz.enable_auto_search()
print(f"auto_search enabled: {lz.is_auto_search_enabled()}")

# Search for a module by name
found = lz.search_module("typing")
print(f"search_module('typing') = {found}")

found = lz.search_module("pathlib")
print(f"search_module('pathlib') = {found}")

# search_class
result = lz.search_class("defaultdict")
print(f"search_class('defaultdict') = {result}")

# Disable
lz.disable_auto_search()
print(f"auto_search disabled: {not lz.is_auto_search_enabled()}")
lz.enable_auto_search()


# =============================================================================
# 7. CACHE MANAGEMENT
# =============================================================================
section("7. CACHE MANAGEMENT")

lz.clear_cache()

# File cache
lz.enable_file_cache()
print(f"file_cache enabled: {lz.is_file_cache_enabled()}")

cache_info = lz.get_file_cache_info()
print(f"file_cache_info: {cache_info}")

lz.force_save_cache()
print(f"force_save_cache() done")

lz.disable_file_cache()
print(f"file_cache disabled: {not lz.is_file_cache_enabled()}")

# Cache config
lz.set_cache_config(
    symbol_index_ttl=3600, stdlib_cache_ttl=7200, enable_compression=True
)
config = lz.get_cache_config()
print(f"cache_config: {config}")

# Cache stats
stats = lz.get_cache_stats()
print(f"cache_stats hit_rate: {stats['hit_rate']:.2%}")

lz.reset_cache_stats()
print(f"cache_stats reset")

lz.invalidate_package_cache("math")
print(f"invalidate_package_cache('math') done")

# Cache directory
orig_dir = lz.get_cache_dir()
print(f"original cache_dir: {orig_dir}")

with tempfile.TemporaryDirectory() as tmpdir:
    lz.set_cache_dir(tmpdir)
    print(f"temp cache_dir set: {lz.get_cache_dir()}")
    lz.reset_cache_dir()
print(f"cache_dir reset: {lz.get_cache_dir()}")


# =============================================================================
# 8. VERSION INFORMATION
# =============================================================================
section("8. VERSION INFORMATION")

lz.clear_cache()
_ = lz.math.pi  # ensure loaded

ver = lz.get_version("math")
print(f"get_version('math') = {ver}")

# Trigger more loads
_ = lz.json.dumps({})
_ = lz.os.getcwd()

# Package versions
cv = lz.get_cache_version()
print(f"cache_version: {cv}")

pv = lz.get_package_version("math")
print(f"package_version('math'): {pv}")

all_v = lz.get_all_package_versions()
print(f"all_package_versions keys: {list(all_v.keys())}")

lz_v = lz.get_laziest_import_version()
print(f"laziest_import_version: {lz_v}")


# =============================================================================
# 9. IMPORT STATISTICS
# =============================================================================
section("9. IMPORT STATISTICS")

lz.clear_cache()

stats = lz.get_import_stats()
print(
    f"import_stats before: total={stats['total_imports']}, avg={stats['average_time'] * 1000:.4f}ms"
)

_ = lz.math.pi
_ = lz.math.sqrt(4)
_ = lz.json.dumps({})

stats = lz.get_import_stats()
print(
    f"import_stats after: total={stats['total_imports']}, avg={stats['average_time'] * 1000:.4f}ms"
)
print(f"  module_times: {stats['module_times']}")
print(f"  module_access_counts: {stats['module_access_counts']}")

lz.reset_import_stats()
stats = lz.get_import_stats()
print(f"import_stats reset: total={stats['total_imports']}")


# =============================================================================
# 10. DEBUG MODE
# =============================================================================
section("10. DEBUG MODE")

print(f"debug_mode: {lz.is_debug_mode()}")
lz.enable_debug_mode()
print(f"debug_mode enabled: {lz.is_debug_mode()}")
_ = lz.math.pi  # will log debug info
lz.disable_debug_mode()
print(f"debug_mode disabled: {not lz.is_debug_mode()}")


# =============================================================================
# 11. IMPORT HOOKS
# =============================================================================
section("11. IMPORT HOOKS")

hook_log = []


def pre_hook(name):
    hook_log.append(f"pre:{name}")


def post_hook(name):
    hook_log.append(f"post:{name}")


lz.add_pre_import_hook(pre_hook)
lz.add_post_import_hook(post_hook)
print(f"hooks registered")

lz.clear_cache()
_ = lz.collections.Counter
print(f"hook_log: {hook_log}")

lz.remove_pre_import_hook(pre_hook)
lz.remove_post_import_hook(post_hook)
print(f"hooks removed")

lz.clear_import_hooks()
print(f"all hooks cleared")


# =============================================================================
# 12. ASYNC IMPORT
# =============================================================================
section("12. ASYNC IMPORT")

import asyncio


async def demo_async():
    mod = await lz.import_async("math")
    print(f"async import 'math': {mod.pi}")

    mods = await lz.import_multiple_async(["os", "json", "re"])
    print(f"async batch import: {list(mods.keys())}")


asyncio.run(demo_async())

# Retry config
lz.enable_retry(max_retries=3, retry_delay=0.1)
print(f"retry enabled: {lz.is_retry_enabled()}")
lz.disable_retry()
print(f"retry disabled: {not lz.is_retry_enabled()}")


# =============================================================================
# 13. SYMBOL SEARCH
# =============================================================================
section("13. SYMBOL SEARCH")

print(f"symbol_search enabled: {lz.is_symbol_search_enabled()}")

lz.enable_symbol_search(interactive=False)
print(f"symbol_search explicitly enabled")

# Search for symbols
symbols = lz.search_symbol("sqrt", max_results=5)
print(f"search_symbol('sqrt'): {len(symbols)} results")
for s in symbols[:3]:
    print(f"  {s.module_name}.{s.symbol_name} ({s.symbol_type})")

symbols2 = lz.search_symbol("DataFrame", max_results=5)
print(f"search_symbol('DataFrame'): {len(symbols2)} results")
for s in symbols2[:3]:
    print(f"  {s.module_name}.{s.symbol_name} ({s.symbol_type})")

# Symbol search config
sc = lz.get_symbol_search_config()
print(f"symbol_search_config: {sc}")

# Symbol cache info
ci = lz.get_symbol_cache_info()
print(f"symbol_cache_info keys: {list(ci.keys())}")

# rebuild
lz.rebuild_symbol_index()
print(f"symbol_index rebuilt")

# clear
lz.clear_symbol_cache()
print(f"symbol_cache cleared")

# sharding
lz.enable_sharding()
print(f"sharding enabled")

ss = lz.search_with_sharding("sin", max_results=3)
print(f"search_with_sharding('sin'): {len(ss)} results")

shard_config = lz.get_sharding_config()
print(f"sharding_config: {shard_config}")

lz.clear_shard_cache()
print(f"shard_cache cleared")

lz.disable_sharding()
print(f"sharding disabled")


# =============================================================================
# 14. SYMBOL PREFERENCES & RESOLUTION
# =============================================================================
section("14. SYMBOL PREFERENCES & RESOLUTION")

lz.set_symbol_preference("array", "numpy")
pref = lz.get_symbol_preference("array")
print(f"symbol preference for 'array': {pref}")

lz.clear_symbol_preference("array")
print(f"symbol preference for 'array' cleared")

lz.set_module_priority("numpy", 100)
prio = lz.get_module_priority("numpy")
print(f"module priority for 'numpy': {prio}")

conflicts = lz.list_symbol_conflicts("sqrt")
print(f"symbol conflicts for 'sqrt': {len(conflicts)} found")
for mod in conflicts[:3]:
    print(f"  {mod}")

lz.enable_auto_symbol_resolution()
print(
    f"auto_symbol_resolution enabled: {lz.get_symbol_resolution_config()['auto_symbol']}"
)

lz.disable_auto_symbol_resolution()
print(
    f"auto_symbol_resolution disabled: {not lz.get_symbol_resolution_config()['auto_symbol']}"
)

ctx = lz.get_loaded_modules_context()
print(f"loaded_modules_context: {len(ctx)} modules")


# =============================================================================
# 15. INCREMENTAL INDEX
# =============================================================================
section("15. INCREMENTAL INDEX")

lz.enable_incremental_index()
print(f"incremental_index enabled")

lz.build_symbol_index_incremental()
print(f"incremental build done")

inc_config = lz.get_incremental_config()
print(f"incremental_config: {inc_config}")


# =============================================================================
# 16. AUTO INSTALL
# =============================================================================
section("16. AUTO INSTALL")

print(f"auto_install enabled: {lz.is_auto_install_enabled()}")

lz.enable_auto_install(interactive=False)
print(f"auto_install enabled (non-interactive)")

ac = lz.get_auto_install_config()
print(f"auto_install_config: {ac}")

lz.set_pip_index("https://pypi.org/simple/")
print(f"pip_index set")

lz.set_pip_extra_args(["--no-deps"])
print(f"pip_extra_args set")

lz.disable_auto_install()
print(f"auto_install disabled")


# =============================================================================
# 17. DEPENDENCY ANALYSIS
# =============================================================================
section("17. DEPENDENCY ANALYSIS")

analyzer = lz.DependencyPreAnalyzer()
print(f"DependencyPreAnalyzer created: {analyzer}")

source = """
import os
import json
from collections import defaultdict
import math
"""
result = lz.analyze_source(source)
print(f"analyze_source:")
print(f"  predicted_imports: {result.predicted_imports}")
print(f"  used_symbols: {result.used_symbols}")

with tempfile.TemporaryDirectory() as tmpdir:
    pyfile = Path(tmpdir) / "test_analysis.py"
    pyfile.write_text(source)
    result2 = lz.analyze_file(str(pyfile))
    print(f"analyze_file: {result2.predicted_imports}")

    pyfile2 = Path(tmpdir) / "test_analysis2.py"
    pyfile2.write_text("import re")
    results3 = lz.analyze_directory(tmpdir, recursive=False)
    print(f"analyze_directory: {len(results3)} files analyzed")


# =============================================================================
# 18. IMPORT PROFILER
# =============================================================================
section("18. IMPORT PROFILER")

profiler = lz.ImportProfiler()
print(f"ImportProfiler created")

lz.start_profiling()
print(f"profiling started")

_ = lz.math.pi
_ = lz.json.dumps({})
_ = lz.os.getcwd()

lz.stop_profiling()
print(f"profiling stopped")

report = lz.get_profile_report()
print(f"profile_report modules: {list(report.modules.keys())}")
for name, profile in report.modules.items():
    print(f"  {name}: {profile.load_time * 1000:.2f}ms")

# Print formatted
lz.print_profile_report()


# =============================================================================
# 19. ENVIRONMENT & CONFLICTS
# =============================================================================
section("19. ENVIRONMENT & CONFLICTS")

env = lz.detect_environment()
print(f"detect_environment: python={env.python_version}")

lz.show_environment()

lz.clear_cache()
_ = lz.math.pi

confs = lz.show_conflicts()
print(f"show_conflicts done")

summary = lz.get_conflicts_summary()
print(f"conflicts_summary: {summary}")


# =============================================================================
# 20. PREFERENCES
# =============================================================================
section("20. PREFERENCES")

lz.save_preferences()
print(f"preferences saved")

lz.load_preferences()
print(f"preferences loaded")

lz.apply_preferences()
print(f"preferences applied")

lz.clear_preferences()
print(f"preferences cleared")


# =============================================================================
# 21. DEPENDENCY TREE
# =============================================================================
section("21. DEPENDENCY TREE")

tree = lz.dependency_tree("math", max_depth=2)
print(f"dependency_tree('math', max_depth=2):")
print(
    f"  root: {tree.root_module}, children: {len(tree.tree.children) if tree.tree else 0}"
)
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
node = lz.DependencyNode("test_node")
print(f"DependencyNode('test_node'): {node}")

dt = lz.DependencyTree(root_module="test_node", tree=node)
print(f"DependencyTree created: root={dt.root_module}")


# =============================================================================
# 22. BENCHMARK
# =============================================================================
section("22. BENCHMARK")

result = lz.benchmark(lambda: lz.math.pi, iterations=50, name="lz.math.pi")
print(
    f"benchmark 'lz.math.pi': {result.avg_time * 1000:.4f}ms mean, {result.std_dev * 1000:.4f}ms std"
)

result2 = lz.benchmark_imports(["math", "json", "os"])
print(f"benchmark_imports: {len(result2.results)} results")

lz.print_benchmark_report(lz.BenchmarkReport(results=[result]))

br = lz.BenchmarkResult(
    name="test",
    iterations=100,
    total_time=0.1,
    avg_time=0.001,
    min_time=0.0009,
    max_time=0.0011,
    std_dev=0.0001,
)
print(f"BenchmarkResult: mean={br.avg_time * 1000:.4f}ms")

brep = lz.BenchmarkReport([br])
print(f"BenchmarkReport: {len(brep.results)} results")


# =============================================================================
# 23. INTROSPECTION
# =============================================================================
section("23. INTROSPECTION")

symbols = lz.list_module_symbols("math")
print(f"list_module_symbols('math'): {len(symbols)} symbols")
print(f"  sample: {symbols[:5]}")

info = lz.get_module_info("math")
print(f"get_module_info('math'): is_package={info['is_package']}, path={info['path']}")

found = lz.search_in_module("math", "pi")
print(f"search_in_module('math', 'pi'): {found}")


# =============================================================================
# 24. WHICH FUNCTION
# =============================================================================
section("24. WHICH FUNCTION")

loc = lz.which("sqrt")
print(f"which('sqrt'): {loc}")

loc2 = lz.which("cos")
print(f"which('cos'): {loc2}")

# which with module hint
loc3 = lz.which("sin", module_hint="math")
print(f"which('sin', module_hint='math'): {loc3}")

# which_all
locs = lz.which_all("sin")
print(f"which_all('sin'): {len(locs)} results")
for loc in locs[:3]:
    print(f"  {loc}")


# =============================================================================
# 25. HELP & EASTER EGG
# =============================================================================
section("25. HELP & EASTER EGG")

help_text = lz.help()
print(f"help() returned {len(help_text)} chars")

help_alias = lz.help("alias")
print(f"help('alias') returned {len(help_alias)} chars")

help_cache = lz.help("cache")
print(f"help('cache') returned {len(help_cache)} chars")

egg = lz.easter_egg()
print(f"easter_egg: {egg}")

egg2 = lz.easter_egg("author")
print(f"easter_egg('author'): {egg2}")

egg3 = lz.easter_egg("unknown")
print(f"easter_egg('unknown'): {egg3}")


# =============================================================================
# 26. CONFIG PATHS
# =============================================================================
section("26. CONFIG PATHS")

paths = lz.get_config_paths()
print(f"config_paths: {paths}")

dirs = lz.get_config_dirs()
print(f"config_dirs: {dirs}")


# =============================================================================
# 27. IMPORT STATISTICS DATA CLASSES
# =============================================================================
section("27. IMPORT STATISTICS DATA CLASSES")

stats_obj = lz.get_import_stats()
imports_count = stats_obj["total_imports"]
print(f"Total imports recorded: {imports_count}")

_ = lz.math.pi
_ = lz.math.sqrt(4)
_ = lz.json.dumps({})

stats_after = lz.get_import_stats()
print(
    f"After 3 more: total={stats_after['total_imports']}, module_times={stats_after['module_times']}"
)


# =============================================================================
# 28. BACKGROUND INDEX BUILD
# =============================================================================
section("28. BACKGROUND INDEX BUILD")

lz.start_background_index_build()
print(f"background index building: {lz.is_index_building()}")

# Wait briefly
import time

time.sleep(0.5)

lz.set_background_timeout(30)
print(f"background_timeout set: {lz.get_background_timeout()}")

lz.wait_for_index(timeout=5)
print(f"wait_for_index completed")

# Preheat config
ph = lz.get_preheat_config()
print(f"preheat_config: {ph}")


# =============================================================================
# 29. RC CONFIG
# =============================================================================
section("29. RC CONFIG")

rc_info = lz.get_rc_info()
print(f"rc_info: {list(rc_info.keys())}")

rc_val = lz.get_rc_value("default_search_mode")
print(f"get_rc_value('default_search_mode'): {rc_val}")

rc2 = lz.reload_rc_config()
print(f"reload_rc_config done")


# =============================================================================
# 30. MODULE RELOAD
# =============================================================================
section("30. MODULE RELOAD")

lz.clear_cache()
_ = lz.math.pi
ok = lz.reload_module("math")
print(f"reload_module('math'): {ok}")


# =============================================================================
# 31. REGISTER / EXPORT / VALIDATE ALIASES
# =============================================================================
section("31. ALIAS EXPORT & VALIDATION")

lz.register_alias("demo_alias", "os")
print(f"registered 'demo_alias' -> 'os'")

exported = lz.export_aliases()
print(f"export_aliases returned {len(exported)} chars (JSON)")

exported_cat = lz.export_aliases(include_categories=False)
print(f"export_aliases(include_categories=False) returned {len(exported_cat)} chars")

validation = lz.validate_aliases()
print(f"validate_aliases: {len(validation)} entries")
for alias, info in list(validation.items())[:3]:
    print(f"  {alias}: {info}")

lz.reload_aliases()
print(f"aliases reloaded")

lz.rebuild_module_cache()
print(f"module cache rebuilt")


# =============================================================================
# 32. CACHE COMPRESSION
# =============================================================================
section("32. CACHE COMPRESSION")

lz.enable_cache_compression(True)
print(f"cache compression enabled")

cfg = lz.get_cache_config()
print(f"compression in config: {cfg.get('enable_compression')}")


# =============================================================================
# 33. RESET ALL
# =============================================================================
section("33. RESET ALL")

lz.clear_cache()
print(f"clear_cache done")

lz.reset_all()
print(f"reset_all done (aliases reloaded, caches cleared)")


# =============================================================================
# 34. NEGATIVE CACHE (should be instant on repeated misses)
# =============================================================================
section("34. NEGATIVE CACHE PERFORMANCE")

import time

lz.clear_cache()
t0 = time.perf_counter()
for _ in range(100):
    try:
        _ = lz.this_module_does_not_exist_at_all_xyz.foo
    except AttributeError:
        pass
t = time.perf_counter() - t0
print(f"100 failed lookups: {t * 1000:.2f}ms total ({t / 100 * 1000:.4f}ms each)")
assert t < 2.0, f"Negative cache too slow: {t:.2f}s"


# =============================================================================
# 35. ENSURE EVERYTHING STILL WORKS AFTER CLEAR
# =============================================================================
section("35. POST-CLEAR VERIFICATION")

lz.clear_cache()
assert lz.math.pi > 3.14, "math.pi still works"
assert lz.os.getcwd() is not None, "os.getcwd still works"
assert lz.json.dumps({"a": 1}) == '{"a": 1}', "json.dumps still works"

lz.register_alias("test_final", "math")
assert lz.test_final.pi > 3.14, "registered alias still works"
lz.unregister_alias("test_final")

print("All systems operational after cache clear!")


# =============================================================================
# SUMMARY
# =============================================================================
section("SUMMARY")

stats = lz.get_import_stats()
print(f"Total imports: {stats['total_imports']}")
loaded = lz.list_loaded()
print(f"Modules loaded this session: {len(loaded)}")
print(f"All tests passed!")


if __name__ == "__main__":
    print("\n=== Comprehensive usage test completed successfully! ===")
