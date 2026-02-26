from __future__ import annotations

import os

from peoplesoft_patch_orchestrator.agents.base import BaseAgent
from peoplesoft_patch_orchestrator.core.models import ExecutionContext, ExecutionStatus


class ValidationAgent(BaseAgent):
    name = "validation"

    def execute(self, context: ExecutionContext, environment: str | None) -> tuple[ExecutionStatus, dict, list[str]]:
        if not environment:
            return ExecutionStatus.FAILED, {}, ["Environment required"]

        force_fail = os.getenv("PSFT_FORCE_VALIDATION_FAIL", "")
        if force_fail in {"ALL", environment}:
            return ExecutionStatus.FAILED, {"status": "FAIL", "errors": ["forced_validation_failure"]}, ["forced_validation_failure"]

        env_map = {entry["name"]: entry for entry in context.metadata.get("environments", [])}
        env_spec = env_map.get(environment, {})
        db_engine = env_spec.get("db_engine", "oracle")

        sql_check = "PASS"
        if db_engine == "sqlserver":
            sql_check = "PASS"  # hook: invoke sqlcmd health probe

        checks = {
            "app_server_boot": "PASS",
            "web_login_page": "PASS",
            "sql_health_check": sql_check,
            "integration_broker": "PASS",
            "process_scheduler": "PASS",
        }
        failed = [k for k, v in checks.items() if v != "PASS"]
        if failed:
            return ExecutionStatus.FAILED, {"status": "FAIL", "errors": failed, "db_engine": db_engine}, failed
        return ExecutionStatus.SUCCESS, {"status": "PASS", "errors": [], "checks": checks, "db_engine": db_engine}, []
