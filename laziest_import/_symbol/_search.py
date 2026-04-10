"""
Symbol search functionality for laziest-import.

This module contains functions for searching symbols and handling conflicts.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
import logging
import warnings

from .._config import (
    _DEBUG_MODE,
    is_initialized,
    _SYMBOL_SEARCH_CONFIG,
    _SYMBOL_CACHE,
    _MODULE_PRIORITY,
    _SYMBOL_PREFERENCES,
    _SYMBOL_RESOLUTION_CONFIG,
    _CONFIRMED_MAPPINGS,
    SearchResult,
    SymbolMatch,
)
from .._fuzzy import (
    _levenshtein_distance,
    _get_common_symbol_misspellings,
    _infer_context,
)
from ._scan import _is_stdlib_module
from ._index import _build_symbol_index


def _compare_signatures(sig1: Optional[str], sig2: Optional[str]) -> float:
    """Compare two signature strings and return a similarity score."""
    if sig1 is None or sig2 is None:
        return 0.5

    def extract_params(sig: str) -> Set[str]:
        try:
            inner = sig.strip("()")
            if not inner:
                return set()
            params = set()
            for part in inner.split(","):
                part = part.strip()
                if part:
                    param_name = part.split("=")[0].split(":")[0].strip()
                    if param_name and not param_name.startswith("*"):
                        params.add(param_name)
            return params
        except Exception:
            return set()

    params1 = extract_params(sig1)
    params2 = extract_params(sig2)

    if not params1 or not params2:
        return 0.5

    intersection = len(params1 & params2)
    union = len(params1 | params2)

    return intersection / union if union > 0 else 0.0


def search_symbol(
    name: str,
    symbol_type: Optional[str] = None,
    signature: Optional[str] = None,
    max_results: Optional[int] = None,
) -> List[SearchResult]:
    """Search for a symbol (class/function) by name across installed packages."""
    if not _SYMBOL_SEARCH_CONFIG["enabled"]:
        return []

    import laziest_import._config as config
    if not config._SYMBOL_INDEX_BUILT:
        _build_symbol_index()

    if name not in _SYMBOL_CACHE:
        name_lower = name.lower()
        matches = []
        for cached_name in _SYMBOL_CACHE.keys():
            if cached_name.lower() == name_lower:
                matches.append(cached_name)
            elif name_lower in cached_name.lower():
                matches.append(cached_name)
            elif _levenshtein_distance(name_lower, cached_name.lower()) <= 2:
                matches.append(cached_name)

        if not matches:
            return []

        all_results = []
        for match_name in matches[:3]:
            all_results.extend(
                _search_symbol_direct(match_name, symbol_type, signature)
            )

        seen = set()
        results = []
        for r in all_results:
            key = (r.module_name, r.symbol_name)
            if key not in seen:
                seen.add(key)
                results.append(r)

        max_res = max_results or _SYMBOL_SEARCH_CONFIG["max_results"]
        return sorted(results, key=lambda x: -x.score)[:max_res]

    return _search_symbol_direct(name, symbol_type, signature, max_results)


def _search_symbol_direct(
    name: str,
    symbol_type: Optional[str] = None,
    signature: Optional[str] = None,
    max_results: Optional[int] = None,
) -> List[SearchResult]:
    """Direct search for an exact symbol name in cache."""
    results = []

    if name not in _SYMBOL_CACHE:
        return results

    for module_name, sym_type, cached_sig in _SYMBOL_CACHE[name]:
        if symbol_type and sym_type != symbol_type:
            continue

        score = 1.0

        if _SYMBOL_SEARCH_CONFIG["skip_stdlib"] and _is_stdlib_module(module_name):
            score *= 0.5

        if signature and cached_sig:
            sig_score = _compare_signatures(signature, cached_sig)
            if _SYMBOL_SEARCH_CONFIG["exact_params"] and sig_score < 0.9:
                continue
            score *= 0.5 + 0.5 * sig_score

        results.append(
            SearchResult(
                module_name=module_name,
                symbol_name=name,
                symbol_type=sym_type,
                signature=cached_sig,
                score=score,
            )
        )

    results.sort(key=lambda x: -x.score)

    max_res = max_results or _SYMBOL_SEARCH_CONFIG["max_results"]
    return results[:max_res]


def _score_symbol_match(
    result: SearchResult, context: Set[str], original_name: str
) -> SymbolMatch:
    """Score a symbol search result with context awareness and priority."""
    confidence = result.score
    module = result.module_name.split(".")[0]
    source = "exact"

    # 1. User preference (highest priority)
    if result.symbol_name in _SYMBOL_PREFERENCES:
        pref = _SYMBOL_PREFERENCES[result.symbol_name]
        pref_base = pref.split(".")[0]
        if module == pref_base:
            return SymbolMatch(
                module_name=result.module_name,
                symbol_name=result.symbol_name,
                symbol_type=result.symbol_type,
                signature=result.signature,
                confidence=1.0,
                source="user_pref",
                obj=result.obj,
            )
        else:
            confidence *= 0.2
            source = "not_preferred"

    # 2. Context awareness
    if _SYMBOL_RESOLUTION_CONFIG["context_aware"] and module in context:
        confidence *= 1.5
        source = "context"

    # 3. Module priority
    priority = _MODULE_PRIORITY.get(module, 50)
    confidence *= priority / 100

    # 4. Exact match vs fuzzy match
    if result.symbol_name != original_name:
        distance = _levenshtein_distance(
            original_name.lower(), result.symbol_name.lower()
        )
        max_dist = max(len(original_name), len(result.symbol_name)) // 3
        fuzzy_penalty = distance / max(max_dist, 1)
        confidence *= 1 - fuzzy_penalty * 0.3
        source = "fuzzy"

    # 5. Penalize stdlib
    if _SYMBOL_SEARCH_CONFIG.get("skip_stdlib") and _is_stdlib_module(
        result.module_name
    ):
        confidence *= 0.5

    confidence = min(confidence, 1.0)

    return SymbolMatch(
        module_name=result.module_name,
        symbol_name=result.symbol_name,
        symbol_type=result.symbol_type,
        signature=result.signature,
        confidence=confidence,
        source=source,
        obj=result.obj,
    )


def _search_symbol_enhanced(
    name: str, auto: bool = True, symbol_type: Optional[str] = None
) -> Optional[SymbolMatch]:
    """Enhanced symbol search with conflict resolution and spell correction."""
    if not _SYMBOL_RESOLUTION_CONFIG["auto_symbol"]:
        return None

    import laziest_import._config as config
    if not config._SYMBOL_INDEX_BUILT:
        _build_symbol_index()

    original_name = name

    # 1. Check symbol misspellings first
    corrected_name = None
    if _SYMBOL_RESOLUTION_CONFIG["symbol_misspelling"]:
        misspellings = _get_common_symbol_misspellings()
        name_lower = name.lower()
        if name_lower in misspellings:
            corrected_name = misspellings[name_lower]
            if _DEBUG_MODE:
                logging.debug(
                    f"[laziest-import] Symbol misspelling corrected: '{name}' -> '{corrected_name}'"
                )

    search_name = corrected_name or name

    # 2. Search for the symbol
    results = search_symbol(search_name, symbol_type=symbol_type)

    # 3. If no exact match, try fuzzy search
    if not results and not corrected_name:
        name_lower = search_name.lower()
        fuzzy_matches: List[Tuple[int, str]] = []

        for cached_name in _SYMBOL_CACHE.keys():
            dist = _levenshtein_distance(name_lower, cached_name.lower())
            max_dist = min(3, max(len(name_lower), len(cached_name)) // 3)
            if dist <= max_dist:
                fuzzy_matches.append((dist, cached_name))

        fuzzy_matches.sort(key=lambda x: x[0])
        for dist, match_name in fuzzy_matches[:3]:
            match_results = search_symbol(match_name, symbol_type=symbol_type)
            results.extend(match_results)

        if results and _DEBUG_MODE:
            logging.debug(
                f"[laziest-import] Fuzzy symbol search found {len(results)} results for '{name}'"
            )

    if not results:
        return None

    # 4. Score all results
    context = _infer_context()
    scored_results = [_score_symbol_match(r, context, original_name) for r in results]

    scored_results.sort(key=lambda x: -x.confidence)

    best = scored_results[0]
    second = scored_results[1] if len(scored_results) > 1 else None

    # 5. Determine if we should auto-select
    if not auto:
        return best

    threshold = _SYMBOL_RESOLUTION_CONFIG["auto_threshold"]
    conflict_threshold = _SYMBOL_RESOLUTION_CONFIG["conflict_threshold"]

    if best.confidence >= threshold:
        if second and (best.confidence - second.confidence) < conflict_threshold:
            if _SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"]:
                _warn_symbol_conflict(original_name, scored_results[:3])
            if best.source in ("user_pref", "context"):
                return best
            return None
        return best

    if _SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"]:
        _warn_symbol_conflict(original_name, scored_results[:3])

    return None


def _warn_symbol_conflict(name: str, matches: List[SymbolMatch]) -> None:
    """Warn about symbol conflict and suggest disambiguation."""
    if not matches:
        return

    suggestions = ", ".join(
        f"{m.module_name}.{m.symbol_name}({m.confidence:.0%})" for m in matches[:3]
    )

    examples = []
    for m in matches[:2]:
        module_alias = m.module_name.split(".")[0]
        examples.append(f"{module_alias}.{m.symbol_name}")

    example_str = " or ".join(examples) if examples else ""

    warnings.warn(
        f"[laziest-import] Symbol '{name}' found in multiple modules: {suggestions}. "
        f"Use module prefix to disambiguate, e.g., {example_str}. "
        f"Or set a preference: set_symbol_preference('{name}', '{matches[0].module_name}')",
        UserWarning,
        stacklevel=4,
    )


def _is_interactive_terminal() -> bool:
    """Check if we're running in an interactive terminal."""
    import sys

    # Check if stdin is a tty (interactive terminal)
    if not sys.stdin.isatty():
        return False
    # Check if stdout is a tty
    if not sys.stdout.isatty():
        return False
    # Check if we're in a Jupyter notebook or IPython
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            # In IPython/Jupyter, input() may not work properly
            # but we can still try if it's a terminal
            return sys.stdin.isatty()
    except ImportError:
        pass
    return True


