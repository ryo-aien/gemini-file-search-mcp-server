"""File Search 検索ツール."""
import json
import logging
from typing import Any, Dict, List, Optional
from gemini_client import get_client
from google.genai import types

logger = logging.getLogger(__name__)


async def search_documents(
    store_names: List[str],
    query: str,
    model: str = "gemini-2.5-flash",
    metadata_filter: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    """
    File Search を使用してドキュメントを検索し、回答を生成する.

    Args:
        store_names: 検索対象ストアのリソース名リスト
        query: 検索クエリ
        model: 使用するモデル（デフォルト: gemini-2.5-flash）
        metadata_filter: メタデータフィルタ式（オプション）
        max_output_tokens: 最大出力トークン数（オプション）
        temperature: 温度パラメータ（オプション）

    Returns:
        answer_text, grounding_metadata, used_stores, model
    """
    try:
        client = get_client()
        logger.info(
            f"Searching documents in stores: {store_names} with query: {query[:100]}..."
        )

        # File Search ツール設定
        file_search_config = {"file_search_stores": store_names}

        if metadata_filter:
            file_search_config["metadata_filter"] = metadata_filter

        file_search_tool = types.Tool(
            file_search=types.FileSearch(**file_search_config)
        )

        # GenerateContent 設定
        config_params = {"tools": [file_search_tool]}

        if max_output_tokens is not None:
            config_params["max_output_tokens"] = max_output_tokens
        if temperature is not None:
            config_params["temperature"] = temperature

        generate_config = types.GenerateContentConfig(**config_params)

        logger.info(f"Generating content with model: {model}")

        # コンテンツ生成
        response = client.models.generate_content(
            model=model, contents=query, config=generate_config
        )

        # 回答テキストを抽出
        answer_text = ""
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                answer_text = "".join(
                    part.text for part in candidate.content.parts if hasattr(part, "text")
                )

        # Grounding metadata を抽出
        grounding_metadata = None
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                # grounding_metadata を JSON 化可能な形式に変換
                try:
                    # protobuf または類似のオブジェクトを辞書に変換
                    grounding_metadata = _convert_to_dict(candidate.grounding_metadata)
                except Exception as e:
                    logger.warning(f"Failed to convert grounding_metadata: {e}")
                    grounding_metadata = str(candidate.grounding_metadata)

        result = {
            "answer_text": answer_text,
            "grounding_metadata": grounding_metadata,
            "used_stores": store_names,
            "model": model,
        }

        logger.info(f"Search completed with answer length: {len(answer_text)}")
        return result

    except Exception as e:
        logger.error(f"Failed to search documents: {str(e)}")
        raise


def _convert_to_dict(obj: Any) -> Any:
    """
    protobuf や Pydantic モデルなどを辞書に変換する.

    Args:
        obj: 変換対象のオブジェクト

    Returns:
        辞書、リスト、またはプリミティブ値
    """
    # None, bool, int, float, str はそのまま返す
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    # リストの場合
    if isinstance(obj, (list, tuple)):
        return [_convert_to_dict(item) for item in obj]

    # 辞書の場合
    if isinstance(obj, dict):
        return {key: _convert_to_dict(value) for key, value in obj.items()}

    # Pydantic モデルの場合
    if hasattr(obj, "model_dump"):
        return obj.model_dump()

    # protobuf の場合（MessageToDict を試みる）
    if hasattr(obj, "DESCRIPTOR"):
        try:
            from google.protobuf.json_format import MessageToDict

            return MessageToDict(obj, preserving_proto_field_name=True)
        except Exception:
            pass

    # __dict__ を持つオブジェクト
    if hasattr(obj, "__dict__"):
        return {
            key: _convert_to_dict(value)
            for key, value in obj.__dict__.items()
            if not key.startswith("_")
        }

    # 上記のいずれでもない場合は文字列化
    return str(obj)
