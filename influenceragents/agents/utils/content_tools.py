from typing import Annotated
from langchain_core.tools import tool
from influenceragents.dataflows.interface import route_to_vendor


@tool
def get_recent_videos(
    username: Annotated[str, "TikTok username"],
    limit: Annotated[int, "Max number of videos to retrieve"] = 20,
) -> str:
    """Retrieve recent video metadata: captions, hashtags, music, duration, post time."""
    return route_to_vendor("get_recent_videos", username, limit)


@tool
def analyze_video_thumbnails(
    username: Annotated[str, "TikTok username"],
    limit: Annotated[int, "Max number of video thumbnails to analyze"] = 10,
) -> str:
    """Analyze video thumbnails/covers using vision model to extract visual tags and content categories."""
    return route_to_vendor("analyze_video_thumbnails", username, limit)


@tool
def get_content_categories(
    username: Annotated[str, "TikTok username"],
) -> str:
    """Analyze hashtags, captions, and content themes to categorize the influencer's content niche."""
    return route_to_vendor("get_content_categories", username)
