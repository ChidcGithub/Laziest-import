"""
Dependency tree analysis module.

Analyze module dependencies and visualize import relationships.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
import importlib.util
import sys
from pathlib import Path


@dataclass
class DependencyNode:
    """A node in the dependency tree."""
    module_name: str
    is_available: bool = True
    is_stdlib: bool = False
    is_third_party: bool = False
    is_local: bool = False
    version: Optional[str] = None
    children: List["DependencyNode"] = field(default_factory=list)
    depth: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "module_name": self.module_name,
            "is_available": self.is_available,
            "is_stdlib": self.is_stdlib,
            "is_third_party": self.is_third_party,
            "is_local": self.is_local,
            "version": self.version,
            "depth": self.depth,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class DependencyTree:
    """Complete dependency tree analysis result."""
    root_module: str
    total_modules: int = 0
    stdlib_count: int = 0
    third_party_count: int = 0
    local_count: int = 0
    unavailable_count: int = 0
    max_depth: int = 0
    tree: Optional[DependencyNode] = None
    circular_dependencies: List[Tuple[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "root_module": self.root_module,
            "total_modules": self.total_modules,
            "stdlib_count": self.stdlib_count,
            "third_party_count": self.third_party_count,
            "local_count": self.local_count,
            "unavailable_count": self.unavailable_count,
            "max_depth": self.max_depth,
            "tree": self.tree.to_dict() if self.tree else None,
            "circular_dependencies": self.circular_dependencies,
        }


# Standard library modules (partial list for detection)
_STDLIB_MODULES = {
    'abc', 'argparse', 'ast', 'asyncio', 'atexit', 'base64', 'bisect',
    'builtins', 'bz2', 'calendar', 'cmath', 'cmd', 'code', 'codecs',
    'collections', 'configparser', 'contextlib', 'copy', 'csv', 'ctypes',
    'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'enum',
    'errno', 'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob',
    'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib',
    'importlib', 'inspect', 'io', 'itertools', 'json', 'keyword',
    'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'marshal',
    'math', 'mimetypes', 'mmap', 'multiprocessing', 'netrc', 'numbers',
    'operator', 'optparse', 'os', 'pathlib', 'pickle', 'platform',
    'plistlib', 'poplib', 'pprint', 'profile', 'queue', 'random', 're',
    'reprlib', 'sched', 'secrets', 'select', 'shelve', 'shlex', 'shutil',
    'signal', 'site', 'smtplib', 'socket', 'socketserver', 'sqlite3',
    'ssl', 'stat', 'statistics', 'string', 'struct', 'subprocess', 'sys',
    'sysconfig', 'tarfile', 'tempfile', 'textwrap', 'threading', 'time',
    'timeit', 'token', 'tokenize', 'trace', 'traceback', 'types', 'typing',
    'unicodedata', 'unittest', 'urllib', 'uuid', 'warnings', 'wave',
    'weakref', 'webbrowser', 'wsgiref', 'xml', 'xmlrpc', 'zipfile',
    'zipimport', 'zlib', 'zoneinfo',
}


class DependencyAnalyzer:
    """Analyze module dependencies."""
    
    def __init__(
        self,
        max_depth: int = 5,
        include_stdlib: bool = True,
        include_third_party: bool = True,
        include_local: bool = True,
    ):
        """
        Initialize the dependency analyzer.
        
        Args:
            max_depth: Maximum depth to traverse
            include_stdlib: Include standard library modules
            include_third_party: Include third-party packages
            include_local: Include local modules
        """
        self.max_depth = max_depth
        self.include_stdlib = include_stdlib
        self.include_third_party = include_third_party
        self.include_local = include_local
        self._visited: Set[str] = set()
        self._circular: List[Tuple[str, str]] = []
        self._in_stack: Set[str] = set()
    
    def _is_stdlib(self, module_name: str) -> bool:
        """Check if module is from standard library."""
        base = module_name.split('.')[0]
        return base in _STDLIB_MODULES
    
    def _is_available(self, module_name: str) -> bool:
        """Check if module is importable."""
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            return False
    
    def _get_version(self, module_name: str) -> Optional[str]:
        """Get module version if available."""
        try:
            mod = importlib.import_module(module_name.split('.')[0])
            return getattr(mod, '__version__', None)
        except Exception:
            return None
    
    def _get_submodules(self, module_name: str) -> List[str]:
        """Get list of submodules for a module."""
        submodules = []
        try:
            mod = importlib.import_module(module_name)
            for name in dir(mod):
                if name.startswith('_'):
                    continue
                attr = getattr(mod, name)
                if hasattr(attr, '__module__') and attr.__module__:
                    full_name = f"{module_name}.{name}"
                    if full_name not in self._visited:
                        submodules.append(name)
        except Exception:
            pass
        return submodules
    
    def _analyze_node(
        self,
        module_name: str,
        depth: int = 0,
    ) -> Optional[DependencyNode]:
        """Recursively analyze a module's dependencies."""
        if depth > self.max_depth:
            return None
        
        # Check for circular dependency
        if module_name in self._in_stack:
            parent = list(self._in_stack)[-1] if self._in_stack else module_name
            self._circular.append((parent, module_name))
            return None
        
        if module_name in self._visited:
            return DependencyNode(
                module_name=module_name,
                is_available=True,
                depth=depth,
            )
        
        self._visited.add(module_name)
        self._in_stack.add(module_name)
        
        try:
            is_stdlib = self._is_stdlib(module_name)
            is_available = self._is_available(module_name)
            version = self._get_version(module_name) if is_available else None
            
            # Determine module type
            if not is_available:
                is_local = False
                is_third_party = False
            elif is_stdlib:
                is_local = False
                is_third_party = False
            else:
                # Check if it's a local module
                spec = importlib.util.find_spec(module_name)
                if spec and spec.origin:
                    is_local = not any(
                        path in spec.origin
                        for path in ['site-packages', 'dist-packages']
                    )
                    is_third_party = not is_local
                else:
                    is_local = False
                    is_third_party = True
            
            # Filter based on configuration
            if is_stdlib and not self.include_stdlib:
                self._in_stack.discard(module_name)
                return None
            if is_third_party and not self.include_third_party:
                self._in_stack.discard(module_name)
                return None
            if is_local and not self.include_local:
                self._in_stack.discard(module_name)
                return None
            
            node = DependencyNode(
                module_name=module_name,
                is_available=is_available,
                is_stdlib=is_stdlib,
                is_third_party=is_third_party,
                is_local=is_local,
                version=version,
                depth=depth,
            )
            
            # Get submodules if available
            if is_available and depth < self.max_depth:
                submodules = self._get_submodules(module_name)
                for sub in submodules[:10]:  # Limit submodules
                    child = self._analyze_node(
                        f"{module_name}.{sub}",
                        depth + 1,
                    )
                    if child:
                        node.children.append(child)
            
            return node
            
        finally:
            self._in_stack.discard(module_name)
    
    def analyze(self, module_name: str) -> DependencyTree:
        """
        Analyze a module's dependency tree.
        
        Args:
            module_name: Name of the module to analyze
            
        Returns:
            DependencyTree with analysis results
        """
        self._visited.clear()
        self._circular.clear()
        self._in_stack.clear()
        
        tree = self._analyze_node(module_name)
        
        # Calculate statistics
        total = len(self._visited)
        stdlib = sum(1 for m in self._visited if self._is_stdlib(m))
        unavailable = sum(1 for m in self._visited if not self._is_available(m))
        third_party = total - stdlib - unavailable
        
        def get_max_depth(node: Optional[DependencyNode]) -> int:
            if node is None:
                return 0
            if not node.children:
                return node.depth
            return max(get_max_depth(c) for c in node.children)
        
        result = DependencyTree(
            root_module=module_name,
            total_modules=total,
            stdlib_count=stdlib,
            third_party_count=third_party,
            local_count=0,  # Simplified
            unavailable_count=unavailable,
            max_depth=get_max_depth(tree),
            tree=tree,
            circular_dependencies=list(self._circular),
        )
        
        return result


