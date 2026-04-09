"""
Interactive help system for laziest-import.
"""

from typing import Optional, Dict, Any, List, Tuple
import inspect
import importlib
import sys
import locale

from ._which import which, which_all, SymbolLocation
from ._config import _SYMBOL_CACHE, _ALIAS_MAP


def _supports_unicode() -> bool:
    """Check if the terminal supports Unicode characters."""
    try:
        # Check if stdout supports unicode
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
            encoding = sys.stdout.encoding.lower()
            if encoding in ('utf-8', 'utf8', 'utf-16', 'utf16', 'utf-32', 'utf32'):
                return True
        
        # Check locale
        preferred_encoding = locale.getpreferredencoding()
        if preferred_encoding and preferred_encoding.lower() in ('utf-8', 'utf8'):
            return True
        
        # Windows with proper code page
        if sys.platform == 'win32':
            try:
                import ctypes
                code_page = ctypes.windll.kernel32.GetConsoleOutputCP()
                if code_page == 65001:  # UTF-8 code page
                    return True
            except Exception:
                pass
        
        return False
    except Exception:
        return False


# Box drawing characters (Unicode and ASCII fallback)
if _supports_unicode():
    _BOX_TOP_LEFT = "╔"
    _BOX_TOP_RIGHT = "╗"
    _BOX_BOTTOM_LEFT = "╚"
    _BOX_BOTTOM_RIGHT = "╝"
    _BOX_HORIZONTAL = "═"
    _BOX_VERTICAL = "║"
else:
    _BOX_TOP_LEFT = "+"
    _BOX_TOP_RIGHT = "+"
    _BOX_BOTTOM_LEFT = "+"
    _BOX_BOTTOM_RIGHT = "+"
    _BOX_HORIZONTAL = "-"
    _BOX_VERTICAL = "|"


