import functools

from influenceragents.agents.utils.agent_utils import build_influencer_context


def create_partnership_strategist(llm, memory):
    def strategist_node(state, name):
        username = state["influencer_username"]
        market = state.get("target_market", "MY")
        influencer_context = build_influencer_context(username, market)
        evaluation_plan = state["evaluation_plan"]

        metrics_report = state["metrics_report"]
        content_report = state["content_report"]
        audience_report = state["audience_report"]
        commerce_report = state["commerce_report"]

        curr_situation = f"{metrics_report}\n\n{content_report}\n\n{audience_report}\n\n{commerce_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for rec in past_memories:
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        from influenceragents.default_config import MARKET_CONFIGS
        market_config = MARKET_CONFIGS.get(market, MARKET_CONFIGS["MY"])
        tiers = market_config["fixed_fee_tiers"]
        symbol = market_config["currency_symbol"]

        tier_info = "\n".join([
            f"  {k}: {v['label']}" for k, v in tiers.items()
        ])

        messages = [
            {
                "role": "system",
                "content": f"""You are a Partnership Strategist developing a concrete collaboration proposal for a TikTok influencer. Based on the evaluation team's analysis, formulate a detailed partnership plan.

Your proposal must include:
1. **Collaboration Format**: Single video or multi-video series (no livestream or affiliate).
2. **Fixed Fee Tier（固定费用档位）**: Assign one of T0/T1/T2/T3 and a specific price per video.
   Fixed Fee Tiers per video ({symbol}):
{tier_info}

   **Tier assignment rules** — start from the follower-based reference tier in the commerce report, then adjust:
   - **Upgrade one tier** (or price toward the upper end of the current tier) if the influencer shows: high engagement rate (>5%), strong TikTok Shop sales record, proven brand collaboration history, or highly purchase-driven audience comments.
   - **Downgrade one tier** (or price toward the lower end of the current tier) if the influencer shows: low engagement rate (<2%), suspected fake followers, no commerce history, or weak audience buying intent.
   - Otherwise, price toward the **mid-to-upper range** of the reference tier as the default.
   - The final suggested price MUST fall within the selected tier's price range. State clearly which signals drove the tier decision.
   - Note: In addition to the fixed fee, a fixed 1% sales commission applies to all partnerships.

3. **Suggested Video Count**: How many videos for the campaign.
4. **Content Direction**: Specific content themes and angles that align with the influencer's strengths.
5. **Key Selling Points**: Why this influencer is (or isn't) worth the investment.

Apply lessons from past partnership decisions:
{past_memory_str}

Conclude with: PARTNERSHIP PROPOSAL: **[Recommend/Conditional/Not Recommend]** with tier and pricing.

Keep your entire response under 900 words. 1-2 sentences per point.

IMPORTANT: Write your entire response in Chinese (Simplified). All analysis, labels, and summaries must be in Chinese.""",
            },
            {
                "role": "user",
                "content": f"Based on analysis of @{username} in the {market} market. {influencer_context}\n\nEvaluation Plan: {evaluation_plan}",
            },
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "strategist_partnership_plan": result.content,
            "sender": name,
        }

    return functools.partial(strategist_node, name="Partnership Strategist")
