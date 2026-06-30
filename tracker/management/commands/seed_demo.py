"""
Populate the database with realistic demo data so the app runs out of the box.

This replaces the original `python services/edgar_client.py` step. It does NOT
hit the SEC API; it generates plausible 13F-HR style holdings for a handful of
well-known funds across several quarters (Japanese ADRs + a few US names).

    python manage.py seed_demo
    python manage.py seed_demo --clear
"""

import random
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from tracker.models import Holding

FUNDS = [
    "Berkshire Hathaway",
    "Pershing Square Capital",
    "Bridgewater Associates",
    "Baupost Group",
    "Third Point",
    "ValueAct Capital",
    "Greenlight Capital",
    "Tiger Global Management",
    "Coatue Management",
    "Appaloosa Management",
]

# (ticker, issuer, cusip)  -- Japanese ADRs + a few US blue chips
SECURITIES = [
    ("MUFG", "Mitsubishi UFJ Financial Group", "606822104"),
    ("SMFG", "Sumitomo Mitsui Financial Group", "865622202"),
    ("MFG", "Mizuho Financial Group", "60687Y109"),
    ("TM", "Toyota Motor Corp", "892331307"),
    ("SONY", "Sony Group Corp", "835699307"),
    ("HMC", "Honda Motor Co", "438128308"),
    ("MARUF", "Marubeni Corp", "57380R109"),
    ("ITOCY", "ITOCHU Corp", "465562106"),
    ("MITSY", "Mitsui & Co", "606827205"),
    ("SSUMY", "Sumitomo Corp", "865477102"),
    ("NTDOY", "Nintendo Co", "654445303"),
    ("TAK", "Takeda Pharmaceutical", "874060205"),
    ("KYCCF", "Keyence Corp", "493855108"),
    ("AAPL", "Apple Inc", "037833100"),
    ("KO", "Coca-Cola Co", "191216100"),
    ("BAC", "Bank of America Corp", "060505104"),
]

QUARTERS = [
    date(2024, 3, 31),
    date(2024, 6, 30),
    date(2024, 9, 30),
    date(2024, 12, 31),
    date(2025, 3, 31),
]


class Command(BaseCommand):
    help = "Seed the database with demo 13F-HR holdings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing holdings before seeding.",
        )
        parser.add_argument(
            "--seed", type=int, default=42, help="RNG seed for reproducibility."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(options["seed"])

        if options["clear"]:
            deleted, _ = Holding.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} rows."))

        objs = []
        for fund in FUNDS:
            # Each fund holds a stable random subset of the universe.
            n_pos = rng.randint(8, 14)
            picks = rng.sample(SECURITIES, n_pos)
            # Base weights per security, kept across quarters with drift.
            base = {t[0]: rng.uniform(0.5, 12.0) for t in picks}

            for q in QUARTERS:
                # Quarterly drift on each weight.
                weights = {
                    tic: max(0.1, w * rng.uniform(0.85, 1.20))
                    for tic, w in base.items()
                }
                total_w = sum(weights.values())
                # Total portfolio value for this fund-quarter ($20B..$300B).
                port_value = rng.uniform(20e9, 300e9)

                for ticker, issuer, cusip in picks:
                    pct = weights[ticker] / total_w * 100.0
                    value = port_value * (weights[ticker] / total_w)
                    objs.append(
                        Holding(
                            fund_name=fund,
                            period_end=q,
                            ticker=ticker,
                            issuer=issuer,
                            cusip=cusip,
                            value_usd=int(value),
                            pct_of_port=round(pct, 4),
                        )
                    )

        Holding.objects.bulk_create(objs, batch_size=500)
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(objs)} holdings across "
                f"{len(FUNDS)} funds × {len(QUARTERS)} quarters."
            )
        )
