"""
Type stubs for laziest-import
"""

from typing import Dict, List, Optional, Set, Any, Tuple, Callable, Union
from types import ModuleType
from pathlib import Path

__version__: str

# ============== Initialization State ==============

def is_initializing() -> bool:
    """Check if currently initializing."""
    ...

def is_initialized() -> bool:
    """Check if initialization completed successfully."""
    ...

def is_init_failed() -> bool:
    """Check if initialization failed."""
    ...

def get_init_error() -> Optional[str]:
    """Get initialization error message if any."""
    ...

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

class LazySymbol:
    """Lazy loading symbol (class/function) proxy class."""
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...
    def __dir__(self) -> List[str]: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
    def __enter__(self) -> Any: ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
    def get_underlying_class(self) -> type:
        """Get the underlying class for isinstance checks."""
        ...

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

class SymbolMatch:
    """Scored symbol match with confidence and source information."""
    module_name: str
    symbol_name: str
    symbol_type: str
    signature: Optional[str]
    confidence: float
    source: str
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

# ============== Symbol Resolution ==============

def set_symbol_preference(symbol: str, module: str) -> None:
    """Set a user preference for symbol resolution."""
    ...

def get_symbol_preference(symbol: str) -> Optional[str]:
    """Get the user preference for a symbol."""
    ...

def clear_symbol_preference(symbol: str) -> bool:
    """Clear a user preference for a symbol."""
    ...

def list_symbol_conflicts(symbol: str) -> List[Dict[str, Any]]:
    """List all modules that define a symbol with potential conflicts."""
    ...

def set_module_priority(module: str, priority: int) -> None:
    """Set the priority for a module in symbol resolution."""
    ...

def get_module_priority(module: str) -> int:
    """Get the priority for a module."""
    ...

def enable_auto_symbol_resolution(
    auto: bool = True,
    threshold: float = 0.7,
    warn_on_conflict: bool = True,
    context_aware: bool = True
) -> None:
    """Configure automatic symbol resolution behavior."""
    ...

def disable_auto_symbol_resolution() -> None:
    """Disable automatic symbol resolution."""
    ...

def get_symbol_resolution_config() -> Dict[str, Any]:
    """Get current symbol resolution configuration."""
    ...

def get_loaded_modules_context() -> Set[str]:
    """Get the set of modules currently loaded/in use."""
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

# ============== Auto Install ==============

def enable_auto_install(
    interactive: bool = True,
    index: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    prefer_uv: bool = False,
    silent: bool = False
) -> None:
    """Enable automatic installation of missing packages."""
    ...

def disable_auto_install() -> None:
    """Disable automatic installation of missing packages."""
    ...

def is_auto_install_enabled() -> bool:
    """Check if automatic installation is enabled."""
    ...

def install_package(
    package_name: str,
    index: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    interactive: Optional[bool] = None
) -> bool:
    """Install a package manually."""
    ...

def get_auto_install_config() -> Dict[str, Any]:
    """Get current auto-install configuration."""
    ...

def set_pip_index(url: Optional[str]) -> None:
    """Set custom PyPI mirror index URL."""
    ...

def set_pip_extra_args(args: List[str]) -> None:
    """Set extra arguments for pip install."""
    ...

# ============== Package Version ==============

def get_package_version(package_name: str) -> Optional[str]:
    """Get the version of an installed package."""
    ...

def get_all_package_versions() -> Dict[str, str]:
    """Get versions of all installed packages."""
    ...

def get_laziest_import_version() -> str:
    """Get the version of laziest-import library."""
    ...

# ============== Incremental Index ==============

def enable_incremental_index(enabled: bool = True) -> None:
    """Enable or disable incremental index updates."""
    ...

def enable_background_build(enabled: bool = True) -> None:
    """Enable or disable background index building."""
    ...

def enable_cache_compression(enabled: bool = True) -> None:
    """Enable or disable cache compression."""
    ...

def get_incremental_config() -> Dict[str, Any]:
    """Get incremental index update configuration."""
    ...

def get_preheat_config() -> Dict[str, Any]:
    """Get background preheat configuration."""
    ...

# ============== Easter Egg & Help ==============

def easter_egg(name: str = "default") -> str:
    """Get a fun easter egg message!
    
    Args:
        name: The easter egg name. Available options:
            - "default": A random fun fact about lazy imports
            - "author": Author's message
            - "quote": A programming quote
            - "tip": A lazy import tip
            - "secret": A secret message (shhh!)
            - "thanks": Special thanks
    
    Returns:
        A fun message string.
    """
    ...

def help(topic: Optional[str] = None) -> str:
    """Get help on laziest-import topics.
    
    Args:
        topic: Optional topic to get help on. Available topics:
            - None: General overview
            - "quickstart": Quick start guide
            - "lazy": How lazy imports work
            - "alias": Alias system
            - "symbol": Symbol search
            - "cache": Caching system
            - "config": Configuration options
            - "async": Async imports
            - "hooks": Import hooks
            - "api": Full API reference
    
    Returns:
        Help text for the requested topic.
    """
    ...

# ============== Module-level attributes ==============

__all__: List[str]

def __getattr__(name: str) -> Union[LazyModule, LazySymbol]: ...
def __dir__() -> List[str]: ...
