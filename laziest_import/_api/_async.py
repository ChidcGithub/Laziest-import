from typing import Any

from .._async_ops import import_async, import_multiple_async


class AsyncNamespace:
    async def get(self, alias: str) -> Any:
        return await import_async(alias)

    async def fetch(self, *aliases: str) -> dict[str, Any]:
        return await import_multiple_async(list(aliases))

    def __repr__(self) -> str:
        return "<AsyncNamespace>"
