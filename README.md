# Gemini File Search MCP Server

Gemini API の File Search を Model Context Protocol (MCP) 準拠のリモートサーバーとして提供する実装です。FastMCP で HTTP (streamable-http) トランスポートのツール群を公開し、ストア管理・ドキュメント取り込み・検索・ユーティリティ操作を行えます。

## 環境変数
- `GEMINI_API_KEY` (必須): Gemini API へのアクセスキー。
- `PORT` (任意): サーバーの待受ポート。デフォルト `8080`。
- `LOG_LEVEL` (任意): ログレベル。デフォルト `INFO`。
- `GENAI_BASE_URL` (任意): Generative Language API のベース URL。デフォルトは公式エンドポイント。

## 起動方法
依存をインストールした上で、次のコマンドで起動できます。

```bash
# 開発向けの追加ツールを含めてインストールする場合
pip install -e .[dev]

# サーバー起動
python server.py
```

Cloud Run などでデプロイする場合も同じエントリーポイントを利用します。

## Docker/Cloud Run デプロイ
リポジトリ直下に用意した `Dockerfile` を使ってイメージをビルドできます。

```bash
# ローカルビルド
docker build -t gemini-file-search-mcp-server .

# 実行例
docker run --rm -p 8080:8080 -e GEMINI_API_KEY=YOUR_KEY gemini-file-search-mcp-server
```

Cloud Run へデプロイする場合は、上記のイメージを Artifact Registry に push した上で
`gcloud run deploy` から参照してください。
