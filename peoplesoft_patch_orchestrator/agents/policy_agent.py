from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from peoplesoft_patch_orchestrator.agents.base import BaseAgent
from peoplesoft_patch_orchestrator.core.models import DagNode, ExecutionContext, ExecutionStatus


class PolicyEngineAgent(BaseAgent):
    name = "policy_engine"

    def __init__(self, policy_path: Path) -> None:
        self.policy_path = policy_path

    def execute(self, context: ExecutionContext, environment: str | None) -> tuple[ExecutionStatus, dict, list[str]]:
        policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        context.metadata["policy"] = policy
        manifest = context.metadata.get("manifest", {})
        threshold = policy["auto_apply"]["minimum_severity"]
        requires_approval = manifest.get("severity") not in threshold
        plan = {
            "requires_approval": requires_approval and not context.auto_approve,
            "maintenance_window_enforced": policy.get("maintenance_windows", {}).get("enforced", True),
            "rollback_triggers": policy.get("rollback", {}).get("triggers", []),
            "promotion": policy.get("promotion", {}),
        }
        dag = [
            DagNode(id="intelligence", agent="patch_intelligence", environment=None),
            DagNode(id="policy", agent="policy_engine", environment=None, depends_on=["intelligence"]),
        ]
        context.metadata["execution_dag"] = [asdict(node) for node in dag]
        context.metadata["policy_plan"] = plan
        if plan["requires_approval"]:
            return ExecutionStatus.SKIPPED, plan, ["Policy requires manual approval"]
        return ExecutionStatus.SUCCESS, plan, []
