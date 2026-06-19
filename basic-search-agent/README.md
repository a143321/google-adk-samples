# 🔎 basic-search-agent (基礎検索エージェント)

ADK v2.0 の基本的な書き方（ツールの呼び出し、ストリーミング等）を学ぶための、最もシンプルな単一エージェントのサンプルです。

## プロジェクト構造

```
basic-search-agent/
├── app/         # エージェントのコアコード
│   ├── agent.py               # エージェントのメインロジック
│   ├── agent_runtime_app.py    # Agent Runtime アプリケーションロジック
│   └── app_utils/             # アプリケーションのユーティリティとヘルパー
├── tests/                     # ユニットテスト、統合テスト、負荷テスト
├── GEMINI.md                  # AI支援開発用ガイド（プロンプト・コンテキスト）
└── pyproject.toml             # プロジェクトの依存関係定義
```

> 💡 **ヒント:** AI支援開発には [Gemini CLI](https://github.com/google-gemini/gemini-cli) を使用してください。本プロジェクトの文脈やルールはあらかじめ `GEMINI.md` に設定されています。

## 開発・実行手順

本プロジェクトの実行環境の要件（Python 3.13等）、前提条件ツールのインストール方法、およびローカル起動（Playground）やデプロイ用のコマンド群については、リポジトリルートの **[README.md](../README.md)** をご参照ください。

## オブザーバビリティ (監視・分析)

Cloud Trace、BigQuery、Cloud Logging への組み込みテレメトリ・エクスポート機能を備えており、エージェントの挙動を詳細に分析可能です。
