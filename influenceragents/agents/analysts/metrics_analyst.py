from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from influenceragents.agents.utils.agent_utils import (
    build_influencer_context,
    get_profile_info,
    get_follower_growth,
    get_engagement_rates,
    get_video_performance_stats,
)


def create_metrics_analyst(llm):

    def metrics_analyst_node(state):
        username = state["influencer_username"]
        market = state.get("target_market", "MY")
        influencer_context = build_influencer_context(username, market)

        tools = [
            get_profile_info,
            get_follower_growth,
            get_engagement_rates,
            get_video_performance_stats,
        ]

        system_message = """You are an influencer metrics analyst. Your task is to analyze the TikTok influencer's quantitative data and detect potential anomalies.

Analyze the following aspects:
1. **Profile Overview**: Follower count, following count, total likes, verification status
2. **Growth Trajectory**: Follower growth trends, posting frequency consistency
3. **Engagement Metrics**: Average views, likes, comments, shares per video; engagement rate calculation
4. **Anomaly Detection**: Look for signs of fake engagement:
   - High followers but very low engagement rate (<0.5%)
   - Sudden follower spikes without corresponding content
   - Abnormal like-to-comment ratios (too many likes, almost no comments)
   - Bot-like comment patterns
5. **Performance Consistency**: Variance in video performance, trending vs average content

First call get_profile_info to get the basic profile, then get_engagement_rates for engagement metrics, and get_video_performance_stats for detailed video data. Use get_follower_growth for growth trend analysis.

Produce a comprehensive metrics report with a summary table at the end."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant analyzing TikTok influencer data."
                    " Use the provided tools to gather data and produce a detailed analysis."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "\n{influencer_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(influencer_context=influencer_context)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "metrics_report": report,
        }

    return metrics_analyst_node
