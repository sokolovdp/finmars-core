import datetime

from django.test import SimpleTestCase

from poms.common.formula_accruals import f_xirr, f_xnpv


class TestFXnpv(SimpleTestCase):
    def test_zero_rate(self):
        data = [
            (datetime.date(2024, 1, 1), -1000),
            (datetime.date(2025, 1, 1), 1100),
        ]
        result = f_xnpv(data, 0.0)
        self.assertAlmostEqual(result, 100.0, places=1)

    def test_rate_minus_one_returns_inf(self):
        data = [
            (datetime.date(2024, 1, 1), -1000),
            (datetime.date(2025, 1, 1), 1100),
        ]
        result = f_xnpv(data, -1)
        self.assertEqual(result, float("inf"))

    def test_positive_rate_discounts(self):
        data = [
            (datetime.date(2024, 1, 1), -1000),
            (datetime.date(2025, 1, 1), 1050),
        ]
        result_at_0 = f_xnpv(data, 0.0)
        result_at_10 = f_xnpv(data, 0.10)
        self.assertGreater(result_at_0, result_at_10)

    def test_result_is_always_real(self):
        data = [
            (datetime.date(2024, 1, 1), -1000),
            (datetime.date(2025, 6, 15), 1100),
        ]
        for rate in [0.0, 0.5, -0.5, -0.99]:
            result = f_xnpv(data, rate)
            self.assertIsInstance(result, float, f"f_xnpv returned non-float for rate={rate}")


class TestFXirr(SimpleTestCase):
    def test_empty_data_returns_zero(self):
        self.assertEqual(f_xirr([]), 0.0)

    def test_simple_positive_return(self):
        data = [
            (datetime.date(2024, 1, 1), -1000),
            (datetime.date(2025, 1, 1), 1100),
        ]
        result = f_xirr(data)
        self.assertAlmostEqual(result, 0.1, places=3)

    def test_simple_negative_return(self):
        """Bought above par, small coupon — YTM should be negative."""
        data = [
            (datetime.date(2024, 1, 1), -1050),
            (datetime.date(2025, 1, 1), 1010),
        ]
        result = f_xirr(data)
        self.assertLess(result, 0)
        self.assertGreater(result, -1)

    def test_result_is_always_float(self):
        data = [
            (datetime.date(2024, 1, 1), -1000),
            (datetime.date(2025, 1, 1), 1050),
        ]
        result = f_xirr(data)
        self.assertIsInstance(result, float)

    def test_never_returns_complex(self):
        """f_xirr must never return a complex number, regardless of input."""
        test_cases = [
            [
                (datetime.date(2024, 1, 1), -1000),
                (datetime.date(2025, 1, 1), 1),
            ],
            [
                (datetime.date(2024, 1, 1), -1000),
                (datetime.date(2025, 1, 1), 0.01),
            ],
            [
                (datetime.date(2024, 1, 1), -10000),
                (datetime.date(2024, 3, 15), 5),
                (datetime.date(2025, 1, 1), 10),
            ],
        ]
        for data in test_cases:
            result = f_xirr(data)
            self.assertNotIsInstance(result, complex, f"f_xirr returned complex for data={data}")
            self.assertIsInstance(result, float)

    def test_maturity_in_past_defaulted_bond(self):
        """
        Reproduces the production error with USP7807HAM71:
        bond in default, maturity_date (2022) is before trade_date (2026).
        Cash flows have dates going backwards, which caused complex numbers.
        YTM should be 0.0 for such instruments.
        """
        data = [
            (datetime.date(2026, 3, 20), -98.5),  # purchase (trade_date)
            (datetime.date(2022, 6, 15), 100.0),  # maturity in the past (defaulted)
        ]
        result = f_xirr(data)
        self.assertIsInstance(result, float)
        self.assertNotIsInstance(result, complex)

    def test_maturity_in_past_with_coupons(self):
        """
        Defaulted bond with past maturity and past coupon dates.
        All future cash flows are in the past relative to purchase.
        """
        data = [
            (datetime.date(2026, 3, 20), -98.5),  # purchase
            (datetime.date(2021, 12, 15), 3.5),  # coupon (past)
            (datetime.date(2022, 6, 15), 3.5),  # coupon (past)
            (datetime.date(2022, 6, 15), 100.0),  # maturity (past)
        ]
        result = f_xirr(data)
        self.assertIsInstance(result, float)
        self.assertNotIsInstance(result, complex)

    def test_extreme_loss_does_not_produce_complex(self):
        """
        Extreme loss scenario: paid a lot, getting almost nothing back.
        Newton-Raphson may try rates below -100%.
        """
        data = [
            (datetime.date(2024, 1, 1), -10000),
            (datetime.date(2025, 1, 1), 1),
        ]
        result = f_xirr(data)
        self.assertIsInstance(result, float)
        self.assertEqual(result, 0.0)

    def test_rate_never_exceeds_minus_one(self):
        """Result should never be <= -1 (below -100%)."""
        data = [
            (datetime.date(2024, 1, 1), -1000),
            (datetime.date(2025, 1, 1), 50),
        ]
        result = f_xirr(data)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, -1)

    def test_with_multiple_cash_flows(self):
        """Standard bond with semiannual coupons."""
        data = [
            (datetime.date(2024, 1, 1), -1000),
            (datetime.date(2024, 7, 1), 25),
            (datetime.date(2025, 1, 1), 25),
            (datetime.date(2025, 7, 1), 25),
            (datetime.date(2026, 1, 1), 1025),
        ]
        result = f_xirr(data)
        self.assertIsInstance(result, float)
        self.assertAlmostEqual(result, 0.05, places=2)

    def test_bad_initial_guess(self):
        """Large x0 far from the real answer should still converge or return 0."""
        data = [
            (datetime.date(2024, 1, 1), -1000),
            (datetime.date(2025, 1, 1), 1050),
        ]
        result = f_xirr(data, x0=10.0)
        self.assertIsInstance(result, float)
        self.assertNotIsInstance(result, complex)

    def test_non_convergence_returns_zero(self):
        """If maxiter=1, method likely won't converge — should return 0.0."""
        data = [
            (datetime.date(2024, 1, 1), -1000),
            (datetime.date(2025, 1, 1), 1050),
        ]
        result = f_xirr(data, maxiter=1)
        self.assertIsInstance(result, float)
