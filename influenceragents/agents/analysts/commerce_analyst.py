from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, ToolMessage

from influenceragents.agents.utils.agent_utils import (
    build_influencer_context,
    get_ecommerce_history,
    get_competitor_pricing,
    get_tiktok_shop_data,
)

_MAX_TOOL_ITERATIONS = 8


def create_commerce_analyst(llm):
    tools = [
        get_ecommerce_history,
        get_competitor_pricing,
        get_tiktok_shop_data,
    ]
    tool_map = {t.name: t for t in tools}

    def commerce_analyst_node(state):
        username = state["influencer_username"]
        market = state.get("target_market", "MY")
        influencer_context = build_influencer_context(username, market)

        system_message = """You are an influencer commerce analyst. Your task is to evaluate the TikTok influencer's e-commerce potential and determine appropriate pricing.

Analyze the following aspects:
1. **E-commerce History**: Past brand collaborations, sponsored content frequency, product promotion track record
2. **TikTok Shop Activity**: Whether the influencer uses TikTok Shop, affiliate links, or product showcases
3. **Conversion Signals**: Comments indicating purchase behavior ("I bought it", "link please", "discount code")
4. **Competitor Pricing**: What do comparable influencers in this niche/follower range charge?
5. **Product Category Fit**: Based on content and audience, what product categories are most suitable?
   - Beauty & Skincare
   - Food & Beverage
   - Fashion & Apparel
   - Electronics & Tech
   - Home & Living
   - Health & Fitness
   - Baby & Kids
   - Others
6. **Commission Tier Assessment**: Based on followers, engagement, and e-commerce track record, suggest T0/T1/T2/T3 tier

First call get_ecommerce_history to analyze past collaborations, then get_competitor_pricing for market rates, and get_tiktok_shop_data for shop activity.

Produce a comprehensive commerce report with pricing recommendation.

IMPORTANT: Write your entire report in Chinese (Simplified). All analysis, labels, and summaries must be in Chinese."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant analyzing TikTok influencer commerce potential."
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
            "commerce_report": report,
            "messages": [HumanMessage(content="Continue")],
        }

    return commerce_analyst_node
