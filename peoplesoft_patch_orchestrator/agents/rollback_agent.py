from __future__ import annotations

from peoplesoft_patch_orchestrator.agents.base import BaseAgent
from peoplesoft_patch_orchestrator.core.models import ExecutionContext, ExecutionStatus


class RollbackAgent(BaseAgent):
    name = "rollback"

    def execute(self, context: ExecutionContext, environment: str | None) -> tuple[ExecutionStatus, dict, list[str]]:
        if not environment:
            return ExecutionStatus.FAILED, {}, ["Environment required"]
        backup = context.metadata.get("backups", {}).get(environment)
        if not backup:
            return ExecutionStatus.FAILED, {}, ["No backup metadata available"]

        actions = [
            "stop_services",
            "restore_ps_home",
            "restore_ps_cfg_home",
            "restore_weblogic_config",
            "restore_tuxedo_config",
            "start_services",
            "post_restore_validation",
        ]
        return ExecutionStatus.SUCCESS, {"environment": environment, "backup": backup, "actions": actions}, []
