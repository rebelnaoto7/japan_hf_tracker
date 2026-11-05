# 開発メモ（Japan HF Ownership Tracker）

README から分けた、開発者向けの補足です。使い方は [README](../README.md) を参照してください。

## 構成図

```text
ブラウザ（dashboard.html ＋ Chart.js）
    │ GET /?fund=...&q=...&top_n=...（CSV は /export.csv）
    ▼
config/urls.py → tracker/views.py
    ├─ dashboard()   KPI・表・グラフ用のデータを計算して HTML を返す
    └─ export_csv()  表示中のファンド × 四半期を CSV で返す
    │ Django ORM
    ▼
Holding モデル（テーブル名 holdings_13f）
    SQLite（既定）／ DATABASE_URL を設定すると PostgreSQL など
    ▲
    │ データ投入
seed_demo（架空のデモデータ）／ import_cache（SQLite の holdings_13f を取り込み）
```

## リクエストの流れ

1. ブラウザが `GET /?fund=...&q=...&top_n=...` を送ります。
2. `tracker.views._build_state()` が選択内容を決めます。存在しないファンドはアルファベット順で最初のファンドに、存在しない四半期はそのファンドの最新の四半期に、`top_n` は 5〜30 に丸めます（数値でなければ 10）。
3. ORM でその四半期の保有銘柄を保有額の降順に取得し、KPI・表・グラフ用のデータを標準の Python で計算します。
4. グラフ用のデータは `json_script` で HTML に埋め込み、ブラウザ側で Chart.js が描画します。
5. `GET /export.csv` も同じ `_build_state()` を使い、表示中のファンド × 四半期の全保有銘柄を CSV（添付ファイル）で返します。

## Streamlit 版との対応表

| Streamlit 版（`app.py`） | Django 版 | 補足 |
| --- | --- | --- |
| `sqlite3` で `data/cache.db` の `holdings_13f` を読む | `tracker.models.Holding`（`db_table = "holdings_13f"`） | テーブル名を変えていないので、`import_cache` でそのまま取り込めます |
| `@st.cache_data(ttl=3600)` | Django ORM のクエリ | キャッシュは未実装です。必要なら `cache_page` などで追加できます |
| サイドバーの `selectbox`（ファンド・四半期） | GET パラメータ `fund`・`q` と `<select>` | URL で共有・ブックマークできます |
| `st.slider("Top N 表示", 5, 30, 10)` | GET パラメータ `top_n` | 5〜30 に丸め、数値でなければ 10 |
| `st.metric`（総額・銘柄数・集中度など） | KPI カードとサイドバーの指標 | 計算はビューで行います |
| `st.tabs`（Top N・推移・全銘柄） | 1 ページ内のタブ（JavaScript で切り替え） | タブの切り替えでページは再読み込みしません |
| `plotly.express`（ドーナツ・折れ線・グループ棒） | Chart.js（同じ 3 種類） | ブラウザ側で描画します |
| `st.download_button`（CSV） | `/export.csv`（`export_csv` ビュー） | 列は `fund_name`〜`pct_of_port` の 7 列に固定。ファイル名の空白は `_` に置き換えます |
| `python services/edgar_client.py` でデータを作る | `seed_demo`・`import_cache` 管理コマンド | データ取得（ETL）は Django 版の対象外です |
| `st.stop()`（データがないとき） | データがないときの案内画面 | 投入コマンドを案内します |

## 移植時の判断

- Streamlit・plotly・pandas を実行時の依存から外し、集計は Django ORM、描画は Chart.js に統一しました。依存が軽くなり、一般的な WSGI サーバーで動かしやすくなります。
- SEC EDGAR からのデータ取得は Django 版の対象外とし、データは `seed_demo`（架空のデモデータ）か `import_cache`（既存の SQLite）で入れる形にしました。

## 移植元のファイル（参考用）

| ファイル | 内容 | 動かすのに必要なもの |
| --- | --- | --- |
| `app.py` | Streamlit 版の画面。`data/cache.db` の `holdings_13f` を読み込みます | streamlit・pandas・plotly |
| `services/edgar_client.py` | edgartools で SEC EDGAR から 13F-HR を取得し、`data/cache.db` に保存します。直接実行すると Berkshire Hathaway（CIK 0001067983）の直近 4 件を取得します | edgartools・pandas・python-dotenv、環境変数 `SEC_USER_AGENT` |
| `data/hedge_fund_ciks.csv` | `edgar_client.list_funds()` が読むファンド名と CIK の一覧（10 件）。`seed_demo` の 10 ファンドとは別のリストです | — |

- `SEC_USER_AGENT` は、SEC にアクセスするときに名乗るアプリ名と連絡先の文字列です。`.env.example` には含まれていません。
- これらのファイルは、今回の検証では実行していません（Django 版の `requirements.txt` にないライブラリが必要なため）。

## 空のファイル（プレースホルダー）

次のファイルは中身が空で、ロードマップの機能のために用意されたものです。

- `pages/1_銘柄ビュー.py`、`pages/2_ファンドビュー.py`、`pages/3_ランキング比較.py`、`pages/4_アラート設定.py`
- `services/__init__.py`、`services/db.py`、`services/edinet_client.py`、`services/merger.py`、`services/normalizer.py`
- `data/japan_adr_map.csv`
- `tests/test_normalizer.py`（`tests/` に `__init__.py` がなく、中身もないため、`manage.py test` では実行されません）

## 開発用のコマンド

```bash
python manage.py check                 # 設定の確認（問題なし）
python manage.py makemigrations --check # モデルとマイグレーションの差分確認（No changes detected）
python manage.py test                  # 自動テスト 7 件
```

括弧内は、Windows 11 / Python 3.13 / Django 6.1.2 で実行したときの結果です（2026 年 11 月）。
