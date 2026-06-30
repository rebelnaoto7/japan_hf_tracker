# 📊 Japan HF Ownership Tracker

> 世界の機関投資家による**日本企業の保有状況**を、SEC 13F-HRとEDINET大量保有報告書から横断的に可視化するStreamlitアプリ。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 プロジェクトの目的

**「ヘッジファンドが日本株をどれだけ・どう買っているか」**を一元的に可視化できるツールは、既存の13F追跡サービス（13F.info、WhaleWisdom等）には存在しません。理由は：

- 米国13Fは**米国上場ADR**しか開示しない
- 日本のEDINET大量保有報告書は**日本語のみ**で機関投資家にとって参照しづらい

本プロジェクトは**両ソースを統合**し、英語UIで日本株オーナーシップを可視化する**未充足ニッチ**を狙う。

---

## ✨ 主な機能（v1.0 MVP）

| 機能 | 状態 | 説明 |
|---|---|---|
| 主要HF 13F-HR取得 | ✅ | Berkshire / Pershing Square / Bridgewater 等10ファンド |
| ファンド別ビュー | ✅ | Top N保有銘柄、四半期推移、比重変化 |
| ポートフォリオ可視化 | ✅ | ドーナツチャート、ライン/バーグラフ |
| CUSIP重複集計 | ✅ | 投資マネージャー別の分散保有を自動集計 |
| SQLiteキャッシュ | ✅ | レート制限回避＆高速再表示 |
| 日本ADR抽出 | 🚧 | v1.1で実装予定 |
| EDINET連携（東証直接保有） | 🚧 | v1.2で実装予定 |
| 複数ファンド比較ビュー | 🚧 | v1.1で実装予定 |
| Streamlit Cloud公開 | 🚧 | v1.1で実装予定 |

---

## 📸 スクリーンショット

（後ほど追加）

---

## 🛠 技術スタック

| カテゴリ | 採用技術 | 理由 |
|---|---|---|
| 言語 | Python 3.11+ | データ処理・型ヒント |
| UI | Streamlit | 高速プロトタイピング、デプロイが簡単 |
| データソース | SEC EDGAR API、EDINET API v2 | 公式・無料・商用可 |
| 13Fパーサ | edgartools 5.30+ | LXML+PyArrow最適化で高速 |
| データ処理 | pandas、SQLAlchemy | 標準的・実用的 |
| 可視化 | Plotly Express | インタラクティブチャート |
| 永続化 | SQLite | サーバ不要、Streamlit Cloudで動作 |
| 文字列正規化 | rapidfuzz | ファンド名の表記揺れ吸収 |

---

## 📁 プロジェクト構造