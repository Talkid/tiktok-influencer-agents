from langchain_core.messages import HumanMessage, RemoveMessage

from influenceragents.agents.utils.profile_tools import (
    get_profile_info,
    get_follower_growth,
    get_engagement_rates,
    get_video_performance_stats,
)
from influenceragents.agents.utils.content_tools import (
    get_recent_videos,
    analyze_video_thumbnails,
    get_content_categories,
)
from influenceragents.agents.utils.audience_tools import (
    get_audience_demographics,
    detect_fake_followers,
)
from influenceragents.agents.utils.commerce_tools import (
    get_ecommerce_history,
    get_competitor_pricing,
    get_tiktok_shop_data,
)


def build_influencer_context(username: str, market: str = "MY") -> str:
    """Describe the influencer so agents use the exact username consistently."""
    return (
        f"The TikTok influencer to analyze is `@{username}`. "
        f"Target market: {market}. "
        "Use this exact username in every tool call, report, and recommendation."
    )


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility."""
        messages = state["messages"]
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        placeholder = HumanMessage(content="Continue")
        return {"messages": removal_operations + [placeholder]}

    return delete_messages
