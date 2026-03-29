import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from utils import check_hadolint_sarif


class TestCheckHadolintSarif(unittest.TestCase):
    def test_main_returns_zero_for_clean_sarif(self):
        sarif_payload = {
            "runs": [
                {
                    "results": [],
                }
            ]
        }

        with TemporaryDirectory() as temp_dir:
            sarif_path = Path(temp_dir) / "clean.sarif"
            sarif_path.write_text(json.dumps(sarif_payload), encoding="utf-8")

            exit_code = check_hadolint_sarif.main([str(sarif_path)])

        self.assertEqual(exit_code, 0)

    def test_main_returns_one_for_warnings_or_errors(self):
        sarif_payload = {
            "runs": [
                {
                    "results": [
                        {"level": "warning"},
                        {"level": "error"},
                    ],
                }
            ]
        }

        with TemporaryDirectory() as temp_dir:
            sarif_path = Path(temp_dir) / "warnings.sarif"
            sarif_path.write_text(json.dumps(sarif_payload), encoding="utf-8")

            exit_code = check_hadolint_sarif.main([str(sarif_path)])

        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