def dependency_tree(
    module_name: str,
    max_depth: int = 3,
    include_stdlib: bool = True,
    include_third_party: bool = True,
    include_local: bool = True,
) -> DependencyTree:
    """
    Analyze a module's dependency tree.
    
    Args:
        module_name: Name of the module to analyze
        max_depth: Maximum depth to traverse (default: 3)
        include_stdlib: Include standard library modules (default: True)
        include_third_party: Include third-party packages (default: True)
        include_local: Include local modules (default: True)
        
    Returns:
        DependencyTree with analysis results
        
    Example:
        >>> import laziest_import as lz
        >>> tree = lz.dependency_tree('numpy', max_depth=2)
        >>> print(tree.total_modules)
        >>> tree.tree.to_dict()
    """
    analyzer = DependencyAnalyzer(
        max_depth=max_depth,
        include_stdlib=include_stdlib,
        include_third_party=include_third_party,
        include_local=include_local,
    )
    return analyzer.analyze(module_name)


def print_dependency_tree(tree: DependencyTree) -> None:
    """
    Print a formatted dependency tree.
    
    Args:
        tree: DependencyTree to print
    """
    print(f"\nDependency Tree: {tree.root_module}")
    print("=" * 50)
    print(f"Total modules: {tree.total_modules}")
    print(f"  - Stdlib: {tree.stdlib_count}")
    print(f"  - Third-party: {tree.third_party_count}")
    print(f"  - Unavailable: {tree.unavailable_count}")
    print(f"Max depth: {tree.max_depth}")
    
    if tree.circular_dependencies:
        print(f"\nCircular dependencies detected: {len(tree.circular_dependencies)}")
        for parent, child in tree.circular_dependencies[:5]:
            print(f"  {parent} -> {child}")
    
    if tree.tree:
        print("\nTree structure:")
        _print_tree_node(tree.tree, indent=0)


def _print_tree_node(node: DependencyNode, indent: int = 0) -> None:
    """Recursively print tree nodes."""
    prefix = "  " * indent + ("├── " if indent > 0 else "")
    
    type_str = ""
    if node.is_stdlib:
        type_str = " [stdlib]"
    elif node.is_third_party:
        type_str = " [third-party]"
    elif node.is_local:
        type_str = " [local]"
    
    version_str = f" ({node.version})" if node.version else ""
    available_str = " ⚠️" if not node.is_available else ""
    
    print(f"{prefix}{node.module_name}{type_str}{version_str}{available_str}")
    
    for child in node.children:
        _print_tree_node(child, indent + 1)
