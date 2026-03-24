from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from influenceragents.agents.utils.agent_utils import (
    build_influencer_context,
    get_ecommerce_history,
    get_competitor_pricing,
    get_tiktok_shop_data,
)


def create_commerce_analyst(llm):

    def commerce_analyst_node(state):
        username = state["influencer_username"]
        market = state.get("target_market", "MY")
        influencer_context = build_influencer_context(username, market)

        tools = [
            get_ecommerce_history,
            get_competitor_pricing,
            get_tiktok_shop_data,
        ]

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

Produce a comprehensive commerce report with pricing recommendation."""

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
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(influencer_context=influencer_context)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "commerce_report": report,
        }

    return commerce_analyst_node
