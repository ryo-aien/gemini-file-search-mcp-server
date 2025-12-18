# Gemini API File Search MCP Server

Gemini API の **File Search**（フルマネージドRAG）を、Model Context Protocol（MCP）準拠の **リモートMCPサーバー** として提供します。

## 目次

- [概要](#概要)
- [主要機能](#主要機能)
- [サポートされるファイル形式](#サポートされるファイル形式)
- [ファイルサイズ制限](#ファイルサイズ制限)
- [技術スタック](#技術スタック)
- [クイックスタート](#クイックスタート)
- [uv のインストール](#uv-のインストール)
- [セットアップ](#セットアップ)
  - [前提条件](#前提条件)
  - [ローカル開発](#ローカル開発)
  - [Docker でのビルドと実行](#docker-でのビルドと実行)
- [Cloud Run へのデプロイ](#cloud-run-へのデプロイ)
- [認証設定](#認証設定)
- [使用方法](#使用方法)
- [テスト](#テスト)
- [ロギング](#ロギング)
- [トラブルシューティング](#トラブルシューティング)
- [ライセンス](#ライセンス)
- [参考資料](#参考資料)

## 概要

このプロジェクトは、Gemini API の File Search 機能を MCP サーバーとして公開し、Claude Desktop などの MCP クライアントから利用可能にします。Cloud Run 上にデプロイすることで、スケーラブルで可用性の高い RAG システムを構築できます。

## 主要機能

### Store 管理
- **create_store**: File Search Store を作成
- **list_stores**: Store の一覧を取得
- **get_store**: 特定の Store の詳細を取得
- **delete_store**: Store を削除

### Document 管理
- **upload_file**: ファイルを直接アップロードして Store に取り込み
- **import_file**: Files API からファイルをインポート
- **list_documents**: Document の一覧を取得
- **get_document**: 特定の Document の詳細を取得
- **delete_document**: Document を削除
- **update_metadata**: Document のメタデータを更新（再取り込み方式）

### 検索
- **search_documents**: File Search を使用してドキュメントを検索し、回答を生成
  - セマンティック検索
  - グラウンディング（引用情報）の取得
  - メタデータフィルタリング

### ユーティリティ
- **get_operation_status**: 長時間実行オペレーション（LRO）のステータスを取得
- **list_supported_formats**: サポートされるファイル形式の一覧を取得
- **get_store_statistics**: Store の統計情報を取得

## サポートされるファイル形式

### Application 系
- PDF: `application/pdf`
- JSON: `application/json`
- Microsoft Office: `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-powerpoint`
- Office Open XML: `application/vnd.openxmlformats-officedocument.*`
- Archive: `application/zip`, `application/x-tar`, `application/gzip`

### Text 系
- Plain text: `text/plain`
- Markdown: `text/markdown`
- CSV: `text/csv`
- HTML/XML: `text/html`, `text/xml`
- Code: `text/x-python`, `text/x-java`, `text/x-go`, `text/x-c`, `text/x-rust`, `text/javascript`, `text/x-typescript`

詳細は `mcp_list_supported_formats` ツールで確認できます。

## ファイルサイズ制限

- **1ドキュメントあたり**: 最大 100MB
- **Store 総容量** (tier 依存):
  - Free: 1GB
  - Tier1: 10GB
  - Tier2: 100GB
  - Tier3: 1TB
- **推奨**: 1 Store は 20GB 未満（レイテンシ最適化）

## 技術スタック

- **言語**: Python 3.10+
- **MCP フレームワーク**: FastMCP
- **Gemini SDK**: `google-genai`
- **実行環境**: GCP Cloud Run
- **コンテナ**: Docker + uv

## クイックスタート

最速で動かすための手順:

```bash
# 0. uv がインストールされていない場合は先にインストール
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# または以下の「uv のインストール」セクションを参照

# 1. リポジトリをクローン
git clone <repository-url>
cd gemini-file-search-mcp

# 2. 仮想環境を作成してアクティベート
uv venv
source .venv/bin/activate  # Linux/macOS
# または .venv\Scripts\activate.bat  # Windows

# 3. 依存関係をインストール
uv pip install -e .

# 4. 環境変数を設定
cp .env.example .env
# エディタで .env を開き、GEMINI_API_KEY を設定

# 5. サーバーを起動
python server.py
```

サーバーが起動したら、`http://localhost:8080/mcp` でアクセスできます。

## uv のインストール

uv は高速な Python パッケージマネージャーです。以下のいずれかの方法でインストールできます。

### Linux / macOS

#### 推奨: インストールスクリプトを使用

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

インストール後、シェルを再起動するか、以下を実行:

```bash
source $HOME/.cargo/env
```

#### Homebrew を使用（macOS）

```bash
brew install uv
```

#### pip を使用

```bash
pip install uv
```

### Windows

#### PowerShell を使用（推奨）

PowerShell を**管理者権限**で開き、以下を実行:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### winget を使用

```powershell
winget install --id=astral-sh.uv -e
```

#### scoop を使用

```powershell
scoop install uv
```

#### pip を使用

```powershell
pip install uv
```

### インストール確認

```bash
# uv がインストールされているか確認
uv --version

# 出力例: uv 0.5.0
```

### uv が使えない場合の代替方法

uv をインストールできない環境では、標準の `pip` と `venv` を使用できます:

```bash
# 仮想環境を作成
python -m venv .venv

# アクティベート
source .venv/bin/activate  # Linux/macOS
# または .venv\Scripts\activate.bat  # Windows

# 依存関係をインストール
pip install -e .

# サーバーを起動
python server.py
```

## セットアップ

### 前提条件

1. **Python 3.10 以上**
   ```bash
   # バージョン確認
   python --version
   # 出力例: Python 3.11.5
   ```

2. **[uv](https://github.com/astral-sh/uv) のインストール**

   詳細なインストール手順は [uv のインストール](#uv-のインストール) セクションを参照してください。

   簡易版:
   ```bash
   # Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

   # または pip でインストール
   pip install uv
   ```

3. **Gemini API キーの取得**

   [Google AI Studio](https://aistudio.google.com/app/apikey) でアカウントを作成し、API キーを取得してください。

   API キーは無料で取得できます（一部機能に制限あり）。

### ローカル開発

#### 方法1: 仮想環境を使用（推奨）

1. リポジトリをクローン:
```bash
git clone <repository-url>
cd gemini-file-search-mcp
```

2. 仮想環境を作成:
```bash
# uv で仮想環境を作成
uv venv

# または Python の venv を使用
python -m venv .venv
```

3. 仮想環境をアクティベート:
```bash
# Linux/macOS の場合
source .venv/bin/activate

# Windows (PowerShell) の場合
.venv\Scripts\Activate.ps1

# Windows (Command Prompt) の場合
.venv\Scripts\activate.bat
```

4. 依存関係をインストール:
```bash
# 仮想環境内で uv を使用
uv pip install -e .

# または pip を使用
pip install -e .
```

5. 環境変数を設定:
```bash
# .env ファイルを作成
cp .env.example .env
# エディタで .env を開き、GEMINI_API_KEY を設定
```

または直接作成:
```bash
cat > .env << EOF
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8080
LOG_LEVEL=INFO
EOF
```

6. サーバーを起動:
```bash
python server.py
```

7. 終了時は仮想環境を無効化:
```bash
deactivate
```

#### 方法2: uv で直接インストール

1. リポジトリをクローン:
```bash
git clone <repository-url>
cd gemini-file-search-mcp
```

2. 依存関係をインストール（システム Python に直接インストール）:
```bash
uv pip install -e .
```

3. 環境変数を設定:
```bash
cp .env.example .env
# エディタで .env を開き、GEMINI_API_KEY を設定
```

4. サーバーを起動:
```bash
python server.py
```

サーバーは `http://localhost:8080/mcp` でリクエストを受け付けます。

### Docker でのビルドと実行

1. Docker イメージをビルド:
```bash
docker build -t gemini-file-search-mcp .
```

2. コンテナを実行:
```bash
docker run -p 8080:8080 -e GEMINI_API_KEY=your_api_key gemini-file-search-mcp
```

## Cloud Run へのデプロイ

### 手動デプロイ

1. Google Cloud プロジェクトを設定:
```bash
gcloud config set project YOUR_PROJECT_ID
```

2. Cloud Run にデプロイ:
```bash
gcloud run deploy gemini-file-search-mcp \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_gemini_api_key_here
```

### Cloud Build を使用したデプロイ

`cloudbuild.yaml` が含まれている場合:

```bash
# 認証トークンを生成（推奨）
TOKEN=$(openssl rand -base64 32)

# デプロイ
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_GEMINI_API_KEY="your-gemini-key",_MCP_AUTH_TOKENS="${TOKEN}:claude-desktop"

# トークンを安全に保存
echo "Your MCP auth token: ${TOKEN}"
```

**重要**: 生成されたトークンは、後でクライアント側の設定に使用するため、安全に保存してください。

## 認証設定

バージョン 0.2.0 以降、このMCPサーバーは **Bearer Token認証** をサポートしています。本番環境では、不正アクセスを防ぐため認証の有効化を強く推奨します。

### 認証の概要

- **認証方式**: Bearer Token（HTTP Authorizationヘッダー）
- **実装**: FastMCPの組み込み `StaticTokenVerifier` を使用
- **トークン形式**: `token:client_id`（カンマ区切りで複数指定可能）
- **環境変数**: `MCP_AUTH_TOKENS`

### トークンの生成

強力なランダムトークンを生成することを推奨します:

```bash
# OpenSSL を使用（推奨）
openssl rand -base64 32

# 出力例: 8mQ7xK9pL2vR5nW3bC1dE4fG6hJ7iK8lM9nO0pQ1rS2=
```

### サーバー側の設定

#### ローカル開発環境

`.env` ファイルに認証トークンを追加:

```bash
# .env ファイルを編集
GEMINI_API_KEY=your_gemini_api_key_here
MCP_AUTH_TOKENS=test-token-123:local-dev
MCP_TRANSPORT=stdio
```

複数のクライアントをサポートする場合:

```bash
MCP_AUTH_TOKENS=token1:claude-desktop,token2:mobile-app,token3:web-client
```

#### Cloud Run環境

**方法1: Cloud Build経由（推奨）**

```bash
# 強力なトークンを生成
TOKEN=$(openssl rand -base64 32)

# デプロイ時にトークンを設定
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_GEMINI_API_KEY="your-key",_MCP_AUTH_TOKENS="${TOKEN}:production-client"
```

**方法2: 環境変数を直接更新**

```bash
# 既存のCloud Runサービスの環境変数を更新
gcloud run services update gemini-file-search-mcp \
  --region=us-central1 \
  --set-env-vars="MCP_AUTH_TOKENS=your-token:client-id"
```

**方法3: Secret Manager使用（本番環境推奨）**

```bash
# シークレットを作成
echo -n "your-strong-token:production-client" | \
  gcloud secrets create mcp-auth-tokens --data-file=-

# Cloud RunでSecretを使用
gcloud run services update gemini-file-search-mcp \
  --region=us-central1 \
  --update-secrets=MCP_AUTH_TOKENS=mcp-auth-tokens:latest
```

### クライアント側の設定

#### Claude Desktop

Claude Desktopの設定ファイル（`claude_desktop_config.json`）に認証ヘッダーを追加:

**設定ファイルの場所**:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**設定例**:

```json
{
  "mcpServers": {
    "gemini-file-search": {
      "url": "https://your-cloud-run-url.run.app/mcp",
      "headers": {
        "Authorization": "Bearer your-auth-token-here"
      }
    }
  }
}
```

**注意**: 公式にはClaude Desktopはstdioトランスポートのみをサポートしています。HTTPトランスポートを使用する場合は、Claude APIまたはAgent SDKの利用を検討してください。

#### Claude API / Agent SDK

Claude APIやAgent SDKからMCPサーバーに接続する場合:

```typescript
import { Anthropic } from '@anthropic-ai/sdk';

const anthropic = new Anthropic();

const response = await anthropic.beta.messages.create({
  model: "claude-sonnet-4-5",
  max_tokens: 1000,
  messages: [{ role: "user", content: "List available tools" }],
  mcp_servers: [
    {
      type: "url",
      url: "https://your-cloud-run-url.run.app/mcp",
      name: "gemini-file-search",
      authorization_token: process.env.MCP_AUTH_TOKEN
    }
  ],
  tools: [
    {
      type: "mcp_toolset",
      mcp_server_name: "gemini-file-search"
    }
  ],
  betas: ["mcp-client-2025-11-20"]
});
```

#### HTTPクライアント（curl等）

```bash
# 認証なしのリクエスト（401エラーになる）
curl https://your-cloud-run-url.run.app/mcp

# 認証ありのリクエスト
curl -H "Authorization: Bearer your-token-here" \
  https://your-cloud-run-url.run.app/mcp
```

### 認証のテスト

#### ローカルテスト

```bash
# 1. .envファイルにトークンを設定
echo 'MCP_AUTH_TOKENS=test-token-123:local-dev' >> .env

# 2. サーバーを起動
python server.py

# 3. 別のターミナルで認証テスト
# 正常なリクエスト
curl -H "Authorization: Bearer test-token-123" http://localhost:8080/mcp

# 認証なし（401エラーになることを確認）
curl http://localhost:8080/mcp

# 無効なトークン（401エラーになることを確認）
curl -H "Authorization: Bearer invalid-token" http://localhost:8080/mcp
```

#### Cloud Runテスト

```bash
# pytestでCloud Runサービスをテスト
pytest tests/test_cloud_run.py -v \
  --url=https://your-cloud-run-url.run.app/mcp \
  --token=your-deployed-token
```

### 認証の無効化

開発環境で認証を無効にする場合、`MCP_AUTH_TOKENS` 環境変数を設定しないでください:

```bash
# .env ファイルから削除または空にする
# MCP_AUTH_TOKENS=
```

サーバー起動時に以下のログが表示されます:
```
WARNING - MCP_AUTH_TOKENS not set - authentication is DISABLED
```

**注意**: 本番環境では必ず認証を有効にしてください。

### セキュリティのベストプラクティス

#### 1. 強力なトークンの使用

```bash
# 32文字以上のランダムトークンを生成
openssl rand -base64 32
```

#### 2. トークンの定期的なローテーション

3〜6ヶ月ごとにトークンを更新することを推奨:

```bash
# 新しいトークンを生成
NEW_TOKEN=$(openssl rand -base64 32)

# Secret Managerで新バージョンを作成
gcloud secrets versions add mcp-auth-tokens \
  --data-file=- <<EOF
${NEW_TOKEN}:production-client
EOF

# クライアント側の設定を更新
# （旧トークンも一時的に有効にしてダウンタイムなし移行も可能）
```

#### 3. トークンの安全な保管

- **絶対にコミットしない**: `.env` ファイルは `.gitignore` に含める
- **Secret Manager使用**: 本番環境ではGCP Secret Managerを使用
- **環境ごとに異なるトークン**: 開発・ステージング・本番で異なるトークンを使用

#### 4. ログ監視

不正なアクセス試行を監視:

```bash
# Cloud Runのログを確認
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=WARNING' \
  --limit=50 \
  --format=json
```

#### 5. HTTPS必須

Cloud Runは自動的にHTTPSを強制しますが、カスタムドメインを使用する場合は必ずHTTPSを設定してください。

### トラブルシューティング

#### 401 Unauthorized エラー

**原因**: トークンが無効または存在しない

**解決方法**:
```bash
# Cloud Runの環境変数を確認
gcloud run services describe gemini-file-search-mcp \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)"

# 環境変数を更新
gcloud run services update gemini-file-search-mcp \
  --region=us-central1 \
  --set-env-vars="MCP_AUTH_TOKENS=new-token:client-id"
```

#### 認証が有効にならない

**原因**: `MCP_AUTH_TOKENS`環境変数が正しく設定されていない

**解決方法**: ログを確認
```bash
gcloud run logs read gemini-file-search-mcp --region=us-central1 --limit=50
```

"Bearer token authentication enabled"メッセージが表示されない場合、環境変数の設定を確認してください。

#### トークン形式エラー

**正しい形式**:
- 単一クライアント: `token:client_id`
- 複数クライアント: `token1:client1,token2:client2`

**NGな例**:
- `token`（client_id なし）
- `token:client1:extra`（コロンが多すぎる）

## 使用方法

### MCP クライアントから接続

Claude Desktop などの MCP クライアントから接続する場合、以下の設定を使用します:

**認証なしの場合**（開発環境のみ推奨）:

```json
{
  "mcpServers": {
    "gemini-file-search": {
      "url": "https://your-cloud-run-url/mcp",
      "transport": "http"
    }
  }
}
```

**認証ありの場合**（本番環境推奨）:

```json
{
  "mcpServers": {
    "gemini-file-search": {
      "url": "https://your-cloud-run-url/mcp",
      "headers": {
        "Authorization": "Bearer your-auth-token-here"
      }
    }
  }
}
```

詳細な認証設定については、[認証設定](#認証設定)セクションを参照してください。

### ツールの使用例

#### 1. Store を作成

```json
{
  "tool": "mcp_create_store",
  "arguments": {
    "display_name": "My Knowledge Base"
  }
}
```

#### 2. ファイルをアップロード

```json
{
  "tool": "mcp_upload_file",
  "arguments": {
    "store_name": "fileSearchStores/abc123",
    "file_bytes_base64": "<base64-encoded-file-content>",
    "display_name": "example.pdf",
    "mime_type": "application/pdf",
    "custom_metadata": [
      {
        "key": "category",
        "string_value": "technical"
      }
    ]
  }
}
```

#### 3. ドキュメントを検索

```json
{
  "tool": "mcp_search_documents",
  "arguments": {
    "store_names": ["fileSearchStores/abc123"],
    "query": "What is the main topic of the document?",
    "model": "gemini-2.5-flash",
    "metadata_filter": "category = 'technical'"
  }
}
```

#### 4. オペレーションのステータスを確認

```json
{
  "tool": "mcp_get_operation_status",
  "arguments": {
    "operation_name": "operations/xyz789"
  }
}
```

### Python スクリプトからの使用例

MCP クライアントを使わずに、Python から直接ツールを呼び出すこともできます:

```python
import asyncio
import base64
from tools.store_tools import create_store
from tools.document_tools import upload_file
from tools.search_tools import search_documents

async def main():
    # Store を作成
    store = await create_store(display_name="Test Store")
    store_name = store["store_name"]
    print(f"Created store: {store_name}")

    # ファイルを読み込んで Base64 エンコード
    with open("example.txt", "rb") as f:
        file_bytes = f.read()
    file_bytes_base64 = base64.b64encode(file_bytes).decode("utf-8")

    # ファイルをアップロード
    upload_result = await upload_file(
        store_name=store_name,
        file_bytes_base64=file_bytes_base64,
        display_name="example.txt",
        mime_type="text/plain",
    )
    print(f"Upload operation: {upload_result['operation_name']}")

    # ドキュメントを検索（アップロード完了後）
    search_result = await search_documents(
        store_names=[store_name],
        query="この文書の要約を教えてください",
    )
    print(f"Answer: {search_result['answer_text']}")

if __name__ == "__main__":
    # 環境変数 GEMINI_API_KEY が必要
    asyncio.run(main())
```

## メタデータ更新の仕様

このサーバーでは、Document のメタデータ更新に **方式1（delete + 再取り込み）** を採用しています。

**理由**: Gemini API の公開ドキュメントに Document の `patch` または `update` API が確認できないため、既存ドキュメントを削除し、新しいメタデータで再アップロードする方式を実装しています。

**注意**: この方式では、Document のリソース名（`document_name`）が変わる可能性があります。

## テスト

### テスト環境のセットアップ

テストを実行する前に、開発用の依存関係をインストールします:

```bash
# 仮想環境をアクティベート（まだの場合）
source .venv/bin/activate  # Linux/macOS
# または .venv\Scripts\activate  # Windows

# テスト用の依存関係をインストール
uv pip install -e ".[dev]"
# または
pip install pytest pytest-asyncio
```

### ローカルテスト

```bash
# 仮想環境内で実行
pytest tests/test_local.py -v

# または詳細なログ出力
pytest tests/test_local.py -v -s
```

### Cloud Run テスト

**認証なしの場合**:

```bash
# 仮想環境内で実行
pytest tests/test_cloud_run.py -v --url=https://your-cloud-run-url/mcp
```

**認証ありの場合**（推奨）:

```bash
# 認証トークンを指定してテスト
pytest tests/test_cloud_run.py -v \
  --url=https://your-cloud-run-url/mcp \
  --token=your-auth-token-here
```

## ロギング

環境変数 `LOG_LEVEL` でログレベルを制御できます:

- `DEBUG`: 詳細なデバッグ情報
- `INFO`: 一般的な情報（デフォルト）
- `WARNING`: 警告メッセージ
- `ERROR`: エラーメッセージ

## トラブルシューティング

### uv 関連

#### uv コマンドが見つからない

```
bash: uv: command not found
```

**解決方法**:

1. **パスが通っているか確認**:
   ```bash
   # Linux/macOS の場合
   echo $PATH | grep cargo

   # パスに ~/.cargo/bin が含まれていない場合は追加
   source $HOME/.cargo/env

   # または .bashrc / .zshrc に追加
   echo 'source $HOME/.cargo/env' >> ~/.bashrc
   source ~/.bashrc
   ```

2. **シェルを再起動**:
   ```bash
   # 新しいターミナルウィンドウを開く
   # または
   exec $SHELL
   ```

3. **uv を再インストール**:
   ```bash
   # 既存の uv を削除
   rm -rf ~/.cargo/bin/uv

   # 再インストール
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. **代替: pip でインストール**:
   ```bash
   pip install --user uv
   # ~/.local/bin にインストールされるので、パスに追加
   export PATH="$HOME/.local/bin:$PATH"
   ```

#### Windows で uv が実行できない

**PowerShell の実行ポリシーエラー**:
```
実行ポリシーの変更
```

**解決方法**:
```powershell
# PowerShell を管理者権限で開き、実行ポリシーを変更
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# または一時的にバイパス
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 仮想環境関連

#### 仮想環境がアクティベートされているか確認

```bash
# プロンプトに (.venv) が表示されているか確認
# または以下のコマンドで確認
which python  # Linux/macOS
where python  # Windows
# 出力に .venv が含まれていれば仮想環境がアクティブ
```

#### 仮想環境を削除して再作成

```bash
# 仮想環境を無効化
deactivate

# 仮想環境を削除
rm -rf .venv  # Linux/macOS
# または rmdir /s .venv  # Windows

# 仮想環境を再作成
uv venv
source .venv/bin/activate
uv pip install -e .
```

### GEMINI_API_KEY が設定されていない

```
ValueError: GEMINI_API_KEY environment variable is required
```

**解決方法**:
1. `.env` ファイルが存在するか確認: `ls -la .env`
2. `.env` ファイル内に `GEMINI_API_KEY=...` が設定されているか確認
3. 直接環境変数を設定する場合:
   ```bash
   export GEMINI_API_KEY=your_api_key_here  # Linux/macOS
   # または
   set GEMINI_API_KEY=your_api_key_here  # Windows
   ```

### モジュールが見つからない (ModuleNotFoundError)

```
ModuleNotFoundError: No module named 'fastmcp'
```

**解決方法**:
1. 仮想環境がアクティベートされているか確認
2. 依存関係を再インストール:
   ```bash
   uv pip install -e .
   ```

### ファイルサイズ超過

```
ValueError: File size (150.00 MB) exceeds 100MB limit
```

ファイルサイズを 100MB 以下に圧縮するか、分割してアップロードしてください。

### メタデータ数の上限超過

```
ValueError: Maximum 20 custom metadata entries allowed per document
```

カスタムメタデータは 1 ドキュメントあたり最大 20 件です。

## ライセンス

MIT License

## 参考資料

- [Gemini API File Search ドキュメント](https://ai.google.dev/gemini-api/docs/file-search)
- [FastMCP ドキュメント](https://github.com/jlowin/fastmcp)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Google Cloud Run](https://cloud.google.com/run)
