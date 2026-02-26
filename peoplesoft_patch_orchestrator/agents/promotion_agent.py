from __future__ import annotations

from peoplesoft_patch_orchestrator.agents.base import BaseAgent
from peoplesoft_patch_orchestrator.core.models import ExecutionContext, ExecutionStatus


class PromotionAgent(BaseAgent):
    name = "promotion"

    def execute(self, context: ExecutionContext, environment: str | None) -> tuple[ExecutionStatus, dict, list[str]]:
        promotion_policy = context.metadata.get("policy", {}).get("promotion", {})
        wait_hours = promotion_policy.get("wait_hours_between_envs", 0)
        return ExecutionStatus.SUCCESS, {
            "current_environment": environment,
            "next_environment": self._next_env(environment),
            "wait_hours": wait_hours,
            "notify": promotion_policy.get("notify", []),
        }, []

    @staticmethod
    def _next_env(environment: str | None) -> str | None:
        order = ["DEV", "TEST", "UAT", "PRE-PROD"]
        if environment not in order:
            return None
        idx = order.index(environment)
        return order[idx + 1] if idx + 1 < len(order) else None
