import importlib
import threading
from typing import Any, Dict

_LAZY_FUNCTION_REGISTRY: Dict[str, str] = {}
_RESOLVED: Dict[str, Any] = {}
_RESOLVED_LOCK = threading.Lock()

def register(name: str, module_path: str) -> None:
    if name not in _LAZY_FUNCTION_REGISTRY:
        _LAZY_FUNCTION_REGISTRY[name] = module_path

def resolve(name: str) -> Any:
    with _RESOLVED_LOCK:
        if name in _RESOLVED:
            return _RESOLVED[name]
    module_path = _LAZY_FUNCTION_REGISTRY.get(name)
    if module_path is None:
        raise KeyError(f"No lazy function registered for '{name}'")
    mod = importlib.import_module(module_path)
    fn = getattr(mod, name)
    with _RESOLVED_LOCK:
        _RESOLVED[name] = fn
    return fn

def has(name: str) -> bool:
    return name in _LAZY_FUNCTION_REGISTRY

def clear_resolved() -> None:
    with _RESOLVED_LOCK:
        _RESOLVED.clear()
