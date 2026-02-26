from __future__ import annotations

import hashlib
from pathlib import Path


def fingerprint_paths(paths: list[Path]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in paths:
        digest = hashlib.sha256()
        if path.is_file():
            digest.update(path.read_bytes())
            result[str(path)] = digest.hexdigest()
    return result
