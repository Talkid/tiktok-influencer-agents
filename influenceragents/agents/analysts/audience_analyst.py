from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, ToolMessage

from influenceragents.agents.utils.agent_utils import (
    build_influencer_context,
    get_audience_demographics,
    detect_fake_followers,
)

_MAX_TOOL_ITERATIONS = 8


def create_audience_analyst(llm):
    tools = [
        get_audience_demographics,
        detect_fake_followers,
    ]
    tool_map = {t.name: t for t in tools}

    def audience_analyst_node(state):
        username = state["influencer_username"]
        market = state.get("target_market", "MY")
        influencer_context = build_influencer_context(username, market)

        system_message = """You are an influencer audience analyst. Your task is to analyze who actually watches and engages with this TikTok influencer's content.

Analyze the following aspects:
1. **Audience Demographics**: Estimated age range, gender split, geographic concentration
2. **Audience Authenticity**: Run fake follower detection to assess:
   - Engagement-to-follower ratio
   - Comment quality and diversity
   - Signs of bot activity or purchased followers
3. **Audience Quality**: Are the followers likely to be genuine consumers?
   - Comment sentiment (positive engagement vs spam)
   - Purchase intent signals in comments ("where to buy", "link?", "price?")
4. **Audience Match**: Does the audience align with the target market?
   - Language of comments vs target market languages
   - Geographic relevance
5. **Audience Loyalty**: Indicators of repeat engagement, fan community strength

First call get_audience_demographics for demographic data, then detect_fake_followers for authenticity analysis.

Provide an authenticity score (1-10) and produce a comprehensive audience report.

IMPORTANT: Write your entire report in Chinese (Simplified). All analysis, labels, and summaries must be in Chinese."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant analyzing TikTok influencer audiences."
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
            "audience_report": report,
            "messages": [HumanMessage(content="Continue")],
        }

    return audience_analyst_node
