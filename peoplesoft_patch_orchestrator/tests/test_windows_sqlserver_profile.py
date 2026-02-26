from __future__ import annotations

import os
import unittest
from pathlib import Path

from peoplesoft_patch_orchestrator.agents.env_agent import EnvironmentDiscoveryAgent
from peoplesoft_patch_orchestrator.agents.patch_agent import PatchApplicationAgent
from peoplesoft_patch_orchestrator.agents.validation_agent import ValidationAgent
from peoplesoft_patch_orchestrator.core.models import ExecutionContext, ExecutionStatus


class WindowsSqlServerProfileTests(unittest.TestCase):
    def test_windows_env_discovery_and_platform_plan(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        env_cfg = project_root / "configs" / "environments_windows_sqlserver.yaml"
        context = ExecutionContext(
            execution_id="test-win",
            patch_dir=project_root / "examples" / "patches" / "Jan2026",
            auto_approve=True,
            dry_run=True,
            simulation_mode=True,
            compliance_mode=True,
        )

        discovery = EnvironmentDiscoveryAgent(env_cfg)
        result = discovery.run(context, None)
        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(context.metadata["environments"][0]["platform"], "windows")
        self.assertEqual(context.metadata["environments"][0]["db_engine"], "sqlserver")

        patch = PatchApplicationAgent().run(context, "DEV")
        self.assertEqual(patch.status, ExecutionStatus.SUCCESS)
        self.assertEqual(patch.details["platform"], "windows")
        self.assertIn("apply_patch_windows.yaml", patch.details["ansible_playbook"])

        validation = ValidationAgent().run(context, "DEV")
        self.assertEqual(validation.status, ExecutionStatus.SUCCESS)
        self.assertEqual(validation.details["db_engine"], "sqlserver")

    def test_secret_ref_env_override_resolution(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        env_cfg = project_root / "configs" / "environments_windows_sqlserver.yaml"
        context = ExecutionContext(
            execution_id="test-secret-ref",
            patch_dir=project_root / "examples" / "patches" / "Jan2026",
            auto_approve=True,
            dry_run=True,
            simulation_mode=True,
            compliance_mode=True,
        )
        EnvironmentDiscoveryAgent(env_cfg).run(context, None)

        os.environ["PSFT_SECRET_REF"] = "oracle-wallet://global/default"
        os.environ["PSFT_SECRET_REF_DEV"] = "oracle-wallet://dev/override"
        try:
            patch = PatchApplicationAgent().run(context, "DEV")
            self.assertEqual(patch.details["secret_ref"], "oracle-wallet://dev/override")

            patch_test = PatchApplicationAgent().run(context, "TEST")
            self.assertEqual(patch_test.details["secret_ref"], "oracle-wallet://global/default")
        finally:
            os.environ.pop("PSFT_SECRET_REF", None)
            os.environ.pop("PSFT_SECRET_REF_DEV", None)


if __name__ == "__main__":
    unittest.main()
