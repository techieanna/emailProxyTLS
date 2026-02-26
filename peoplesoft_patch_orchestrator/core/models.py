from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    OPTIONAL = "OPTIONAL"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass(slots=True)
class PatchManifest:
    patch_id: str
    cvss_score: float
    severity: Severity
    components: list[str]
    requires_db_changes: bool
    source_path: Path
    cves: list[str] = field(default_factory=list)
    checksums: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class EnvironmentSpec:
    name: str
    order: int
    hosts: list[str]
    ps_home: str
    ps_cfg_home: str
    tuxedo_domain: str
    weblogic_domain: str
    peopletools_version: str
    maintenance_window: str


@dataclass(slots=True)
class ExecutionEvent:
    event_type: str
    timestamp: str
    environment: str | None
    agent: str
    payload: dict[str, Any]


@dataclass(slots=True)
class AgentResult:
    agent: str
    environment: str | None
    status: ExecutionStatus
    started_at: str
    completed_at: str
    details: dict[str, Any]
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExecutionContext:
    execution_id: str
    patch_dir: Path
    auto_approve: bool
    dry_run: bool
    simulation_mode: bool
    compliance_mode: bool
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DagNode:
    id: str
    agent: str
    environment: str | None
    depends_on: list[str] = field(default_factory=list)
    retry_limit: int = 2
