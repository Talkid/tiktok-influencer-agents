def create_advocate_researcher(llm, memory):
    def advocate_node(state) -> dict:
        suitability_debate_state = state["suitability_debate_state"]
        history = suitability_debate_state.get("history", "")
        advocate_history = suitability_debate_state.get("advocate_history", "")
        current_response = suitability_debate_state.get("current_response", "")

        metrics_report = state["metrics_report"]
        content_report = state["content_report"]
        audience_report = state["audience_report"]
        commerce_report = state["commerce_report"]

        market = state.get("target_market", "MY")

        curr_situation = f"{metrics_report}\n\n{content_report}\n\n{audience_report}\n\n{commerce_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for rec in past_memories:
            past_memory_str += rec["recommendation"] + "\n\n"

        from influenceragents.default_config import MARKET_CONFIGS
        market_config = MARKET_CONFIGS.get(market, MARKET_CONFIGS["MY"])
        tiers = market_config["fixed_fee_tiers"]
        symbol = market_config["currency_symbol"]
        tier_table = "\n".join([f"  {k}: {v['label']}" for k, v in tiers.items()])

        prompt = f"""You are the Advocate Analyst. Your core goal is to maximize the probability that the influencer will ACCEPT our partnership offer. Your pricing recommendations must be grounded in this acceptance probability — propose a fixed fee per video that is attractive enough to secure the deal while remaining cost-effective.

Fixed Fee Tiers for reference ({symbol}/video):
{tier_table}
The commerce report contains a **final tier recommendation** (after applying any upgrades or downgrades from engagement/commerce data). Use that **final adjusted tier** — not the raw follower-based baseline — as your starting point. Argue for pricing at the mid-to-upper range of that final tier. All price recommendations must fall within a valid tier's range.

Key points to focus on:
- Acceptance Probability: Assess how likely the influencer is to accept a given offer based on their market position, follower count, engagement rate, and past collaboration behavior. Higher acceptance probability should anchor your recommended price range.
- Fair Value Pricing: Recommend a specific fixed fee per video within the appropriate tier range. The goal is a price the influencer is very likely to say yes to (note: 1% sales commission is fixed and non-negotiable; only the fixed fee per video is adjustable).
- Partnership Fit: Highlight reasons the influencer would be motivated to collaborate — audience alignment, brand relevance, content style match.
- Commerce Upside: Reference any conversion data, TikTok Shop activity, or past collaboration evidence to justify the investment.
- Skeptic Counterpoints: Directly address the skeptic's concerns with specific data and reasoning.
- Engagement: Present your argument in a conversational style, debating effectively rather than just listing data.

Resources available:
Metrics report: {metrics_report}
Content report: {content_report}
Audience report: {audience_report}
Commerce report: {commerce_report}
Debate history: {history}
Last skeptic argument: {current_response}
Lessons from past analyses: {past_memory_str}

Deliver a compelling case for partnering, with a concrete price recommendation that gives us the highest chance of the influencer accepting. Address past lessons and learn from previous mistakes.

Keep your response under 400 words. Focus on 1-2 key points only.

IMPORTANT: Write your entire response in Chinese (Simplified)."""

        response = llm.invoke(prompt)
        argument = f"Advocate Analyst: {response.content}"
        
                
        print("=" * 60)
        print("合作方 (Skeptic Researcher)")
        print("=" * 60)
        print(argument)
        print()

        new_state = {
            "history": history + "\n" + argument,
            "advocate_history": advocate_history + "\n" + argument,
            "skeptic_history": suitability_debate_state.get("skeptic_history", ""),
            "current_response": argument,
            "count": suitability_debate_state["count"] + 1,
            "judge_decision": suitability_debate_state.get("judge_decision", ""),
        }

        return {"suitability_debate_state": new_state}

    return advocate_node
