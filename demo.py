"""
Demo: exercise laziest-import from a user's perspective.
"""
import os as _os
_RUN_ID = _os.urandom(4).hex()

from laziest_import import lz


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── 1. Basic info ──────────────────────────────────────────────
section("1. Basic Info")
print(f"lz object : {lz}")
print(f"version   : {lz.__version__}")
print(f"version_of: {lz.version_of('laziest-import')}")
print(f"version_ns: {lz.version}")


# ── 2. Lazy module access via __getattr__ ──────────────────────
section("2. Lazy Module Access (by name)")
os_mod = lz.os
print(f"lz.os == os: {os_mod.__name__}")

np_mod = lz.module.numpy
print(f"lz.module.numpy: {np_mod.__name__}, array: {np_mod.array([1,2,3])}")

try:
    lz.nonexistent_xyzzy
except AttributeError as e:
    print(f"AttributeError for unknown name: {e}")


# ── 3. Module namespace ────────────────────────────────────────
section("3. Module Namespace")
print(f"module:           {lz.module}")
print(f"available (≤5):   {lz.module.list_available()[:5]}")
print(f"loaded:           {lz.module.list_loaded()}")
print(f"is_loaded('os'): {lz.module.is_loaded('os')}")

json_mod = lz.module.load("json")
print(f"load('json'):      {json_mod.__name__}")


# ── 4. Config namespace ────────────────────────────────────────
section("4. Config Namespace")
print(f"config:        {lz.config}")
print(f"debug:         {lz.config.debug}")
print(f"auto_search:   {lz.config.auto_search}")
print(f"auto_install:  {lz.config.auto_install}")
print(f"retry:         {lz.config.retry}")
print(f"symbol_search: {lz.config.symbol_search}")
print(f"import_stats:  {lz.config.import_stats}")

lz.config.debug = True
print(f"debug (after True):  {lz.config.debug}")
lz.config.debug = False
print(f"debug (after False): {lz.config.debug}")

with lz.config.temp_config(debug=True, auto_search=False):
    print(f"  inside temp: debug={lz.config.debug}, auto_search={lz.config.auto_search}")
print(f"outside temp: debug={lz.config.debug}, auto_search={lz.config.auto_search}")

snap = lz.config.snapshot()
print(f"snapshot keys: {list(snap.keys())}")


# ── 5. Symbol search ───────────────────────────────────────────
section("5. Symbol Search")
lz.symbol.config.enable()
results = lz.symbol.search("json")
print(f"search('json'): {len(results)} results")
if results:
    print(f"  first: {results[0]}")

conflicts = lz.symbol.conflicts("json") or []
print(f"conflicts('json'): {len(conflicts)}")

summary = lz.symbol.conflict_summary()
print(f"conflict_summary keys: {list(summary.keys())}")

where = lz.symbol.which("json")
print(f"which('json'): {where}")

all_where = lz.symbol.which_all("json")
print(f"which_all('json'): {len(all_where)} found")

print(f"symbol.config:        {lz.symbol.config}")
print(f"symbol.index:         {lz.symbol.index}")
print(f"symbol.cache_info:     {lz.symbol.cache_info()}")


# ── 6. Cache operations ────────────────────────────────────────
section("6. Cache Operations")
print(f"cache:            {lz.cache}")
print(f"cache.dir:        {lz.cache.dir}")
print(f"cache.symbols:    {lz.cache.symbols}")
print(f"cache.files:      {lz.cache.files}")
print(f"cache.config:     {lz.cache.config}")
print(f"cache.config['max_cache_size_mb']: {lz.cache.config['max_cache_size_mb']}")
print(f"cache.config.max_size_mb:          {lz.cache.config.max_size_mb}")


# ── 7. Alias operations ────────────────────────────────────────
section("7. Alias Operations")
result = lz.alias.validate()
valid = result.get('valid', [])
print(f"alias.validate(): {len(valid)} valid")
print(f"aliases:           {lz.alias}")


# ── 8. Hooks ───────────────────────────────────────────────────
section("8. Hooks")
called = False

def my_hook(name: str) -> None:
    global called
    called = f"Hook fired for '{name}'"

lz.hooks.pre.add(my_hook)
lz.hooks.pre("pandas")
print(f"hook_called:  {called}")
lz.hooks.pre.remove(my_hook)
print(f"hooks:        {lz.hooks}")


# ── 9. Background index ────────────────────────────────────────
section("9. Background Index")
print(f"background:   {lz.background}")
lz.background.enable(True)


# ── 10. Analyze namespace ──────────────────────────────────────
section("10. Analyze Namespace")
print(f"analyze:  {lz.analyze}")
print(f"profile:  {lz.profile}")
print(f"install:  {lz.install}")
print(f"rc:       {lz.rc}")


# ── Done ───────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("  ALL DEMO SECTIONS COMPLETED SUCCESSFULLY")
print(f"{'='*60}")
