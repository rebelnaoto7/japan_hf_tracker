"""
Japan HF Ownership Tracker - Streamlit App (v1).
"""
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------- 設定 ----------
st.set_page_config(
    page_title="Japan HF Ownership Tracker",
    page_icon="📊",
    layout="wide",
)

DB_PATH = Path(__file__).parent / "data" / "cache.db"


# ---------- データ取得 ----------
@st.cache_data(ttl=3600)
def load_holdings():
    if not DB_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(
            "SELECT * FROM holdings_13f ORDER BY period_end DESC, value_usd DESC",
            con,
        )
    df["period_end"] = pd.to_datetime(df["period_end"]).dt.date
    return df


# ---------- ヘッダ ----------
st.title("📊 Japan Hedge Fund Ownership Tracker")
st.caption(
    "SEC 13F-HR データを横断的に可視化するMVP。"
    "EDINET連携・日本ADR抽出は次フェーズで実装予定。"
)

df = load_holdings()

if df.empty:
    st.error("データがありません。先に `python services/edgar_client.py` を実行してください。")
    st.stop()

# ---------- サイドバー ----------
with st.sidebar:
    st.header("🔎 フィルタ")
    funds = sorted(df["fund_name"].unique())
    selected_fund = st.selectbox("ヘッジファンド", funds, index=0)

    fund_df = df[df["fund_name"] == selected_fund]
    quarters = sorted(fund_df["period_end"].unique(), reverse=True)
    selected_q = st.selectbox("四半期", quarters, index=0)

    top_n = st.slider("Top N 表示", 5, 30, 10)

    st.divider()
    st.metric("登録ファンド数", df["fund_name"].nunique())
    st.metric("総レコード数", f"{len(df):,}")
    st.metric("カバー期間", f"{df['period_end'].min()} ~ {df['period_end'].max()}")

# ---------- メイン ----------
view = fund_df[fund_df["period_end"] == selected_q].copy()
total_value = view["value_usd"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("ポートフォリオ総額", f"${total_value/1e9:.1f}B")
col2.metric("保有銘柄数", f"{len(view)}")
col3.metric(
    "Top 10集中度",
    f"{view.nlargest(10, 'value_usd')['pct_of_port'].sum():.1f}%",
)

st.divider()

tab1, tab2, tab3 = st.tabs(["📋 Top N", "📈 推移", "🔍 全銘柄"])

with tab1:
    st.subheader(f"Top {top_n} Holdings @ {selected_q}")
    top = view.nlargest(top_n, "value_usd")[
        ["ticker", "issuer", "value_usd", "pct_of_port"]
    ].reset_index(drop=True)
    top["value_usd_b"] = (top["value_usd"] / 1e9).round(2)
    top["pct_of_port"] = top["pct_of_port"].round(2)

    st.dataframe(
        top[["ticker", "issuer", "value_usd_b", "pct_of_port"]].rename(
            columns={
                "ticker": "Ticker",
                "issuer": "Issuer",
                "value_usd_b": "Value ($B)",
                "pct_of_port": "% of Port",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    fig_pie = px.pie(
        top,
        values="value_usd",
        names="ticker",
        title=f"Top {top_n} Allocation",
        hole=0.4,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.subheader("Top 5銘柄の四半期推移")
    top5_tickers = view.nlargest(5, "value_usd")["ticker"].tolist()
    trend = fund_df[fund_df["ticker"].isin(top5_tickers)].copy()
    trend["value_usd_b"] = trend["value_usd"] / 1e9

    fig_line = px.line(
        trend,
        x="period_end",
        y="value_usd_b",
        color="ticker",
        markers=True,
        title=f"{selected_fund}: Top 5 Holdings Value Trend",
        labels={"period_end": "四半期末", "value_usd_b": "評価額 ($B)"},
    )
    st.plotly_chart(fig_line, use_container_width=True)

    fig_bar = px.bar(
        trend,
        x="period_end",
        y="pct_of_port",
        color="ticker",
        title="ポートフォリオ比重 (%) 推移",
        barmode="group",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.subheader(f"全保有銘柄 @ {selected_q}")
    full = view[["ticker", "issuer", "cusip", "value_usd", "pct_of_port"]].copy()
    full["value_usd"] = full["value_usd"].apply(
        lambda x: f"${x/1e9:.2f}B" if x >= 1e9 else f"${x/1e6:.0f}M"
    )
    full["pct_of_port"] = full["pct_of_port"].round(3)
    st.dataframe(full, use_container_width=True, hide_index=True)

    csv = view.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 CSV ダウンロード",
        csv,
        f"{selected_fund}_{selected_q}.csv",
        "text/csv",
    )

# ---------- フッタ ----------
st.divider()
st.caption(
    "Source: SEC EDGAR 13F-HR | "
    "Note: 13Fはロング側のみで、ショート/スワップ/海外株は含まれません | "
    "45日ラグあり"
)streamlit run app.py