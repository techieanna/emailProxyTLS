from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from peoplesoft_patch_orchestrator.agents.base import BaseAgent
from peoplesoft_patch_orchestrator.core.models import ExecutionContext, ExecutionStatus, Severity


class PatchIntelligenceAgent(BaseAgent):
    name = "patch_intelligence"

    def execute(self, context: ExecutionContext, environment: str | None) -> tuple[ExecutionStatus, dict, list[str]]:
        patch_readme = next(context.patch_dir.glob("README*"), None)
        if not patch_readme:
            return ExecutionStatus.FAILED, {}, ["Patch README not found"]

        readme_text = patch_readme.read_text(encoding="utf-8", errors="ignore")
        cvss_score = self._extract_cvss(readme_text)
        patch_id = self._extract_patch_id(readme_text) or context.patch_dir.name
        cves = sorted(set(re.findall(r"CVE-\d{4}-\d{4,7}", readme_text, flags=re.IGNORECASE)))
        components = self._infer_components(readme_text)

        severity = Severity.OPTIONAL
        if cvss_score >= 9:
            severity = Severity.CRITICAL
        elif cvss_score >= 7:
            severity = Severity.HIGH

        checksums = {
            file.name: self._sha256(file)
            for file in context.patch_dir.iterdir()
            if file.is_file()
        }

        manifest = {
            "patch_id": patch_id,
            "cvss_score": cvss_score,
            "severity": severity.value,
            "components": components,
            "requires_db_changes": "datapatch" in readme_text.lower() or "sql" in readme_text.lower(),
            "cves": cves,
            "checksums": checksums,
        }
        context.metadata["manifest"] = manifest
        (context.patch_dir / "manifest.generated.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return ExecutionStatus.SUCCESS, manifest, []

    @staticmethod
    def _extract_cvss(readme: str) -> float:
        matches = re.findall(r"CVSS\s*(?:v3(?:\.1)?)?\s*[:=]\s*(\d+(?:\.\d+)?)", readme, flags=re.IGNORECASE)
        if matches:
            return max(float(x) for x in matches)
        return 0.0

    @staticmethod
    def _extract_patch_id(readme: str) -> str | None:
        found = re.search(r"Patch\s*(?:ID|Number)?\s*[:=]\s*(\d{6,})", readme, flags=re.IGNORECASE)
        return found.group(1) if found else None

    @staticmethod
    def _infer_components(readme: str) -> list[str]:
        components: list[str] = []
        lower = readme.lower()
        if "peopletools" in lower:
            components.append("PeopleTools")
        if "weblogic" in lower or "pia" in lower:
            components.append("WebLogic")
        if "tuxedo" in lower:
            components.append("Tuxedo")
        if "oracle database" in lower or "db" in lower:
            components.append("Database")
        return components or ["PeopleTools"]

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
