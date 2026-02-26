from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Protocol

from .models import AgentResult, DagNode, ExecutionContext, ExecutionStatus


class Agent(Protocol):
    name: str

    def run(self, context: ExecutionContext, environment: str | None) -> AgentResult:
        ...


class ExecutionEngine:
    def __init__(self, max_backoff_seconds: int = 120) -> None:
        self.max_backoff_seconds = max_backoff_seconds

    def execute_with_retry(self, agent: Agent, node: DagNode, context: ExecutionContext) -> AgentResult:
        attempt = 0
        while attempt <= node.retry_limit:
            attempt += 1
            result = agent.run(context=context, environment=node.environment)
            if result.status == ExecutionStatus.SUCCESS:
                return result
            if attempt <= node.retry_limit:
                backoff = min(self.max_backoff_seconds, (2 ** attempt) + random.random())
                time.sleep(backoff)
        return result

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()
