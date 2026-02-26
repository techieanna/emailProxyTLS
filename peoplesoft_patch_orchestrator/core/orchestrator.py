from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from peoplesoft_patch_orchestrator.agents.backup_agent import BackupSnapshotAgent
from peoplesoft_patch_orchestrator.agents.env_agent import EnvironmentDiscoveryAgent
from peoplesoft_patch_orchestrator.agents.intelligence_agent import PatchIntelligenceAgent
from peoplesoft_patch_orchestrator.agents.patch_agent import PatchApplicationAgent
from peoplesoft_patch_orchestrator.agents.policy_agent import PolicyEngineAgent
from peoplesoft_patch_orchestrator.agents.promotion_agent import PromotionAgent
from peoplesoft_patch_orchestrator.agents.reporting_agent import ReportingAgent
from peoplesoft_patch_orchestrator.agents.rollback_agent import RollbackAgent
from peoplesoft_patch_orchestrator.agents.validation_agent import ValidationAgent
from peoplesoft_patch_orchestrator.core.events import EventBus
from peoplesoft_patch_orchestrator.core.execution_engine import ExecutionEngine
from peoplesoft_patch_orchestrator.core.logging_utils import build_logger
from peoplesoft_patch_orchestrator.core.models import ExecutionContext, ExecutionEvent, ExecutionStatus
from peoplesoft_patch_orchestrator.core.observability import MetricsRegistry
from peoplesoft_patch_orchestrator.core.state_manager import StateManager


class MasterOrchestrator:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.logger = build_logger("orchestrator", base_dir / "logs" / "orchestrator.jsonl")
        self.state = StateManager(base_dir / "logs" / "state.db")
        self.engine = ExecutionEngine()
        self.metrics = MetricsRegistry(counters={})
        self.event_bus = EventBus()
        self.event_bus.subscribe("agent_completed", self._on_agent_completed)

        self.intelligence = PatchIntelligenceAgent()
        self.policy = PolicyEngineAgent(base_dir / "configs" / "policy.yaml")
        self.env_discovery = EnvironmentDiscoveryAgent(base_dir / "configs" / "environments.yaml")
        self.backup = BackupSnapshotAgent(base_dir / "logs" / "backups")
        self.patch = PatchApplicationAgent()
        self.validation = ValidationAgent()
        self.rollback = RollbackAgent()
        self.promotion = PromotionAgent()
        self.reporting = ReportingAgent(base_dir / "logs" / "reports")

    def run(self, patch_dir: Path, auto_approve: bool, dry_run: bool, simulation_mode: bool, compliance_mode: bool) -> int:
        context = ExecutionContext(
            execution_id=str(uuid.uuid4()),
            patch_dir=patch_dir,
            auto_approve=auto_approve,
            dry_run=dry_run,
            simulation_mode=simulation_mode,
            compliance_mode=compliance_mode,
        )

        if not self.state.acquire_lock(context.execution_id):
            self.logger.error("Patch lock is already held", extra={"context": {"execution_id": context.execution_id}})
            return 2

        try:
            for agent in [self.intelligence, self.policy, self.env_discovery]:
                result = agent.run(context=context, environment=None)
                self._record_outcome(context.execution_id, result, None)
                if result.status in {ExecutionStatus.FAILED, ExecutionStatus.SKIPPED}:
                    return 1

            self._export_execution_graph(context)

            for env in [entry["name"] for entry in context.metadata["environments"]]:
                env_status = self._run_environment_pipeline(context, env)
                if not env_status:
                    return 1

            final = self.reporting.run(context=context, environment=None)
            self._record_outcome(context.execution_id, final, None)

            metrics_file = self.base_dir / "logs" / f"metrics_{context.execution_id}.prom"
            metrics_file.write_text(self.metrics.export_prometheus(), encoding="utf-8")
            self.logger.info("Execution completed", extra={"context": {"execution_id": context.execution_id}})
            return 0
        finally:
            self.state.release_lock(context.execution_id)

    def _run_environment_pipeline(self, context: ExecutionContext, env: str) -> bool:
        for agent in [self.backup, self.patch, self.validation, self.promotion]:
            result = self.engine.execute_with_retry(agent, node=self._node(agent.name, env), context=context)
            self._record_outcome(context.execution_id, result, env)
            if result.status == ExecutionStatus.FAILED:
                rollback = self.rollback.run(context=context, environment=env)
                self._record_outcome(context.execution_id, rollback, env)
                return False
        return True

    def _record_outcome(self, execution_id: str, result, environment: str | None) -> None:
        self.state.record_result(execution_id, result)
        self.metrics.inc(f"agent_runs_total{{agent='{result.agent}',status='{result.status.value}'}}")
        event = ExecutionEvent(
            event_type="agent_completed",
            timestamp=datetime.now(timezone.utc).isoformat(),
            environment=environment,
            agent=result.agent,
            payload=result.details,
        )
        self.state.record_event(execution_id, event)
        self.event_bus.publish("agent_completed", {"execution_id": execution_id, "agent": result.agent, "environment": environment})

    @staticmethod
    def _node(agent: str, env: str):
        from peoplesoft_patch_orchestrator.core.models import DagNode

        return DagNode(id=f"{agent}:{env}", agent=agent, environment=env)

    def _export_execution_graph(self, context: ExecutionContext) -> None:
        graph = {
            "execution_id": context.execution_id,
            "nodes": context.metadata.get("execution_dag", []),
            "environments": [entry["name"] for entry in context.metadata.get("environments", [])],
        }
        out = self.base_dir / "logs" / f"graph_{context.execution_id}.json"
        out.write_text(json.dumps(graph, indent=2), encoding="utf-8")

    def _on_agent_completed(self, payload: dict) -> None:
        self.logger.info("Agent completed", extra={"context": payload})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PeopleSoft patch orchestration framework")
    parser.add_argument("--patch-dir", required=True, type=Path)
    parser.add_argument("--auto", action="store_true", help="Auto-approve medium severity patches")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--simulation-mode", action="store_true")
    parser.add_argument("--compliance-mode", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    orchestrator = MasterOrchestrator(base_dir=Path(__file__).resolve().parents[1])
    exit(orchestrator.run(args.patch_dir, args.auto, args.dry_run, args.simulation_mode, args.compliance_mode))


if __name__ == "__main__":
    main()
