from __future__ import annotations

import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path


class SecretHandlingError(RuntimeError):
    """Raised when secret material cannot be handled safely."""


@contextmanager
def ephemeral_response_file(content: str, suffix: str = ".resp"):
    """
    Create a response file in tmpfs-friendly location with 0600 permissions,
    then securely remove it on exit.
    """
    fd, path = tempfile.mkstemp(prefix="psft_", suffix=suffix, dir="/dev/shm" if Path("/dev/shm").exists() else None)
    try:
        os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        file_mode = stat.S_IMODE(os.stat(path).st_mode)
        if file_mode != 0o600:
            raise SecretHandlingError(f"Response file permissions are not strict enough: {oct(file_mode)}")

        yield Path(path)
    finally:
        _secure_delete(Path(path))


def _secure_delete(path: Path) -> None:
    if not path.exists():
        return
    try:
        size = path.stat().st_size
        with path.open("r+b") as handle:
            handle.write(b"\x00" * size)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        path.unlink(missing_ok=True)
