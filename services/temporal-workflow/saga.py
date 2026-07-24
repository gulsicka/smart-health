from typing import Callable, Awaitable


class Saga:
    def __init__(self) -> None:
        self._compensations: list[Callable[[], Awaitable[None]]] = []

    def add_compensation(self, fn: Callable[[], Awaitable[None]]) -> None:
        self._compensations.append(fn)

    async def compensate(self) -> None:
        for fn in reversed(self._compensations):
            try:
                await fn()
            except Exception as e:
                print(f"[Saga] Compensation step failed: {e}")
