from __future__ import annotations

import json
from pathlib import Path

from peoplesoft_patch_orchestrator.agents.base import BaseAgent
from peoplesoft_patch_orchestrator.core.models import ExecutionContext, ExecutionStatus


class ReportingAgent(BaseAgent):
    name = "reporting"

    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root

    def execute(self, context: ExecutionContext, environment: str | None) -> tuple[ExecutionStatus, dict, list[str]]:
        self.output_root.mkdir(parents=True, exist_ok=True)
        report = {
            "execution_id": context.execution_id,
            "manifest": context.metadata.get("manifest", {}),
            "policy_plan": context.metadata.get("policy_plan", {}),
            "environments": context.metadata.get("environments", []),
            "backups": context.metadata.get("backups", {}),
        }
        json_file = self.output_root / f"{context.execution_id}.json"
        html_file = self.output_root / f"{context.execution_id}.html"
        json_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        html_file.write_text(self._to_html(report), encoding="utf-8")
        return ExecutionStatus.SUCCESS, {"json": str(json_file), "html": str(html_file)}, []

    @staticmethod
    def _to_html(report: dict) -> str:
        return f"""<html><body><h1>PeopleSoft Patch Report</h1><pre>{json.dumps(report, indent=2)}</pre></body></html>"""
