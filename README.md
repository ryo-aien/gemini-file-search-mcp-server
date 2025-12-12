# Gemini File Search MCP Server

GoogleのGemini API File Search機能を活用した、強力なファイル検索・取得機能を提供するModel Context Protocol (MCP) サーバーです。ClaudeをはじめとするMCPクライアントから、Geminiの高度なRAG（Retrieval-Augmented Generation）機能を利用できます。

## 主な機能

- **Store管理**: File Search Storeの作成と管理
- **ドキュメントアップロード**: 様々なファイル形式のアップロードとインデックス化
- **セマンティック検索**: 引用情報付きの強力なセマンティック検索
- **メタデータフィルタリング**: カスタムメタデータによる検索結果の絞り込み
- **ドキュメント管理**: ドキュメントの一覧表示、取得、削除
- **自動リトライ**: 一時的なエラーに対する自動リトライ機能
- **詳細なログ**: デバッグとモニタリングのための構造化ログ

## 対応ファイル形式

テキストファイル、ドキュメント、スプレッドシート、プレゼンテーション、コードファイルなど:
- **ドキュメント**: PDF, DOCX, DOC, ODT, RTF
- **テキスト**: TXT, MD, HTML, JSON, YAML, XML
- **スプレッドシート**: CSV, XLSX, XLS, ODS
- **プレゼンテーション**: PPTX, PPT, ODP
- **コード**: Python, JavaScript, TypeScript, Java, C++, Go, Rust など150種類以上

## インストール

### 必要な環境

