"""
Deep debug: why search returns 0 after comprehensive test.
"""

import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from laziest_import._symbol import search_symbol, get_symbol_cache_info
from laziest_import._config import _SYMBOL_SEARCH_CONFIG, _SYMBOL_CACHE, _SYMBOL_INDEX_BUILT
from laziest_import._fuzzy import _levenshtein_distance

print("SEARCH_CONFIG:", json.dumps(_SYMBOL_SEARCH_CONFIG))
print("INDEX_BUILT before search:", _SYMBOL_INDEX_BUILT)

result = search_symbol("numpy")
print("numpy results:", len(result))

if len(result) == 0:
    if not _SYMBOL_SEARCH_CONFIG["enabled"]:
        print("REASON: search disabled!")

    info = get_symbol_cache_info()
    print("INDEX_BUILT:", info["built"])
    print("Cache size:", info["symbol_count"])

    matching = [
        k
        for k in _SYMBOL_CACHE
        if "numpy" in k.lower() or "dump" in k.lower() or "pytest" in k.lower()
    ]
    print("Matching keys:", matching[:10])

    sample_keys = list(_SYMBOL_CACHE.keys())[:20]
    print("Sample keys:", sample_keys)
    for k in sample_keys:
        ld = _levenshtein_distance("numpy", k.lower())
        if ld <= 2:
            print(f"  distance(numpy, {k}) = {ld} - MATCH!")
