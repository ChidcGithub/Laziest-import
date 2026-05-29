"""Validate alias files: JSON format, duplicates, stale entries."""

import json
import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALIASES_DIR = REPO_ROOT / "laziest_import" / "aliases"
MAPPINGS_DIR = REPO_ROOT / "laziest_import" / "mappings"


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
    try:
        from laziest_import._alias import validate_aliases_importable, _load_all_aliases
    except ImportError:
        print("::warning::laziest-import not installed, skipping stale check")
        return 0

    aliases = _load_all_aliases(check_duplicates=False)
    result = validate_aliases_importable(aliases)
    stale = result.get("not_importable", {})

    if stale:
        print("::error::Stale aliases detected", file=sys.stderr)
        for alias, info in sorted(stale.items()):
            print(f"  - '{alias}' -> '{info['module']}': {info['error']}", file=sys.stderr)
        return 1
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
