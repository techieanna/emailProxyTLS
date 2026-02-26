from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from peoplesoft_patch_orchestrator.agents.base import BaseAgent
from peoplesoft_patch_orchestrator.core.models import ExecutionContext, ExecutionStatus


class BackupSnapshotAgent(BaseAgent):
    name = "backup_snapshot"

    def __init__(self, backup_root: Path) -> None:
        self.backup_root = backup_root

    def execute(self, context: ExecutionContext, environment: str | None) -> tuple[ExecutionStatus, dict, list[str]]:
        if not environment:
            return ExecutionStatus.FAILED, {}, ["Environment required"]
        now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = self.backup_root / environment / now
        backup_path.mkdir(parents=True, exist_ok=True)

        metadata = {
            "env": environment,
            "timestamp": now,
            "backup_path": str(backup_path),
            "artifacts": ["PS_HOME", "PS_CFG_HOME", "weblogic", "tuxedo", "integration_gateway"],
        }
        digest = hashlib.sha256(str(metadata).encode("utf-8")).hexdigest()
        metadata["checksum"] = digest
        context.metadata.setdefault("backups", {})[environment] = metadata
        return ExecutionStatus.SUCCESS, metadata, []
