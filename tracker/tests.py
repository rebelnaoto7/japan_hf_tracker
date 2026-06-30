"""Tests for the Japan HF Ownership Tracker (Django port)."""

from datetime import date

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Holding


def _mk(fund, period, ticker, issuer, value, pct, cusip="000000000"):
    return Holding.objects.create(
        fund_name=fund, period_end=period, ticker=ticker, issuer=issuer,
        cusip=cusip, value_usd=value, pct_of_port=pct,
    )


@override_settings(ALLOWED_HOSTS=["testserver", "localhost"])
class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        q1, q2 = date(2024, 12, 31), date(2025, 3, 31)
        # Fund A, two quarters
        _mk("Fund A", q1, "TM", "Toyota", 5_000_000_000, 50.0, "892331307")
        _mk("Fund A", q1, "SONY", "Sony", 3_000_000_000, 30.0, "835699307")
        _mk("Fund A", q1, "MUFG", "Mitsubishi UFJ", 2_000_000_000, 20.0, "606822104")
        _mk("Fund A", q2, "TM", "Toyota", 6_000_000_000, 60.0, "892331307")
        _mk("Fund A", q2, "SONY", "Sony", 4_000_000_000, 40.0, "835699307")
        # Fund B
        _mk("Fund B", q2, "AAPL", "Apple", 900_000_000, 100.0, "037833100")

    def test_empty_state(self):
        Holding.objects.all().delete()
        resp = Client().get(reverse("tracker:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "データがありません")

    def test_default_dashboard(self):
        resp = self.client.get(reverse("tracker:dashboard"))
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context
        self.assertEqual(ctx["selected_fund"], "Fund A")        # first alpha
        self.assertEqual(ctx["selected_q"], "2025-03-31")        # newest quarter
        self.assertEqual(ctx["top_n"], 10)                       # default
        # total = 6B + 4B = 10B -> 10.0
        self.assertEqual(ctx["total_value_b"], 10.0)
        self.assertEqual(ctx["n_holdings"], 2)
        self.assertEqual(ctx["top10_concentration"], 100.0)
        self.assertEqual(ctx["n_funds"], 2)
        self.assertEqual(ctx["n_records"], 6)

    def test_fund_switch_resets_quarter(self):
        resp = self.client.get(reverse("tracker:dashboard"), {"fund": "Fund B"})
        self.assertEqual(resp.context["selected_fund"], "Fund B")
        self.assertEqual(resp.context["selected_q"], "2025-03-31")
        self.assertEqual(resp.context["n_holdings"], 1)

    def test_top_n_clamped(self):
        for raw, expected in [("3", 5), ("999", 30), ("bad", 10), ("7", 7)]:
            resp = self.client.get(reverse("tracker:dashboard"), {"top_n": raw})
            self.assertEqual(resp.context["top_n"], expected, raw)

    def test_invalid_fund_and_quarter_fallback(self):
        resp = self.client.get(
            reverse("tracker:dashboard"),
            {"fund": "Nope", "q": "not-a-date"},
        )
        self.assertEqual(resp.context["selected_fund"], "Fund A")
        self.assertEqual(resp.context["selected_q"], "2025-03-31")

    def test_trend_alignment(self):
        resp = self.client.get(reverse("tracker:dashboard"), {"fund": "Fund A"})
        labels = resp.context["quarter_labels"]
        self.assertEqual(labels, ["2024-12-31", "2025-03-31"])
        line = {d["label"]: d["data"] for d in resp.context["line_datasets"]}
        # Trend tracks the Top-5 of the *selected* quarter (Q2 = TM, SONY).
        # MUFG (only in Q1) is intentionally excluded, matching the original.
        self.assertEqual(set(line.keys()), {"TM", "SONY"})
        self.assertEqual(line["TM"], [5.0, 6.0])     # both quarters
        self.assertEqual(line["SONY"], [3.0, 4.0])   # both quarters

    def test_csv_export(self):
        resp = self.client.get(
            reverse("tracker:export_csv"),
            {"fund": "Fund A", "q": "2025-03-31"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/csv")
        self.assertIn("attachment; filename=", resp["Content-Disposition"])
        rows = resp.content.decode().strip().splitlines()
        self.assertEqual(rows[0],
                         "fund_name,period_end,ticker,issuer,cusip,value_usd,pct_of_port")
        self.assertEqual(len(rows) - 1, 2)  # two holdings in Fund A @ Q2
