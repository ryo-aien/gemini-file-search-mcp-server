# Gemini File Search MCP Server - クイックスタートガイド

## 1. セットアップ

### 必要なもの
- Python 3.10以上
- Gemini APIキー（[Google AI Studio](https://makersuite.google.com/app/apikey)から取得）

### インストール手順

```bash
# 1. 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 依存関係のインストール
pip install -r requirements.txt

# 3. 環境変数の設定
cp .env.example .env
# .envファイルを編集してGEMINI_API_KEYを設定

# 4. サーバーの起動
python -m src.server
```

> **Tip:** 次回以降は `source venv/bin/activate` (Windows: `venv\Scripts\activate`) で仮想環境を有効化してからサーバーを起動してください。

## 2. Claude Desktopとの統合

Claude DesktopのMCP設定ファイルに以下を追加:

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

## 3. 基本的な使い方

### ステップ1: Storeを作成

Claude Desktopで以下のように入力:

```
Create a file search store named "Company Documents"
```

レスポンス例:
```json
{
  "store_name": "fileSearchStores/abc123",
  "display_name": "Company Documents",
  "status": "ACTIVE"
}
```

### ステップ2: ファイルをアップロード

```
Upload the file /path/to/employee-handbook.pdf to store fileSearchStores/abc123
with display name "Employee Handbook" and metadata {"category": "hr", "version": "2024"}
```

### ステップ3: ドキュメントを検索

```
Search in fileSearchStores/abc123 for "What is the vacation policy?"
```

レスポンス例:
```json
{
  "response": "Based on the employee handbook, the vacation policy allows...",
  "citations": [
    {
      "source": "fileSearchStores/abc123/documents/xyz789",
      "snippet": "Employees are entitled to 20 days of paid vacation...",
      "metadata": {"category": "hr"}
    }
  ],
  "num_citations": 1
}
```

### ステップ4: ドキュメント一覧を表示

```
List all documents in store fileSearchStores/abc123
```

## 4. よく使うコマンド

### Store管理

```bash
# Storeの一覧表示
List all file search stores

# Storeの削除
Delete the file search store fileSearchStores/abc123
```

### ドキュメント管理

```bash
# ドキュメントの詳細取得
Get document information for fileSearchStores/abc123/documents/xyz789

# ドキュメントの削除
Delete document fileSearchStores/abc123/documents/xyz789
```

### 高度な検索

```bash
# メタデータフィルタを使った検索
Search in fileSearchStores/abc123 for "security policy"
with metadata filter 'category="security"'

# 複数のStoreを検索
Search in fileSearchStores/abc123,fileSearchStores/def456
for "project timeline"
```

## 5. 対応ファイル形式

- **ドキュメント**: PDF, DOCX, DOC, ODT, RTF
- **テキスト**: TXT, MD, HTML, JSON, YAML
- **スプレッドシート**: CSV, XLSX, XLS
- **プレゼンテーション**: PPTX, PPT
- **コード**: Python, JavaScript, TypeScript, Java, C++, Go, Rust など150+種類

## 6. トラブルシューティング

### APIキーエラー
```
Error: Failed to initialize Gemini client
```
→ `.env`ファイルに正しいAPIキーが設定されているか確認

### ファイルアップロードエラー
```
Error: File too large
```
→ ファイルサイズが100MB以下であることを確認

### 検索結果が空
```
"num_citations": 0
```
→ ドキュメントの状態が`ACTIVE`になっているか確認（処理に数分かかる場合があります）

## 7. 次のステップ

- [README.md](./README.md) - 詳細なドキュメント
- [仕様書](./SPECIFICATION.md) - 完全な技術仕様
- テストの実行: `pytest tests/ -v`

## 8. サポート

問題が発生した場合:
1. ログを確認（`LOG_LEVEL=DEBUG`で詳細ログを有効化）
2. GitHubのIssuesで報告
3. ドキュメントを参照
