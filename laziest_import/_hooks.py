from typing import Callable

from ._config import _PRE_IMPORT_HOOKS, _POST_IMPORT_HOOKS


def add_pre_import_hook(hook: Callable) -> None:
    _PRE_IMPORT_HOOKS.append(hook)


def add_post_import_hook(hook: Callable) -> None:
    _POST_IMPORT_HOOKS.append(hook)


def remove_pre_import_hook(hook: Callable) -> bool:
    if hook in _PRE_IMPORT_HOOKS:
        _PRE_IMPORT_HOOKS.remove(hook)
        return True
    return False


def remove_post_import_hook(hook: Callable) -> bool:
    if hook in _POST_IMPORT_HOOKS:
        _POST_IMPORT_HOOKS.remove(hook)
        return True
    return False


def clear_import_hooks() -> None:
    _PRE_IMPORT_HOOKS.clear()
    _POST_IMPORT_HOOKS.clear()
