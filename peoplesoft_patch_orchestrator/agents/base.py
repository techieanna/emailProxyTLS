from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from peoplesoft_patch_orchestrator.core.models import AgentResult, ExecutionContext, ExecutionStatus


class BaseAgent(ABC):
    name = "base"

    @abstractmethod
    def execute(self, context: ExecutionContext, environment: str | None) -> tuple[ExecutionStatus, dict, list[str]]:
        ...

    def run(self, context: ExecutionContext, environment: str | None) -> AgentResult:
        started_at = datetime.now(timezone.utc).isoformat()
        status, details, errors = self.execute(context=context, environment=environment)
        completed_at = datetime.now(timezone.utc).isoformat()
        return AgentResult(
            agent=self.name,
            environment=environment,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            details=details,
            errors=errors,
        )
