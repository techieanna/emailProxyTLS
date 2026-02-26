from __future__ import annotations

import json
from pathlib import Path

from peoplesoft_patch_orchestrator.agents.base import BaseAgent
from peoplesoft_patch_orchestrator.core.models import ExecutionContext, ExecutionStatus


class EnvironmentDiscoveryAgent(BaseAgent):
    name = "environment_discovery"

    def __init__(self, env_path: Path) -> None:
        self.env_path = env_path

    def execute(self, context: ExecutionContext, environment: str | None) -> tuple[ExecutionStatus, dict, list[str]]:
        env_cfg = json.loads(self.env_path.read_text(encoding="utf-8"))
        envs = env_cfg["environments"]
        compatible = []
        errors: list[str] = []
        for env in envs:
            platform = env.get("platform", "linux").lower()
            db_engine = env.get("db_engine", "oracle").lower()

            if platform not in {"linux", "windows"}:
                errors.append(f"Unsupported platform for {env['name']}: {platform}")
                continue
            if db_engine not in {"oracle", "sqlserver"}:
                errors.append(f"Unsupported db_engine for {env['name']}: {db_engine}")
                continue
            if not env.get("peopletools_version", "").startswith("8.5"):
                errors.append(f"Unsupported PeopleTools version for {env['name']}")
                continue

            compatible.append(
                {
                    "name": env["name"],
                    "platform": platform,
                    "db_engine": db_engine,
                    "ps_home": env["ps_home"],
                    "ps_cfg_home": env["ps_cfg_home"],
                    "tuxedo_domain": env["tuxedo_domain"],
                    "weblogic_domain": env["weblogic_domain"],
                    "admin_host": env.get("admin_host", ""),
                }
            )

        if errors:
            return ExecutionStatus.FAILED, {"environments": compatible}, errors

        context.metadata["environments"] = compatible
        return ExecutionStatus.SUCCESS, {"environments": compatible}, []
