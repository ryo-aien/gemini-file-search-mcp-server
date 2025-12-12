# トラブルシューティングガイド

## Cloud Run デプロイエラー

### エラー: "Container failed to start and listen on the port"

このエラーは、コンテナが起動してポートでリッスンできなかった場合に発生します。

#### 解決方法

**1. ローカルでテスト**

まず、ローカル環境でHTTPサーバーが正常に起動するか確認：

```bash
# 依存関係をインストール
pip install -r requirements.txt

# テストスクリプトを実行
chmod +x test_http_server.sh
./test_http_server.sh
```

または手動でテスト：

```bash
export GEMINI_API_KEY="your_api_key"
python -m uvicorn src.http_server:app --host 0.0.0.0 --port 8080
```

別のターミナルで：

```bash
curl http://localhost:8080/health
```

**2. Dockerコンテナでテスト**

```bash
# Dockerイメージをビルド
docker build -t gemini-mcp-test .

# コンテナを起動
docker run -p 8080:8080 \
  -e GEMINI_API_KEY="your_api_key" \
  gemini-mcp-test

# 別のターミナルで
curl http://localhost:8080/health
```

**3. Cloud Runのログを確認**

```bash
gcloud run services logs read gemini-file-search-mcp \
  --region us-central1 \
  --limit 50
```

**4. よくある原因**

- **GEMINI_API_KEYが設定されていない**
  ```bash
  # 環境変数を確認
  echo $GEMINI_API_KEY
  ```

- **ポート設定の問題**
  - Cloud RunはPORT環境変数を動的に設定します
  - start.shスクリプトが正しく実行されているか確認

- **依存関係のインストール失敗**
  - requirements.txtの内容を確認
  - Dockerビルドログを確認

- **メモリ不足**
  - メモリを1Giに増やす：
  ```bash
  gcloud run services update gemini-file-search-mcp \
    --region us-central1 \
    --memory 1Gi
  ```

**5. デバッグモードで再デプロイ**

```bash
# デバッグ用の環境変数を追加
gcloud run deploy gemini-file-search-mcp \
  --image gcr.io/${GCP_PROJECT_ID}/gemini-file-search-mcp \
  --region us-central1 \
  --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY},LOG_LEVEL=DEBUG \
  --memory 1Gi \
  --timeout 300
```

### エラー: "Revision failed"

**解決方法:**

1. **以前のリビジョンを確認**

```bash
gcloud run revisions list \
  --service gemini-file-search-mcp \
  --region us-central1
```

2. **動作していたリビジョンにロールバック**

```bash
gcloud run services update-traffic gemini-file-search-mcp \
  --region us-central1 \
  --to-revisions REVISION_NAME=100
```

### エラー: "Permission denied"

**解決方法:**

```bash
# サービスアカウントに権限を付与
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/run.admin"
```

## 一般的な問題

### Gemini APIエラー

**症状:** ツール呼び出し時に"Failed to initialize Gemini client"エラー

**解決方法:**

1. APIキーが正しいか確認
2. Gemini APIが有効化されているか確認
3. クォータ制限を超えていないか確認

```bash
# APIキーをテスト
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${GEMINI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

### MCPツールが表示されない

**症状:** Claude Desktopでツールが表示されない

**解決方法:**

1. サービスURLが正しいか確認
2. `/mcp`エンドポイントにアクセスできるか確認

```bash
curl -X POST https://your-service-url.run.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

3. Claude Desktopの設定を確認

```json
{
  "mcpServers": {
    "gemini-file-search": {
      "url": "https://your-service-url.run.app/mcp"
    }
  }
}
```

4. Claude Desktopを再起動

### タイムアウトエラー

**症状:** リクエストがタイムアウトする

**解決方法:**

```bash
# タイムアウトを延長
gcloud run services update gemini-file-search-mcp \
  --region us-central1 \
  --timeout 300
```

## デバッグコマンド集

### サービス情報の確認

```bash
# サービスの詳細
gcloud run services describe gemini-file-search-mcp \
  --region us-central1

# 環境変数の確認
gcloud run services describe gemini-file-search-mcp \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

### ログの確認

```bash
# リアルタイムログ
gcloud run services logs tail gemini-file-search-mcp \
  --region us-central1

# エラーのみ
gcloud run services logs read gemini-file-search-mcp \
  --region us-central1 \
  --log-filter="severity>=ERROR"
```

### メトリクスの確認

```bash
# リクエスト数
gcloud monitoring time-series list \
  --filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"' \
  --format=json
```

## サポート

問題が解決しない場合：

1. [Cloud Run トラブルシューティング](https://cloud.google.com/run/docs/troubleshooting)
2. [Gemini API ドキュメント](https://ai.google.dev/gemini-api/docs)
3. GitHubのIssuesで報告
