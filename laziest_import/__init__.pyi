"""
Type stubs for laziest-import
"""

from typing import Dict, List, Optional, Set, Any, Tuple, Callable, Union
from types import ModuleType
from pathlib import Path

__version__: str

# ============== LazyModule Classes ==============

class LazyModule:
    """Lazy loading module proxy class."""
    def __getattr__(self, name: str) -> Any: ...
    def __dir__(self) -> List[str]: ...
    def __repr__(self) -> str: ...
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

class LazySubmodule:
    """Lazy loading submodule proxy class."""
    def __getattr__(self, name: str) -> Any: ...
    def __dir__(self) -> List[str]: ...
    def __repr__(self) -> str: ...
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

# ============== Alias Management ==============

def register_alias(alias: str, module_name: str) -> None:
    """Register a custom module alias."""
    ...

def register_aliases(aliases: Dict[str, str]) -> List[str]:
    """Register multiple module aliases at once."""
    ...

def unregister_alias(alias: str) -> bool:
    """Remove a registered alias."""
    ...

def list_loaded() -> List[str]:
    """Return list of loaded module aliases."""
    ...

def list_available() -> List[str]:
    """Return list of all available module aliases."""
    ...

def get_module(alias: str) -> Optional[ModuleType]:
    """Get a loaded module object."""
    ...

def clear_cache() -> None:
    """Clear the loaded module cache."""
    ...

# ============== Version & Reload ==============

def get_version(alias: str) -> Optional[str]:
    """Get the version of a loaded module."""
    ...

def reload_module(alias: str) -> bool:
    """Reload a loaded module."""
    ...

# ============== Auto-search ==============

def enable_auto_search() -> None:
    """Enable auto-search functionality."""
    ...

def disable_auto_search() -> None:
    """Disable auto-search functionality."""
    ...

def is_auto_search_enabled() -> bool:
    """Check if auto-search is enabled."""
    ...

def search_module(name: str) -> Optional[str]:
    """Search for a matching module name."""
    ...

def search_class(class_name: str) -> Optional[Tuple[str, Any]]:
    """Search for a class in loaded modules."""
    ...

def rebuild_module_cache() -> None:
    """Rebuild the module cache."""
    ...

# ============== Symbol Search ==============

class SearchResult:
    """Search result for a symbol."""
    module_name: str
    symbol_name: str
    symbol_type: str
    signature: Optional[str]
    score: float
    obj: Optional[Any]

def enable_symbol_search(
    interactive: bool = True,
    exact_params: bool = False,
    max_results: int = 5,
    search_depth: int = 1,
    skip_stdlib: bool = False
) -> None:
    """Enable symbol search functionality."""
    ...

def disable_symbol_search() -> None:
    """Disable symbol search functionality."""
    ...

def is_symbol_search_enabled() -> bool:
    """Check if symbol search is enabled."""
    ...

def search_symbol(
    name: str,
    symbol_type: Optional[str] = None,
    signature: Optional[str] = None,
    max_results: Optional[int] = None
) -> List[SearchResult]:
    """Search for a symbol (class/function) by name across installed packages."""
    ...

def rebuild_symbol_index() -> None:
    """Rebuild the symbol index."""
    ...

def get_symbol_search_config() -> Dict[str, Any]:
    """Get current symbol search configuration."""
    ...

def get_symbol_cache_info() -> Dict[str, Any]:
    """Get information about the symbol cache."""
    ...

def clear_symbol_cache() -> None:
    """Clear the symbol cache."""
    ...

# ============== Configuration ==============

def reload_aliases() -> None:
    """Reload aliases from all configuration files."""
    ...

def export_aliases(path: Optional[str] = None, include_categories: bool = True) -> str:
    """Export current aliases to a JSON file."""
    ...

def validate_aliases(aliases: Optional[Dict[str, str]] = None) -> Dict[str, List[str]]:
    """Validate alias entries."""
    ...

def validate_aliases_importable(aliases: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, Any]]:
    """Validate that aliases can actually be imported."""
    ...

def get_config_paths() -> List[str]:
    """Get all configuration file paths in priority order."""
    ...

# ============== Debug & Statistics ==============

def enable_debug_mode() -> None:
    """Enable debug mode for detailed logging."""
    ...

def disable_debug_mode() -> None:
    """Disable debug mode."""
    ...

def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    ...

def get_import_stats() -> Dict[str, Any]:
    """Get import statistics."""
    ...

def reset_import_stats() -> None:
    """Reset import statistics."""
    ...

# ============== Import Hooks ==============

def add_pre_import_hook(hook: Callable[[str], None]) -> None:
    """Add a hook to be called before a module is imported."""
    ...

def add_post_import_hook(hook: Callable[[str, Any], None]) -> None:
    """Add a hook to be called after a module is imported."""
    ...

def remove_pre_import_hook(hook: Callable[[str], None]) -> bool:
    """Remove a pre-import hook."""
    ...

def remove_post_import_hook(hook: Callable[[str, Any], None]) -> bool:
    """Remove a post-import hook."""
    ...

def clear_import_hooks() -> None:
    """Remove all import hooks."""
    ...

# ============== Async Import ==============

async def import_async(alias: str) -> Any:
    """Asynchronously import a module."""
    ...

async def import_multiple_async(aliases: List[str]) -> Dict[str, Any]:
    """Asynchronously import multiple modules in parallel."""
    ...

# ============== Retry Configuration ==============

def enable_retry(max_retries: int = 3, retry_delay: float = 0.5, 
                 modules: Optional[Set[str]] = None) -> None:
    """Enable automatic retry for module imports."""
    ...

def disable_retry() -> None:
    """Disable automatic retry for module imports."""
    ...

def is_retry_enabled() -> bool:
    """Check if retry is enabled."""
    ...

# ============== File Cache ==============

def enable_file_cache() -> None:
    """Enable file-level caching for faster subsequent imports."""
    ...

def disable_file_cache() -> None:
    """Disable file-level caching."""
    ...

def is_file_cache_enabled() -> bool:
    """Check if file-level caching is enabled."""
    ...

def clear_file_cache(file_path: Optional[str] = None) -> int:
    """Clear file cache(s)."""
    ...

def get_file_cache_info() -> Dict[str, Any]:
    """Get information about the current file cache."""
    ...

def force_save_cache() -> bool:
    """Force save the current file cache immediately."""
    ...

def set_cache_dir(path: Union[str, Path]) -> None:
    """Set custom cache directory."""
    ...

def get_cache_dir() -> Path:
    """Get current cache directory path."""
    ...

def reset_cache_dir() -> None:
    """Reset cache directory to default location."""
    ...

# ============== Module-level attributes ==============

__all__: List[str]

def __getattr__(name: str) -> LazyModule: ...
def __dir__() -> List[str]: ...
