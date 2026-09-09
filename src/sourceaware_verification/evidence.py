"""Evidence storage and the two retrieval services used in the manuscript."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .io import dump_json, load_json, load_jsonl, validate_identifier


UNAVAILABLE = "[Evidence unavailable under the current retrieval setting]"


class EvidenceStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def _optional(self, kind: str, sample_id: str) -> dict[str, Any] | None:
        safe_id = validate_identifier(sample_id, "sample_id")
        path = self.root / kind / f"{safe_id}.json"
        return load_json(path) if path.is_file() else None

    def image(self, sample_id: str) -> dict[str, Any] | None:
        return self._optional("image", sample_id)

    def text(self, sample_id: str) -> dict[str, Any] | None:
        return self._optional("text", sample_id)

    @staticmethod
    def render_text(value: dict[str, Any] | None, limit: int = 3) -> str:
        if not value:
            return UNAVAILABLE
        rendered = []
        for index, item in enumerate(value.get("items", [])[:limit], 1):
            rendered.append(
                f"[{index}] Title: {item.get('title', '')}\n"
                f"Snippet: {item.get('snippet', '')}\n"
                f"URL: {item.get('link', '')}"
            )
        return "\n\n".join(rendered) if rendered else UNAVAILABLE

    @staticmethod
    def render_image(value: dict[str, Any] | None, limit: int = 3) -> str:
        if not value:
            return UNAVAILABLE
        parts = []
        labels = value.get("best_guess_labels", [])[:limit]
        entities = value.get("web_entities", [])[:limit]
        if labels:
            parts.append("Best-guess labels: " + "; ".join(map(str, labels)))
        if entities:
            parts.append(
                "Web entities: "
                + "; ".join(str(item.get("description", "")) for item in entities)
            )
        for index, page in enumerate(value.get("pages_with_matching_images", [])[:limit], 1):
            parts.append(
                f"[{index}] Page title: {page.get('page_title', '')}\n"
                f"Context: {page.get('description') or page.get('surrounding_text', '')}\n"
                f"URL: {page.get('url', '')}"
            )
        return "\n\n".join(parts) if parts else UNAVAILABLE


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.skip_depth = 0
        self.title: list[str] = []
        self.text: list[str] = []
        self.description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript"}:
            self.skip_depth += 1
        if normalized == "title":
            self.in_title = True
        if normalized == "meta":
            values = {key.lower(): value or "" for key, value in attrs}
            if values.get("name", "").lower() == "description" or values.get(
                "property", ""
            ).lower() == "og:description":
                self.description = values.get("content", self.description)

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
        if normalized == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if not value or self.skip_depth:
            return
        if self.in_title:
            self.title.append(value)
        self.text.append(value)


def _page_context(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {}
    try:
        import requests

        response = requests.get(
            url,
            timeout=(5, 10),
            headers={"User-Agent": "source-aware-verification-review-artifact/0.1"},
        )
        response.raise_for_status()
        if "html" not in response.headers.get("content-type", "").lower():
            return {}
        parser = _PageParser()
        parser.feed(response.content[:1_000_000].decode(response.encoding or "utf-8", errors="replace"))
        return {
            "retrieved_title": " ".join(parser.title)[:500],
            "description": " ".join(parser.description.split())[:1000],
            "surrounding_text": " ".join(parser.text)[:1500],
        }
    except Exception:
        return {}


def collect_text_evidence(
    manifest: str | Path,
    output_root: str | Path,
    limit: int = 3,
    api_key: str | None = None,
    search_engine_id: str | None = None,
) -> int:
    if not 1 <= limit <= 10:
        raise ValueError("retrieval limit must be between 1 and 10")
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("Install the evidence extra: pip install -e '.[evidence]'") from exc
    key = api_key or os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
    engine = search_engine_id or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
    if not key or not engine:
        raise RuntimeError("Set GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
    destination = Path(output_root).expanduser().resolve() / "text"
    count = 0
    for row in load_jsonl(manifest):
        if not str(row.get("text", "")).strip():
            continue
        sample_id = validate_identifier(row.get("sample_id"), "sample_id")
        query = str(row["text"])
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": key, "cx": engine, "q": query, "num": limit},
            timeout=30,
        )
        response.raise_for_status()
        items = []
        for item in response.json().get("items", [])[:limit]:
            items.append(
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                }
            )
        dump_json(
            destination / f"{sample_id}.json",
            {
                "sample_id": sample_id,
                "provider": "google_custom_search",
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "query": query,
                "limit": limit,
                "items": items,
            },
        )
        count += 1
    return count


def collect_image_evidence(
    manifest: str | Path,
    output_root: str | Path,
    limit: int = 3,
    media_root: str | Path | None = None,
    fetch_page_context: bool = True,
) -> int:
    if limit < 1:
        raise ValueError("retrieval limit must be positive")
    try:
        from google.cloud import vision
    except ImportError as exc:
        raise RuntimeError("Install the evidence extra: pip install -e '.[evidence]'") from exc
    client = vision.ImageAnnotatorClient()
    destination = Path(output_root).expanduser().resolve() / "image"
    root = Path(media_root).expanduser().resolve() if media_root else Path(manifest).resolve().parent
    count = 0
    for row in load_jsonl(manifest):
        if not str(row.get("image_path", "")).strip():
            continue
        sample_id = validate_identifier(row.get("sample_id"), "sample_id")
        image_path = Path(str(row["image_path"])).expanduser()
        if not image_path.is_absolute():
            image_path = root / image_path
        response = client.web_detection(image=vision.Image(content=image_path.read_bytes()))
        if response.error.message:
            raise RuntimeError(f"{sample_id}: {response.error.message}")
        web = response.web_detection
        pages = []
        for page in web.pages_with_matching_images[:limit]:
            item: dict[str, Any] = {
                "url": page.url,
                "page_title": page.page_title,
                "full_matching_images": [image_ref.url for image_ref in page.full_matching_images],
                "partial_matching_images": [image_ref.url for image_ref in page.partial_matching_images],
            }
            if fetch_page_context:
                item.update(_page_context(page.url))
            pages.append(item)
        dump_json(
            destination / f"{sample_id}.json",
            {
                "sample_id": sample_id,
                "provider": "google_vision_web_detection",
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "limit": limit,
                "best_guess_labels": [item.label for item in web.best_guess_labels[:limit]],
                "web_entities": [
                    {"description": item.description, "score": item.score}
                    for item in web.web_entities[:limit]
                ],
                "pages_with_matching_images": pages,
            },
        )
        count += 1
    return count
