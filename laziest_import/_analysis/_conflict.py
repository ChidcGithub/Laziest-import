"""Symbol conflict detection and visualization."""

from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass

from .._config import _SYMBOL_CACHE, _SYMBOL_PREFERENCES


@dataclass
class SymbolConflict:
    """Information about a symbol conflict."""
    symbol_name: str
    locations: List[Tuple[str, str]]  # (module_name, symbol_type)
    recommended: Optional[str] = None


def find_symbol_conflicts() -> Dict[str, SymbolConflict]:
    """
    Find all symbols that exist in multiple modules.
    
    Returns:
        Dictionary mapping symbol name to conflict info
    """
    conflicts: Dict[str, SymbolConflict] = {}
    
    for symbol_name, locations in _SYMBOL_CACHE.items():
        if len(locations) > 1:
            # Get unique modules
            modules = {}
            for loc in locations:
                module_name = loc[0]
                symbol_type = loc[1]
                if module_name not in modules:
                    modules[module_name] = symbol_type
            
            if len(modules) > 1:
                # Find recommended module from preferences
                recommended = _SYMBOL_PREFERENCES.get(symbol_name)
                
                conflicts[symbol_name] = SymbolConflict(
                    symbol_name=symbol_name,
                    locations=[(m, t) for m, t in modules.items()],
                    recommended=recommended
                )
    
    return conflicts


def show_conflicts(
    symbol_filter: Optional[str] = None,
    max_results: int = 20
) -> None:
    """
    Display symbol conflicts in a formatted table.
    
    Args:
        symbol_filter: Optional filter string to narrow results
        max_results: Maximum number of conflicts to show
    """
    conflicts = find_symbol_conflicts()
    
    if not conflicts:
        print("No symbol conflicts found.")
        return
    
    # Filter if requested
    if symbol_filter:
        conflicts = {
            k: v for k, v in conflicts.items()
            if symbol_filter.lower() in k.lower()
        }
    
    if not conflicts:
        print(f"No conflicts matching '{symbol_filter}' found.")
        return
    
    # Sort by number of locations (most conflicts first)
    sorted_conflicts = sorted(
        conflicts.items(),
        key=lambda x: -len(x[1].locations)
    )[:max_results]
    
    print("\n" + "=" * 70)
    print("                    Symbol Conflicts")
    print("=" * 70)
    
    for symbol, conflict in sorted_conflicts:
        print(f"\n  {symbol}:")
        for module, sym_type in conflict.locations:
            pref_marker = " *" if module == conflict.recommended else ""
            print(f"    - {module} [{sym_type}]{pref_marker}")
        
        if conflict.recommended:
            print(f"    (preferred: {conflict.recommended})")
    
    print(f"\n  Showing {len(sorted_conflicts)} of {len(conflicts)} conflicts")
    print("=" * 70)


def get_conflicts_summary() -> Dict[str, Any]:
    """
    Get a summary of all symbol conflicts.
    
    Returns:
        Summary dictionary
    """
    conflicts = find_symbol_conflicts()
    
    # Count by module
    module_counts: Dict[str, int] = defaultdict(int)
    for conflict in conflicts.values():
        for module, _ in conflict.locations:
            module_counts[module] += 1
    
    return {
        "total_conflicts": len(conflicts),
        "modules_with_conflicts": dict(sorted(
            module_counts.items(),
            key=lambda x: -x[1]
        )[:10]),
        "top_conflicts": [
            {
                "symbol": symbol,
                "modules": [m for m, _ in conflict.locations]
            }
            for symbol, conflict in sorted(
                conflicts.items(),
                key=lambda x: -len(x[1].locations)
            )[:10]
        ]
    }
