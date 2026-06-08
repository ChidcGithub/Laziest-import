"""Fetch top PyPI packages and generate missing aliases + renames."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
ALIASES_DIR = REPO_ROOT / "laziest_import" / "aliases"
MAPPINGS_DIR = REPO_ROOT / "laziest_import" / "mappings"
RENAME_FILE = MAPPINGS_DIR / "package_rename.json"

TOP_PYPI_URL = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages.json"

PIP_TO_IMPORT = {
    "scikit-learn": "sklearn",
    "scikit-image": "skimage",
    "pillow": "PIL",
    "opencv-python": "cv2",
    "opencv-contrib-python": "cv2",
    "beautifulsoup4": "bs4",
    "pyyaml": "yaml",
    "python-dotenv": "dotenv",
    "pyjwt": "jwt",
    "python-dateutil": "dateutil",
    "pycryptodome": "Crypto",
    "pyopengl": "OpenGL",
    "pymupdf": "fitz",
    "python-docx": "docx",
    "python-pptx": "pptx",
    "pywin32": "win32com",
    "kafka-python": "kafka",
    "paho-mqtt": "mqtt",
    "pyzmq": "zmq",
    "typing-extensions": "typing_extensions",
    "protobuf": "google.protobuf",
    "python-multipart": "multipart",
    "python-slugify": "slugify",
    "drf-yasg": "drf_yasg",
    "djangorestframework": "rest_framework",
    "fastapi": "fastapi",
    "pydantic": "pydantic",
    "sqlalchemy": "sqlalchemy",
    "alembic": "alembic",
    "httpx": "httpx",
    "orjson": "orjson",
    "uvicorn": "uvicorn",
    "gunicorn": "gunicorn",
    "jinja2": "jinja2",
    "aiohttp": "aiohttp",
    "aioredis": "redis.asyncio",
    "celery": "celery",
    "redis": "redis",
    "psycopg2": "psycopg2",
    "asyncpg": "asyncpg",
    "motor": "motor",
    "beanie": "beanie",
    "pendulum": "pendulum",
    "arrow": "arrow",
    "click": "click",
    "typer": "typer",
    "rich": "rich",
    "textual": "textual",
    "pytest": "pytest",
    "tox": "tox",
    "nox": "nox",
    "black": "black",
    "ruff": "ruff",
}

IMPORT_TO_PIP = {v: k for k, v in PIP_TO_IMPORT.items()}

STDLIB_MODULES = {
    "os",
    "sys",
    "json",
    "math",
    "re",
    "datetime",
    "collections",
    "itertools",
    "functools",
    "pathlib",
    "typing",
    "abc",
    "time",
    "random",
    "hashlib",
    "base64",
    "copy",
    "enum",
    "decimal",
    "fractions",
    "statistics",
    "string",
    "struct",
    "textwrap",
    "pprint",
    "reprlib",
    "logging",
    "gettext",
    "locale",
    "io",
    "fileinput",
    "filecmp",
    "tempfile",
    "glob",
    "fnmatch",
    "linecache",
    "shutil",
    "pickle",
    "shelve",
    "marshal",
    "dbm",
    "sqlite3",
    "bz2",
    "gzip",
    "lzma",
    "zipfile",
    "tarfile",
    "csv",
    "configparser",
    "netrc",
    "plistlib",
    "tomllib",
    "asyncio",
    "threading",
    "multiprocessing",
    "concurrent",
    "subprocess",
    "signal",
    "socket",
    "ssl",
    "select",
    "email",
    "json",
    "html",
    "http",
    "urllib",
    "xml",
    "webbrowser",
    "cgi",
    "warnings",
    "dataclasses",
    "inspect",
    "ast",
    "dis",
    "tokenize",
    "keyword",
    "token",
    "unittest",
    "doctest",
    "pdb",
    "profile",
    "trace",
    "argparse",
    "getopt",
    "optparse",
    "ctypes",
    "struct",
    "codecs",
    "re",
}


def pip_to_import(pkg: str) -> str:
    if pkg in PIP_TO_IMPORT:
        return PIP_TO_IMPORT[pkg]
    name = pkg.replace("-", "_").replace(".", "_")
    return name


def load_aliases() -> dict[str, str]:
    result = {}
    for f in sorted(ALIASES_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            for k, v in data.items():
                if k == "_meta" or not isinstance(v, str):
                    continue
                result[k] = v
        except (json.JSONDecodeError, OSError):
            pass
    return result


def load_renames() -> dict[str, str]:
    if not RENAME_FILE.exists():
        return {}
    try:
        data = json.loads(RENAME_FILE.read_text(encoding="utf-8"))
        renames = {}
        for cat, items in data.items():
            if cat.startswith("_"):
                continue
            if isinstance(items, dict):
                renames.update(items)
        return renames
    except (json.JSONDecodeError, OSError):
        return {}


def add_to_letter_file(aliases: dict[str, str]) -> None:
    groups: dict[str, dict[str, str]] = {}
    for alias, module in aliases.items():
        letter = alias[0].upper() if alias and alias[0].isalpha() else "_"
        groups.setdefault(letter, {})[alias] = module

    for letter, entries in groups.items():
        fpath = ALIASES_DIR / f"{letter}.json"
        existing = {}
        if fpath.exists():
            data = json.loads(fpath.read_text(encoding="utf-8"))
            existing = {k: v for k, v in data.items() if k != "_meta" and isinstance(v, str)}
        existing.update(entries)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(dict(sorted(existing.items())), f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"  ⇢ {fpath.name}: {len(existing)} aliases (+{len(entries)} new)")


def fetch_top_packages(limit: int = 300) -> list[tuple[str, float]]:
    import requests

    print(f"Fetching top {limit} PyPI packages from {TOP_PYPI_URL} ...")
    resp = requests.get(TOP_PYPI_URL, timeout=30)
    resp.raise_for_status()
    rows = resp.json().get("rows", [])
    return [(r["project"], float(r.get("download_count", 0))) for r in rows[:limit]]


def _write_sync_results(new_aliases: dict[str, str], new_renames: dict[str, str], dry_run: bool) -> None:
    if dry_run:
        print("Dry-run mode, no files modified")
        return
    if new_aliases:
        add_to_letter_file(new_aliases)
    if new_renames:
        try:
            data = json.loads(RENAME_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
        if "auto_sync" not in data:
            data["auto_sync"] = {}
        data["auto_sync"].update(new_renames)
        with open(RENAME_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"  ⇢ package_rename.json: {len(new_renames)} new mappings")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync aliases from PyPI")
    parser.add_argument("--limit", type=int, default=300, help="Number of packages")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not ALIASES_DIR.exists():
        print(f"::error::Aliases directory not found: {ALIASES_DIR}", file=sys.stderr)
        return 1

    top_pkgs = fetch_top_packages(args.limit)
    if not top_pkgs:
        print("::warning::No packages fetched, skipping")
        return 0

    existing_aliases = load_aliases()
    existing_renames = load_renames()
    existing_aliases_lower = {k.lower(): v for k, v in existing_aliases.items()}

    new_aliases: dict[str, str] = {}
    new_renames: dict[str, str] = {}

    for pkg, downloads in top_pkgs:
        import_name = pip_to_import(pkg)

        if import_name.lower() in STDLIB_MODULES:
            continue
        if import_name.lower() in existing_aliases_lower:
            continue
        if import_name.replace("_", "-") == pkg:
            continue

        if import_name != pkg.replace("-", "_"):
            if import_name not in existing_renames and import_name not in new_renames:
                new_renames[import_name] = pkg
                print(f"  [rename] '{pkg}' → '{import_name}'")
        elif import_name not in existing_aliases and import_name not in new_aliases:
            new_aliases[import_name] = import_name
            print(f"  [alias] '{import_name}' (https://pypi.org/p/{pkg})")

    print(f"\nSummary: {len(new_aliases)} new aliases, {len(new_renames)} new renames")

    if not new_aliases and not new_renames:
        return 0

    _write_sync_results(new_aliases, new_renames, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
