"""
laziest-import Demo: Lazy Imports + Strict Mode + Freeze Report

Demonstrates:
  - Bare-name aliases (np, pd, plt) via `from laziest_import import *`
  - Profile & analyze
  - Symbol search with conflict detection
  - Strict mode (AmbiguousSymbolError)
  - Freeze report (alias -> module mapping)
  - RC config
"""

from laziest_import import *


def main():
    print("=" * 58)
    print("1. Profiled lazy imports")
    print("=" * 58)

    lz.profile.start()
    _ = np.array([1, 2, 3])
    _ = pd.DataFrame({"a": [1]})
    lz.profile.stop()

    report = lz.profile.report()
    for name, profile in report.modules.items():
        print(f"  {name}: {profile.load_time * 1000:.2f}ms")

    lz.profile.print_report()

    print()
    print("=" * 58)
    print("2. Dependency tree")
    print("=" * 58)
    print(lz.version.current)
    print(f"   Modules: {lz.analyze.dep_tree('numpy').total_modules}")

    print()
    print("=" * 58)
    print("3. 3D Graphics (bare-name plt / np)")
    print("=" * 58)

    fig = plt.figure(figsize=(12, 5))
    ax1 = fig.add_subplot(121, projection="3d")
    x = np.linspace(-5, 5, 100)
    y = np.linspace(-5, 5, 100)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(np.sqrt(X**2 + Y**2))
    ax1.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8)
    ax1.set_title("3D Surface")

    ax2 = fig.add_subplot(122, projection="3d")
    theta = np.linspace(0, 2 * np.pi, 30)
    phi = np.linspace(0, np.pi, 30)
    Theta, Phi = np.meshgrid(theta, phi)
    Xs = 2 * np.sin(Phi) * np.cos(Theta)
    Ys = 2 * np.sin(Phi) * np.sin(Theta)
    Zs = 2 * np.cos(Phi)
    ax2.plot_wireframe(Xs, Ys, Zs, color="cyan", alpha=0.6)
    ax2.set_title("Wireframe Sphere")

    plt.tight_layout()
    plt.savefig("demo_output.png", dpi=100)
    print("  [OK] Figure saved to demo_output.png")

    stats = lz.cache.stats
    print(f"  Cache: {stats['total_requests']} req, {stats['hit_rate']:.0%} hit rate")
    print(f"  Loaded: {lz.module.list_loaded()}")

    print()
    print("=" * 58)
    print("4. Symbol search & conflicts")
    print("=" * 58)

    results = lz.symbol.search("array", max_results=5)
    if results:
        print(f"  Symbol 'array' found in:")
        for r in results[:3]:
            print(f"    - {r.module_name}")
        conflicts = lz.symbol.conflicts("array")
        if conflicts:
            print(f"  Total conflicts: {len(conflicts)}")

    lz.symbol.prefer("array", "numpy")
    pref = lz.symbol.preference("array")
    print(f"  Preference: array -> {pref}")

    print()
    print("=" * 58)
    print("5. Strict mode (AmbiguousSymbolError)")
    print("=" * 58)

    from laziest_import._symbol import _search_symbol_enhanced, AmbiguousSymbolError, _build_symbol_index
    from laziest_import._config import _SYMBOL_RESOLUTION_CONFIG

    print("  Enabling strict mode & building symbol index...")
    _SYMBOL_RESOLUTION_CONFIG["strict"] = True
    _build_symbol_index(force=True)

    try:
        result = _search_symbol_enhanced("array", auto=True)
        print(f"  array -> {result.module_name}.{result.symbol_name} (unambiguous)")
    except AmbiguousSymbolError as e:
        print(f"  [OK] Strict mode caught:")
        for c in e.candidates[:3]:
            print(f"    - {c.module_name}.{c.symbol_name} ({c.confidence:.0%})")

    lz.symbol.prefer("array", "numpy")
    print("  Set preference: array -> numpy")
    try:
        result = _search_symbol_enhanced("array", auto=True)
        if result:
            print(f"  array now resolves to: {result.module_name}.{result.symbol_name}")
    except AmbiguousSymbolError as e:
        print(f"  Still ambiguous: {e}")

    _SYMBOL_RESOLUTION_CONFIG["strict"] = False
    print("  Strict mode disabled.")

    print()
    print("=" * 58)
    print("6. Freeze report (alias -> module mapping)")
    print("=" * 58)

    import json
    from laziest_import._config import _ALIAS_MAP

    freeze = {"version": "1.0", "aliases": {}, "files": {}}
    for alias, module in sorted(_ALIAS_MAP.items()):
        if len(alias) <= 6 or alias in ("numpy", "pandas", "matplotlib"):
            freeze["aliases"][alias] = module

    print(json.dumps(freeze, indent=2, ensure_ascii=False))

    print()
    print("=" * 58)
    print("7. RC config preview")
    print("=" * 58)

    print(f"  Paths checked:")
    for p in lz.rc.paths():
        print(f"    - {p}")
    print(f"  Active: {lz.rc.paths_list}")
    info = lz.rc.info()
    if info.get("active_path"):
        print(f"  Loaded from: {info['active_path']}")
    else:
        print("  (no .laziestrc found — using defaults)")

    print()
    print("=" * 58)
    print("[OK] Demo completed successfully!")
    print("=" * 58)


if __name__ == "__main__":
    main()
