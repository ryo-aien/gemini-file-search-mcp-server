"""File Search Document 管理ツール."""
import base64
import logging
import mimetypes
import os
import tempfile
from typing import Any, Dict, List, Optional
from gemini_client import get_client

logger = logging.getLogger(__name__)


def _build_chunking_config(chunking_config: Optional[Dict[str, Any]]) -> Optional[Dict]:
    """
    チャンク化設定を構築する.

    Args:
        chunking_config: チャンク化設定（white_space_config を含む）

    Returns:
        Gemini API に渡す chunking_config、または None
    """
    if not chunking_config:
        return None

    # white_space_config が含まれている場合
    if "white_space_config" in chunking_config:
        return {
            "chunking_strategy": "white_space",
            "white_space_config": chunking_config["white_space_config"],
        }

    return chunking_config


def _build_custom_metadata(
    custom_metadata: Optional[List[Dict[str, Any]]]
) -> Optional[List[Dict]]:
    """
    カスタムメタデータを構築する.

    Args:
        custom_metadata: メタデータリスト
            [{key: str, string_value|numeric_value|string_list_value: ...}]

    Returns:
        Gemini API に渡すメタデータリスト、または None
    """
    if not custom_metadata:
        return None

    if len(custom_metadata) > 20:
        raise ValueError("Maximum 20 custom metadata entries allowed per document")

    result = []
    for entry in custom_metadata:
        if "key" not in entry:
            raise ValueError("Each metadata entry must have a 'key' field")

        meta = {"key": entry["key"]}

        # string_value, numeric_value, string_list_value のいずれかを設定
        if "string_value" in entry:
            meta["string_value"] = entry["string_value"]
        elif "numeric_value" in entry:
            meta["numeric_value"] = entry["numeric_value"]
        elif "string_list_value" in entry:
            meta["string_list_value"] = entry["string_list_value"]
        else:
            raise ValueError(
                f"Metadata entry '{entry['key']}' must have string_value, "
                "numeric_value, or string_list_value"
            )

        result.append(meta)

    return result


