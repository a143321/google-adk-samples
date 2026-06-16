# 🗺️ Google ADK v2.0 Developer Samples (Monorepo)

本リポジトリは、Google の AI エージェント開発フレームワーク **Agent Development Kit (ADK) v2.0** の新機能やベストプラクティスを示すためのサンプルコード集です。
モノリポジトリ形式で整理されており、各プロジェクトは**完全に独立して動作する設計**となっています。他のフォルダを意識することなく、フォルダごと別の場所に移動しても独立して起動・デプロイ・テストが可能です。

---

## 🚀 システム要件と技術的制約

- **フレームワーク**: **Agent Development Kit (ADK) 2.0 (`google-adk[gcp]>=2.0.0`)** を使用しています。
- **Python**: `3.11` 以上 `3.14` 未満（ローカル開発では速度面の利点から **`3.13`** を推奨）
- **CLI ツール**: [`google-agents-cli`](https://github.com/google/agents-cli) (Python 3.11+ 必須)
- **パッケージ・環境管理**: `uv` (推奨) もしくは `pip`
- **クラウド実行環境**: Vertex AI Agent Runtime は Python `3.10` 〜 `3.13` をサポート（本リポジトリの Terraform 設定では `3.12` を指定）

---

## 📂 収録プロジェクト一覧

段階的に理解を深められるよう、以下の2つの独立したプロジェクトを同梱しています。

### 1. [basic-search-agent (基礎プロジェクト)](./basic-search-agent/)
- **フォルダ名**: `basic-search-agent`
- **概要**: 最もシンプルな単一エージェント（Single Agent）構成。
- **機能**: Google検索ツールを使用したシンプルなファクト調査。
- **目的**: 
  - **Memory Bank（記憶の永続化）や複数エージェントの連携を含みません**。
  - ADK 2.0 の基本的な書き方（エージェント定義、ツール呼出、SSEストリーミング）と、テスト実行の流れを理解するための入門用です。

### 2. [travel-guide-japan (応用プロジェクト)](./travel-guide-japan/)
- **フォルダ名**: `travel-guide-japan`
- **概要**: ポートフォリオとして成果をアピールできる、実用的なマルチエージェント協調システム。
- **機能**:
  - **ADK 2.0 協調エージェント（Collaborative Agents）**: 親エージェントが、日本全国の天気情報の専門エージェント (`weather_agent`) やWeb検索エージェント (`search_agent`) に自律的にタスクを振り分けます。
  - **Memory Bank（長期記憶）の統合**: ユーザーの過去の会話から旅行日程や食事の好み（アレルギー等）、移動手段（レンタカー等）の嗜好を自動的に Memory Bank へ記憶し、次回以降の提案をパーソナライズします。
- **目的**: 実際のプロダクション開発を想定し、カスタムメモリトピック定義 (`update.py`) や自動品質評価（ADK Eval）を含み、より高度なユースケースに対応します。

---

## 💡 ADK v2.0 を採用する理由とテストの容易性

ADK v2.0 は **グラフベースの実行エンジン（Workflow Runtime）** へと刷新されました。これにより、以下の大きな開発上のメリットが得られます：

1. **テストと評価の容易性**:
   - 各処理（エージェントの思考、コード関数、外部APIコールなど）がグラフの「ノード（Node）」としてカプセル化されるため、各ステップの入出力を決定論的にトレース・モックしやすくなりました。
   - `adk conformance test` や `pytest` を用いたユニットテスト/統合テストが非常に直感的に記述でき、再現性の高いテスト自動化が可能です。
2. **堅牢な状態管理とマルチエージェント制御**:
   - サブエージェントの動作モード（`mode="single_turn"` や `"task"`）を指定することで、親エージェントとの間で制御権が自動的に行き来し、複雑な手続きを安全に実装できます。

---

## 🛠️ 環境構築方法 (Environment Setup)

エージェントをローカル環境で動作させたり、Vertex AI にデプロイするための環境構築手順です。各プロジェクトフォルダは独立しているため、どちらを実行する場合も以下の手順に沿って設定を行います。

### 1. パッケージ管理ツール `uv` のインストール
本プロジェクトでは高速なパッケージ管理と仮想環境構築のために `uv` を使用します。未インストールの場合は、端末の OS に合わせて以下を実行してください。

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 💡 (補足) `uv` を使用した Python バージョンの管理方法

システムの global な Python バージョンを変更することなく、特定の Python バージョン（例: Python 3.13 の最新パッチ）をダウンロードして各プロジェクトの仮想環境に適用させることができます。

**1. 特定の Python バージョンをローカルにインストール:**
```bash
uv python install 3.13
```

**2. そのバージョンを指定して仮想環境（`.venv`）を再作成・同期する:**
各プロジェクトフォルダ内（`basic-search-agent` など）で以下を実行します。
```bash
rm -rf .venv
uv sync --python 3.13 --dev
```

**3. 仮想環境内で使用されている Python バージョンを確認する:**
```bash
uv run python --version
```

### 2. Google Cloud の認証とプロジェクト設定
Geminiモデルや Vertex AI サービスと安全に通信するため、以下の認証設定を行います。

```bash
# 1. ユーザーアカウントでのログイン
gcloud auth login

# 2. アプリケーションデフォルト資格情報 (ADC) の取得 (ADKライブラリが使用します)
gcloud auth application-default login

# 3. 使用する Google Cloud プロジェクトの設定
gcloud config set project YOUR_PROJECT_ID
```

### 3. 環境変数（`.env`）の作成
実行したいプロジェクトのフォルダ（`basic-search-agent` または `travel-guide-japan`）に移動し、テンプレートから `.env` ファイルを作成してください。

```bash
# 例: 基礎プロジェクトの場合
cd basic-search-agent

# テンプレートのコピー
cp .env.example .env
```

作成した `.env` ファイルを開き、`GOOGLE_CLOUD_PROJECT` にご自身のGoogle CloudプロジェクトIDを設定します。

```env
GOOGLE_CLOUD_PROJECT="あなたのGoogle CloudプロジェクトID"
GOOGLE_CLOUD_LOCATION="asia-northeast1"
GOOGLE_GENAI_USE_VERTEXAI="True"
```

---

## 🚀 各プロジェクトの実行手順

本プロジェクトでは `Makefile` を用意しているため、`make` コマンドを使用して簡単にローカル実行やテストが可能です。（`make` を使用しない場合は、`uvx google-agents-cli` コマンドで直接実行できます。）

### 1. 基礎プロジェクト (basic-search-agent) の実行
```bash
cd basic-search-agent

# 依存関係のインストール（仮想環境の自動作成と ADK 2.0 のセットアップ）
make install         # または uvx google-agents-cli install

# ローカル Web UI (Playground) の起動
make playground      # または uvx google-agents-cli playground

# テストの実行
make test            # または uv run pytest
```

### 2. 応用プロジェクト (travel-guide-japan) の実行
```bash
cd travel-guide-japan

# 依存関係のインストール
make install         # または uvx google-agents-cli install

# ローカル Web UI (Playground) の起動
make playground      # または uvx google-agents-cli playground

# テストの実行
make test            # または uv run pytest
```

---

## ☁️ Google Cloud へのデプロイ手順 (Deployment)

各プロジェクトは、**Vertex AI Reasoning Engine (Agent Runtime)** へ簡単にデプロイできるよう構成されています。

### 1. デプロイ事前準備
デプロイを実行する前に、以下のコマンドを使用して Google Cloud のアクティブプロジェクトを設定してください。

```bash
# デプロイ先プロジェクトの設定
gcloud config set project YOUR_PROJECT_ID

# アプリケーションデフォルト資格情報（ADC）の有効化
gcloud auth application-default login
```

### 2. デプロイの実行
各プロジェクトフォルダ（`basic-search-agent` または `travel-guide-japan`）に移動し、`make deploy` を実行します。

```bash
cd basic-search-agent
make deploy
```
> 💡 **補足**: `basic-search-agent` の `make deploy` は標準コマンドを呼び出しますが、`travel-guide-japan` ではコンピュート課金を節約（Scale-to-Zero）するため、リソースを抑制するカスタムスクリプト (`deploy.py`) 経由でデプロイが行われます。

### 📘 詳細な仕組みとトラブルシューティング
デプロイ時に実行される Terraform（API の有効化、IAM設定、BigQueryを用いたテレメトリ連携など）の詳細やトラブルシューティングについては、[詳細導入ガイド（docs/ARCHITECTURE.md）](./docs/ARCHITECTURE.md) を参照してください。

### 💰 コストと課金に関する注意点 (重要)
本プロジェクトで使用される **Google Search Grounding（Google検索ツール）** は、月 **5,000 プロンプトの無料枠**を超過すると **1,000クエリあたり $14 USD** の追加料金が発生します（料金は変更される場合があります。最新情報は [Vertex AI 料金ページ](https://cloud.google.com/vertex-ai/generative-ai/pricing) をご確認ください）。開発中の頻繁な起動テストや無限ループには十分ご注意ください。
* コンピュート課金を防ぐため、本サンプル (`travel-guide-japan`) ではアイドル時に料金がゼロになるよう、Terraform と `deploy.py` の両方で **`min_instances = 0` (Scale-to-Zero)** とメモリ削減 (`2Gi`) を強制設定しています。標準コマンド (`agents-cli deploy`) をそのまま叩くとデフォルトで常時稼働 (`min=1`) となってしまうため、このカスタムスクリプトを経由しています。
* テレメトリ保存用の GCS や BigQuery は通常無料枠内に収まりますが、不要になったリソースは削除することを推奨します。詳細は、[詳細導入ガイドの「9. コストに関する注意点」](./docs/ARCHITECTURE.md#9--cost--billing-cautions) をご確認ください。

---

## 🔗 参考リンク (Reference Links)

- [ADK 2.0 公式ドキュメント (Welcome to ADK 2.0)](https://adk.dev/2.0/) — ADK v2.0 の新機能やマイグレーション情報
- [ADK Python クイックスタート (Python Quickstart for ADK)](https://adk.dev/get-started/python/) — 導入手順とシステム要件（Python 3.10+）
- [google-adk-python GitHub リポジトリ](https://github.com/google/adk-python) — 公式の Python ADK 実装ソースコード
- [agents-cli Getting Started](https://google.github.io/agents-cli/guide/getting-started/) — CLI セットアップ手順とシステム要件（Python 3.11+）
- [agents-cli GitHub リポジトリ](https://github.com/google/agents-cli) — CLI のソースコードとリリースノート

---

## 📄 ライセンス

Copyright 2026 Google LLC. Licensed under the Apache License, Version 2.0.
