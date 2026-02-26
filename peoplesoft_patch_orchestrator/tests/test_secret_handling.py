from __future__ import annotations

import os
import stat
import unittest
from pathlib import Path

from peoplesoft_patch_orchestrator.core.secrets import ephemeral_response_file


class SecretHandlingTests(unittest.TestCase):
    def test_ephemeral_response_file_permissions_and_cleanup(self) -> None:
        payload = "PASSWORD=not-logged"
        path_str = None
        with ephemeral_response_file(payload) as resp_path:
            path_str = str(resp_path)
            self.assertTrue(resp_path.exists())
            mode = stat.S_IMODE(resp_path.stat().st_mode)
            self.assertEqual(mode, 0o600)
            self.assertIn("PASSWORD=not-logged", resp_path.read_text(encoding="utf-8"))

        self.assertIsNotNone(path_str)
        self.assertFalse(Path(path_str).exists())


if __name__ == "__main__":
    unittest.main()
