from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, ToolMessage

from influenceragents.agents.utils.agent_utils import (
    build_influencer_context,
    get_profile_info,
    get_follower_growth,
    get_engagement_rates,
    get_video_performance_stats,
)

_MAX_TOOL_ITERATIONS = 8


def create_metrics_analyst(llm):
    tools = [
        get_profile_info,
        get_follower_growth,
        get_engagement_rates,
        get_video_performance_stats,
    ]
    tool_map = {t.name: t for t in tools}

    def metrics_analyst_node(state):
        username = state["influencer_username"]
        market = state.get("target_market", "MY")
        influencer_context = build_influencer_context(username, market)

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

Produce a comprehensive metrics report with a summary table at the end.

IMPORTANT: Write your entire report in Chinese (Simplified). All analysis, labels, and summaries must be in Chinese."""

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
        prompt = prompt.partial(tool_names=", ".join([t.name for t in tools]))
        prompt = prompt.partial(influencer_context=influencer_context)

        chain = prompt | llm.bind_tools(tools)
        messages = list(state["messages"])
        report = ""

        for _ in range(_MAX_TOOL_ITERATIONS):
            result = chain.invoke(messages)
            if not result.tool_calls:
                report = result.content
                break
            messages.append(result)
            for tc in result.tool_calls:
                try:
                    output = tool_map[tc["name"]].invoke(tc["args"])
                except Exception as e:
                    output = f"工具调用失败 ({tc['name']}): {e}"
                messages.append(ToolMessage(content=str(output), tool_call_id=tc["id"]))

        return {
            "metrics_report": report,
            "messages": [HumanMessage(content="Continue")],
        }

    return metrics_analyst_node
