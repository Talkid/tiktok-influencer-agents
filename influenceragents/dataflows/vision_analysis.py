"""Vision analysis pipeline for video thumbnails/covers.

Downloads thumbnail images and analyzes them using vision-capable LLMs
(Claude Vision, GPT-4V) to extract visual tags and content categories.
"""

import json
import base64
from typing import List, Optional

import httpx

from influenceragents.dataflows.config import get_config


def _download_image_as_base64(url: str, timeout: float = 15.0) -> Optional[str]:
    """Download image and return as base64 string."""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode("utf-8")
    except Exception:
        return None


def _get_media_type(url: str) -> str:
    """Infer media type from URL."""
    url_lower = url.lower()
    if ".png" in url_lower:
        return "image/png"
    if ".webp" in url_lower:
        return "image/webp"
    return "image/jpeg"


def analyze_thumbnails_claude(username: str, limit: int = 10) -> str:
    """Analyze video thumbnails using Claude Vision."""
    from influenceragents.dataflows.apify_tiktok import get_apify_video_thumbnails
    from influenceragents.llm_clients import create_llm_client

    config = get_config()
    market = config.get("target_market", "MY")

    # Get thumbnail data
    thumbnails_json = get_apify_video_thumbnails(username, limit)
    try:
        covers = json.loads(thumbnails_json)
    except (json.JSONDecodeError, TypeError):
        return f"Could not parse thumbnail data for @{username}"

    if not covers:
        return f"No thumbnails available for @{username}"

    # Download and encode images
    images = []
    for cover in covers[:5]:  # Limit to 5 to control costs
        b64 = _download_image_as_base64(cover["url"])
        if b64:
            images.append({
                "base64": b64,
                "media_type": _get_media_type(cover["url"]),
                "caption": cover.get("caption", ""),
            })

    if not images:
        return f"Could not download any thumbnails for @{username}"

    # Build vision prompt
    vision_provider = config.get("vision_llm_provider", "anthropic")
    vision_client = create_llm_client(
        provider=vision_provider,
        model=config.get("vision_llm_model", "claude-sonnet-4-20250514"),
        base_url=config.get("backend_url") if vision_provider not in ("anthropic",) else None,
    )
    vision_llm = vision_client.get_llm()

    # Construct message with images
    content_blocks = [
        {
            "type": "text",
            "text": (
                f"Analyze these {len(images)} TikTok video thumbnails from @{username} (target market: {market}). "
                "For each image, identify:\n"
                "1. Estimated age range of the person(s)\n"
                "2. Content category (beauty, food, tech, lifestyle, parenting, fashion, etc.)\n"
                "3. Production quality (professional/amateur/home setting/outdoor)\n"
                "4. Lifestyle indicators (luxury brands, kids present, home decor, car, etc.)\n"
                "5. Text overlays and their language\n\n"
                "After analyzing all images, provide a SUMMARY with:\n"
                "- Dominant content themes\n"
                "- Influencer age estimate\n"
                "- Target audience age range\n"
                "- Key lifestyle tags\n"
                "- Overall content style\n"
                "- Brand-friendliness assessment"
            ),
        }
    ]

    for img in images:
        content_blocks.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{img['media_type']};base64,{img['base64']}",
            },
        })
        if img["caption"]:
            content_blocks.append({
                "type": "text",
                "text": f"Caption: {img['caption']}",
            })

    messages = [{"role": "user", "content": content_blocks}]

    try:
        result = vision_llm.invoke(messages)
        return result.content
    except Exception as e:
        return f"Vision analysis error for @{username}: {e}"


def analyze_thumbnails_openai(username: str, limit: int = 10) -> str:
    """Analyze video thumbnails using OpenAI GPT-4V."""
    # Same structure as Claude but uses OpenAI's vision endpoint
    from influenceragents.dataflows.apify_tiktok import get_apify_video_thumbnails
    from influenceragents.llm_clients import create_llm_client

    config = get_config()

    thumbnails_json = get_apify_video_thumbnails(username, limit)
    try:
        covers = json.loads(thumbnails_json)
    except (json.JSONDecodeError, TypeError):
        return f"Could not parse thumbnail data for @{username}"

    if not covers:
        return f"No thumbnails available for @{username}"

    # Use cover URLs directly (OpenAI supports URL-based image input)
    vision_client = create_llm_client(
        provider="openai",
        model="gpt-4o",
    )
    vision_llm = vision_client.get_llm()

    market = config.get("target_market", "MY")
    content_blocks = [
        {
            "type": "text",
            "text": (
                f"Analyze these TikTok video thumbnails from @{username} (market: {market}). "
                "Identify content themes, influencer demographics, lifestyle tags, and brand-friendliness."
            ),
        }
    ]

    for cover in covers[:5]:
        content_blocks.append({
            "type": "image_url",
            "image_url": {"url": cover["url"]},
        })

    messages = [{"role": "user", "content": content_blocks}]

    try:
        result = vision_llm.invoke(messages)
        return result.content
    except Exception as e:
        return f"Vision analysis error for @{username}: {e}"
