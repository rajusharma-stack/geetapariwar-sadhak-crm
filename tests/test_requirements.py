import unittest
from pathlib import Path


class RequirementsTest(unittest.TestCase):
    def test_ttkbootstrap_is_declared(self):
        requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
        requirements = requirements_path.read_text(encoding="utf-8")
        self.assertRegex(requirements, r"(?m)^\s*ttkbootstrap\b")


if __name__ == "__main__":
    unittest.main()
