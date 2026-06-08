import logging
from collections.abc import Iterator
from typing import Any, Callable, List

from .. import _config


class HookList:
    def __init__(self, hook_list: list[Callable]) -> None:
        self._hooks = hook_list

    def add(self, callback: Callable) -> None:
        if callback not in self._hooks:
            self._hooks.append(callback)

    def remove(self, callback: Callable) -> bool:
        try:
            self._hooks.remove(callback)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        self._hooks.clear()

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        for hook in list(self._hooks):
            try:
                hook(*args, **kwargs)
            except Exception as e:
                logging.warning(f"Hook '{hook.__name__}' raised: {e}")

    def __iadd__(self, callback: Callable) -> "HookList":
        self.add(callback)
        return self

    def __isub__(self, callback: Callable) -> "HookList":
        self.remove(callback)
        return self

    def __len__(self) -> int:
        return len(self._hooks)

    def __iter__(self) -> Iterator[Callable]:
        return iter(self._hooks)

    def __repr__(self) -> str:
        return f"HookList(hooks={len(self._hooks)})"


class HookNamespace:
    @property
    def pre(self) -> HookList:
        return HookList(_config._PRE_IMPORT_HOOKS)

    @property
    def post(self) -> HookList:
        return HookList(_config._POST_IMPORT_HOOKS)

    def clear(self) -> None:
        _config._PRE_IMPORT_HOOKS.clear()
        _config._POST_IMPORT_HOOKS.clear()

    def __repr__(self) -> str:
        return (
            f"<HookNamespace: pre={len(_config._PRE_IMPORT_HOOKS)}, "
            f"post={len(_config._POST_IMPORT_HOOKS)}>"
        )
