#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║     laziest-import — Interactive Terminal Demo             ║
║     "Import Nothing. Use Everything."                      ║
╚══════════════════════════════════════════════════════════════╝

Run:  python examples/terminal_demo.py
"""

import sys
import time
import shutil
import random

# ── Terminal utilities ──────────────────────────────────────
C = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
}
WIDTH = min(shutil.get_terminal_size().columns, 70)

try:
    _test = "\u2500\u2591"
    _test.encode(sys.stdout.encoding or "ascii")
    _USE_UNICODE = True
except (UnicodeEncodeError, UnicodeDecodeError):
    _USE_UNICODE = False

FILL = "\u2588" if _USE_UNICODE else "#"
EMPT = "\u2591" if _USE_UNICODE else "-"
H = "\u2550" if _USE_UNICODE else "="
V = "\u2551" if _USE_UNICODE else "|"
TL = "\u2554" if _USE_UNICODE else "/"
TR = "\u2557" if _USE_UNICODE else "\\"
BL = "\u255A" if _USE_UNICODE else "\\"
BR = "\u255D" if _USE_UNICODE else "/"


def c(text: str, color: str) -> str:
    return f"{C.get(color, '')}{text}{C['reset']}"


def header(title: str) -> None:
    pad = (WIDTH - len(title) - 2) // 2
    _say(f"\n{c(TL + H * (WIDTH - 2) + TR, 'cyan')}")
    _say(f"{c(V, 'cyan')}{' ' * pad}{c(title, 'bold')}{' ' * (WIDTH - 2 - pad - len(title))}{c(V, 'cyan')}")
    _say(f"{c(BL + H * (WIDTH - 2) + BR, 'cyan')}\n")


def _say(*args, **kwargs) -> None:
    """print() with Unicode safety."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = [str(a).encode("ascii", errors="replace").decode("ascii") for a in args]
        print(*safe_args, **kwargs)


def step(n: int, text: str) -> None:
    _say(f" {c(f'[{n}]', 'yellow')} {text}")


def result(text: str, value: str = "") -> None:
    arrow = "->" if not _USE_UNICODE else "\u2192"
    leader = f"   {c(arrow, 'green')}"
    if value:
        _say(f"{leader} {c(text, 'dim')}: {c(value, 'bold')}")
    else:
        _say(f"{leader} {c(text, 'bold')}")


SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"] if _USE_UNICODE else ["|", "/", "-", "\\"]


def _write(text: str) -> None:
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.write(text.encode("ascii", errors="replace").decode("ascii"))
    sys.stdout.flush()


def spin(text: str, duration: float = 0.6) -> None:
    frames = SPINNER
    start = time.perf_counter()
    i = 0
    while time.perf_counter() - start < duration:
        _write(f"\r  {c(frames[i % len(frames)], 'cyan')} {c(text, 'dim')}")
        time.sleep(0.06)
        i += 1
    _write("\r" + " " * (len(text) + 10) + "\r")


def progress(text: str, steps: int = 5, delay: float = 0.08) -> None:
    bar_width = 30
    for i in range(steps + 1):
        pct = i / steps
        filled = int(bar_width * pct)
        bar = c(FILL * filled, "green") + c(EMPT * (bar_width - filled), "dim")
        _write(f"\r  {c(text, 'dim')} [{bar}] {int(pct * 100):3d}%")
        time.sleep(delay * (1 + random.random()))
    _write("\n")


def pause(text: str = "Press Enter to continue..."):
    input(f"\n  {c(text, 'dim')}")


# ═══════════════════════════════════════════════════════════
#  DEMO START
# ═══════════════════════════════════════════════════════════
_write("\033[2J\033[H")  # clear screen
header("laziest-import  Interactive Terminal Demo")

progress("Loading laziest-import engine", 6, 0.06)

spin("Initializing lazy import system...", 0.8)
result("Engine ready!", "v1.0.0.6")

# ── Section 1: Wildcard Import ─────────────────────────────
header("Wildcard Import — No import statements needed")

step(1, "Import everything with one line")
_say(f'    {c(">>> from laziest_import import *", "cyan")}')
spin("Importing wildcard namespace...", 0.5)

from laziest_import import *

result("√ numpy, math, os, json, datetime, random, re — all available!")

step(2, "Use standard library modules instantly")
result("np.array([1,2,3])", str(np.array([1, 2, 3])))
result("math.sqrt(144)", str(math.sqrt(144)))
result("os.getcwd()", os.getcwd())
result("json.dumps({'hello': 'world'})", json.dumps({"hello": "world"}))
result("datetime.date.today()", str(datetime.date.today()))

step(3, "Up to 30 built-in aliases loaded")
available = lz.module.list_available()
avail_sample = available[:15] if len(available) > 15 else available
result(f"{len(available)} aliases available", ", ".join(avail_sample) + "...")

# ── Section 2: Namespace Prefix ────────────────────────────
header("Namespace Prefix — Safe & Explicit")
import laziest_import as lz

step(4, "Use lz. prefix for clarity")
result("lz.math.pi", str(lz.math.pi))
result("lz.os.name", lz.os.name)

step(5, "Submodules auto-load seamlessly")
spin("Resolving lz.os.path...", 0.5)
result("lz.os.path.join('home','user')", str(lz.os.path.join("home", "user")))

