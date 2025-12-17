"""ローカル環境でのツールテスト."""
import base64
import os
import pytest
from dotenv import load_dotenv

from tools.store_tools import create_store, delete_store, get_store, list_stores
from tools.document_tools import (
    delete_document,
    get_document,
    list_documents,
    upload_file,
)
from tools.search_tools import search_documents
from tools.util_tools import (
    get_operation_status,
    get_store_statistics,
    list_supported_formats,
)

# 環境変数をロード
load_dotenv()

# テストをスキップするかどうかの判定
skip_if_no_api_key = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set",
)


class TestStoreTools:
    """Store 管理ツールのテスト."""

    @skip_if_no_api_key
    @pytest.mark.asyncio
    async def test_create_and_delete_store(self):
        """Store の作成と削除をテストする."""
        # Store を作成
        result = await create_store(display_name="Test Store")
        assert "store_name" in result
        assert result["display_name"] == "Test Store"

        store_name = result["store_name"]

        # Store を取得
        store = await get_store(store_name)
        assert store["name"] == store_name

        # Store を削除
        delete_result = await delete_store(store_name, force=True)
        assert delete_result["deleted"] is True

    @skip_if_no_api_key
    @pytest.mark.asyncio
    async def test_list_stores(self):
        """Store の一覧取得をテストする."""
        result = await list_stores(page_size=10)
        assert "stores" in result
        assert isinstance(result["stores"], list)


class TestUtilTools:
    """ユーティリティツールのテスト."""

    @pytest.mark.asyncio
    async def test_list_supported_formats(self):
        """サポートされるファイル形式の一覧を取得する."""
        result = await list_supported_formats()
        assert "supported_mime_types" in result
        assert "application" in result["supported_mime_types"]
        assert "text" in result["supported_mime_types"]
        assert "application/pdf" in result["supported_mime_types"]["application"]
        assert "text/plain" in result["supported_mime_types"]["text"]


class TestDocumentTools:
    """Document 管理ツールのテスト."""

    @skip_if_no_api_key
    @pytest.mark.asyncio
    async def test_upload_and_delete_document(self):
        """ドキュメントのアップロードと削除をテストする."""
        # テスト用の Store を作成
        store_result = await create_store(display_name="Test Doc Store")
        store_name = store_result["store_name"]

        try:
            # テスト用のファイルを作成
            test_content = "This is a test document for Gemini File Search."
            file_bytes = test_content.encode("utf-8")
            file_bytes_base64 = base64.b64encode(file_bytes).decode("utf-8")

            # ファイルをアップロード
            upload_result = await upload_file(
                store_name=store_name,
                file_bytes_base64=file_bytes_base64,
                display_name="test.txt",
                mime_type="text/plain",
            )

            assert "operation_name" in upload_result
            operation_name = upload_result["operation_name"]

            # オペレーションのステータスを確認
            # 注: 実際の環境では完了まで時間がかかるため、ここでは取得のみテスト
            status = await get_operation_status(operation_name)
            assert "done" in status

            # ドキュメント一覧を取得
            docs_result = await list_documents(store_name, page_size=10)
            assert "documents" in docs_result

        finally:
            # Store を削除（クリーンアップ）
            await delete_store(store_name, force=True)


class TestSearchTools:
    """検索ツールのテスト."""

    @skip_if_no_api_key
    @pytest.mark.asyncio
    async def test_search_documents_basic(self):
        """基本的な検索機能をテストする."""
        # 注: 実際の検索テストには Store とドキュメントが必要
        # ここでは API 呼び出しの形式のみテスト

        # テスト用の Store を作成
        store_result = await create_store(display_name="Test Search Store")
        store_name = store_result["store_name"]

        try:
            # 空のストアでも検索は実行可能（結果が空になるだけ）
            result = await search_documents(
                store_names=[store_name],
                query="Test query",
                model="gemini-2.5-flash",
            )

            assert "answer_text" in result
            assert "used_stores" in result
            assert store_name in result["used_stores"]

        finally:
            # Store を削除（クリーンアップ）
            await delete_store(store_name, force=True)


class TestStoreStatistics:
    """Store 統計情報のテスト."""

    @skip_if_no_api_key
    @pytest.mark.asyncio
    async def test_get_store_statistics(self):
        """Store の統計情報を取得する."""
        # テスト用の Store を作成
        store_result = await create_store(display_name="Test Stats Store")
        store_name = store_result["store_name"]

        try:
            # 統計情報を取得
            stats = await get_store_statistics(store_name)

            assert "document_count" in stats
            assert "total_size_bytes" in stats
            assert "states_breakdown" in stats
            assert stats["document_count"] == 0  # 新規作成直後なので 0

        finally:
            # Store を削除（クリーンアップ）
            await delete_store(store_name, force=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