- Python 3.10以上
- Gemini APIキー（[Google AI Studio](https://makersuite.google.com/app/apikey)から取得）

### セットアップ手順

1. リポジトリをクローン:
```bash
git clone <repository-url>
cd gemini-file-search-mcp
```

2. 仮想環境を作成して有効化:

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (コマンドプロンプト):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

3. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

4. 環境変数を設定:
```bash
cp .env.example .env
# .envファイルを編集してGEMINI_API_KEYを設定
```

5. サーバーを起動:
```bash
python -m src.server
```

> **Note:** サーバーを使用する際は、毎回仮想環境を有効化してください（`source venv/bin/activate` または `venv\Scripts\activate`）

## 設定

`.env`ファイルを編集してサーバーを設定します:

```env
# 必須: Gemini APIキー
GEMINI_API_KEY=your_api_key_here

# オプション: 使用するモデル（デフォルト: gemini-2.0-flash-exp）
DEFAULT_MODEL=gemini-2.0-flash-exp

# オプション: チャンキング設定
DEFAULT_CHUNK_SIZE=200
DEFAULT_CHUNK_OVERLAP=20

# オプション: ファイルサイズ上限（MB）
MAX_FILE_SIZE_MB=100

# オプション: 検索クエリあたりの最大Store数
MAX_STORES_PER_QUERY=5

# オプション: ログレベル
LOG_LEVEL=INFO
```

## MCPツール一覧

### Store管理

#### `create_file_search_store`
ドキュメントインデックス用の新しいFile Search Storeを作成します。

**入力:**
```json
{
  "display_name": "My Knowledge Base",
  "description": "オプションの説明"
}
```

**出力:**
```json
{
  "store_name": "fileSearchStores/xxx",
  "display_name": "My Knowledge Base",
  "status": "ACTIVE",
  "created_at": "2024-01-01T00:00:00",
  "num_documents": 0,
  "storage_bytes": 0
}
```

#### `list_file_search_stores`
すべてのFile Search Storeを一覧表示します。

**入力:**
```json
{
  "page_size": 10
}
```

**出力:**
```json
{
  "stores": [
    {
      "name": "fileSearchStores/xxx",
      "display_name": "My Knowledge Base",
      "num_documents": 5,
      "storage_bytes": 1024000,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "total_count": 1
}
```

#### `delete_file_search_store`
File Search Storeとそのすべてのドキュメントを削除します。

**入力:**
```json
{
  "store_name": "fileSearchStores/xxx"
}
```

### ドキュメント管理

#### `upload_file_to_store`
インデックス化のためにStoreにファイルをアップロードします。

**入力:**
```json
{
  "store_name": "fileSearchStores/xxx",
  "file_path": "/path/to/document.pdf",
  "display_name": "ユーザーマニュアル",
  "metadata": {
    "category": "documentation",
    "version": "1.0"
  },
  "chunking_config": {
    "chunk_size": 200,
    "chunk_overlap": 20
  }
}
```

**出力:**
```json
{
  "document_name": "fileSearchStores/xxx/documents/yyy",
  "display_name": "ユーザーマニュアル",
  "status": "PROCESSING",
  "file_size_bytes": 1024000
}
```

#### `list_documents`
Store内のすべてのドキュメントを一覧表示します。

**入力:**
```json
{
  "store_name": "fileSearchStores/xxx",
  "page_size": 10
}
```

#### `get_document`
特定のドキュメントの情報を取得します。

**入力:**
```json
{
  "document_name": "fileSearchStores/xxx/documents/yyy"
}
```

#### `delete_document`
Storeからドキュメントを削除します。

**入力:**
```json
{
  "document_name": "fileSearchStores/xxx/documents/yyy"
}
```

### 検索

#### `search_documents`
セマンティック検索を使用してドキュメントを検索します。

**入力:**
```json
{
  "store_names": ["fileSearchStores/xxx"],
  "query": "パスワードをリセットするにはどうすればよいですか？",
  "model": "gemini-2.0-flash-exp",
  "metadata_filter": "category=\"documentation\"",
  "max_results": 10
}
```

**出力:**
```json
{
  "response": "パスワードをリセットするには...",
  "citations": [
    {
      "source": "fileSearchStores/xxx/documents/yyy",
      "snippet": "「パスワードを忘れた」リンクをクリックして...",
      "metadata": {
        "category": "documentation"
      }
    }
  ],
  "grounding_metadata": {},
  "num_citations": 1
}
```

## 使用例

### Claude Desktopとの連携

Claude DesktopのMCP設定に以下を追加します:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gemini-file-search": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/gemini-file-search-mcp",
      "env": {
        "GEMINI_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### ローカル実行

```json
{
  "mcpServers": {
    "gemini-file-search": {
      "command": "/bin/bash",
      "args": [
        "-c",
        "cd /path/to/gemini-file-search-mcp && source venv/bin/activate && exec python -m src.server"
      ],
      "env": {
        "GEMINI_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Cloud Run経由で使用

Cloud Runにデプロイした場合：

```json
{
  "mcpServers": {
    "gemini-file-search": {
      "url": "https://your-service-url.run.app/mcp"
    }
  }
}
```

詳細は [CLOUD_RUN_DEPLOYMENT.md](./CLOUD_RUN_DEPLOYMENT.md) を参照してください。

### 基本的なワークフロー

1. **Storeを作成:**
```
"会社ドキュメント"という名前のfile search storeを作成してください
```

2. **ドキュメントをアップロード:**
```
/path/to/employee-handbook.pdfをfileSearchStores/xxxにアップロードしてください
```

3. **検索:**
```
fileSearchStores/xxxで"休暇ポリシーは何ですか？"を検索してください
```

## Cloud Runへのデプロイ

### クイックスタート

```bash
# 環境変数を設定
export GCP_PROJECT_ID="your-gcp-project-id"
export GEMINI_API_KEY="your_gemini_api_key"

# デプロイ
chmod +x deploy_cloudrun.sh
./deploy_cloudrun.sh
```

### 手動デプロイ

```bash
# イメージをビルド
gcloud builds submit --tag gcr.io/${GCP_PROJECT_ID}/gemini-file-search-mcp

# Cloud Runにデプロイ
gcloud run deploy gemini-file-search-mcp \
    --image gcr.io/${GCP_PROJECT_ID}/gemini-file-search-mcp \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY}
```

詳細なデプロイ手順は [CLOUD_RUN_DEPLOYMENT.md](./CLOUD_RUN_DEPLOYMENT.md) を参照してください。

## API制限

### Gemini APIクォータ

- **ファイルサイズ**: ファイルあたり最大100MB
- **Store制限**: プロジェクトあたり最大10個
- **ストレージ容量**:
  - 無料枠: 1GB
  - 有料枠: 最大1TB
- **同時検索**: クエリあたり最大5個のStore

### 料金

- **インデックス化**: 100万トークンあたり$0.15（初回のみ）
- **ストレージ**: 無料
- **クエリ埋め込み**: 無料
- **取得されたコンテキスト**: 標準のコンテキストトークン料金

## 開発

### テストの実行

```bash
# 開発用依存関係をインストール
pip install -e ".[dev]"

# テストを実行
pytest tests/ -v

# カバレッジ付きでテストを実行
pytest tests/ --cov=src --cov-report=html
```

### コード品質

```bash
# コードをフォーマット
black src/ tests/

# コードをリント
ruff check src/ tests/

# 型チェック
mypy src/
```

## アーキテクチャ

```
┌─────────────┐
│   Claude    │
│  (Client)   │
└──────┬──────┘
       │ MCP Protocol
       │
┌──────▼──────────────────────┐
│  MCP Server (Python)        │
│  ┌────────────────────┐     │
│  │ Tool Handlers      │     │
│  ├────────────────────┤     │
│  │ Gemini API Client  │     │
│  └────────────────────┘     │
└──────┬──────────────────────┘
       │ HTTPS
       │
┌──────▼──────────────────────┐
│  Gemini API                 │
│  ┌────────────────────┐     │
│  │ File Search Store  │     │
│  │ Vector Embeddings  │     │
│  └────────────────────┘     │
└─────────────────────────────┘
```

## トラブルシューティング

### APIキーの問題

APIキーエラーが発生した場合:
1. `.env`ファイルでキーが正しいことを確認
2. File Search APIアクセスが有効になっていることを確認
3. クォータ制限を超えていないことを確認

### ファイルアップロードの失敗

アップロードが失敗する場合:
1. ファイル形式がサポートされているか確認
2. ファイルサイズが100MB以下であることを確認
3. ファイルパスが正しくアクセス可能であることを確認
4. ファイルのアクセス権限を確認

### 検索結果が空

検索結果が空の場合:
1. ドキュメントの処理が完了するまで待機（ステータスを確認）
2. ドキュメントがACTIVE状態であることを確認
3. より広範な検索クエリを試す
4. メタデータフィルタが正しいことを確認

## コントリビューション

コントリビューションを歓迎します！以下の手順に従ってください:
1. リポジトリをフォーク
2. 機能ブランチを作成
3. 新機能のテストを追加
4. すべてのテストが通ることを確認
5. プルリクエストを送信

## ライセンス

MIT License - 詳細はLICENSEファイルを参照してください

## サポート

問題や質問がある場合:
- GitHub Issues: [repository-url]/issues
- ドキュメント: [repository-url]/wiki

## 謝辞

- [Model Context Protocol](https://modelcontextprotocol.io/)を使用して構築
- [Gemini API](https://ai.google.dev/)を利用
- AIアプリケーションにおけるより良いドキュメント検索の必要性に触発されて開発