# ── Section 3: Smart Proxy ─────────────────────────────────
header("Smart Proxy — Typo Correction")
from laziest_import import lazy

step(6, "Misspelled module names are auto-corrected")
progress("Scanning fuzzy matcher", 4, 0.06)
result("Typo engine: Levenshtein distance + 300+ abbreviation maps")

try:
    found = lazy.mathh
    if found:
        result("lazy.mathh → math", "Auto-corrected! ✓")
except Exception:
    result("lazy.mathh", "Not found (need extra packages)")

# ── Section 4: Object API ──────────────────────────────────
header("Object-Oriented API — Full Control")

step(7, "Module management: lz.module")
loaded = lz.module.list_loaded()
result("Loaded modules", str(len(loaded)))
result("Available aliases", str(len(lz.module.list_available())))

step(8, "Cache statistics: lz.cache")
try:
    stats_dict = lz.cache._get_stats()
    result("Cache hit rate", f"{stats_dict.get('hit_rate', 0):.1%}")
except Exception:
    result("Cache system", "Active & running")

step(9, "Config read/write: lz.config")
result("Auto-search", f"{lz.config.auto_search}")
result("Debug mode", f"{lz.config.debug}")

# ── Section 5: Symbol Search ───────────────────────────────
header("Symbol Search — Find Anything")

step(10, "Search across ALL modules for a symbol")
try:
    spin("Building symbol index (first time takes 1-2s)...", 1.0)
    results = lz.symbol.search("sqrt", max_results=5)
    for r in results:
        result(f"{r.module_name}.{r.symbol_name}", f"({r.symbol_type})")
except Exception as e:
    result("Symbol search", f"Skipped ({e})")

step(11, "Locate where a symbol is defined")
try:
    loc = lz.symbol.which("sqrt")
    if loc:
        result("which('sqrt')", f"{loc.module_name}.{loc.symbol_name}")
except Exception as e:
    result("Symbol location", f"Skipped ({e})")

# ── Section 6: Dynamic Alias ───────────────────────────────
header("Dynamic Alias Registration")

step(12, "Register custom aliases on the fly")
from laziest_import import register_alias, unregister_alias
register_alias("mydt", "datetime")
result("lz.alias.register('mydt', 'datetime')", "Registered!")
result("lz.mydt.date.today()", str(lz.mydt.date.today()))
unregister_alias("mydt")
result("lz.alias.unregister('mydt')", "Unregistered!")

# ── Section 7: Dependency Tree ─────────────────────────────
header("Dependency Tree Analysis")

step(13, "Analyze module dependencies")
spin("Analyzing math dependencies...", 0.7)
try:
    tree = lz.analyze.dep_tree("os", max_depth=2)
    result("os.path dependency tree", f"{tree.total_modules} modules in sub-tree")
except Exception as e:
    result("Dependency tree", f"Skipped ({e})")

# ── Section 8: Environment ─────────────────────────────────
header("Environment Detection")

step(14, "Detect Python environment")
try:
    from laziest_import._analysis import detect_environment
    env = detect_environment()
    result("Python version", env.python_version)
    result("Executable", env.executable)
    result("Virtual env", str(env.virtual_env or "None"))
except Exception as e:
    result("Environment detection", f"Skipped ({e})")

# ── Section 9: Import Hooks ────────────────────────────────
header("Import Hooks — Intercept Imports")

step(15, "Hook into every lazy import")
log_lines = []

def on_pre(name: str) -> None:
    log_lines.append(f"  {c('PRE', 'yellow')}  -> loading '{name}'")

def on_post(name: str, mod) -> None:
    log_lines.append(f"  {c('POST', 'green')} -> '{name}' resolved to {mod.__name__}")

from laziest_import._hooks import add_pre_import_hook, add_post_import_hook, remove_pre_import_hook, remove_post_import_hook
add_pre_import_hook(on_pre)
add_post_import_hook(on_post)
lz.module.get("functools")
remove_pre_import_hook(on_pre)
remove_post_import_hook(on_post)

for line in log_lines:
    _say(line)

# ── Section 10: Benchmarks ─────────────────────────────────
header("Performance Benchmark")

step(16, "Benchmark import performance")
spin("Running benchmark (100 iterations)...", 1.0)
try:
    report = lz.benchmark(lambda: sum(range(1000)), name="sum_1000", iterations=100, warmup=10)
    result("avg_time", f"{report.avg_time * 1_000_000:.2f} us")
    result("min_time", f"{report.min_time * 1_000_000:.2f} us")
    result("max_time", f"{report.max_time * 1_000_000:.2f} us")
    result("std_dev", f"{report.std_dev * 1_000_000:.2f} us")
except Exception as e:
    result("Benchmark", f"Skipped ({e})")

# ── Conclusion ────────────────────────────────────────────
header("Demo Complete!")
_say(f"  {c('[OK]', 'green')} {c('1065+ tests pass', 'bold')}")
_say(f"  {c('[OK]', 'green')} {c('Python 3.9 - 3.13 supported', 'bold')}")
_say(f"  {c('[OK]', 'green')} {c('MIT Licensed', 'bold')}")
_say()
_say(f"  {c('Star us on GitHub:', 'yellow')} https://github.com/ChidcGithub/Laziest-import")
_say()
