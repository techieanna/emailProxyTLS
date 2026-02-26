from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class MetricsRegistry:
    counters: Dict[str, int]

    def inc(self, key: str, amount: int = 1) -> None:
        self.counters[key] = self.counters.get(key, 0) + amount

    def export_prometheus(self) -> str:
        lines = []
        for key, value in sorted(self.counters.items()):
            lines.append(f"# TYPE {key} counter")
            lines.append(f"{key} {value}")
        return "\n".join(lines) + "\n"
