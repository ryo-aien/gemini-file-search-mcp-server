"""File Search Store 管理ツール."""
import logging
from typing import Any, Dict, Optional
from gemini_client import get_client

logger = logging.getLogger(__name__)


async def create_store(display_name: Optional[str] = None) -> Dict[str, Any]:
    """
    File Search Store を作成する.

    Args:
        display_name: ストアの表示名（最大512文字、オプション）

    Returns:
        作成されたストアの情報（store_name, display_name, create_time）

    Raises:
        Exception: Gemini API エラー
    """
    try:
        client = get_client()
        config = {}
        if display_name:
            if len(display_name) > 512:
                raise ValueError("display_name must be <= 512 characters")
            config["display_name"] = display_name

        logger.info(f"Creating file search store with config: {config}")
        store = client.file_search_stores.create(config=config)

        result = {
            "store_name": store.name,
            "display_name": getattr(store, "display_name", ""),
        }

        # create_time が存在する場合は追加
        if hasattr(store, "create_time"):
            result["create_time"] = str(store.create_time)

        logger.info(f"Store created: {result['store_name']}")
        return result

    except Exception as e:
        logger.error(f"Failed to create store: {str(e)}")
        raise


async def list_stores(
    page_size: Optional[int] = None, page_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    File Search Store の一覧を取得する.

    Args:
        page_size: 1ページあたりの最大件数
        page_token: ページネーショントークン

    Returns:
        ストアの一覧と次ページトークン（stores, next_page_token）
    """
    try:
        client = get_client()
        config = {}
        if page_size is not None:
            config["page_size"] = page_size
        if page_token:
            config["page_token"] = page_token

        logger.info(f"Listing file search stores with config: {config}")
        response = client.file_search_stores.list(config=config)

        stores = []
        for store in response:
            store_info = {
                "name": store.name,
                "display_name": getattr(store, "display_name", ""),
            }
            if hasattr(store, "create_time"):
                store_info["create_time"] = str(store.create_time)
            if hasattr(store, "update_time"):
                store_info["update_time"] = str(store.update_time)
            stores.append(store_info)

        result = {"stores": stores}

        # next_page_token が存在する場合は追加
        if hasattr(response, "next_page_token") and response.next_page_token:
            result["next_page_token"] = response.next_page_token

        logger.info(f"Listed {len(stores)} stores")
        return result

    except Exception as e:
        logger.error(f"Failed to list stores: {str(e)}")
        raise


async def get_store(store_name: str) -> Dict[str, Any]:
    """
    指定された File Search Store の詳細情報を取得する.

    Args:
        store_name: ストアのリソース名（例: fileSearchStores/...）

    Returns:
        ストアの詳細情報
    """
    try:
        client = get_client()
        logger.info(f"Getting file search store: {store_name}")

        store = client.file_search_stores.get(name=store_name)

        result = {
            "name": store.name,
            "display_name": getattr(store, "display_name", ""),
        }

        # 追加の属性があれば含める
        if hasattr(store, "create_time"):
            result["create_time"] = str(store.create_time)
        if hasattr(store, "update_time"):
            result["update_time"] = str(store.update_time)

        logger.info(f"Retrieved store: {store_name}")
        return result

    except Exception as e:
        logger.error(f"Failed to get store {store_name}: {str(e)}")
        raise


async def delete_store(store_name: str, force: bool = False) -> Dict[str, bool]:
    """
    File Search Store を削除する.

    Args:
        store_name: ストアのリソース名（例: fileSearchStores/...）
        force: ドキュメントが残っていても強制削除するか（デフォルト: False）

    Returns:
        削除成功の確認（{"deleted": True}）

    Raises:
        Exception: force=False でドキュメントが残っている場合など
    """
    try:
        client = get_client()
        config = {"force": force}

        logger.info(f"Deleting file search store: {store_name} (force={force})")
        client.file_search_stores.delete(name=store_name, config=config)

        logger.info(f"Store deleted: {store_name}")
        return {"deleted": True}

    except Exception as e:
        logger.error(f"Failed to delete store {store_name}: {str(e)}")
        raise
