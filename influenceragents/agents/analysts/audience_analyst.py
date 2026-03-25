from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from influenceragents.agents.utils.agent_utils import (
    build_influencer_context,
    get_audience_demographics,
    detect_fake_followers,
)


def create_audience_analyst(llm):

    def audience_analyst_node(state):
        username = state["influencer_username"]
        market = state.get("target_market", "MY")
        influencer_context = build_influencer_context(username, market)

        tools = [
            get_audience_demographics,
            detect_fake_followers,
        ]

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

Provide an authenticity score (1-10). Output format — use bullet points per section. Be concise: 2-4 bullets each, key data only, no verbose paragraphs. Total report must stay under 500 words.

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
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(influencer_context=influencer_context)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "audience_report": report,
        }

    return audience_analyst_node