async def upload_file(
    store_name: str,
    file_bytes_base64: str,
    display_name: Optional[str] = None,
    mime_type: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
    custom_metadata: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    ファイルを直接アップロードして File Search Store に取り込む.

    Args:
        store_name: ストアのリソース名
        file_bytes_base64: Base64 エンコードされたファイルバイト
        display_name: ドキュメントの表示名（オプション）
        mime_type: MIME タイプ（オプション、未指定なら推定）
        chunking_config: チャンク化設定（オプション）
        custom_metadata: カスタムメタデータ（オプション、最大20件）

    Returns:
        operation_name と document_name（可能であれば）
    """
    try:
        client = get_client()

        # Base64 デコード
        file_bytes = base64.b64decode(file_bytes_base64)
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if file_size_mb > 100:
            raise ValueError(
                f"File size ({file_size_mb:.2f} MB) exceeds 100MB limit"
            )

        logger.info(
            f"Uploading file to store {store_name} (size: {file_size_mb:.2f} MB)"
        )

        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            # MIME タイプの推定
            if not mime_type and display_name:
                mime_type, _ = mimetypes.guess_type(display_name)

            # アップロード設定の構築
            config = {}
            if display_name:
                config["display_name"] = display_name
            if mime_type:
                config["mime_type"] = mime_type

            # チャンク化設定
            chunking = _build_chunking_config(chunking_config)
            if chunking:
                config["chunking_config"] = chunking

            # カスタムメタデータ
            metadata = _build_custom_metadata(custom_metadata)
            if metadata:
                config["custom_metadata"] = metadata

            logger.info(f"Upload config: {config}")

            # uploadToFileSearchStore を実行
            # 注: SDK の実装によっては異なる可能性があるため、エラー処理を追加
            operation = client.file_search_stores.upload(
                store_name=store_name, file_path=temp_path, config=config
            )

            result = {"operation_name": operation.name}

            # document_name が取得できる場合は追加
            if hasattr(operation, "metadata") and operation.metadata:
                if hasattr(operation.metadata, "document_name"):
                    result["document_name"] = operation.metadata.document_name

            logger.info(f"Upload operation started: {operation.name}")
            return result

        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}")
        raise


async def import_file(
    store_name: str,
    file_name: str,
    display_name: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
    custom_metadata: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """
    Files API で作成済みのファイルを File Search Store に取り込む.

    Args:
        store_name: ストアのリソース名
        file_name: Files API のファイルリソース名（例: files/...）
        display_name: ドキュメントの表示名（オプション）
        chunking_config: チャンク化設定（オプション）
        custom_metadata: カスタムメタデータ（オプション）

    Returns:
        operation_name
    """
    try:
        client = get_client()
        logger.info(f"Importing file {file_name} to store {store_name}")

        # インポート設定の構築
        config = {"file_name": file_name}

        if display_name:
            config["display_name"] = display_name

        # チャンク化設定
        chunking = _build_chunking_config(chunking_config)
        if chunking:
            config["chunking_config"] = chunking

        # カスタムメタデータ
        metadata = _build_custom_metadata(custom_metadata)
        if metadata:
            config["custom_metadata"] = metadata

        logger.info(f"Import config: {config}")

        # importFile を実行
        operation = client.file_search_stores.import_file(
            store_name=store_name, config=config
        )

        logger.info(f"Import operation started: {operation.name}")
        return {"operation_name": operation.name}

    except Exception as e:
        logger.error(f"Failed to import file: {str(e)}")
        raise


async def list_documents(
    store_name: str,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    File Search Store 内のドキュメント一覧を取得する.

    Args:
        store_name: ストアのリソース名
        page_size: 1ページあたりの最大件数
        page_token: ページネーショントークン

    Returns:
        documents と next_page_token
    """
    try:
        client = get_client()
        config = {}
        if page_size is not None:
            config["page_size"] = page_size
        if page_token:
            config["page_token"] = page_token

        logger.info(f"Listing documents in store {store_name}")

        # ストアのドキュメントコレクションを取得
        response = client.file_search_stores.documents.list(
            parent=store_name, config=config
        )

        documents = []
        for doc in response:
            doc_info = {
                "name": doc.name,
                "display_name": getattr(doc, "display_name", ""),
                "state": getattr(doc, "state", ""),
            }

            # 追加の属性を含める
            if hasattr(doc, "size_bytes"):
                doc_info["size_bytes"] = doc.size_bytes
            if hasattr(doc, "mime_type"):
                doc_info["mime_type"] = doc.mime_type
            if hasattr(doc, "custom_metadata"):
                doc_info["custom_metadata"] = doc.custom_metadata
            if hasattr(doc, "create_time"):
                doc_info["create_time"] = str(doc.create_time)
            if hasattr(doc, "update_time"):
                doc_info["update_time"] = str(doc.update_time)

            documents.append(doc_info)

        result = {"documents": documents}

        # next_page_token が存在する場合は追加
        if hasattr(response, "next_page_token") and response.next_page_token:
            result["next_page_token"] = response.next_page_token

        logger.info(f"Listed {len(documents)} documents")
        return result

    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise


async def get_document(document_name: str) -> Dict[str, Any]:
    """
    指定されたドキュメントの詳細情報を取得する.

    Args:
        document_name: ドキュメントのリソース名
            （例: fileSearchStores/.../documents/...）

    Returns:
        ドキュメントの詳細情報
    """
    try:
        client = get_client()
        logger.info(f"Getting document: {document_name}")

        doc = client.file_search_stores.documents.get(name=document_name)

        result = {
            "name": doc.name,
            "display_name": getattr(doc, "display_name", ""),
            "state": getattr(doc, "state", ""),
        }

        # 追加の属性を含める
        if hasattr(doc, "size_bytes"):
            result["size_bytes"] = doc.size_bytes
        if hasattr(doc, "mime_type"):
            result["mime_type"] = doc.mime_type
        if hasattr(doc, "custom_metadata"):
            result["custom_metadata"] = doc.custom_metadata
        if hasattr(doc, "create_time"):
            result["create_time"] = str(doc.create_time)
        if hasattr(doc, "update_time"):
            result["update_time"] = str(doc.update_time)

        logger.info(f"Retrieved document: {document_name}")
        return result

    except Exception as e:
        logger.error(f"Failed to get document {document_name}: {str(e)}")
        raise


async def delete_document(
    document_name: str, force: bool = False
) -> Dict[str, bool]:
    """
    ドキュメントを削除する.

    Args:
        document_name: ドキュメントのリソース名
        force: 強制削除フラグ（オプション）

    Returns:
        削除成功の確認
    """
    try:
        client = get_client()
        config = {"force": force}

        logger.info(f"Deleting document: {document_name} (force={force})")
        client.file_search_stores.documents.delete(
            name=document_name, config=config
        )

        logger.info(f"Document deleted: {document_name}")
        return {"deleted": True}

    except Exception as e:
        logger.error(f"Failed to delete document {document_name}: {str(e)}")
        raise


async def update_metadata(
    document_name: str,
    new_custom_metadata: List[Dict[str, Any]],
    original_file_bytes_base64: str,
    display_name: Optional[str] = None,
    mime_type: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    ドキュメントのメタデータを更新する.

    方式1: 既存ドキュメントを削除し、同じファイルを新しいメタデータで再取り込み.

    注意: Document 名が変わる可能性があります.

    Args:
        document_name: 既存のドキュメントリソース名
        new_custom_metadata: 新しいカスタムメタデータ
        original_file_bytes_base64: 元のファイルバイト（Base64）
        display_name: ドキュメントの表示名（オプション、未指定なら既存から取得）
        mime_type: MIME タイプ（オプション）
        chunking_config: チャンク化設定（オプション）

    Returns:
        new_document_name と operation_name
    """
    try:
        client = get_client()
        logger.info(f"Updating metadata for document: {document_name}")

        # 既存ドキュメント情報を取得（display_name などを引き継ぐため）
        existing_doc = await get_document(document_name)

        # ストア名を抽出
        # document_name 形式: fileSearchStores/{store_id}/documents/{doc_id}
        parts = document_name.split("/")
        if len(parts) < 4:
            raise ValueError(f"Invalid document_name format: {document_name}")
        store_name = f"{parts[0]}/{parts[1]}"

        # 既存ドキュメントを削除
        await delete_document(document_name, force=True)
        logger.info(f"Deleted existing document: {document_name}")

        # 新しいメタデータで再アップロード
        upload_result = await upload_file(
            store_name=store_name,
            file_bytes_base64=original_file_bytes_base64,
            display_name=display_name or existing_doc.get("display_name"),
            mime_type=mime_type or existing_doc.get("mime_type"),
            chunking_config=chunking_config,
            custom_metadata=new_custom_metadata,
        )

        result = {
            "operation_name": upload_result["operation_name"],
        }
        if "document_name" in upload_result:
            result["new_document_name"] = upload_result["document_name"]

        logger.info(f"Metadata update operation started: {result['operation_name']}")
        return result

    except Exception as e:
        logger.error(f"Failed to update metadata for {document_name}: {str(e)}")
        raise
