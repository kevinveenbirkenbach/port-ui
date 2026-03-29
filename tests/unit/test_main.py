import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import main as portfolio_main


class TestMainCli(unittest.TestCase):
    def test_load_targets_parses_help_comments(self):
        makefile_content = """
.PHONY: foo bar
foo:
\t# Run foo
\t@echo foo

bar:
\t@echo bar
""".lstrip()

        with TemporaryDirectory() as temp_dir:
            makefile_path = Path(temp_dir) / "Makefile"
            makefile_path.write_text(makefile_content, encoding="utf-8")

            targets = portfolio_main.load_targets(makefile_path)

        self.assertEqual(targets, [("foo", "Run foo"), ("bar", "")])

    @patch("main.subprocess.check_call")
    def test_run_command_executes_subprocess(self, mock_check_call):
        portfolio_main.run_command(["make", "lint"])

        mock_check_call.assert_called_once_with(["make", "lint"])

    @patch("main.sys.exit", side_effect=SystemExit(7))
    @patch(
        "main.subprocess.check_call",
        side_effect=subprocess.CalledProcessError(7, ["make", "lint"]),
    )
    def test_run_command_exits_with_subprocess_return_code(
        self,
        _mock_check_call,
        mock_sys_exit,
    ):
        with self.assertRaises(SystemExit) as context:
            portfolio_main.run_command(["make", "lint"])

        self.assertEqual(context.exception.code, 7)
        mock_sys_exit.assert_called_once_with(7)

    @patch("main.run_command")
    @patch("main.load_targets", return_value=[("lint", "Run lint suite")])
    def test_main_dispatches_selected_target(
        self, _mock_load_targets, mock_run_command
    ):
        with patch("sys.argv", ["main.py", "lint"]):
            portfolio_main.main()

        mock_run_command.assert_called_once_with(["make", "lint"], dry_run=False)

    @patch("main.run_command")
    @patch("main.load_targets", return_value=[("lint", "Run lint suite")])
    def test_main_passes_dry_run_flag(self, _mock_load_targets, mock_run_command):
        with patch("sys.argv", ["main.py", "--dry-run", "lint"]):
            portfolio_main.main()

        mock_run_command.assert_called_once_with(["make", "lint"], dry_run=True)


if __name__ == "__main__":
    unittest.main()
