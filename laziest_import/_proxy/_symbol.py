"""
LazySymbol class for lazy loading symbols (classes/functions).
"""

from typing import Any
import logging
import importlib

from .._config import (
    _DEBUG_MODE,
    _IMPORT_STATS,
    _SYMBOL_CACHE,
)


class LazySymbol:
    """
    Lazy loading symbol proxy class.
    
    Imports the actual symbol (class/function) from a module when accessed.
    Supports transparent usage as the underlying class/function.
    """
    
    __slots__ = ('_symbol_name', '_module_name', '_symbol_type', '_cached_obj', '_loaded')
    
    def __init__(self, symbol_name: str, module_name: str, symbol_type: str = 'class'):
        object.__setattr__(self, '_symbol_name', symbol_name)
        object.__setattr__(self, '_module_name', module_name)
        object.__setattr__(self, '_symbol_type', symbol_type)
        object.__setattr__(self, '_cached_obj', None)
        object.__setattr__(self, '_loaded', False)
    
    def _get_object(self) -> Any:
        """Get the actual symbol object (lazy load)."""
        cached = object.__getattribute__(self, '_cached_obj')
        if cached is not None:
            return cached
        
        symbol_name = object.__getattribute__(self, '_symbol_name')
        module_name = object.__getattribute__(self, '_module_name')
        
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            raise ImportError(
                f"Cannot import module '{module_name}' for symbol '{symbol_name}': {e}"
            ) from e
        
        obj = getattr(module, symbol_name, None)
        if obj is None:
            raise AttributeError(
                f"Module '{module_name}' has no attribute '{symbol_name}'"
            )
        
        object.__setattr__(self, '_cached_obj', obj)
        object.__setattr__(self, '_loaded', True)
        
        if symbol_name not in _SYMBOL_CACHE:
            _SYMBOL_CACHE[symbol_name] = []
        
        _IMPORT_STATS.total_imports += 1
        _IMPORT_STATS.module_access_counts[module_name] = _IMPORT_STATS.module_access_counts.get(module_name, 0) + 1
        
        if _DEBUG_MODE:
            logging.info(
                f"[laziest-import] Loaded symbol '{symbol_name}' from '{module_name}'"
            )
        
        return obj
    
    def __getattr__(self, name: str) -> Any:
        obj = self._get_object()
        return getattr(obj, name)
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            obj = self._get_object()
            setattr(obj, name, value)
    
    def __call__(self, *args, **kwargs) -> Any:
        obj = self._get_object()
        if not callable(obj):
            raise TypeError(f"'{self._symbol_name}' object is not callable")
        return obj(*args, **kwargs)
    
    def __repr__(self) -> str:
        loaded = object.__getattribute__(self, '_loaded')
        symbol_name = object.__getattribute__(self, '_symbol_name')
        module_name = object.__getattribute__(self, '_module_name')
        symbol_type = object.__getattribute__(self, '_symbol_type')
        
        if loaded:
            obj = object.__getattribute__(self, '_cached_obj')
            return f"<LazySymbol {symbol_type} '{symbol_name}' from '{module_name}' (loaded: {obj})>"
        return f"<LazySymbol {symbol_type} '{symbol_name}' from '{module_name}' (not loaded)>"
    
    def __str__(self) -> str:
        obj = self._get_object()
        return str(obj)
    
    def get_underlying_class(self) -> type:
        """Get the underlying class object.
        
        Use this for isinstance checks:
            lazy_class = LazySymbol('DataFrame', 'pandas')
            df = lazy_class()
            assert isinstance(df, lazy_class.get_underlying_class())
        
        Note: Direct isinstance(obj, lazy_class) won't work because
        LazySymbol is not a metaclass. Use get_underlying_class() instead.
        """
        obj = self._get_object()
        return obj if isinstance(obj, type) else type(obj)
    
    def __origin__(self) -> Any:
        obj = self._get_object()
        return getattr(obj, '__origin__', obj)
    
    def __args__(self) -> tuple:
        obj = self._get_object()
        return getattr(obj, '__args__', ())
    
    def __enter__(self):
        obj = self._get_object()
        return obj.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        obj = self._get_object()
        return obj.__exit__(exc_type, exc_val, exc_tb)
    
    async def __aenter__(self):
        obj = self._get_object()
        return await obj.__aenter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        obj = self._get_object()
        return await obj.__aexit__(exc_type, exc_val, exc_tb)
    
    def __iter__(self):
        obj = self._get_object()
        return iter(obj)
    
    def __next__(self):
        obj = self._get_object()
        return next(obj)
    
    def __aiter__(self):
        obj = self._get_object()
        return obj.__aiter__()
    
    async def __anext__(self):
        obj = self._get_object()
        return await obj.__anext__()
    
    def __get__(self, obj, objtype=None):
        underlying = self._get_object()
        if hasattr(underlying, '__get__'):
            return underlying.__get__(obj, objtype)
        return underlying
    
    # Arithmetic operators
    def __add__(self, other): return self._get_object() + other
    def __sub__(self, other): return self._get_object() - other
    def __mul__(self, other): return self._get_object() * other
    def __truediv__(self, other): return self._get_object() / other
    def __floordiv__(self, other): return self._get_object() // other
    def __mod__(self, other): return self._get_object() % other
    def __pow__(self, other): return self._get_object() ** other
    def __matmul__(self, other): return self._get_object() @ other
    
    # Comparison operators
    def __eq__(self, other): return self._get_object() == other
    def __ne__(self, other): return self._get_object() != other
    def __lt__(self, other): return self._get_object() < other
    def __le__(self, other): return self._get_object() <= other
    def __gt__(self, other): return self._get_object() > other
    def __ge__(self, other): return self._get_object() >= other
    
    # Indexing
    def __getitem__(self, key): return self._get_object()[key]
    def __setitem__(self, key, value): self._get_object()[key] = value
    def __delitem__(self, key): del self._get_object()[key]
    
    # Length
    def __len__(self): return len(self._get_object())
    
    # Boolean
    def __bool__(self): return bool(self._get_object())
    
    # Hash
    def __hash__(self): return hash(self._get_object())
    
    # Generic type support (PEP 560)
    @classmethod
    def __class_getitem__(cls, item):
        """Support for generic type hints like List[LazySymbol].
        
        This allows LazySymbol to be used in type annotations:
            from typing import List
            df_list: List[DataFrame] = []  # Where DataFrame is a LazySymbol
        
        Note: This returns a proper GenericAlias for type hint purposes.
        The actual type checking will be done against the underlying class
        when it's loaded.
        """
        # Normalize item to a tuple
        if not isinstance(item, tuple):
            item = (item,)
        
        try:
            from types import GenericAlias
            return GenericAlias(cls, item)
        except ImportError:
            # Fallback for Python < 3.9: create a simple wrapper
            # that mimics GenericAlias behavior for type hints
            class _LazyGenericAlias:
                __slots__ = ('_origin', '_args')
                
                def __init__(self, origin, args):
                    object.__setattr__(self, '_origin', origin)
                    object.__setattr__(self, '_args', args)
                
                def __repr__(self):
                    args_str = ', '.join(repr(a) for a in self._args)
                    return f"{self._origin.__name__}[{args_str}]"
                
                def __str__(self):
                    args_str = ', '.join(str(a) for a in self._args)
                    return f"{self._origin.__name__}[{args_str}]"
                
                def __eq__(self, other):
                    if isinstance(other, _LazyGenericAlias):
                        return self._origin == other._origin and self._args == other._args
                    return NotImplemented
                
                def __hash__(self):
                    return hash((self._origin, self._args))
                
                def __getitem__(self, inner_item):
                    # Support nested generics like List[List[DataFrame]]
                    if not isinstance(inner_item, tuple):
                        inner_item = (inner_item,)
                    return _LazyGenericAlias(self._origin, self._args + inner_item)
            
            return _LazyGenericAlias(cls, item)
