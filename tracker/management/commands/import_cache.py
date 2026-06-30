"""
Import the original Streamlit cache (data/cache.db, table holdings_13f) into
the Django database.

    python manage.py import_cache                 # reads ./data/cache.db
    python manage.py import_cache --path /x/y.db  # custom path
    python manage.py import_cache --clear         # wipe first

The source table is expected to have the columns produced by the original
edgar_client pipeline:
    fund_name, period_end, ticker, issuer, cusip, value_usd, pct_of_port
Extra columns are ignored; missing optional columns default sensibly.
"""

import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tracker.models import Holding


class Command(BaseCommand):
    help = "Import holdings_13f rows from the original SQLite cache."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(Path(settings.BASE_DIR) / "data" / "cache.db"),
            help="Path to the source cache.db.",
        )
        parser.add_argument("--clear", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        src = Path(options["path"])
        if not src.exists():
            raise CommandError(f"Source DB not found: {src}")

        if options["clear"]:
            deleted, _ = Holding.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} rows."))

        con = sqlite3.connect(str(src))
        con.row_factory = sqlite3.Row
        try:
            rows = con.execute(
                "SELECT fund_name, period_end, ticker, issuer, cusip, "
                "value_usd, pct_of_port FROM holdings_13f"
            ).fetchall()
        except sqlite3.OperationalError as exc:
            raise CommandError(f"Could not read holdings_13f: {exc}")
        finally:
            con.close()

        objs = []
        for r in rows:
            period = str(r["period_end"])[:10]  # YYYY-MM-DD (strip any time)
            objs.append(
                Holding(
                    fund_name=r["fund_name"],
                    period_end=period,
                    ticker=r["ticker"] or "",
                    issuer=r["issuer"] or "",
                    cusip=(r["cusip"] or "")[:12],
                    value_usd=int(r["value_usd"] or 0),
                    pct_of_port=float(r["pct_of_port"] or 0.0),
                )
            )

        Holding.objects.bulk_create(
            objs, batch_size=500, ignore_conflicts=True
        )
        self.stdout.write(
            self.style.SUCCESS(f"Imported {len(objs)} rows from {src}.")
        )
