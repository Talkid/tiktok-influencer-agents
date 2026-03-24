from typing import Annotated
from langchain_core.tools import tool
from influenceragents.dataflows.interface import route_to_vendor


@tool
def get_audience_demographics(
    username: Annotated[str, "TikTok username"],
) -> str:
    """Estimate audience demographics from comment analysis and available platform data."""
    return route_to_vendor("get_audience_demographics", username)


@tool
def detect_fake_followers(
    username: Annotated[str, "TikTok username"],
) -> str:
    """Analyze follower authenticity: engagement-to-follower ratio, comment quality, follower growth patterns."""
    return route_to_vendor("detect_fake_followers", username)