class HelpTopic:
    """Represents a help topic."""

    def __init__(
        self,
        name: str,
        description: str,
        examples: Optional[List[str]] = None,
        related: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.examples = examples or []
        self.related = related or []
        self.details = details or {}

    def __str__(self) -> str:
        lines = [
            f"{_BOX_TOP_LEFT}{_BOX_HORIZONTAL * 58}{_BOX_TOP_RIGHT}",
            f"{_BOX_VERTICAL} {self.name:<56} {_BOX_VERTICAL}",
            f"{_BOX_BOTTOM_LEFT}{_BOX_HORIZONTAL * 58}{_BOX_BOTTOM_RIGHT}",
            "",
            self.description,
            "",
        ]

        if self.examples:
            lines.append("Examples:")
            for ex in self.examples:
                lines.append(f"  {ex}")
            lines.append("")

        if self.details:
            lines.append("Details:")
            for key, value in self.details.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        if self.related:
            lines.append(f"Related: {', '.join(self.related)}")

        return "\n".join(lines)


_TOPICS: Dict[str, HelpTopic] = {}


def _register_default_topics() -> None:
    """Register default help topics."""
    global _TOPICS

    _TOPICS = {
        "quickstart": HelpTopic(
            name="Quick Start",
            description="Get started with laziest-import in 30 seconds.",
            examples=[
                "from laziest_import import *",
                "arr = np.array([1, 2, 3])  # No import needed!",
                "df = pd.DataFrame({'a': [1, 2]})",
            ],
            related=["lazy", "alias", "config"],
        ),
        "lazy": HelpTopic(
            name="How Lazy Imports Work",
            description=(
                "Laziest-import provides lazy loading for Python modules. "
                "Modules are only imported when you first access them, "
                "reducing startup time and memory usage."
            ),
            examples=[
                "import laziest_import as lz",
                "lz.math  # math is imported here",
                "lz.math.sqrt(4)  # sqrt() runs now",
            ],
            related=["quickstart", "symbol", "cache"],
        ),
        "alias": HelpTopic(
            name="Alias System",
            description=(
                "Aliases map short names to module paths. "
                "np → numpy, pd → pandas, plt → matplotlib.pyplot"
            ),
            examples=[
                "lz.register_alias('np', 'numpy')",
                "lz.list_available()  # See all aliases",
                "lz.unregister_alias('np')",
            ],
            related=["quickstart", "config"],
        ),
        "symbol": HelpTopic(
            name="Symbol Search",
            description=(
                "Search for classes, functions, and constants across all modules. "
                "Automatically resolves symbol names to their defining modules."
            ),
            examples=[
                "lz.search_symbol('DataFrame')",
                "lz.which('sqrt')",
                "lz.search_symbol('array', symbol_type='class')",
            ],
            related=["which", "cache"],
        ),
        "cache": HelpTopic(
            name="Caching System",
            description=(
                "Laziest-import caches imported modules and symbol indices "
                "for fast subsequent access. Cache is persistent across sessions."
            ),
            examples=[
                "lz.clear_cache()  # Clear module cache",
                "lz.clear_symbol_cache()  # Clear symbol index",
                "lz.get_cache_stats()  # View cache stats",
            ],
            related=["lazy", "config"],
        ),
        "config": HelpTopic(
            name="Configuration",
            description=(
                "Configure laziest-import behavior through code or config files. "
                "Supports ~/.laziestrc, environment variables, and programmatic API."
            ),
            examples=[
                "lz.enable_debug_mode()",
                "lz.enable_auto_install(interactive=True)",
                "lz.set_cache_config(symbol_index_ttl=86400)",
            ],
            related=["alias", "rcfile"],
        ),
        "rcfile": HelpTopic(
            name="Configuration File (.laziestrc)",
            description=(
                "Create ~/.laziestrc to persist your configuration. "
                "Supports JSON format with aliases, settings, and preferences."
            ),
            examples=[
                "from laziest_import import create_rc_file",
                "create_rc_file()  # Creates ~/.laziestrc",
                "# Then edit it with your preferences",
            ],
            related=["config"],
        ),
        "async": HelpTopic(
            name="Async Imports",
            description=(
                "Import modules asynchronously without blocking. "
                "Useful for preloading modules in background tasks."
            ),
            examples=[
                "await lz.import_async('numpy')",
                "modules = await lz.import_multiple_async(['numpy', 'pandas'])",
            ],
            related=["lazy", "hooks"],
        ),
        "hooks": HelpTopic(
            name="Import Hooks",
            description=(
                "Register callbacks to be called before/after module imports. "
                "Useful for logging, monitoring, or custom import behavior."
            ),
            examples=[
                "def my_hook(name, module): print(f'Imported {name}')",
                "lz.add_post_import_hook(my_hook)",
                "lz.remove_post_import_hook(my_hook)",
            ],
            related=["lazy", "async"],
        ),
        "api": HelpTopic(
            name="API Reference",
            description="Complete list of public API functions.",
            examples=[
                "import laziest_import as lz",
                "# See all functions: dir(lz)",
            ],
            related=["lazy", "config"],
        ),
        "jupyter": HelpTopic(
            name="Jupyter/IPython",
            description="Use laziest-import in Jupyter notebooks.",
            examples=[
                "%load_ext laziest_import",
                "%%lazy -m numpy",
                "%lazyimport numpy pandas",
                "%lazylist  # See available modules",
            ],
            related=["quickstart", "magic"],
        ),
        "magic": HelpTopic(
            name="Magic Commands",
            description="IPython/Jupyter magic commands for lazy importing.",
            examples=[
                "%lazyimport numpy pandas  # Lazy import in current session",
                "%lazylist  # List available modules",
                "%lazysearch sqrt  # Search for symbols",
                "%%lazy -m torch  # Lazy import in cell",
            ],
            related=["jupyter"],
        ),
        "which": HelpTopic(
            name="which() Function",
            description="Find where a symbol is defined (like Unix which).",
            examples=[
                "lz.which('array')  # Find numpy array",
                "lz.which('DataFrame', 'pandas')  # In specific module",
                "lz.which_all('sqrt')  # All locations",
            ],
            related=["symbol"],
        ),
        "tips": HelpTopic(
            name="Pro Tips",
            description="Tips for using laziest-import effectively.",
            examples=[
                "# 1. Use abbreviations (np, pd, plt) for faster typing",
                "# 2. Enable debug mode during development",
                "# 3. Use symbol search to discover APIs",
                "# 4. Customize priorities for your workflow",
            ],
            related=["quickstart", "config"],
        ),
    }


def help(topic: Optional[str] = None) -> str:
    """
    Get help on laziest-import topics.

    Args:
        topic: Topic name. Available topics:
            - None/empty: Show overview
            - "quickstart": Quick start guide
            - "lazy": How lazy imports work
            - "alias": Alias system
            - "symbol": Symbol search
            - "cache": Caching system
            - "config": Configuration
            - "rcfile": Config file (.laziestrc)
            - "async": Async imports
            - "hooks": Import hooks
            - "api": API reference
            - "jupyter": Jupyter/IPython usage
            - "magic": Magic commands
            - "which": which() function
            - "tips": Pro tips

    Returns:
        Help text string

    Example:
        >>> help()
        >>> help("quickstart")
        >>> help("which")
    """
    if not _TOPICS:
        _register_default_topics()

    if topic is None or topic == "":
        return _get_overview()

    topic = topic.lower().strip()

    if topic in _TOPICS:
        return str(_TOPICS[topic])

    # Try partial match
    matches = [k for k in _TOPICS.keys() if topic in k]
    if matches:
        suggestions = ", ".join(matches)
        return f"Topic '{topic}' not found. Did you mean: {suggestions}\n\n{_get_overview()}"

    return f"Topic '{topic}' not found.\n\n{_get_overview()}"


def _get_overview() -> str:
    """Get overview help text."""
    if not _TOPICS:
        _register_default_topics()

    topics_list = "\n".join(
        f"  {name:<12} {topic.description.split('.')[0]}"
        for name, topic in _TOPICS.items()
    )

    return f"""{_BOX_TOP_LEFT}{_BOX_HORIZONTAL * 58}{_BOX_TOP_RIGHT}
{_BOX_VERTICAL} laziest-import: Lazy Import Library{" " * 26}{_BOX_VERTICAL}
{_BOX_BOTTOM_LEFT}{_BOX_HORIZONTAL * 58}{_BOX_BOTTOM_RIGHT}

Quick Start:
  from laziest_import import *
  arr = np.array([1, 2, 3])  # No import needed!

Available Topics:
{topics_list}

Type help("topic_name") for details.
Example: help("quickstart")
"""


def get_symbol_help(symbol_name: str) -> str:
    """
    Get detailed help for a specific symbol.

    Args:
        symbol_name: Name of the symbol (class, function, etc.)

    Returns:
        Formatted help string
    """
    locations = which_all(symbol_name)

    if not locations:
        return f"No symbol found for '{symbol_name}'. Try lz.search_symbol('{symbol_name}')"

    lines = [
        f"╔{'═' * 58}╗",
        f"║ Help: {symbol_name:<50} ║",
        f"╚{'═' * 58}╝",
        "",
    ]

    for i, loc in enumerate(locations, 1):
        lines.append(f"[{i}] {loc.module_name}.{loc.symbol_name}")
        lines.append(f"    Type: {loc.symbol_type}")

        if loc.signature:
            lines.append(f"    Signature: {loc.symbol_name}{loc.signature}")

        if loc.file_path:
            lines.append(f"    Location: {loc.file_path}", end="")
            if loc.line_number:
                lines[-1] += f":{loc.line_number}"
            lines.append()

        if loc.doc:
            doc_lines = loc.doc.split("\n")[:5]
            lines.append(f"    Doc: {doc_lines[0]}")
            if len(doc_lines) > 1:
                lines.append(
                    f"         {' '.join(d.strip() for d in doc_lines[1:3])}..."
                )

        lines.append("")

    if len(locations) > 1:
        lines.append(
            f"Found in {len(locations)} location(s). Use lz.which('{symbol_name}', '<module>') for specific module."
        )

    return "\n".join(lines)


def add_topic(name: str, topic: HelpTopic) -> None:
    """Add a custom help topic."""
    if not _TOPICS:
        _register_default_topics()
    _TOPICS[name.lower()] = topic


def list_topics() -> List[str]:
    """List all available help topics."""
    if not _TOPICS:
        _register_default_topics()
    return sorted(_TOPICS.keys())


# Register default topics on module load
_register_default_topics()
