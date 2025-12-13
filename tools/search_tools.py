from typing import Any, Dict, List, Optional

from google.genai import types as genai_types

from gemini_client import get_client

SUPPORTED_MODELS = [
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-preview",
    "gemini-2.5-flash-lite-preview",
]


def search_documents(
    *,
    model: str = "gemini-2.5-flash",
    store_names: List[str],
    query: str,
    metadata_filter: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    client = get_client()

    file_search = genai_types.FileSearch(
        store_names=store_names,
        metadata_filter=metadata_filter,
    )

    tool = genai_types.Tool(file_search=file_search)
    config = genai_types.GenerateContentConfig(
        tools=[tool],
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )

    response = client.models.generate_content(
        model=model,
        contents=[genai_types.Content(role="user", parts=[genai_types.Part.from_text(query)])],
        config=config,
    )

    candidate = response.candidates[0]
    answer_text = "".join(part.text for part in candidate.content.parts if hasattr(part, "text"))

    return {
        "answer_text": answer_text,
        "grounding_metadata": candidate.grounding_metadata,
        "used_stores": store_names,
        "model": model,
    }
