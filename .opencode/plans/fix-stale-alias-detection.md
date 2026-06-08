# Fix Stale Alias Detection

## Problem
The weekly CI job `validate-aliases.yml` runs `scripts/validate_aliases.py --stale`, which calls `validate_aliases_importable()` from `_alias.py`. This function uses `importlib.util.find_spec()` to check if each alias's target module is importable. In the GitHub Actions CI environment (Ubuntu + Python 3.11), only `laziest-import` itself is installed, so ALL third-party packages (numpy, pandas, tensorflow, etc.) are flagged as "not found" — producing false positives every run.

## Solution
Modify `scripts/validate_aliases.py` to add PyPI JSON API fallback. When a module is not found locally, query `https://pypi.org/pypi/{root_package}/json` to verify the package actually exists on PyPI.

## Changes

### File: `scripts/validate_aliases.py`

**1. Add imports** (at top):
```python
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
```

**2. Add PyPI check functions** (after existing constants):
```python
_PYPI_CACHE: dict[str, bool | None] = {}

def _get_root_package(module_name: str) -> str:
    return module_name.split(".")[0]

def _check_single_pypi_package(root: str) -> bool | None:
    if root in _PYPI_CACHE:
        return _PYPI_CACHE[root]
    url = f"https://pypi.org/pypi/{root}/json"
    req = urllib.request.Request(url, headers={"User-Agent": "laziest-import-validator/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            exists = resp.status == 200
    except urllib.error.HTTPError as e:
        exists = e.code != 404
    except Exception:
        exists = False
    _PYPI_CACHE[root] = exists
    time.sleep(0.05)
    return exists

def _check_pypi_batch(module_names: set[str]) -> dict[str, bool | None]:
    roots = {_get_root_package(m) for m in module_names}
    remaining = [r for r in roots if r not in _PYPI_CACHE]
    if not remaining:
        return {m: _PYPI_CACHE.get(_get_root_package(m)) for m in module_names}

    with ThreadPoolExecutor(max_workers=5) as pool:
        fut = {pool.submit(_check_single_pypi_package, r): r for r in remaining}
        for f in as_completed(fut):
            try:
                f.result()
            except Exception:
                pass

    return {m: _PYPI_CACHE.get(_get_root_package(m)) for m in module_names}
```

**3. Modify `check_stale()`** (replace existing function):
```python
def check_stale() -> int:
    """Check if aliases point to importable modules."""
    try:
        from laziest_import._alias import validate_aliases_importable, _load_all_aliases
    except ImportError:
        print("::warning::laziest-import not installed, skipping stale check")
        return 0

    aliases = _load_all_aliases(check_duplicates=False)
    result = validate_aliases_importable(aliases)
    stale = result.get("not_importable", {})

    if stale:
        module_names = {info["module"] for info in stale.values()}
        print(f"[INFO] Checking {len(module_names)} unique modules against PyPI...")
        pypi_results = _check_pypi_batch(module_names)

        truly_stale = {}
        not_installed = {}
        for alias, info in sorted(stale.items()):
            module = info["module"]
            pypi_status = pypi_results.get(module)
            if pypi_status is False:
                truly_stale[alias] = info
            else:
                not_installed[alias] = info

        if truly_stale:
            print("::error::Stale aliases detected (not found on PyPI)", file=sys.stderr)
            for alias, info in sorted(truly_stale.items()):
                print(f"  - '{alias}' -> '{info['module']}': {info['error']}", file=sys.stderr)
            if not_installed:
                print(f"[INFO] {len(not_installed)} aliases skipped (valid package, just not installed)")
            return 1

        if not_installed:
            print(f"[OK] No stale aliases ({len(not_installed)} packages valid on PyPI but not installed locally)")
        return 0

    print(f"[OK] All {len(result.get('importable', {}))} aliases importable")
    return 0
```

## Verification
After applying changes, run:
```
python scripts/validate_aliases.py --stale
```

Expected: Most aliases should be reported as "valid on PyPI but not installed locally" rather than "stale". Exit code 0.
