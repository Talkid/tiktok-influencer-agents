from typing import Annotated
from langchain_core.tools import tool
from influenceragents.dataflows.interface import route_to_vendor


@tool
def get_ecommerce_history(
    username: Annotated[str, "TikTok username"],
) -> str:
    """Detect past brand collaborations, sponsored posts, product mentions, and TikTok Shop usage."""
    return route_to_vendor("get_ecommerce_history", username)


@tool
def get_competitor_pricing(
    username: Annotated[str, "TikTok username"],
) -> str:
    """Research pricing of comparable influencers in the same niche and follower range."""
    return route_to_vendor("get_competitor_pricing", username)


@tool
def get_tiktok_shop_data(
    username: Annotated[str, "TikTok username"],
) -> str:
    """Retrieve TikTok Shop product listing data, if available."""
    return route_to_vendor("get_tiktok_shop_data", username)
