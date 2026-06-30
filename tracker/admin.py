from django.contrib import admin

from .models import Holding


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = (
        "fund_name",
        "period_end",
        "ticker",
        "issuer",
        "value_usd",
        "pct_of_port",
    )
    list_filter = ("fund_name", "period_end")
    search_fields = ("ticker", "issuer", "cusip", "fund_name")
    ordering = ("-period_end", "-value_usd")
    list_per_page = 50
