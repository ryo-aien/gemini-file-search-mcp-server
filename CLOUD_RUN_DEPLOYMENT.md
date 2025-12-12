# Cloud Run デプロイガイド

Gemini File Search MCP ServerをGCP Cloud Runにデプロイする手順です。

## 前提条件

- Google Cloud Platform (GCP) アカウント
- Google Cloud SDK (gcloud) がインストール済み
- Gemini API キー
- Cloud Run API が有効化されている

## セットアップ手順

### 1. GCPプロジェクトの設定

```bash
# GCPプロジェクトIDを設定
export GCP_PROJECT_ID="your-gcp-project-id"
export GCP_REGION="us-central1"  # またはお好みのリージョン

# gcloudでプロジェクトを設定
gcloud config set project ${GCP_PROJECT_ID}
```

### 2. 必要なAPIを有効化

```bash
# Cloud Run API を有効化
gcloud services enable run.googleapis.com

# Container Registry API を有効化
gcloud services enable containerregistry.googleapis.com

# Cloud Build API を有効化
gcloud services enable cloudbuild.googleapis.com
```

### 3. Gemini API キーを設定

```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

### 4. デプロイスクリプトに実行権限を付与

```bash
chmod +x deploy_cloudrun.sh
```

### 5. Cloud Runにデプロイ

```bash
./deploy_cloudrun.sh
```

または、手動でデプロイ：

```bash
# Docker イメージをビルド
gcloud builds submit --tag gcr.io/${GCP_PROJECT_ID}/gemini-file-search-mcp

# Cloud Run にデプロイ
gcloud run deploy gemini-file-search-mcp \
    --image gcr.io/${GCP_PROJECT_ID}/gemini-file-search-mcp \
    --platform managed \
    --region ${GCP_REGION} \
    --allow-unauthenticated \
    --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY} \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10
```

## デプロイ後の確認

### ヘルスチェック

```bash
SERVICE_URL=$(gcloud run services describe gemini-file-search-mcp \
    --platform managed \
    --region ${GCP_REGION} \
    --format 'value(status.url)')

curl ${SERVICE_URL}/health
```

期待されるレスポンス：
```json
{
  "status": "healthy"
}
```

### ツール一覧の取得

```bash
curl -X POST ${SERVICE_URL}/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

## Claude Desktopとの連携

デプロイが完了したら、Claude Desktopの設定ファイルを更新します。

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gemini-file-search": {
      "url": "https://your-service-url.run.app/mcp"
    }
  }
}
```

**注意**: `your-service-url.run.app` を実際のCloud Run URLに置き換えてください。

## 環境変数の設定

Cloud Runサービスで設定可能な環境変数：

| 環境変数 | 説明 | デフォルト |
|---------|------|-----------|
| `GEMINI_API_KEY` | Gemini API キー (必須) | - |
| `DEFAULT_MODEL` | 使用するモデル | `gemini-2.0-flash-exp` |
| `LOG_LEVEL` | ログレベル | `INFO` |
| `MAX_FILE_SIZE_MB` | 最大ファイルサイズ | `100` |

環境変数を更新する場合：

```bash
gcloud run services update gemini-file-search-mcp \
    --region ${GCP_REGION} \
    --update-env-vars DEFAULT_MODEL=gemini-2.0-flash-exp,LOG_LEVEL=DEBUG
```

## モニタリング

### ログの確認

```bash
# リアルタイムログ
gcloud run services logs read gemini-file-search-mcp \
    --region ${GCP_REGION} \
    --follow

# 最近のログ
gcloud run services logs tail gemini-file-search-mcp \
    --region ${GCP_REGION}
```

### メトリクスの確認

Google Cloud Console で確認：
1. Cloud Run サービスページにアクセス
2. `gemini-file-search-mcp` をクリック
3. 「メトリクス」タブでリクエスト数、レイテンシ、エラー率を確認

## スケーリング設定

### 最小/最大インスタンス数の設定

```bash
gcloud run services update gemini-file-search-mcp \
    --region ${GCP_REGION} \
    --min-instances 0 \
    --max-instances 10
```

### 同時実行数の設定

```bash
gcloud run services update gemini-file-search-mcp \
    --region ${GCP_REGION} \
    --concurrency 80
```

## セキュリティ

### 認証が必要な場合

認証を有効にする場合：

```bash
# 認証を要求
gcloud run services update gemini-file-search-mcp \
    --region ${GCP_REGION} \
    --no-allow-unauthenticated

# サービスアカウントにアクセス権を付与
gcloud run services add-iam-policy-binding gemini-file-search-mcp \
    --region ${GCP_REGION} \
    --member='user:your-email@example.com' \
    --role='roles/run.invoker'
```

### Secret Managerの使用

Gemini API キーをSecret Managerで管理する場合：

```bash
# Secretを作成
echo -n "your_gemini_api_key" | gcloud secrets create gemini-api-key --data-file=-

# Cloud Runサービスに権限を付与
gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Secretを環境変数として設定
gcloud run services update gemini-file-search-mcp \
    --region ${GCP_REGION} \
    --update-secrets GEMINI_API_KEY=gemini-api-key:latest
```

## コスト最適化

### 料金の見積もり

Cloud Runの料金は以下で構成されます：
- CPU時間
- メモリ使用量
- リクエスト数
- ネットワーク帯域幅

無料枠：
- 月間200万リクエスト
- 36万GB秒のメモリ
- 18万vCPU秒

### コスト削減のヒント

1. **最小インスタンス数を0に設定**（コールドスタート許容）
2. **適切なメモリ/CPU設定**（512MiB/1vCPUで十分）
3. **タイムアウトの最適化**
4. **不要な場合はログを減らす**

## トラブルシューティング

### デプロイエラー

```bash
# ビルドログを確認
gcloud builds list --limit 5

# 詳細ログを確認
gcloud builds log BUILD_ID
```

### サービスが起動しない

```bash
# サービスの詳細を確認
gcloud run services describe gemini-file-search-mcp \
    --region ${GCP_REGION}

# ログを確認
gcloud run services logs read gemini-file-search-mcp \
    --region ${GCP_REGION} \
    --limit 50
```

### 接続エラー

1. ヘルスチェックエンドポイントを確認
2. 環境変数が正しく設定されているか確認
3. Gemini API キーが有効か確認

## サービスの削除

```bash
gcloud run services delete gemini-file-search-mcp \
    --region ${GCP_REGION}

# コンテナイメージも削除
gcloud container images delete gcr.io/${GCP_PROJECT_ID}/gemini-file-search-mcp
```

## 参考リンク

- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Cloud Run 料金](https://cloud.google.com/run/pricing)
- [Gemini API ドキュメント](https://ai.google.dev/gemini-api/docs)
- [MCP 仕様](https://modelcontextprotocol.io/)
