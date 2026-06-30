"""SEC EDGAR 13F-HR client (v2 - 集計対応版)."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from edgar import Company, set_identity

load_dotenv()
_UA = os.getenv("SEC_USER_AGENT")
if not _UA:
    raise RuntimeError("SEC_USER_AGENT を .env に設定してください")
set_identity(_UA)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "cache.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS holdings_13f (
    cik TEXT NOT NULL,
    fund_name TEXT,
    period_end DATE NOT NULL,
    filed_at DATETIME,
    cusip TEXT,
    ticker TEXT,
    issuer TEXT,
    value_usd REAL,
    shares INTEGER,
    pct_of_port REAL,
    PRIMARY KEY (cik, period_end, cusip)
);
"""

def _init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.executescript(_SCHEMA)
_init_db()


def _purge_fund(cik):
    """指定CIKの古い行だけ削除（DBファイル全体は消さない）"""
    with sqlite3.connect(DB_PATH) as con:
        con.execute("DELETE FROM holdings_13f WHERE cik = ?", (str(cik).zfill(10),))

SHARE_CANDS = ["shares_amount", "ssh_prnamt", "sshprnamt", "shrsorprnamt", "shares"]
VALUE_CANDS = ["value", "value_usd", "value_amount"]
CUSIP_CANDS = ["cusip", "cusip_number"]
ISSUER_CANDS = ["issuer", "name_of_issuer", "issuer_name", "company_name"]
TICKER_CANDS = ["ticker", "symbol"]


def _resolve(df, cands):
    for c in cands:
        if c in df.columns:
            return c
    return None


class EdgarClient:
    FORM = "13F-HR"

    def get_holdings(self, cik, quarters=4, save=True):
        print(f"[INFO] Fetching {cik}...")
        company = Company(cik)
        fund_name = company.name
        print(f"[INFO] Fund: {fund_name}")

        filings = company.get_filings(form=self.FORM).head(quarters)
        print(f"[INFO] Found {len(filings)} filings")
        if len(filings) == 0:
            return pd.DataFrame()

        frames = []
        for f in filings:
            try:
                holdings = f.obj().infotable
            except Exception as e:
                print(f"[WARN] {f.period_of_report}: {e}")
                continue

            df = holdings.copy()
            df.columns = [c.lower() for c in df.columns]

            v = _resolve(df, VALUE_CANDS)
            s = _resolve(df, SHARE_CANDS)
            c = _resolve(df, CUSIP_CANDS)
            i = _resolve(df, ISSUER_CANDS)
            t = _resolve(df, TICKER_CANDS)

            rename = {}
            if v: rename[v] = "value_usd"
            if s: rename[s] = "shares"
            if c: rename[c] = "cusip"
            if i: rename[i] = "issuer"
            if t: rename[t] = "ticker"
            df = df.rename(columns=rename)

            if "cusip" not in df.columns or "value_usd" not in df.columns:
                print(f"[WARN] missing cols: {list(df.columns)}")
                continue

            for col in ["ticker", "issuer", "shares"]:
                if col not in df.columns:
                    df[col] = None

            agg = df.groupby("cusip", as_index=False).agg(
                ticker=("ticker", "first"),
                issuer=("issuer", "first"),
                value_usd=("value_usd", "sum"),
                shares=("shares", "sum"),
            )

            agg["cik"] = str(cik).zfill(10)
            agg["fund_name"] = fund_name
            agg["period_end"] = pd.to_datetime(f.period_of_report).date()
            agg["filed_at"] = pd.to_datetime(f.filing_date)

            total = agg["value_usd"].sum()
            agg["pct_of_port"] = (agg["value_usd"] / total * 100).round(3) if total else 0.0

            print(f"[INFO]   {f.period_of_report}: {len(df)} rows -> {len(agg)} CUSIPs, ${total/1e9:.1f}B")

            cols = ["cik","fund_name","period_end","filed_at","cusip","ticker","issuer","value_usd","shares","pct_of_port"]
            frames.append(agg[cols])

        if not frames:
            return pd.DataFrame()

        result = pd.concat(frames, ignore_index=True)
        if save:
            self._upsert(result)
        return result

    @staticmethod
    def _upsert(df):
        with sqlite3.connect(DB_PATH) as con:
            df.to_sql("_tmp", con, if_exists="replace", index=False)
            con.execute("""
                INSERT OR REPLACE INTO holdings_13f
                  (cik, fund_name, period_end, filed_at, cusip, ticker, issuer, value_usd, shares, pct_of_port)
                SELECT cik, fund_name, period_end, filed_at, cusip, ticker, issuer, value_usd, shares, pct_of_port FROM _tmp;
            """)
            con.execute("DROP TABLE _tmp;")

    @staticmethod
    def list_funds(csv_path="data/hedge_fund_ciks.csv"):
        return pd.read_csv(csv_path, dtype={"cik": str})


if __name__ == "__main__":
    print("=" * 60)
    print("EDGAR Client v2.1 (lock-safe)")
    print("=" * 60)

    target_cik = "0001067983"
    _purge_fund(target_cik)
    print(f"[CLEAN] purged old rows for {target_cik}")

    client = EdgarClient()
    df = client.get_holdings(target_cik, quarters=4)

    if df.empty:
        print("[ERROR] no data")
    else:
        latest = df["period_end"].max()
        top10 = df[df["period_end"] == latest].nlargest(10, "value_usd")
        print(f"\n--- Top 10 @ {latest} ---")
        for _, r in top10.iterrows():
            issuer = (r['issuer'] or '')[:25]
            print(f"  {r['ticker'] or '':<8} {issuer:<25} ${r['value_usd']/1e9:>6.1f}B  {r['pct_of_port']:>6.2f}%")
        print(f"\n[DONE] {len(df)} rows saved")