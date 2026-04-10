"""Pre-analysis module for predicting required imports."""

from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import ast
from dataclasses import dataclass
from collections import defaultdict

from .._config import _ALIAS_MAP, _SYMBOL_CACHE
from .._alias import _build_known_modules_cache


@dataclass
class PreAnalysisResult:
    """Result of pre-analysis scan."""
    file_path: str
    predicted_imports: Set[str]
    used_symbols: Set[str]
    confidence: Dict[str, float]  # module -> confidence score


class DependencyPreAnalyzer:
    """
    Scan code files to predict required imports.
    
    Usage:
        analyzer = DependencyPreAnalyzer()
        result = analyzer.analyze_file('my_script.py')
        print(result.predicted_imports)  # {'numpy', 'pandas', ...}
    """
    
    def __init__(self):
        self._known_modules: Optional[Set[str]] = None
        self._alias_to_module: Dict[str, str] = {}
        self._module_aliases: Dict[str, Set[str]] = defaultdict(set)
        self._build_reverse_aliases()
    
    def _build_reverse_aliases(self) -> None:
        """Build reverse alias mapping."""
        for alias, module in _ALIAS_MAP.items():
            self._alias_to_module[alias] = module
            self._module_aliases[module].add(alias)
    
    def _get_known_modules(self) -> Set[str]:
        """Get or build known modules cache."""
        if self._known_modules is None:
            self._known_modules = _build_known_modules_cache()
        return self._known_modules
    
    def analyze_file(self, file_path: str) -> PreAnalysisResult:
        """
        Analyze a Python file to predict imports.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            PreAnalysisResult with predicted imports
        """
        path = Path(file_path)
        if not path.exists():
            return PreAnalysisResult(file_path, set(), set(), {})
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
        except (OSError, UnicodeDecodeError):
            return PreAnalysisResult(file_path, set(), set(), {})
        
        return self.analyze_source(source, file_path)
    
    def analyze_source(self, source: str, file_path: str = "<string>") -> PreAnalysisResult:
        """
        Analyze source code to predict imports.
        
        Args:
            source: Python source code
            file_path: Optional file path for reference
            
        Returns:
            PreAnalysisResult with predicted imports
        """
        predicted: Set[str] = set()
        used_symbols: Set[str] = set()
        confidence: Dict[str, float] = {}
        
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return PreAnalysisResult(file_path, predicted, used_symbols, confidence)
        
        # Collect all names used in the code
        visitor = _NameVisitor()
        visitor.visit(tree)
        
        known_modules = self._get_known_modules()
        
        # Analyze each name
        for name in visitor.names:
            used_symbols.add(name)
            
            # Check if it's a known alias
            if name in self._alias_to_module:
                module = self._alias_to_module[name]
                predicted.add(module)
                confidence[module] = confidence.get(module, 0.0) + 1.0
            # Check if it's a module name
            elif name in known_modules:
                predicted.add(name)
                confidence[name] = confidence.get(name, 0.0) + 0.8
            # Check symbol cache
            elif name in _SYMBOL_CACHE:
                for loc in _SYMBOL_CACHE[name][:3]:
                    module = loc[0].split('.')[0]
                    predicted.add(module)
                    confidence[module] = confidence.get(module, 0.0) + 0.5
        
        # Analyze attribute access patterns like "np.array"
        for obj, attr in visitor.attribute_accesses:
            if obj in self._alias_to_module:
                module = self._alias_to_module[obj]
                predicted.add(module)
                confidence[module] = confidence.get(module, 0.0) + 1.0
        
        # Analyze from imports
        for module in visitor.imported_modules:
            predicted.add(module)
            confidence[module] = 1.0
        
        # Normalize confidence scores
        max_conf = max(confidence.values()) if confidence else 1.0
        for module in confidence:
            confidence[module] = min(1.0, confidence[module] / max_conf)
        
        return PreAnalysisResult(file_path, predicted, used_symbols, confidence)
    
    def analyze_directory(
        self, 
        dir_path: str,
        recursive: bool = True,
        exclude: Optional[Set[str]] = None
    ) -> List[PreAnalysisResult]:
        """
        Analyze all Python files in a directory.
        
        Args:
            dir_path: Directory path
            recursive: Include subdirectories
            exclude: Set of directory/file names to exclude
            
        Returns:
            List of PreAnalysisResult for each file
        """
        exclude = exclude or {'__pycache__', '.git', '.venv', 'venv', 'node_modules'}
        results = []
        
        path = Path(dir_path)
        if not path.exists():
            return results
        
        pattern = '**/*.py' if recursive else '*.py'
        
        for py_file in path.glob(pattern):
            # Skip excluded paths
            if any(exc in py_file.parts for exc in exclude):
                continue
            results.append(self.analyze_file(str(py_file)))
        
        return results
    
    def get_preload_order(self, results: List[PreAnalysisResult]) -> List[str]:
        """
        Get optimal preload order based on analysis results.
        
        Args:
            results: List of analysis results
            
        Returns:
            List of module names in optimal load order
        """
        # Aggregate confidence scores
        total_confidence: Dict[str, float] = defaultdict(float)
        
        for result in results:
            for module, conf in result.confidence.items():
                total_confidence[module] += conf
        
        # Sort by confidence (highest first)
        sorted_modules = sorted(
            total_confidence.items(),
            key=lambda x: (-x[1], x[0])
        )
        
        return [module for module, _ in sorted_modules]


class _NameVisitor(ast.NodeVisitor):
    """AST visitor to collect names and attribute accesses."""
    
    def __init__(self):
        self.names: Set[str] = set()
        self.attribute_accesses: Set[Tuple[str, str]] = set()
        self.imported_modules: Set[str] = set()
    
    def visit_Name(self, node: ast.Name) -> None:
        self.names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name):
            self.attribute_accesses.add((node.value.id, node.attr))
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name
            self.names.add(name)
            self.imported_modules.add(alias.name.split('.')[0])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imported_modules.add(node.module.split('.')[0])
        for alias in node.names:
            name = alias.asname or alias.name
            self.names.add(name)
        self.generic_visit(node)
