from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from peoplesoft_patch_orchestrator.core.orchestrator import MasterOrchestrator


class OrchestratorSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = Path(__file__).resolve().parents[1]
        self.patch_dir = self.project_root / "examples" / "patches" / "Jan2026"

    def test_dry_run_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._copy_runtime_tree(base)
            orchestrator = MasterOrchestrator(base_dir=base)
            code = orchestrator.run(
                patch_dir=self.patch_dir,
                auto_approve=True,
                dry_run=True,
                simulation_mode=True,
                compliance_mode=True,
            )
            self.assertEqual(code, 0)

    def test_validation_failure_triggers_rollback(self) -> None:
        os.environ["PSFT_FORCE_VALIDATION_FAIL"] = "DEV"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                self._copy_runtime_tree(base)
                orchestrator = MasterOrchestrator(base_dir=base)
                code = orchestrator.run(
                    patch_dir=self.patch_dir,
                    auto_approve=True,
                    dry_run=True,
                    simulation_mode=True,
                    compliance_mode=False,
                )
                self.assertEqual(code, 1)
                # state db should exist and include rollback records
                self.assertTrue((base / "logs" / "state.db").exists())
        finally:
            os.environ.pop("PSFT_FORCE_VALIDATION_FAIL", None)

    def _copy_runtime_tree(self, base: Path) -> None:
        (base / "configs").mkdir(parents=True, exist_ok=True)
        (base / "logs").mkdir(parents=True, exist_ok=True)
        (base / "configs" / "policy.yaml").write_text(
            (self.project_root / "configs" / "policy.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (base / "configs" / "environments.yaml").write_text(
            (self.project_root / "configs" / "environments.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
