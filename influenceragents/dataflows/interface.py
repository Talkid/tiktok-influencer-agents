"""Data vendor routing interface.

Routes tool calls to appropriate vendor implementations (Apify, vision models, etc.)
with fallback support.
"""

from .config import get_config
from .apify_tiktok import (
    get_apify_profile_info,
    get_apify_follower_growth,
    get_apify_engagement_rates,
    get_apify_video_performance_stats,
    get_apify_recent_videos,
    get_apify_content_categories,
    get_apify_audience_demographics,
    get_apify_fake_followers,
    get_apify_ecommerce_history,
    get_apify_competitor_pricing,
    get_apify_tiktok_shop_data,
)
from .vision_analysis import (
    analyze_thumbnails_claude,
    analyze_thumbnails_openai,
)

# Tools organized by category
TOOLS_CATEGORIES = {
    "profile_data": {
        "description": "Profile and follower statistics",
        "tools": [
            "get_profile_info",
            "get_follower_growth",
            "get_engagement_rates",
            "get_video_performance_stats",
        ],
    },
    "content_data": {
        "description": "Video content and visual analysis",
        "tools": [
            "get_recent_videos",
            "analyze_video_thumbnails",
            "get_content_categories",
        ],
    },
    "audience_data": {
        "description": "Audience demographics and authenticity",
        "tools": [
            "get_audience_demographics",
            "detect_fake_followers",
        ],
    },
    "commerce_data": {
        "description": "E-commerce and pricing intelligence",
        "tools": [
            "get_ecommerce_history",
            "get_competitor_pricing",
            "get_tiktok_shop_data",
        ],
    },
}

VENDOR_LIST = [
    "apify",
    "claude_vision",
    "openai_vision",
]

# Mapping of methods to their vendor-specific implementations
VENDOR_METHODS = {
    # profile_data
    "get_profile_info": {
        "apify": get_apify_profile_info,
    },
    "get_follower_growth": {
        "apify": get_apify_follower_growth,
    },
    "get_engagement_rates": {
        "apify": get_apify_engagement_rates,
    },
    "get_video_performance_stats": {
        "apify": get_apify_video_performance_stats,
    },
    # content_data
    "get_recent_videos": {
        "apify": get_apify_recent_videos,
    },
    "analyze_video_thumbnails": {
        "claude_vision": analyze_thumbnails_claude,
        "openai_vision": analyze_thumbnails_openai,
    },
    "get_content_categories": {
        "apify": get_apify_content_categories,
    },
    # audience_data
    "get_audience_demographics": {
        "apify": get_apify_audience_demographics,
    },
    "detect_fake_followers": {
        "apify": get_apify_fake_followers,
    },
    # commerce_data
    "get_ecommerce_history": {
        "apify": get_apify_ecommerce_history,
    },
    "get_competitor_pricing": {
        "apify": get_apify_competitor_pricing,
    },
    "get_tiktok_shop_data": {
        "apify": get_apify_tiktok_shop_data,
    },
}


def get_category_for_method(method: str) -> str:
    """Get the category that contains the specified method."""
    for category, info in TOOLS_CATEGORIES.items():
        if method in info["tools"]:
            return category
    raise ValueError(f"Method '{method}' not found in any category")


def get_vendor(category: str, method: str = None) -> str:
    """Get the configured vendor for a data category or specific tool method."""
    config = get_config()

    # Check tool-level configuration first
    if method:
        tool_vendors = config.get("tool_vendors", {})
        if method in tool_vendors:
            return tool_vendors[method]

    # Fall back to category-level configuration
    vendors = config.get("data_vendors", {})

    # Special case: vision analysis tools default to vision_analysis vendor
    if method == "analyze_video_thumbnails":
        return vendors.get("vision_analysis", "claude_vision")

    return vendors.get(category, "apify")


def route_to_vendor(method: str, *args, **kwargs):
    """Route method calls to appropriate vendor implementation."""
    category = get_category_for_method(method)
    vendor_config = get_vendor(category, method)
    primary_vendors = [v.strip() for v in vendor_config.split(",")]

    if method not in VENDOR_METHODS:
        raise ValueError(f"Method '{method}' not supported")

    # Build fallback chain
    all_available_vendors = list(VENDOR_METHODS[method].keys())
    fallback_vendors = primary_vendors.copy()
    for vendor in all_available_vendors:
        if vendor not in fallback_vendors:
            fallback_vendors.append(vendor)

    for vendor in fallback_vendors:
        if vendor not in VENDOR_METHODS[method]:
            continue

        vendor_impl = VENDOR_METHODS[method][vendor]
        impl_func = vendor_impl[0] if isinstance(vendor_impl, list) else vendor_impl

        try:
            return impl_func(*args, **kwargs)
        except Exception:
            continue

    raise RuntimeError(f"No available vendor for '{method}'")
