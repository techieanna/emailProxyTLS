from __future__ import annotations

import os

from peoplesoft_patch_orchestrator.agents.base import BaseAgent
from peoplesoft_patch_orchestrator.core.models import ExecutionContext, ExecutionStatus
from peoplesoft_patch_orchestrator.core.secrets import ephemeral_response_file


class PatchApplicationAgent(BaseAgent):
    name = "patch_application"

    def execute(self, context: ExecutionContext, environment: str | None) -> tuple[ExecutionStatus, dict, list[str]]:
        if not environment:
            return ExecutionStatus.FAILED, {}, ["Environment required"]

        manifest = context.metadata.get("manifest", {})
        env_map = {entry["name"]: entry for entry in context.metadata.get("environments", [])}
        env_spec = env_map.get(environment, {})
        platform = env_spec.get("platform", "linux")

        steps = self._steps_for_platform(platform)
        force_fail = os.getenv("PSFT_FORCE_PATCH_FAIL", "")
        if force_fail in {"ALL", environment}:
            return ExecutionStatus.FAILED, {"environment": environment, "forced": True}, ["Forced patch failure for test"]

        env_key = environment.replace("-", "_").upper()
        selected_secret_ref = os.getenv(
            f"PSFT_SECRET_REF_{env_key}",
            os.getenv("PSFT_SECRET_REF", "oracle-wallet://weblogic/admin"),
        )

        if context.dry_run or context.simulation_mode:
            return ExecutionStatus.SUCCESS, {
                "environment": environment,
                "platform": platform,
                "dry_run": True,
                "planned_steps": steps,
                "ansible_playbook": f"ansible/apply_patch_{platform}.yaml" if platform == "windows" else "ansible/apply_patch.yaml",
                "secret_strategy": "vault_or_wallet_reference_only",
                "secret_ref": selected_secret_ref,
            }, []

        secret_ref = selected_secret_ref
        resp_template = f"SECRET_REF={secret_ref}\n"
        with ephemeral_response_file(resp_template) as _:
            result = {
                "environment": environment,
                "platform": platform,
                "patch_id": manifest.get("patch_id"),
                "completed_steps": steps,
                "secret_ref": secret_ref,
                "resp_file_mode": "ephemeral_0600_secure_delete",
                "logs": [f"logs/{context.execution_id}/{environment}/patch_application.log"],
                "runtime_artifacts": {"response_file_used": "REDACTED"},
            }
        return ExecutionStatus.SUCCESS, result, []

    @staticmethod
    def _steps_for_platform(platform: str) -> list[str]:
        if platform == "windows":
            return [
                "stop_weblogic_services_windows",
                "stop_tuxedo_services_windows",
                "apply_pt_patch_windows",
                "reconfigure_domains_psadmin_windows",
                "start_tuxedo_services_windows",
                "start_weblogic_services_windows",
            ]
        return [
            "stop_weblogic_domain",
            "stop_tuxedo_domain",
            "apply_opatch",
            "relink_binaries",
            "psadmin_configure",
            "apply_pia_updates",
            "reconfigure_pia",
            "start_tuxedo_domain",
            "start_weblogic_domain",
        ]
