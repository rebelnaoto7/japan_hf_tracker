<div align="center">

# 📊 Japan HF Ownership Tracker

**世界の機関投資家による「日本企業の保有状況」を、SEC 13F-HR データから横断的に可視化する Web アプリ**

_Streamlit 製プロトタイプ（`app.py`）を、本番運用を見据えて **Django** へ移植したリファレンス実装_

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.x-FF6384?logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Tests](https://img.shields.io/badge/tests-7%20passing-brightgreen)](#-テスト)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 📑 目次

1. [プロジェクトの目的](#-プロジェクトの目的)
2. [スクリーンショット](#-スクリーンショット)
3. [主な機能](#-主な機能v10-mvp)
4. [技術スタック](#-技術スタック)
5. [クイックスタート（3 コマンド）](#-クイックスタート3-コマンド)
6. [データの投入方法](#-データの投入方法)
7. [プロジェクト構造](#-プロジェクト構造)
8. [アーキテクチャ](#-アーキテクチャ)
9. [Streamlit → Django 移植マッピング](#-streamlit--django-移植マッピング)
10. [設定（環境変数）](#-設定環境変数)
11. [テスト](#-テスト)
12. [本番デプロイ（Azure App Service）](#-本番デプロイazure-app-service)
13. [Chart.js のローカル配置（社内ネットワーク向け）](#-chartjs-のローカル配置社内ネットワーク向け)
14. [トラブルシューティング](#-トラブルシューティング)
15. [ロードマップ](#-ロードマップ)
16. [ライセンス / 注意事項](#-ライセンス--注意事項)

---

## 🎯 プロジェクトの目的

**「ヘッジファンドが日本株をどれだけ・どう買っているか」** を一元的に可視化できるツールは、
既存の 13F 追跡サービス（13F.info、WhaleWisdom 等）には存在しません。理由は次の 2 点です。

- 米国 13F は **米国上場 ADR** しか開示しない
- 日本の EDINET 大量保有報告書は **日本語のみ** で、海外機関投資家にとって参照しづらい

本プロジェクトは将来的に **両ソースを統合** し、英語 UI で日本株オーナーシップを可視化する
**未充足のニッチ** を狙います。本リポジトリはその第一歩として、SEC 13F-HR データを
Django 上で可視化する MVP です。

---

## 📸 スクリーンショット

> 実画面のキャプチャは後日追加します。下記は画面構成の概要です。

```
┌──────────────┬────────────────────────────────────────────────┐
│  🔎 フィルタ   │  📊 Japan Hedge Fund Ownership Tracker          │
│              │                                                │
│  ファンド ▼   │  ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  四半期   ▼   │  │ 総額     │ │ 銘柄数   │ │Top10集中 │ ← KPI    │
│  Top N  ──●─ │  │ $128.4B │ │   12    │ │ 73.2 %  │           │
│              │  └─────────┘ └─────────┘ └─────────┘           │
│  登録ファンド  │  ┌ 📋 Top N ┬ 📈 推移 ┬ 🔍 全銘柄 ┐ ← タブ    │
│  総レコード数  │  │ 上位テーブル + ドーナツ / 折れ線 + 棒 / 全件表 │
│  カバー期間   │  │                            [📥 CSV]        │
└──────────────┴────────────────────────────────────────────────┘
```

---

## ✨ 主な機能（v1.0 MVP）

| 機能 | 状態 | 説明 |
|------|:----:|------|
| 主要 HF 13F-HR の可視化 | ✅ | Berkshire / Pershing Square / Bridgewater 等 10 ファンド |
| ファンド別ビュー | ✅ | Top N 保有銘柄・四半期推移・比重 |
| ポートフォリオ可視化 | ✅ | ドーナツ / 折れ線 / グループ棒（Chart.js） |
| KPI ダッシュボード | ✅ | 総額・保有銘柄数・Top 10 集中度 |
| CSV エクスポート | ✅ | 選択中ファンド × 四半期の全保有をダウンロード |
| SQLite キャッシュ取込 | ✅ | 既存 `data/cache.db` をそのまま import 可能 |
| Django Admin | ✅ | 保有データの検索・絞り込み・編集 |
| 自動テスト | ✅ | 7 ケース（フィルタ・クランプ・CSV 等） |
| 日本 ADR 抽出 | 🚧 | v1.1 で実装予定 |
| EDINET 連携（東証直接保有） | 🚧 | v1.2 で実装予定 |
| 複数ファンド比較ビュー | 🚧 | v1.1 で実装予定 |

---

## 🛠 技術スタック

| カテゴリ | 採用技術 | 理由 |
|----------|----------|------|
| 言語 | Python 3.11+ | データ処理・型ヒント |
| Web フレームワーク | **Django 5.x** | 認証・ORM・Admin・本番運用が標準装備 |
| データソース | SEC EDGAR API（取込済データを利用） | 公式・無料・商用可 |
| 可視化 | **Chart.js 4.x** | クライアント描画でサーバ依存を削減 |
| 永続化 | SQLite（既定） / PostgreSQL（任意） | 開発はサーバ不要、本番は `DATABASE_URL` で切替 |
| 静的配信 | WhiteNoise | 別途 Web サーバ不要で本番配信 |
| 本番サーバ | Gunicorn | Azure App Service で標準的 |

> **移植時の設計判断**：オリジナルの Streamlit / Plotly / pandas 依存は実行時から外し、
> 集計は Django ORM、描画は Chart.js に統一しました。これにより依存が軽量化し、
> Azure などへの配置が容易になります。

---

## 🚀 クイックスタート（3 コマンド）

> 前提：Python 3.11 以上がインストール済み。

```bash
# 0) 仮想環境（推奨）
py -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate           # macOS / Linux

# 1) 依存をインストール
pip install -r requirements.txt

# 2) DB 作成（マイグレーション）＆デモデータ投入
python manage.py migrate
python manage.py seed_demo

# 3) 起動
python manage.py runserver
```

ブラウザで <http://127.0.0.1:8000/> を開きます。
管理画面は `/admin/`（`python manage.py createsuperuser` で管理者を作成）。

---

## 📥 データの投入方法

本アプリは 2 通りのデータ投入をサポートします。

### A. デモデータ（すぐ試す）

```bash
python manage.py seed_demo            # 10 ファンド × 5 四半期の擬似データ
python manage.py seed_demo --clear    # 既存を消してから投入
python manage.py seed_demo --seed 7   # 乱数シードを指定（再現性）
```

### B. 既存の Streamlit キャッシュを取り込む

オリジナル `app.py` が生成した `data/cache.db`（テーブル `holdings_13f`）をそのまま取込可能です。

```bash
python manage.py import_cache                      # 既定: ./data/cache.db
python manage.py import_cache --path C:\path\cache.db
python manage.py import_cache --clear              # 取込前に全削除
```

> 取込元テーブルは
> `fund_name, period_end, ticker, issuer, cusip, value_usd, pct_of_port`
> の列を想定しています（余分な列は無視）。

---

## 📁 プロジェクト構造

```
japan_hf_tracker/
├─ manage.py
├─ requirements.txt
├─ .env.example                 # 環境変数テンプレート
├─ .gitignore                   # db.sqlite3 / .venv / data/cache.db 等を除外
├─ config/                      # プロジェクト設定
│  ├─ settings.py               # 環境変数駆動・WhiteNoise・DATABASE_URL 対応
│  ├─ urls.py
│  └─ wsgi.py
└─ tracker/                     # アプリ本体
   ├─ models.py                 # Holding（db_table="holdings_13f"）
   ├─ views.py                  # dashboard / export_csv
   ├─ urls.py                   # "/" と "/export.csv"
   ├─ admin.py                  # HoldingAdmin（検索・フィルタ）
   ├─ tests.py                  # 自動テスト 7 件
   ├─ templates/tracker/
   │  └─ dashboard.html         # ダークテーマ UI・タブ・Chart.js
   ├─ static/tracker/js/        # ← chart.umd.min.js をローカル配置する場所
   └─ management/commands/
      ├─ seed_demo.py           # デモデータ生成
      └─ import_cache.py        # 既存 cache.db 取り込み
```

---

## 🏗 アーキテクチャ

```
        ┌──────────────────────────────────────────────────────┐
        │                     Browser (UI)                      │
        │   dashboard.html  +  Chart.js (doughnut/line/bar)     │
        └───────────────▲───────────────────────┬──────────────┘
                        │ HTML / json_script     │ GET ?fund&q&top_n
                        │                         ▼
        ┌──────────────────────────────────────────────────────┐
        │                   Django (config)                     │
        │   urls.py → tracker.views                             │
        │     • dashboard()   集計・KPI・チャート用データ生成      │
        │     • export_csv()  CSV ストリーム出力                 │
        └───────────────▲───────────────────────┬──────────────┘
                        │ ORM Query              │
                        ▼                         │
        ┌──────────────────────────────────────────────────────┐
        │             Holding model (holdings_13f)              │
        │        SQLite（既定） / PostgreSQL（DATABASE_URL）       │
        └──────────────────────────────────────────────────────┘
                        ▲
                        │ 投入
        ┌───────────────┴───────────────┐
        │ seed_demo  /  import_cache     │
        └────────────────────────────────┘
```

- **集計は ORM + 素の Python**（pandas 非依存）でサーバを軽量化
- **チャートデータは `json_script` で安全に受け渡し**（XSS 対策）
- **日付は View 側で文字列整形** → テンプレートの `date` フィルタや TZ 設定差異に非依存

---

## 🔁 Streamlit → Django 移植マッピング

| Streamlit（`app.py`） | Django 移植先 | 備考 |
|------------------------|---------------|------|
| `sqlite3` + `holdings_13f` テーブル | `tracker.models.Holding`（`db_table="holdings_13f"`） | テーブル名を維持し既存 DB と互換 |
| `@st.cache_data` で SQL 読込 | Django ORM クエリ（`views.py`） | キャッシュは将来 `cache_page` 等で追加可 |
| サイドバー `selectbox`（ファンド／四半期） | GET パラメータ `?fund=...&q=YYYY-MM-DD` + `<select>` | URL 共有可能・ブックマーク可 |
| `slider("Top N", 5, 30, 10)` | GET パラメータ `?top_n=`（5〜30 にクランプ） | 不正値は安全側へ補正 |
| `st.metric`（総額／銘柄数／集中度） | KPI カード（テンプレート） | 表示計算は View 側 |
| `st.tabs([...])` | 1 ページ内タブ UI（JS 切替） | リロード不要 |
| `plotly.express`（pie / line / bar） | **Chart.js**（doughnut / line / grouped bar） | サーバ依存削減 |
| `st.download_button` で CSV | `/export.csv` ビュー（`export_csv`） | ストリーム出力 |
| `python services/edgar_client.py` で投入 | `seed_demo` / `import_cache` 管理コマンド | ETL は別フェーズ |
| `st.stop()`（データ無し時） | 空状態テンプレート（投入案内を表示） | UX を維持 |

---

## ⚙ 設定（環境変数）

`config/settings.py` は本番値を環境変数から読み込み、同一コードで開発・本番を切り替えます。
`.env.example` をコピーして `.env` を作成するか、Azure の App Settings に設定します。

| 変数 | 既定値 | 説明 |
|------|--------|------|
| `DJANGO_SECRET_KEY` | （開発用ダミー） | 本番では必ずランダムな長い文字列に変更 |
| `DJANGO_DEBUG` | `True` | 本番では `False` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | カンマ区切りホスト名 |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | （空） | 例：`https://<app>.azurewebsites.net` |
| `DJANGO_TIME_ZONE` | `Asia/Tokyo` | タイムゾーン |
| `DJANGO_USE_TZ` | `True` | タイムゾーン対応 |
| `DATABASE_URL` | （未設定 → SQLite） | 例：`postgres://USER:PASS@HOST:5432/DB` |

> **シークレットキー生成**
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(50))"
> ```

---

## ✅ テスト

```bash
python manage.py test
```

`tracker/tests.py` に **7 ケース** を実装済みです。

| # | テスト | 検証内容 |
|---|--------|----------|
| 1 | `test_empty_state` | データ無し時に投入案内を表示 |
| 2 | `test_default_dashboard` | 既定ファンド／最新四半期／Top 10・KPI 計算 |
| 3 | `test_fund_switch_resets_quarter` | ファンド切替時の四半期再選択 |
| 4 | `test_top_n_clamped` | `top_n` の 5〜30 クランプと不正値補正 |
| 5 | `test_invalid_fund_and_quarter_fallback` | 不正パラメータの安全なフォールバック |
| 6 | `test_trend_alignment` | 推移チャートの四半期整列と欠損ギャップ |
| 7 | `test_csv_export` | CSV ヘッダ・行数・Content-Type |

---

## ☁ 本番デプロイ（Azure App Service）

```bash
# App Settings（環境変数）例
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<ランダムな十分長い文字列>
DJANGO_ALLOWED_HOSTS=<your-app>.azurewebsites.net
DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-app>.azurewebsites.net
# 管理 DB を使う場合のみ
DATABASE_URL=postgres://USER:PASS@HOST:5432/DBNAME
```

```bash
# 起動前コマンド（リリース時）
python manage.py migrate
python manage.py collectstatic --noinput

# 起動コマンド
gunicorn config.wsgi:application
```

- `whitenoise` が静的ファイルを配信するため、別途 Web サーバは不要です。
- `DATABASE_URL` を設定すると `dj-database-url` 経由で **PostgreSQL** に切り替わります（未設定なら SQLite）。
- 短時間のデモ用途であれば SQLite のまま `seed_demo` で投入しても動作します。

---

## 🌐 Chart.js のローカル配置（社内ネットワーク向け）

既定では CDN（jsDelivr）から Chart.js を読み込みますが、**CDN がブロックされる環境**では
テンプレートの `onerror` フォールバックでローカル版を自動利用します。

```text
1) chart.umd.min.js を入手し、次へ配置
   tracker/static/tracker/js/chart.umd.min.js
2) 本番では collectstatic を実行
   python manage.py collectstatic --noinput
```

これで CDN 不通時にもチャートが描画されます。

---

## 🧰 トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `Activate.ps1 が認識されません` | `.venv` 未作成 or 場所違い | `py -m venv .venv` を実行／`manage.py` のある階層へ `cd` |
| `can't open file 'manage.py'` | カレントディレクトリが違う | `Get-ChildItem -Recurse -Filter manage.py` で場所を確認し移動 |
| `Activate.ps1` が実行ポリシーで拒否 | PowerShell の制限 | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| グラフが表示されない | CDN がブロック | [Chart.js のローカル配置](#-chartjs-のローカル配置社内ネットワーク向け) を実施 |
| `データがありません` 表示 | データ未投入 | `python manage.py seed_demo` または `import_cache` |
| 本番で静的ファイルが出ない | collectstatic 未実行 | `python manage.py collectstatic --noinput` |

---

## 🗺 ロードマップ

- **v1.1**：複数ファンド比較ビュー、日本 ADR 抽出、Streamlit Cloud 相当の公開手順
- **v1.2**：EDINET API v2 連携（東証直接保有の取込）、英語／日本語の銘柄名正規化
- **将来**：四半期差分の自動ハイライト、ファンド横断の集中度分析、保有変化アラート

---

## 📄 ライセンス / 注意事項

- ライセンス：**MIT**
- データ表記：`Source: SEC EDGAR 13F-HR`
- **重要**：13F はロング側のみの開示で、ショート／スワップ／海外株は含まれません。
  また提出には **約 45 日のラグ** があります。投資判断の唯一の根拠としないでください。

---

<div align="center">
<sub>Built with Django · Visualized with Chart.js · Ported from a Streamlit MVP</sub>
</div>
