from __future__ import annotations

import stat
import subprocess
import unittest

from ntt_learning.course import REPO_ROOT, REQUIRED_SCRIPT_NAMES


class RepoOpsTests(unittest.TestCase):
    def test_required_scripts_exist_and_are_executable(self) -> None:
        for script_name in REQUIRED_SCRIPT_NAMES:
            script_path = REPO_ROOT / "scripts" / script_name
            self.assertTrue(script_path.exists(), script_name)
            mode = script_path.stat().st_mode
            self.assertTrue(mode & stat.S_IXUSR, f"{script_name} is not executable")

    def test_status_commands_report_repo_state(self) -> None:
        for command in (
            ["bash", "scripts/app.sh", "status"],
            ["bash", "scripts/status.sh"],
        ):
            with self.subTest(command=" ".join(command)):
                completed = subprocess.run(
                    command,
                    cwd=REPO_ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertIn("repo_root=", completed.stdout)
                self.assertIn("notebooks_dir=", completed.stdout)


if __name__ == "__main__":
    unittest.main()
