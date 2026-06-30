"""
Views for the Japan HF Ownership Tracker.

Direct Django port of the original Streamlit app (app.py). The sidebar
`selectbox`/`slider` controls become GET query parameters:

    ?fund=<fund name>&q=<YYYY-MM-DD>&top_n=<5..30>

No pandas at runtime: all aggregation is done with the Django ORM + plain
Python so the app stays lightweight in production.
"""

import csv
from datetime import date

from django.db.models import Count, Max, Min, Sum
from django.http import HttpResponse
from django.shortcuts import render

from .models import Holding

TOP_N_MIN = 5
TOP_N_MAX = 30
TOP_N_DEFAULT = 10


def _parse_date(value):
    """Parse 'YYYY-MM-DD' -> date, or None on failure."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _clamp_top_n(raw):
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return TOP_N_DEFAULT
    return max(TOP_N_MIN, min(TOP_N_MAX, n))


def _build_state(request):
    """
    Resolve the current filter selection and load the matching rows.

    Returns a dict shared by the dashboard view and the CSV export view, or
    ``None`` when there is no data at all (mirrors Streamlit's st.stop()).
    """
    funds = list(
        Holding.objects.order_by("fund_name")
        .values_list("fund_name", flat=True)
        .distinct()
    )
    if not funds:
        return None

    # ---------- fund selection ----------
    requested_fund = request.GET.get("fund")
    selected_fund = requested_fund if requested_fund in funds else funds[0]

    fund_qs = Holding.objects.filter(fund_name=selected_fund)

    # ---------- quarter selection (newest first, like the original) ----------
    quarters = list(
        fund_qs.order_by("-period_end")
        .values_list("period_end", flat=True)
        .distinct()
    )
    requested_q = _parse_date(request.GET.get("q"))
    selected_q = requested_q if requested_q in quarters else quarters[0]

    # ---------- top N slider ----------
    top_n = _clamp_top_n(request.GET.get("top_n"))

    # ---------- current quarter view (value desc) ----------
    view = list(fund_qs.filter(period_end=selected_q).order_by("-value_usd"))

    return {
        "funds": funds,
        "selected_fund": selected_fund,
        "fund_qs": fund_qs,
        "quarters": quarters,
        "selected_q": selected_q,
        "top_n": top_n,
        "view": view,
    }


def dashboard(request):
    state = _build_state(request)

    if state is None:
        return render(
            request,
            "tracker/dashboard.html",
            {
                "no_data": True,
                "top_n_range": range(TOP_N_MIN, TOP_N_MAX + 1, 5),
            },
        )

    funds = state["funds"]
    fund_qs = state["fund_qs"]
    selected_fund = state["selected_fund"]
    selected_q = state["selected_q"]
    top_n = state["top_n"]
    view = state["view"]

    # ---------- header KPIs ----------
    total_value = sum(h.value_usd for h in view)
    top10_concentration = sum(h.pct_of_port for h in view[:10])

    # ---------- sidebar global metrics ----------
    agg = Holding.objects.aggregate(
        n_funds=Count("fund_name", distinct=True),
        n_records=Count("id"),
        period_min=Min("period_end"),
        period_max=Max("period_end"),
    )

    # ---------- Tab 1: Top N table + donut ----------
    top_rows = view[:top_n]
    top_table = [
        {
            "ticker": h.ticker,
            "issuer": h.issuer,
            "value_b": round(h.value_usd / 1e9, 2),
            "pct": round(h.pct_of_port, 2),
        }
        for h in top_rows
    ]
    pie_labels = [h.ticker for h in top_rows]
    pie_values = [h.value_usd for h in top_rows]

    # ---------- Tab 2: Top-5 trend (line = value $B, bar = % of port) ----------
    top5_tickers = [h.ticker for h in view[:5]]
    trend_qs = fund_qs.filter(ticker__in=top5_tickers).order_by("period_end")

    # Sorted ascending quarter axis for the whole fund.
    trend_quarters = sorted(set(state["quarters"]))
    quarter_labels = [q.isoformat() for q in trend_quarters]
    q_index = {q: i for i, q in enumerate(trend_quarters)}

    value_by_ticker = {t: [None] * len(trend_quarters) for t in top5_tickers}
    pct_by_ticker = {t: [None] * len(trend_quarters) for t in top5_tickers}
    for h in trend_qs:
        if h.ticker in value_by_ticker and h.period_end in q_index:
            idx = q_index[h.period_end]
            value_by_ticker[h.ticker][idx] = round(h.value_usd / 1e9, 4)
            pct_by_ticker[h.ticker][idx] = round(h.pct_of_port, 4)

    line_datasets = [
        {"label": t, "data": value_by_ticker[t]} for t in top5_tickers
    ]
    bar_datasets = [
        {"label": t, "data": pct_by_ticker[t]} for t in top5_tickers
    ]

    # ---------- Tab 3: full holdings ----------
    def fmt_value(v):
        return f"${v/1e9:.2f}B" if v >= 1e9 else f"${v/1e6:.0f}M"

    full_table = [
        {
            "ticker": h.ticker,
            "issuer": h.issuer,
            "cusip": h.cusip,
            "value_disp": fmt_value(h.value_usd),
            "pct": round(h.pct_of_port, 3),
        }
        for h in view
    ]

    context = {
        "no_data": False,
        # filter controls (dates pre-formatted to strings to avoid relying on
        # the template `date` filter / server timezone config)
        "funds": funds,
        "selected_fund": selected_fund,
        "quarters": [q.isoformat() for q in state["quarters"]],
        "selected_q": selected_q.isoformat(),
        "top_n": top_n,
        "top_n_range": range(TOP_N_MIN, TOP_N_MAX + 1, 5),
        # header KPIs
        "total_value_b": round(total_value / 1e9, 1),
        "n_holdings": len(view),
        "top10_concentration": round(top10_concentration, 1),
        # sidebar metrics
        "n_funds": agg["n_funds"],
        "n_records": agg["n_records"],
        "period_min": agg["period_min"].isoformat() if agg["period_min"] else "",
        "period_max": agg["period_max"].isoformat() if agg["period_max"] else "",
        # tab 1
        "top_table": top_table,
        "pie_labels": pie_labels,
        "pie_values": pie_values,
        # tab 2
        "quarter_labels": quarter_labels,
        "line_datasets": line_datasets,
        "bar_datasets": bar_datasets,
        # tab 3
        "full_table": full_table,
    }
    return render(request, "tracker/dashboard.html", context)


def export_csv(request):
    """Replicates Streamlit's st.download_button CSV export of the view."""
    state = _build_state(request)
    if state is None:
        return HttpResponse("No data", status=404)

    selected_fund = state["selected_fund"]
    selected_q = state["selected_q"]
    view = state["view"]

    filename = f"{selected_fund}_{selected_q}.csv".replace(" ", "_")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(
        ["fund_name", "period_end", "ticker", "issuer", "cusip", "value_usd", "pct_of_port"]
    )
    for h in view:
        writer.writerow(
            [
                h.fund_name,
                h.period_end.isoformat(),
                h.ticker,
                h.issuer,
                h.cusip,
                h.value_usd,
                h.pct_of_port,
            ]
        )
    return response
