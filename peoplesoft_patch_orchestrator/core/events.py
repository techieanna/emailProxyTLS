from __future__ import annotations

from collections import defaultdict
from typing import Callable


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Callable[[dict], None]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[[dict], None]) -> None:
        self._subs[event_name].append(callback)

    def publish(self, event_name: str, payload: dict) -> None:
        for callback in self._subs[event_name]:
            callback(payload)
