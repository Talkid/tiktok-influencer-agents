from typing import Annotated
from langchain_core.tools import tool
from influenceragents.dataflows.interface import route_to_vendor


@tool
def get_profile_info(
    username: Annotated[str, "TikTok username (without @)"],
) -> str:
    """Retrieve basic TikTok profile information: bio, follower/following counts, total likes, verification status."""
    return route_to_vendor("get_profile_info", username)


@tool
def get_follower_growth(
    username: Annotated[str, "TikTok username"],
    days: Annotated[int, "Lookback period in days"] = 30,
) -> str:
    """Retrieve follower growth data over time."""
    return route_to_vendor("get_follower_growth", username, days)


@tool
def get_engagement_rates(
    username: Annotated[str, "TikTok username"],
) -> str:
    """Calculate engagement rates from recent videos (avg likes/comments/shares per video vs views)."""
    return route_to_vendor("get_engagement_rates", username)


@tool
def get_video_performance_stats(
    username: Annotated[str, "TikTok username"],
    limit: Annotated[int, "Number of recent videos to analyze"] = 30,
) -> str:
    """Retrieve detailed performance stats for recent videos: views, likes, comments, shares, durations."""
    return route_to_vendor("get_video_performance_stats", username, limit)
