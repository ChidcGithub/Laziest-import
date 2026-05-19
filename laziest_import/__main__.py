"""
CLI entry point for laziest-import.

Usage:
    python -m laziest_import freeze [--output FILE] [paths...]
    python -m laziest_import init    [--output FILE]
"""

import sys
import json
import ast
import os
from pathlib import Path
from typing import Dict, Set, List, Optional


def main() -> None:
    import laziest_import
    laziest_import  # ensure initialized

    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    command = sys.argv[1]

    if command == "freeze":
        _cmd_freeze()
    elif command == "init":
        _cmd_init()
    else:
        print(f"Unknown command: {command}")
        print(__doc__.strip())
        sys.exit(1)


def _resolve_aliases() -> Dict[str, str]:
    from laziest_import._config import _ALIAS_MAP
    return dict(_ALIAS_MAP)


def _scan_file_for_aliases(filepath: Path, aliases: Dict[str, str]) -> Dict[str, str]:
    """Scan a single Python file for alias usage and return alias -> module mapping."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except (OSError, IOError):
        return {}

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return {}

    found: Dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            alias = node.value.id
            if alias in aliases and alias not in found:
                found[alias] = aliases[alias]

    return found


def _scan_path_for_aliases(
    paths: List[str], aliases: Dict[str, str]
) -> Dict[str, Set[str]]:
    """Scan paths for alias usage, return alias -> set of files using it."""
    result: Dict[str, Set[str]] = {}

    for path_str in paths:
        p = Path(path_str)
        if p.is_file() and p.suffix == ".py":
            used = _scan_file_for_aliases(p, aliases)
            for alias, module in used.items():
                if alias not in result:
                    result[alias] = set()
                result[alias].add(str(p))
        elif p.is_dir():
            for py_file in p.rglob("*.py"):
                used = _scan_file_for_aliases(py_file, aliases)
                for alias, module in used.items():
                    if alias not in result:
                        result[alias] = set()
                    result[alias].add(str(py_file))

    return result


def _cmd_freeze() -> None:
    args = sys.argv[2:]
    output = "imports.laziest.json"
    paths: List[str] = []

    i = 0
    while i < len(args):
        if args[i] in ("-o", "--output") and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i].startswith("--output="):
            output = args[i].split("=", 1)[1]
            i += 1
        else:
            paths.append(args[i])
            i += 1

    if not paths:
        paths.append(".")

    aliases = _resolve_aliases()
    if not aliases:
        print("[laziest-import freeze] No aliases found. Is laziest-import initialized?")
        sys.exit(1)

    usage = _scan_path_for_aliases(paths, aliases)

    used_aliases: Dict[str, str] = {}
    for alias in sorted(usage):
        used_aliases[alias] = aliases[alias]

    report = {
        "version": "1.0",
        "generated_by": "laziest-import freeze",
        "paths_scanned": [str(Path(p).resolve()) for p in paths],
        "files_scanned": len({
            f for files in usage.values() for f in files
        }),
        "alias_count": len(used_aliases),
        "aliases": used_aliases,
        "files": {
            alias: sorted(files)
            for alias, files in sorted(usage.items())
        },
    }

    with open(output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[laziest-import freeze] Generated {output}")
    print(f"  Aliases found: {report['alias_count']}")
    print(f"  Files scanned: {report['files_scanned']}")


def _cmd_init() -> None:
    args = sys.argv[2:]
    output: Optional[str] = None

    i = 0
    while i < len(args):
        if args[i] in ("-o", "--output") and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i].startswith("--output="):
            output = args[i].split("=", 1)[1]
            i += 1
        else:
            output = args[i]
            i += 1

    from laziest_import._rcconfig import create_rc_file, _get_default_config_template

    if output:
        target = Path(output)
    else:
        target = Path.home() / ".laziestrc"

    if target.exists():
        print(f"[laziest-import init] File already exists: {target}")
        sys.exit(1)

    config = _get_default_config_template()
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    print(f"[laziest-import init] Created {target}")


if __name__ == "__main__":
    main()
