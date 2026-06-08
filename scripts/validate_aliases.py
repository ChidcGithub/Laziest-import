"""Validate alias files: JSON format, duplicates, stale entries."""

import argparse
import contextlib
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALIASES_DIR = REPO_ROOT / "laziest_import" / "aliases"
MAPPINGS_DIR = REPO_ROOT / "laziest_import" / "mappings"

_HTTP_OK = 200
_HTTP_NOT_FOUND = 404

_PYPI_CACHE: dict[str, bool | None] = {}
_IMPORT_TO_PIP: dict[str, str] = {}


def _load_package_rename_map() -> dict[str, str]:
    mapping = {}
    rename_file = MAPPINGS_DIR / "package_rename.json"
    if not rename_file.exists():
        return mapping
    data = json.loads(rename_file.read_text(encoding="utf-8"))
    for category in data.values():
        if isinstance(category, dict):
            for import_name, pip_name in category.items():
                if isinstance(import_name, str) and isinstance(pip_name, str):
                    mapping[import_name] = pip_name
    return mapping


def _get_root_package(module_name: str) -> str:
    return module_name.split(".", maxsplit=1)[0]


def _check_single_pypi_package(name: str) -> bool | None:
    if name in _PYPI_CACHE:
        return _PYPI_CACHE[name]
    url = f"https://pypi.org/pypi/{name}/json"
    req = urllib.request.Request(url, headers={"User-Agent": "laziest-import-validator/2.0"})  # noqa: S310 — validated PyPI HTTPS URL
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 — validated PyPI HTTPS URL
            exists = resp.status == _HTTP_OK
    except urllib.error.HTTPError as e:
        exists = e.code != _HTTP_NOT_FOUND
    except Exception:
        exists = False
    _PYPI_CACHE[name] = exists
    time.sleep(0.05)
    return exists


def _get_pypi_candidates(module_name: str) -> list[str]:
    candidates = []
    root = _get_root_package(module_name)

    # 1) the full module name as-is
    if module_name not in candidates:
        candidates.append(module_name)

    # 2) the root package (for submodules)
    if root != module_name and root not in candidates:
        candidates.append(root)

    # 3) pip install name for the full module name
    pip_name = _IMPORT_TO_PIP.get(module_name)
    if pip_name and pip_name not in candidates:
        candidates.append(pip_name)

    # 4) pip install name for the root
    pip_name_root = _IMPORT_TO_PIP.get(root)
    if pip_name_root and pip_name_root not in candidates:
        candidates.append(pip_name_root)

    # 5) try the module name with dots replaced by hyphens (PEP 503)
    normalised = module_name.replace(".", "-")
    if normalised not in candidates:
        candidates.append(normalised)

    # 6) try root with dots replaced by hyphens (for submodules like "ruamel.yaml")
    if root != module_name:
        normalised_root = root.replace(".", "-")
        if normalised_root not in candidates:
            candidates.append(normalised_root)

    return candidates


def _build_pypi_candidates(
    module_names: set[str], alias_map: dict[str, str] | None = None
) -> tuple[set[str], dict[str, list[str]]]:
    all_candidates: set[str] = set()
    module_to_aliases: dict[str, list[str]] = {}
    for m in module_names:
        all_candidates.update(_get_pypi_candidates(m))
        module_to_aliases.setdefault(m, [])
    if alias_map:
        for alias, module in alias_map.items():
            if module in module_names:
                module_to_aliases[module].append(alias)
                if alias not in all_candidates:
                    all_candidates.add(alias)
    return all_candidates, module_to_aliases


def _batch_check_remaining(remaining: list[str]) -> None:
    if not remaining:
        return
    with ThreadPoolExecutor(max_workers=5) as pool:
        futs = {pool.submit(_check_single_pypi_package, c): c for c in remaining}
        for f in as_completed(futs):
            with contextlib.suppress(Exception):
                f.result()


def _build_pypi_results(
    module_names: set[str], module_to_aliases: dict[str, list[str]]
) -> dict[str, bool | None]:
    result: dict[str, bool | None] = {}
    for m in module_names:
        for candidate in _get_pypi_candidates(m):
            status = _PYPI_CACHE.get(candidate)
            if status is True:
                result[m] = True
                break
            if status is None:
                result[m] = None
        else:
            for alias in module_to_aliases.get(m, []):
                status = _PYPI_CACHE.get(alias)
                if status is True:
                    result[m] = True
                    break
                if status is None:
                    result[m] = None
            else:
                result[m] = False
    return result


def _check_pypi_batch(module_names: set[str], alias_map: dict[str, str] | None = None) -> dict[str, bool | None]:
    all_candidates, module_to_aliases = _build_pypi_candidates(module_names, alias_map)
    remaining = [c for c in all_candidates if c not in _PYPI_CACHE]
    _batch_check_remaining(remaining)
    return _build_pypi_results(module_names, module_to_aliases)


def validate_json() -> int:
    errors = []
    for f in sorted(ALIASES_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                errors.append(f"{f.name}: top-level is not dict")
            for k, v in data.items():
                if k == "_meta":
                    continue
                if not isinstance(v, str):
                    errors.append(f"{f.name}: '{k}' value is not string")
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: {e}")

    for f in sorted(MAPPINGS_DIR.glob("*.json")):
        try:
            json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: {e}")

    if errors:
        print("::error::JSON validation failed", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    alias_count = len(list(ALIASES_DIR.glob("*.json")))
    map_count = len(list(MAPPINGS_DIR.glob("*.json")))
    print(f"[OK] All JSON files valid ({alias_count} alias, {map_count} mapping)")
    return 0


def check_duplicates() -> int:
    all_aliases: dict[str, str] = {}
    errors = []

    for f in sorted(ALIASES_DIR.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for k, v in data.items():
            if k == "_meta" or not isinstance(v, str):
                continue
            if k in all_aliases and all_aliases[k] != v:
                errors.append(f"'{k}': '{all_aliases[k]}' vs '{v}' (in {f.name})")
            all_aliases[k] = v

    if errors:
        print("::error::Duplicate aliases found", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"[OK] No duplicates ({len(all_aliases)} unique aliases)")
    return 0


def check_stale() -> int:
    """Check if aliases point to importable modules."""
    _IMPORT_TO_PIP.update(_load_package_rename_map())

    try:
        from laziest_import._alias import (
            _load_all_aliases,
            validate_aliases_importable,
        )
    except ImportError:
        print("::warning::laziest-import not installed, skipping stale check")
        return 0

    aliases = _load_all_aliases(check_duplicates=False)
    result = validate_aliases_importable(aliases)
    stale = result.get("not_importable", {})

    if stale:
        module_names = {info["module"] for info in stale.values()}
        stale_alias_map = {alias: info["module"] for alias, info in stale.items()}
        print(f"[INFO] Checking {len(module_names)} unique modules against PyPI...")
        pypi_results = _check_pypi_batch(module_names, stale_alias_map)

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
                print(f"[INFO] {len(not_installed)} aliases skipped (valid on PyPI, just not installed)")
            return 1

        if not_installed:
            print(f"[OK] No stale aliases ({len(not_installed)} valid on PyPI but not installed locally)")
        return 0

    print(f"[OK] All {len(result.get('importable', {}))} aliases importable")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stale", action="store_true", help="Check stale aliases")
    args = parser.parse_args()

    if args.stale:
        return check_stale()

    rc = validate_json()
    if rc:
        return rc
    return check_duplicates()


if __name__ == "__main__":
    sys.exit(main())
