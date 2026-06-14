# travel-guide-japan

Simple ReAct agent
Agent generated with `agents-cli` version `0.4.0`

## Project Structure

```
travel-guide-japan/
├── app/         # Core agent code
│   ├── agent.py               # Main agent logic
│   ├── agent_runtime_app.py    # Agent Runtime application logic
│   └── app_utils/             # App utilities and helpers
├── tests/                     # Unit, integration, and load tests
├── GEMINI.md                  # AI-assisted development guide
└── pyproject.toml             # Project dependencies
```

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)

> ⚠️ **Note for Cloned Repositories**: 
> If you are cloning this repository to deploy it to your own Google Cloud project:
> 1. For Terraform deployments, copy `deployment/terraform/single-project/vars/env.tfvars.example` to `env.tfvars` and set your `project_id`.
> 2. `deployment_metadata.json` will be automatically generated upon your first successful `make deploy`.



## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |
| `agents-cli deploy`  | Deploy agent to Agent Runtime                                                                |
| `agents-cli publish gemini-enterprise` | Register deployed agent to Gemini Enterprise                    |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

## Deployment

```bash
gcloud config set project <your-project-id>

# デフォルト設定（CPU: 1, メモリ: 2Gi）でデプロイする場合
make deploy

# リソースやインスタンス数をカスタマイズしてデプロイする場合の例
make deploy ARGS="--cpu 2 --memory 4Gi --min-instances 1 --max-instances 5"
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.

## Troubleshooting (ハマったポイント)

今回の開発・デプロイにおいて直面したエラーとその解決策の備忘録です。

### 1. `deploy.py` 実行時の `ModuleNotFoundError`
- **症状**: `make deploy`（実態は `uv run python deploy.py`）を実行すると、`ModuleNotFoundError: No module named 'google.agents'` というエラーが発生。
- **原因**: `deploy.py` 内で `google.agents.cli` をインポートしていますが、`uv run` はローカルの仮想環境（`.venv`）のみを参照するため、グローバルに `uvx` でインストールされたCLIモジュールが見つからなかったため。
- **解決策**: `Makefile` の `deploy` ターゲットを `uv run --with google-agents-cli python deploy.py` に変更し、実行時に必要なパッケージを動的に解決させるようにしました。

### 2. コード編集時の `IndentationError` と文字化け
- **症状**: `app/agent.py` にて `IndentationError: unindent does not match any outer indentation level` が発生し、`make test` 等がすべて失敗。修復を試みる過程で文字化けも併発。
- **原因**: 手作業でのコード編集やコピペのミスにより、`get_jma_weather` 関数内の `try:` ブロックに対する `except` ブロックと関数の末尾 `return` 文が欠落してしまったため。
- **解決策**: 欠落していた `except Exception as e:` ブロックとエラー時の `return` 文を正しいインデント位置で復元し、構文エラーを解消しました。

## Execution Results

![実行結果1](docs/images/result-image1.png)
![実行結果2](docs/images/result-image2.png)

