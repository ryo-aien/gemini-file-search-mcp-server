"""ユーティリティツール."""
import logging
from typing import Any, Dict, Optional
from gemini_client import get_client
from tools.document_tools import list_documents

logger = logging.getLogger(__name__)

# Gemini File Search でサポートされる MIME タイプ（公式ドキュメントより）
SUPPORTED_MIME_TYPES = {
    "application": [
        "application/pdf",
        "application/json",
        "application/msword",
        "application/vnd.ms-excel",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
        "application/x-tar",
        "application/gzip",
        "application/xml",
        "application/rtf",
        "application/x-latex",
    ],
    "text": [
        "text/plain",
        "text/markdown",
        "text/csv",
        "text/html",
        "text/xml",
        "text/yaml",
        "text/css",
        "text/javascript",
        "text/x-python",
        "text/x-java",
        "text/x-c",
        "text/x-c++",
        "text/x-go",
        "text/x-ruby",
        "text/x-php",
        "text/x-rust",
        "text/x-typescript",
        "text/x-shell",
    ],
}


async def get_operation_status(operation_name: str) -> Dict[str, Any]:
    """
    Long-running operation（LRO）のステータスを取得する.

    Args:
        operation_name: オペレーションのリソース名

    Returns:
        done（完了フラグ）、error（エラー情報）、response（レスポンス）
    """
    try:
        client = get_client()
        logger.info(f"Getting operation status: {operation_name}")

        # operations.get を実行
        operation = client.operations.get(name=operation_name)

        result = {"done": getattr(operation, "done", False)}

        # エラーがある場合
        if hasattr(operation, "error") and operation.error:
            result["error"] = {
                "code": getattr(operation.error, "code", None),
                "message": getattr(operation.error, "message", ""),
                "details": getattr(operation.error, "details", []),
            }

        # レスポンスがある場合
        if hasattr(operation, "response") and operation.response:
            # response を辞書化
            response_dict = {}
            if hasattr(operation.response, "__dict__"):
                response_dict = {
                    k: v
                    for k, v in operation.response.__dict__.items()
                    if not k.startswith("_")
                }
            else:
                response_dict = str(operation.response)

            result["response"] = response_dict

        # メタデータがある場合
        if hasattr(operation, "metadata") and operation.metadata:
            metadata_dict = {}
            if hasattr(operation.metadata, "__dict__"):
                metadata_dict = {
                    k: v
                    for k, v in operation.metadata.__dict__.items()
                    if not k.startswith("_")
                }
                # document_name などがあれば抽出
                if "document_name" in metadata_dict:
                    result["document_name"] = metadata_dict["document_name"]

        logger.info(f"Operation status: done={result['done']}")
        return result

    except Exception as e:
        logger.error(f"Failed to get operation status: {str(e)}")
        raise


async def list_supported_formats() -> Dict[str, Any]:
    """
    File Search でサポートされるファイル形式（MIME タイプ）の一覧を返す.

    Returns:
        supported_mime_types（application と text のカテゴリ別リスト）
    """
    logger.info("Listing supported MIME types")
    return {"supported_mime_types": SUPPORTED_MIME_TYPES}


async def get_store_statistics(store_name: str) -> Dict[str, Any]:
    """
    File Search Store の統計情報を取得する.

    Args:
        store_name: ストアのリソース名

    Returns:
        document_count, total_size_bytes, states_breakdown
    """
    try:
        logger.info(f"Getting statistics for store: {store_name}")

        # ドキュメント一覧をページングしながら全件取得
        all_documents = []
        page_token = None

        while True:
            result = await list_documents(
                store_name=store_name, page_size=100, page_token=page_token
            )
            all_documents.extend(result["documents"])

            page_token = result.get("next_page_token")
            if not page_token:
                break

        # 統計を計算
        document_count = len(all_documents)
        total_size_bytes = sum(
            doc.get("size_bytes", 0) for doc in all_documents
        )

        # 状態別の集計
        states_breakdown = {}
        for doc in all_documents:
            state = doc.get("state", "UNKNOWN")
            states_breakdown[state] = states_breakdown.get(state, 0) + 1

        result = {
            "document_count": document_count,
            "total_size_bytes": total_size_bytes,
            "states_breakdown": states_breakdown,
        }

        logger.info(
            f"Store statistics: {document_count} documents, "
            f"{total_size_bytes} bytes, states: {states_breakdown}"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to get store statistics: {str(e)}")
        raise
