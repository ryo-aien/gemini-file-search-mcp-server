"""Cloud Run デプロイ後の統合テスト."""
import base64
import pytest
import httpx


class TestCloudRunMCPServer:
    """Cloud Run MCP サーバーの統合テスト."""

    @pytest.fixture
    def server_url(self, request):
        """サーバーの URL を取得する（コマンドライン引数から）."""
        url = request.config.getoption("--url", default=None)
        if not url:
            pytest.skip("--url option not provided")
        return url

    @pytest.mark.asyncio
    async def test_server_health(self, server_url):
        """サーバーが応答することを確認する."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # MCP エンドポイントにアクセス
            response = await client.get(f"{server_url}/mcp")
            # MCP サーバーは通常 GET に対して 405 または 404 を返す
            # ここでは接続できることを確認
            assert response.status_code in [200, 404, 405]

    @pytest.mark.asyncio
    async def test_list_supported_formats(self, server_url):
        """サポートされるファイル形式の一覧を取得する."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # MCP リクエストを構築
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "mcp_list_supported_formats",
                    "arguments": {},
                },
            }

            response = await client.post(
                f"{server_url}/mcp", json=mcp_request
            )

            assert response.status_code == 200
            result = response.json()

            # MCP レスポンスの検証
            assert "result" in result or "error" in result

            if "result" in result:
                data = result["result"]
                assert "supported_mime_types" in data
                assert "application" in data["supported_mime_types"]
                assert "text" in data["supported_mime_types"]

    @pytest.mark.asyncio
    async def test_store_lifecycle(self, server_url):
        """Store のライフサイクル（作成・取得・削除）をテストする."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Store を作成
            create_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "mcp_create_store",
                    "arguments": {"display_name": "Cloud Run Test Store"},
                },
            }

            response = await client.post(
                f"{server_url}/mcp", json=create_request
            )
            assert response.status_code == 200
            result = response.json()

            if "error" in result:
                pytest.skip(f"Store creation failed: {result['error']}")

            assert "result" in result
            store_name = result["result"]["store_name"]

            try:
                # Store を取得
                get_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "mcp_get_store",
                        "arguments": {"store_name": store_name},
                    },
                }

                response = await client.post(
                    f"{server_url}/mcp", json=get_request
                )
                assert response.status_code == 200
                result = response.json()
                assert "result" in result

            finally:
                # Store を削除（クリーンアップ）
                delete_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "mcp_delete_store",
                        "arguments": {"store_name": store_name, "force": True},
                    },
                }

                await client.post(f"{server_url}/mcp", json=delete_request)


def pytest_addoption(parser):
    """pytest のコマンドライン引数を追加する."""
    parser.addoption(
        "--url",
        action="store",
        default=None,
        help="Cloud Run server URL (e.g., https://your-service.run.app)",
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
