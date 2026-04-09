from django.test import SimpleTestCase

from poms.transactions.utils import _sanitize_ytm


class TestSanitizeYtm(SimpleTestCase):
    def test_none_returns_zero(self):
        self.assertEqual(_sanitize_ytm(None), 0.0)

    def test_complex_returns_zero(self):
        self.assertEqual(_sanitize_ytm(complex(-0.98, 0.58)), 0.0)

    def test_complex_with_tiny_imaginary_returns_zero(self):
        """Even complex with negligible imaginary part should return 0."""
        self.assertEqual(_sanitize_ytm(complex(-0.617, 8.3e-17)), 0.0)

    def test_complex_from_production_error(self):
        """Exact complex values from production error logs."""
        self.assertEqual(
            _sanitize_ytm(complex(-0.9802270234352741, 0.586687270683598)),
            0.0,
        )
        self.assertEqual(
            _sanitize_ytm(complex(-1.6290682385111677, 0.24653067562824657)),
            0.0,
        )
        self.assertEqual(
            _sanitize_ytm(complex(-0.6171933097394031, 8.336640977585254e-17)),
            0.0,
        )

    def test_nan_returns_zero(self):
        self.assertEqual(_sanitize_ytm(float("nan")), 0.0)

    def test_inf_returns_zero(self):
        self.assertEqual(_sanitize_ytm(float("inf")), 0.0)
        self.assertEqual(_sanitize_ytm(float("-inf")), 0.0)

    def test_normal_float_passes_through(self):
        result = _sanitize_ytm(0.05)
        self.assertIsInstance(result, float)
        self.assertAlmostEqual(result, 0.05, places=4)

    def test_negative_float_passes_through(self):
        result = _sanitize_ytm(-0.03)
        self.assertIsInstance(result, float)
        self.assertAlmostEqual(result, -0.03, places=4)

    def test_zero_returns_zero(self):
        self.assertEqual(_sanitize_ytm(0), 0.0)
        self.assertEqual(_sanitize_ytm(0.0), 0.0)

    def test_integer_works(self):
        result = _sanitize_ytm(1)
        self.assertIsInstance(result, (int, float))

    def test_string_returns_zero(self):
        self.assertEqual(_sanitize_ytm("0.05"), 0.0)

    def test_result_is_never_complex(self):
        test_values = [
            None,
            0,
            0.0,
            1,
            -1,
            0.05,
            -0.05,
            float("nan"),
            float("inf"),
            float("-inf"),
            complex(1, 0),
            complex(0, 1),
            complex(-0.98, 0.58),
        ]
        for val in test_values:
            result = _sanitize_ytm(val)
            self.assertNotIsInstance(result, complex, f"_sanitize_ytm({val!r}) returned complex")
            self.assertIsInstance(result, (int, float), f"_sanitize_ytm({val!r}) didn't return a number")
