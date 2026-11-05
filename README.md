# 日本株ヘッジファンド保有トラッカー（Japan HF Ownership Tracker）

米国 SEC の 13F-HR（機関投資家が四半期ごとに提出する保有銘柄の報告書）のデータを、ファンドごとに KPI カード・表・グラフで可視化する Django 製の Web アプリです。Streamlit で作ったプロトタイプを Django に移植したもので、ヘッジファンドによる日本企業の保有状況を追えるようにすることを目指しています。

[![Python](https://img.shields.io/badge/Python-3.13%20tested-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-%3E%3D5.0%2C%20%3C7.0-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4.3-FF6384?logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Tests](https://img.shields.io/badge/tests-7%20passed-brightgreen)](#テスト)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#ライセンス)

> **English summary:** A Django web app that visualizes institutional investors' SEC 13F-HR holdings per fund and quarter: KPI cards, a Top-N table, doughnut / line / bar charts (Chart.js), CSV export and the Django admin. It is a port of a Streamlit prototype. The bundled `seed_demo` command generates **synthetic** demo data for 10 funds × 5 quarters; the app itself does not download data from SEC EDGAR. Extracting Japanese ADRs and EDINET integration are on the roadmap.

<p align="center">
  <img src="docs/images/dashboard.png" alt="ダッシュボードの Top N タブ。左のサイドバーにファンド・四半期・Top N のフィルタ、右に KPI カードと上位 10 銘柄の表" width="860">
</p>
<p align="center"><sub>画面の数値はすべて <code>seed_demo</code> が乱数で生成した架空のデータで、実在するファンドの実際の保有状況ではありません。左下の「DEMO DATA」の注記は撮影時に書き加えたもので、アプリの画面にはありません。</sub></p>

## 目次

- [主な機能](#主な機能)
- [クイックスタート](#クイックスタート)
- [使い方](#使い方)
- [技術スタック](#技術スタック)
- [プロジェクト構成](#プロジェクト構成)
- [設計のポイント](#設計のポイント)
- [テスト](#テスト)
- [本番環境で使うとき](#本番環境で使うとき)
- [ロードマップ](#ロードマップ)
- [既知の制限](#既知の制限)
- [データと免責](#データと免責)
- [ライセンス](#ライセンス)

## 主な機能

| 機能 | 状態 | 内容 |
| --- | :---: | --- |
| ファンド別ダッシュボード | ✅ | ファンド・四半期・Top N（5〜30）を選ぶと、KPI カード（ポートフォリオ総額・保有銘柄数・Top 10 集中度）と表・グラフが切り替わります |
| Top N タブ | ✅ | 保有額の大きい順に上位 N 銘柄の表と、構成比のドーナツグラフを表示します |
| 推移タブ | ✅ | 選んだ四半期の上位 5 銘柄について、保有額の折れ線グラフと組入比率の棒グラフを四半期ごとに表示します |
| 全銘柄タブ | ✅ | ティッカー・発行体・CUSIP（米国の証券識別コード）・保有額・組入比率の一覧です |
| CSV ダウンロード | ✅ | 表示中のファンド × 四半期の全保有銘柄を CSV で保存します |
| URL で表示を共有 | ✅ | 選択内容が `?fund=...&q=YYYY-MM-DD&top_n=...` の形で URL に入るので、ブックマークや共有ができます |
| 管理画面 | ✅ | Django admin で保有データを検索・絞り込み・編集できます |
| データ投入コマンド | ✅ | `seed_demo`（架空のデモデータを生成）と `import_cache`（SQLite の 13F データを取り込み） |
| 日本 ADR の抽出 | 🚧 | 予定（v1.1）。ADR は米国市場で取引される外国株の預託証券です |
| 複数ファンドの比較ビュー | 🚧 | 予定（v1.1） |
| EDINET 連携 | 🚧 | 予定（v1.2）。EDINET は金融庁の電子開示システムです |

## クイックスタート

前提：Python 3.12 以上と Git（動作確認：Windows 11 / Python 3.13 / Django 6.1.2、2026 年 11 月）。

### Windows（PowerShell）

```powershell
git clone https://github.com/rebelnaoto7/japan_hf_tracker.git
cd japan_hf_tracker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### macOS / Linux

```bash
git clone https://github.com/rebelnaoto7/japan_hf_tracker.git
cd japan_hf_tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

ブラウザで <http://127.0.0.1:8000/> を開くと、ダッシュボードが表示されます。`seed_demo` を実行していない場合は「データがありません」という案内が表示されます。

管理画面（<http://127.0.0.1:8000/admin/>）を使うときは、先に管理者ユーザーを作成します。

```bash
python manage.py createsuperuser
```

グラフを描く Chart.js は CDN（jsDelivr）から読み込みます。インターネットに接続できない環境では、KPI と表は表示されますが、グラフは表示されません（[既知の制限](#既知の制限)）。

### うまく動かないとき

| 症状 | 対処 |
| --- | --- |
| `Activate.ps1` が実行ポリシーで止められる | そのウィンドウだけ許可します：`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `can't open file 'manage.py'` | `manage.py` があるリポジトリ直下に `cd` してから実行します |
| 画面に「データがありません」と出る | `python manage.py seed_demo` を実行します |
| 2 回目の `seed_demo` が `IntegrityError` で止まる | 同じデータがすでにあるためです。`python manage.py seed_demo --clear` で入れ直します |
| グラフだけが表示されない | jsDelivr（`cdn.jsdelivr.net`）に接続できるか確認します |

## 使い方

### 画面の見方

1. 左のサイドバーで **ヘッジファンド** と **四半期** を選び、**Top N 表示** のスライダーで表に出す銘柄数（5〜30）を決めます。選ぶとすぐにページが更新されます。
2. 上部の KPI カードに、選んだ四半期のポートフォリオ総額・保有銘柄数・Top 10 集中度（上位 10 銘柄の組入比率の合計）が表示されます。
3. タブで表示を切り替えます。
   - **Top N**：上位 N 銘柄の表と、その構成比のドーナツグラフ（表の下）
   - **推移**：上位 5 銘柄の保有額（折れ線）と組入比率（棒）の四半期推移
   - **全銘柄**：全保有銘柄の一覧と **CSV ダウンロード** ボタン
4. サイドバーの下には、登録ファンド数・総レコード数・データの期間が表示されます。

<p align="center">
  <img src="docs/images/trend.png" alt="推移タブ。上位 5 銘柄の保有額の折れ線グラフと、組入比率の棒グラフ" width="860">
</p>
<p align="center">
  <img src="docs/images/holdings.png" alt="全銘柄タブ。ティッカー・発行体・CUSIP・保有額・組入比率の表と CSV ダウンロードボタン" width="860">
</p>
<p align="center"><sub>上：推移タブ　下：全銘柄タブ（どちらも <code>seed_demo</code> の架空データ）</sub></p>

### URL パラメータ

| パラメータ | 例 | 説明 |
| --- | --- | --- |
| `fund` | `Pershing Square Capital` | ファンド名。存在しない名前のときは、アルファベット順で最初のファンドになります |
| `q` | `2024-12-31` | 四半期末日（`YYYY-MM-DD`）。そのファンドにない日付のときは最新の四半期になります |
| `top_n` | `15` | 5〜30 の範囲に丸めます。数値でないときは 10 になります |

例：<http://127.0.0.1:8000/?fund=Pershing%20Square%20Capital&q=2024-12-31&top_n=15>

CSV は `/export.csv?fund=...&q=...` でも直接ダウンロードできます。ファイル名は `<ファンド名>_<四半期>.csv`（空白は `_`）で、列は `fund_name, period_end, ticker, issuer, cusip, value_usd, pct_of_port` です。

### デモデータを入れる（seed_demo）

```bash
python manage.py seed_demo                  # 10 ファンド × 5 四半期の架空データ（490 件）
python manage.py seed_demo --clear          # 既存データをすべて削除してから入れ直す
python manage.py seed_demo --clear --seed 7 # 乱数のシードを変える（件数も変わります）
```

- ファンド名と銘柄名は実在するものを使っていますが、保有額と組入比率は乱数で作った架空の値です（既定のシードは 42 で、毎回同じデータになります）。
- 銘柄は米国で取引される日本企業 13 社（ADR や店頭取引の銘柄）と、米国株 3 社（AAPL・KO・BAC）です。四半期は 2024-03-31〜2025-03-31 の 5 期です。
- データがある状態で `--clear` を付けずに実行すると、一意制約違反（`IntegrityError`）で失敗します。この場合、データは変わりません。

### 手持ちの 13F データを取り込む（import_cache）

SQLite ファイルの `holdings_13f` テーブルを取り込みます。

```bash
python manage.py import_cache                         # 既定：data/cache.db
python manage.py import_cache --path path/to/cache.db # ファイルを指定
python manage.py import_cache --clear                 # 取り込む前に既存データをすべて削除
```

取り込み元のテーブルには、次の 7 列が必要です（ほかの列は無視します）。

| 列 | 内容 |
| --- | --- |
| `fund_name` | ファンド名 |
| `period_end` | 四半期末日（`YYYY-MM-DD`。時刻が付いていても日付部分だけを使います） |
| `ticker` | ティッカー |
| `issuer` | 発行体名 |
| `cusip` | CUSIP |
| `value_usd` | 保有額（米ドル） |
| `pct_of_port` | 組入比率（%） |

- 「ファンド・四半期・CUSIP」が同じ行は重複としてスキップします。ただし、完了メッセージの件数にはスキップした行も含まれます。
- `data/cache.db` は `.gitignore` の対象で、リポジトリには含まれません。
- 移植元の Streamlit 版では、`services/edgar_client.py`（SEC EDGAR から 13F を取得する旧スクリプト）が `data/cache.db` を作っていました。このスクリプトには `requirements.txt` にないライブラリ（edgartools・pandas）と環境変数 `SEC_USER_AGENT`（SEC へのアクセスに使う連絡先）が必要です。今回の検証では実行していません。

## 技術スタック

| 分類 | 使用技術 |
| --- | --- |
| 言語 | Python（3.13 で動作確認） |
| Web フレームワーク | Django（`>=5.0,<7.0`。6.1.2 で動作確認） |
| グラフ | Chart.js 4.4.3（jsDelivr の CDN から読み込み） |
| データベース | SQLite（既定）。`DATABASE_URL` を設定すると PostgreSQL など（dj-database-url・psycopg） |
| 静的ファイルの配信 | WhiteNoise |
| 本番用 WSGI サーバー | Gunicorn（Linux・macOS 用） |

`requirements.txt` には python-dotenv も入っていますが、使っているのは旧スクリプト `services/edgar_client.py` だけです。Django の設定（`config/settings.py`）は `.env` を読み込みません。

## プロジェクト構成

```text
japan_hf_tracker/
├── manage.py
├── requirements.txt            # Django 版の依存パッケージ
├── .env.example                # 環境変数の例（Django は .env を自動では読み込みません）
├── config/                     # Django プロジェクトの設定
│   ├── settings.py             # 環境変数による設定・WhiteNoise・DATABASE_URL
│   ├── urls.py                 # /admin/ と tracker アプリの URL
│   ├── asgi.py
│   └── wsgi.py
├── tracker/                    # Django アプリ本体
│   ├── models.py               # Holding モデル（テーブル名 holdings_13f）
│   ├── views.py                # dashboard（画面）と export_csv（CSV）
│   ├── urls.py                 # / と /export.csv
│   ├── admin.py                # 管理画面の一覧・検索・絞り込み
│   ├── tests.py                # 自動テスト 7 件
│   ├── templates/tracker/
│   │   └── dashboard.html      # 画面（ダークテーマ・タブ・Chart.js）
│   ├── management/commands/
│   │   ├── seed_demo.py        # 架空のデモデータを生成
│   │   └── import_cache.py     # SQLite の holdings_13f を取り込み
│   └── migrations/
├── app.py                      # 移植元の Streamlit 版（参考用）
├── services/
│   ├── edgar_client.py         # 移植元の SEC EDGAR 取得スクリプト（参考用）
│   └── __init__.py, db.py, edinet_client.py, merger.py, normalizer.py   # すべて空ファイル
├── pages/                      # Streamlit のマルチページ用の空ファイル 4 つ
├── data/
│   ├── hedge_fund_ciks.csv     # 旧スクリプト用のファンド名と CIK（SEC の登録番号）
│   └── japan_adr_map.csv       # 空ファイル
├── tests/
│   └── test_normalizer.py      # 空ファイル（manage.py test の対象外）
└── docs/
    ├── DEVELOPMENT.md          # 開発メモ（構成図・Streamlit 版との対応表）
    └── images/                 # README のスクリーンショット
```

- Django 版として動くのは `config/` と `tracker/` です。
- `app.py` と `services/edgar_client.py` は移植元の Streamlit 版で、参考として残しています。Django 版の `requirements.txt` では動きません（streamlit・pandas・plotly・edgartools などが別途必要です）。
- 中身が空のファイル（`pages/` の 4 ファイル、`services/` の 5 ファイル、`data/japan_adr_map.csv`、`tests/test_normalizer.py`）は、ロードマップの機能のために用意されたプレースホルダーで、まだ実装はありません。

## 設計のポイント

- **既存データとの互換性**：`Holding` モデルは Streamlit 版と同じテーブル名 `holdings_13f` を使います。「ファンド・四半期・CUSIP」の一意制約で重複を防ぎます。
- **pandas なしで集計**：集計は Django ORM と標準の Python で行うため、実行時に pandas や plotly は不要です。
- **状態は GET パラメータで持つ**：URL だけで同じ画面を再現できます。不正な値は安全な既定値に戻します（`top_n` は 5〜30 に丸め、存在しないファンドや四半期は既定の選択に戻します）。
- **グラフのデータは `json_script` で渡す**：Django の `json_script` フィルタでエスケープして埋め込むので、データに含まれる文字列がスクリプトとして実行されません。
- **日付は文字列にしてから渡す**：ビューで ISO 形式（`YYYY-MM-DD`）の文字列に整形するので、テンプレートの日付表示がタイムゾーン設定に左右されません。
- **本番設定は環境変数で切り替え**：`DJANGO_DEBUG=False` のときだけ、WhiteNoise の圧縮・マニフェスト付きストレージを使います。

構成図と Streamlit 版との対応表は [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) にまとめています。

## テスト

```bash
python manage.py test
```

`tracker/tests.py` の 7 件がすべて成功します（Windows 11 / Python 3.13 / Django 6.1.2）。実行結果の抜粋です。

```text
Found 7 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.......
----------------------------------------------------------------------
Ran 7 tests in 0.051s

OK
Destroying test database for alias 'default'...
```

`collectstatic` を実行する前は、WhiteNoise の `UserWarning: No directory at: ...staticfiles` が表示されます。`staticfiles/` フォルダがまだないことを知らせる警告で、テスト結果には影響しません。

| テスト | 確かめていること |
| --- | --- |
| `test_empty_state` | データが 0 件のとき「データがありません」の案内を表示する |
| `test_default_dashboard` | 既定でアルファベット順の最初のファンドと最新の四半期を選び、KPI と件数を正しく計算する |
| `test_fund_switch_resets_quarter` | ファンドを切り替えると、そのファンドの最新の四半期を選ぶ |
| `test_top_n_clamped` | `top_n` を 5〜30 に丸め、数値でない値は 10 にする |
| `test_invalid_fund_and_quarter_fallback` | 存在しないファンドや不正な日付は既定の選択に戻す |
| `test_trend_alignment` | 推移グラフのデータが、選んだ四半期の上位銘柄を四半期順にそろえている |
| `test_csv_export` | CSV のヘッダー・行数・Content-Type |

## 本番環境で使うとき

`config/settings.py` は、次の環境変数を読み込みます。Django は `.env` ファイルを自動では読み込まないので、シェルやホスティング先の設定で環境変数として渡してください。

| 環境変数 | 既定値 | 説明 |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | 開発用の固定値 | 本番では必ず長いランダムな値にします |
| `DJANGO_DEBUG` | `True` | 本番では `False`。文字列が `True` のときだけデバッグモードになります |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | 公開するホスト名（カンマ区切り） |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | （空） | HTTPS で公開するときのオリジン（例：`https://example.com`） |
| `DJANGO_TIME_ZONE` | `Asia/Tokyo` | タイムゾーン |
| `DJANGO_USE_TZ` | `True` | タイムゾーン対応の有無 |
| `DATABASE_URL` | （未設定なら SQLite） | 例：`postgres://USER:PASSWORD@HOST:5432/DBNAME` |

SECRET_KEY は次のコマンドで作れます。

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 1. Chart.js をローカルに置く（DEBUG=False では必須）

テンプレートは `{% static 'tracker/js/chart.umd.min.js' %}` を参照していますが、このファイルはリポジトリに含まれていません。`DEBUG=False` で使うマニフェスト付きストレージは参照先のファイルがないとエラーにするため、**このまま `DEBUG=False` で起動すると、ダッシュボード（`/`）が 500 エラーになります**（管理画面と CSV ダウンロードは動きます）。また、`chart.umd.min.js` の末尾にはソースマップ `chart.umd.js.map` への参照があり、`collectstatic` はこのファイルもないと失敗します。そのため、2 つのファイルを置きます。

```powershell
# Windows（PowerShell）
New-Item -ItemType Directory -Force tracker\static\tracker\js | Out-Null
curl.exe -fsSL -o tracker\static\tracker\js\chart.umd.min.js https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js
curl.exe -fsSL -o tracker\static\tracker\js\chart.umd.js.map https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.js.map
```

```bash
# macOS / Linux
mkdir -p tracker/static/tracker/js
curl -fsSL -o tracker/static/tracker/js/chart.umd.min.js https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js
curl -fsSL -o tracker/static/tracker/js/chart.umd.js.map https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.js.map
```

### 2. 環境変数を設定して起動する

Linux サーバーでの例です。

```bash
export DJANGO_DEBUG=False
export DJANGO_SECRET_KEY="（上のコマンドで作った値）"
export DJANGO_ALLOWED_HOSTS=example.com
export DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com
export DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DBNAME   # PostgreSQL を使う場合だけ

python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application
```

手元の Windows で `DEBUG=False` の動きを確かめるときは、次のようにします（静的ファイルは WhiteNoise が配信します）。

```powershell
$env:DJANGO_DEBUG = "False"
$env:DJANGO_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(50))"
python manage.py collectstatic --noinput
python manage.py runserver
```

### 3. 公開前に確認すること

- `python manage.py check --deploy` を実行すると、HSTS・HTTPS へのリダイレクト・Cookie の `Secure` 属性についての警告（`security.W004`・`W008`・`W012`・`W016`）が出ます。`settings.py` にはこれらを切り替える設定がないため、HTTPS で公開するときは設定の追加を検討してください。
- ダッシュボードにはログイン機能がなく、URL を知っていればだれでも閲覧できます（管理画面だけがログイン必須です）。
- Gunicorn は Linux・macOS 用で、Windows では動きません。この README の検証は Windows で行ったため、Gunicorn での起動と PostgreSQL への接続は確認していません。

## ロードマップ

- **v1.1**：複数ファンドの比較ビュー、日本 ADR の抽出、公開手順の整備
- **v1.2**：EDINET API v2 との連携（東証での直接保有の取り込み）、英語・日本語の銘柄名の正規化
- **その後**：四半期ごとの差分のハイライト、ファンド横断の集中度分析、保有変化のアラート

## 既知の制限

- **CDN に接続できないとグラフが出ない**：テンプレートには、CDN から読み込めなかったときにローカルの Chart.js へ切り替える `onerror` 処理があります。しかしブラウザは、読み込みに失敗した `<script>` の `src` を書き換えても読み込み直さないため、実際には切り替わりません（Chromium 系のブラウザで確認）。オフラインで使うときは、[本番環境で使うとき](#本番環境で使うとき)の手順でファイルを置いたうえで、`dashboard.html` の `<script>` の `src` を `{% static 'tracker/js/chart.umd.min.js' %}` に書き換える必要があります。
- **実データの取得は含まれない**：Django 版には SEC EDGAR からデータを取得する機能がありません。実データを使うには、別途用意した `holdings_13f` テーブルを `import_cache` で取り込みます。
- **デモデータは架空**：`seed_demo` のデータは乱数で作ったもので、分析には使えません。
- **プレースホルダー**：中身が空のファイルが残っています（[プロジェクト構成](#プロジェクト構成)を参照）。

## データと免責

- 想定しているデータの出典は、米国 SEC の EDGAR で公開されている Form 13F-HR です。アプリの画面の下部にも、出典と注意書きを表示しています。
- 13F で開示されるのは、米国で取引される対象証券（米国株や ADR など）のロング（買い）ポジションです。空売り（ショート）やスワップ、日本の取引所で直接保有している株式は含まれません。
- 13F-HR は四半期末から 45 日以内に提出されるため、内容は最新の保有状況ではありません。
- `seed_demo` のデータは、実在するファンド名・銘柄名に乱数の値を組み合わせた架空のデータです。実際の保有状況を表すものではありません。
- このアプリは学習・研究用です。投資助言ではありません。投資判断はご自身の責任で行ってください。

## ライセンス

MIT License