def _interactive_confirm(
    results: List[SearchResult], symbol_name: str
) -> Optional[str]:
    """Interactively ask user to confirm which module to use."""
    if not results:
        return None

    if not _SYMBOL_SEARCH_CONFIG["interactive"]:
        return results[0].module_name

    # Check if we're in an interactive terminal
    if not _is_interactive_terminal():
        # Not interactive, auto-select first result with a warning
        if _DEBUG_MODE:
            logging.debug(
                f"[laziest-import] Non-interactive environment, auto-selecting "
                f"'{results[0].module_name}' for symbol '{symbol_name}'"
            )
        return results[0].module_name

    print(f"\n[laziest-import] Found {len(results)} match(es) for '{symbol_name}':")
    print("-" * 60)

    for i, r in enumerate(results, 1):
        sig_str = f" {r.signature}" if r.signature else ""
        type_str = f"[{r.symbol_type}]"
        print(f"  {i}. {r.module_name}.{r.symbol_name} {type_str}{sig_str}")

    print(f"  0. Skip (do not register)")
    print("-" * 60)

    try:
        choice = input(f"Select [1-{len(results)}, 0 to skip] (default=1): ").strip()

        if not choice:
            choice = "1"

        if choice == "0":
            return None

        idx = int(choice) - 1
        if 0 <= idx < len(results):
            return results[idx].module_name

        print(f"Invalid choice: {choice}")
        return None
    except (ValueError, EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return None
    except OSError:
        # OSError can occur in some non-interactive environments
        if _DEBUG_MODE:
            logging.debug(
                f"[laziest-import] OSError during interactive confirm, "
                f"auto-selecting '{results[0].module_name}'"
            )
        return results[0].module_name


def _handle_symbol_not_found(name: str) -> Optional[str]:
    """Handle a symbol not found error by searching and prompting user."""
    from .._alias import register_alias

    if not is_initialized():
        return None

    if name in _CONFIRMED_MAPPINGS:
        return _CONFIRMED_MAPPINGS[name]

    results = search_symbol(name)

    if not results:
        return None

    selected_module = _interactive_confirm(results, name)

    if selected_module:
        _CONFIRMED_MAPPINGS[name] = selected_module
        register_alias(name, selected_module)
        print(f"[laziest-import] Registered alias: {name} -> {selected_module}")
        return selected_module

    return None
