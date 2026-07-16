import unittest
from services.prn_service import PrnResult, _clean_phone, _select_best_prn_result


class PrnServiceTests(unittest.TestCase):
    def test_clean_phone_strips_country_code(self) -> None:
        self.assertEqual(_clean_phone("+919876543210"), "9876543210")
        self.assertEqual(_clean_phone("+9779812345678"), "9812345678")
        self.assertEqual(_clean_phone("009779812345678"), "9812345678")
        self.assertEqual(_clean_phone("09876543210"), "09876543210")
        self.assertEqual(_clean_phone("9849123377"), "9849123377")

    def test_select_best_prn_result_prefers_exact_phone_match(self) -> None:
        results = [
            PrnResult(prn="PRN-2", name="Alice", phone="+9779800000000", email=None),
            PrnResult(prn="PRN-1", name="Bob", phone="+9779812345678", email=None),
        ]

        best = _select_best_prn_result(results, "9812345678")

        self.assertIsNotNone(best)
        self.assertEqual(best.prn, "PRN-1")


if __name__ == "__main__":
    unittest.main()
