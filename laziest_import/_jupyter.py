"""
Jupyter/IPython magic commands for laziest-import.
"""

from typing import Optional, List, Any
import sys

_IPYTHON_AVAILABLE = False


def _create_lazy_magics():
    """Create LazyMagics class if IPython is available."""
    try:
        from IPython.core.magic import magics_class, cell_magic, line_magic, Magics
        from IPython.core.magic_arguments import (
            argument,
            magic_arguments,
            parse_argstring,
        )
        from IPython import get_ipython

        global _IPYTHON_AVAILABLE
        _IPYTHON_AVAILABLE = True

        LAZY_MAGIC_COMMANDS = [
            "np",
            "pd",
            "plt",
            "tf",
            "torch",
            "os",
            "sys",
            "json",
            "re",
            "math",
            "random",
            "datetime",
            "pathlib",
        ]

        @magics_class
        class LazyMagics(Magics):
            """IPython magic commands for lazy importing."""

            def __init__(self, shell: Optional[Any] = None) -> None:
                super().__init__(shell)
                self._lazy_modules: List[str] = []

            @cell_magic
            @magic_arguments()
            @argument("-m", "--module", action="append", help="Modules to import")
            @argument("-q", "--quiet", action="store_true", help="Suppress output")
            def lazy(self, line: str, cell: str) -> None:
                """
                %%lazy - Execute cell with lazy imports enabled.

                Usage:
                    %%lazy -m numpy -m pandas
                    %%lazy -m np -m pd --quiet
                    %%lazy
                """
                args = parse_argstring(self.lazy, line)

                modules = args.module or []
                quiet = args.quiet

                import laziest_import as lz

                # Get IPython shell's user namespace as base
                shell = get_ipython()
                cell_locals = dict(shell.user_ns) if shell else {}

                # Import modules lazily into the local namespace
                for module in modules:
                    if module in lz.list_available():
                        cell_locals[module] = getattr(lz, module)
                    elif "." in module:
                        alias = module.split(".")[0]
                        cell_locals[alias] = getattr(lz, alias, None)

                try:
                    exec(cell, cell_locals, cell_locals)
                except Exception as e:
                    raise e

            @line_magic
            @magic_arguments()
            @argument("modules", nargs="*", help="Modules to import")
            @argument("-q", "--quiet", action="store_true", help="Suppress output")
            def lazyimport(self, line: str) -> None:
                """
                %lazyimport - Import modules lazily in IPython.

                Usage:
                    %lazyimport numpy pandas
                    %lazyimport np pd -q
                """
                args = parse_argstring(self.lazyimport, line)
                modules = args.modules or LAZY_MAGIC_COMMANDS
                quiet = args.quiet

                import laziest_import as lz

                shell = get_ipython()

                if shell is None:
                    raise RuntimeError("This magic must be run in IPython")

                for module in modules:
                    aliases = {
                        "numpy": "np",
                        "pandas": "pd",
                        "matplotlib.pyplot": "plt",
                        "tensorflow": "tf",
                        "torch": "torch",
                    }

                    if module in aliases:
                        alias = aliases[module]
                    else:
                        alias = module.replace(".", "_")

                    try:
                        obj = getattr(lz, module.split(".")[0], None)
                        if obj is not None:
                            shell.user_ns[alias] = obj
                            self._lazy_modules.append(alias)
                            if not quiet:
                                print(f"Lazy imported {module} as {alias}")
                    except AttributeError:
                        if not quiet:
                            print(f"Warning: Could not lazy import {module}")

            @line_magic
            def lazylist(self, line: str) -> None:
                """
                %lazylist - List available lazy modules.

                Usage:
                    %lazylist
                """
                import laziest_import as lz

                available = lz.list_available()
                lazy_loaded = self._lazy_modules

                print("Available lazy modules:")
                print("-" * 40)

                stdlib = [
                    m
                    for m in available
                    if m in dir(__builtins__)
                    or m in ["os", "sys", "math", "json", "re"]
                ]
                common = ["np", "pd", "plt", "tf", "torch"]
                other = [m for m in available if m not in stdlib and m not in common]

                if stdlib:
                    print("Standard Library:", ", ".join(sorted(stdlib)))
                if common:
                    print(
                        "Common Packages:",
                        ", ".join(c for c in common if c in available),
                    )
                if other:
                    print(
                        "Other:",
                        ", ".join(sorted(other)[:20]),
                        "..." if len(other) > 20 else "",
                    )

                if lazy_loaded:
                    print(f"\nCurrently lazy loaded: {', '.join(lazy_loaded)}")

            @line_magic
            def lazysearch(self, line: str) -> None:
                """
                %lazysearch - Search for symbols across modules.

                Usage:
                    %lazysearch sqrt
                    %lazysearch DataFrame
                """
                import laziest_import as lz

                parts = line.strip().split("--")
                symbol = parts[0].strip()
                sym_type = None

                for part in parts[1:]:
                    if part.strip().startswith("type"):
                        sym_type = part.split("type")[1].strip()

                if not symbol:
                    print("Usage: %lazysearch <symbol_name> [--type class|function]")
                    return

                results = lz.search_symbol(symbol, symbol_type=sym_type, max_results=10)

                if not results:
                    print(f"No results found for '{symbol}'")
                    return

                print(f"Symbol '{symbol}' found in:")
                print("-" * 50)

                for r in results:
                    print(f"  {r.module_name}.{r.symbol_name} ({r.symbol_type})")
                    if r.signature:
                        print(f"    Signature: {r.signature}")

                print(f"\nTotal: {len(results)} result(s)")

        return LazyMagics

    except ImportError:
        return None


LazyMagics = _create_lazy_magics()


def load_ipython_extension(ipython: Any) -> None:
    """Load the IPython extension."""
    if not _IPYTHON_AVAILABLE:
        raise ImportError("IPython is required. Install with: pip install ipython")

    if LazyMagics is not None:
        ipython.register_magics(LazyMagics)


def unload_ipython_extension(ipython: Any) -> None:
    """Unload the IPython extension."""
    pass


def enable_in_jupyter() -> bool:
    """
    Enable laziest-import in current Jupyter/IPython environment.

    Returns:
        True if successful, False otherwise
    """
    if not _IPYTHON_AVAILABLE:
        return False

    try:
        from IPython import get_ipython

        ipython = get_ipython()
        if ipython is None:
            return False

        if LazyMagics is not None:
            ipython.register_magics(LazyMagics)
        return True
    except Exception:
        return False
