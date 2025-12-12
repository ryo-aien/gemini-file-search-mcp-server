#!/usr/bin/env python3
"""
Interactive MCP Server Test
対話的にMCPサーバーをテストする
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPTester:
    def __init__(self):
        self.session = None

    async def connect(self):
        """サーバーに接続"""
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "src.server"],
            env=None
        )

        self.read, self.write = await stdio_client(server_params).__aenter__()
        self.session = await ClientSession(self.read, self.write).__aenter__()
        await self.session.initialize()
        print("✅ サーバーに接続しました")

    async def list_tools(self):
        """利用可能なツールを表示"""
        tools = await self.session.list_tools()
        print(f"\n📋 利用可能なツール ({len(tools.tools)}個):")
        for i, tool in enumerate(tools.tools, 1):
            print(f"\n{i}. {tool.name}")
            print(f"   説明: {tool.description}")

    async def call_tool(self, tool_name: str, arguments: dict):
        """ツールを呼び出し"""
        print(f"\n🔧 {tool_name} を実行中...")
        print(f"引数: {json.dumps(arguments, ensure_ascii=False)}")

        result = await self.session.call_tool(tool_name, arguments)

        print("\n📊 結果:")
        for content in result.content:
            if hasattr(content, 'text'):
                data = json.loads(content.text)
                print(json.dumps(data, indent=2, ensure_ascii=False))

        return result


async def main():
    """メイン関数"""
    tester = MCPTester()

    try:
        await tester.connect()

        # ツール一覧を表示
        await tester.list_tools()

        print("\n" + "=" * 60)
        print("テストケース実行")
        print("=" * 60)

        # テスト1: Store一覧を取得
        print("\n【テスト1】Store一覧を取得")
        await tester.call_tool("list_file_search_stores", {"page_size": 10})

        # テスト2: Storeを作成（コメントアウトを外して実行）
        # print("\n【テスト2】Storeを作成")
        # await tester.call_tool("create_file_search_store", {
        #     "display_name": "テスト用Store",
        #     "description": "テストで作成したStore"
        # })

        # テスト3: 検索（Store IDを指定する必要があります）
        # print("\n【テスト3】ドキュメント検索")
        # await tester.call_tool("search_documents", {
        #     "store_names": ["fileSearchStores/YOUR_STORE_ID"],
        #     "query": "テストクエリ"
        # })

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
