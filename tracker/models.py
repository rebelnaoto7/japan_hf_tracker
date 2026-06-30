"""
Data model for 13F-HR holdings.

This mirrors the `holdings_13f` table that the original Streamlit app read
from `data/cache.db` via:

    SELECT * FROM holdings_13f ORDER BY period_end DESC, value_usd DESC
"""

from django.db import models


class Holding(models.Model):
    """A single 13F-HR position (one fund, one security, one quarter)."""

    fund_name = models.CharField(max_length=255, db_index=True)
    period_end = models.DateField(db_index=True)  # quarter-end date
    ticker = models.CharField(max_length=20)
    issuer = models.CharField(max_length=255)
    cusip = models.CharField(max_length=12, blank=True)
    value_usd = models.BigIntegerField(help_text="Reported market value in USD")
    pct_of_port = models.FloatField(help_text="Position weight as % of portfolio")

    class Meta:
        db_table = "holdings_13f"  # keep the original table name
        ordering = ["-period_end", "-value_usd"]
        indexes = [
            models.Index(fields=["fund_name", "period_end"]),
            models.Index(fields=["fund_name", "ticker"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["fund_name", "period_end", "cusip"],
                name="uniq_fund_period_cusip",
            )
        ]

    def __str__(self) -> str:
        return f"{self.fund_name} | {self.ticker} | {self.period_end}"

    @property
    def value_usd_b(self) -> float:
        return round(self.value_usd / 1e9, 2)
