def create_skeptic_researcher(llm, memory):
    def skeptic_node(state) -> dict:
        suitability_debate_state = state["suitability_debate_state"]
        history = suitability_debate_state.get("history", "")
        skeptic_history = suitability_debate_state.get("skeptic_history", "")
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

        prompt = f"""You are the Skeptic Analyst. Your goal is NOT to kill the deal, but to ensure we don't overpay given the risks. You must propose a risk-adjusted fixed fee per video that reflects your concerns — a price that still gives a reasonable chance of the influencer accepting, but protects us from excessive loss.

Fixed Fee Tiers for reference ({symbol}/video):
{tier_table}
The commerce report contains a **final tier recommendation** (after applying any upgrades or downgrades from engagement/commerce data). Use that **final adjusted tier** — not the raw follower-based baseline — as your starting point. Argue for pricing at the mid-to-lower range of that final tier, or argue for downgrading one tier only if the risks are severe. All price recommendations must fall within a valid tier's range. Do not propose prices below the lowest tier's minimum.

Key points to focus on:
- Risk-Adjusted Pricing: Based on the identified risks, propose a specific lower fixed fee per video within the appropriate tier range. Some loss is acceptable; catastrophic loss is not. (note: 1% sales commission is fixed and non-negotiable; only the fixed fee per video is adjustable.)
- Acceptance Probability: Your proposed price should still have a realistic chance of being accepted — do not propose an insulting lowball. Balance risk protection with deal viability.
- Fake Engagement / Metric Risks: If there are signs of inflated metrics, quantify the discount this warrants.
- Audience Mismatch or Content Risks: Factor these into your price reduction rationale.
- Commerce Performance: If conversion data is weak, argue for a lower guaranteed fee with upside tied to commission.
- Advocate Counterpoints: Critically engage with the advocate's optimistic assumptions and explain why a lower price is more prudent.

Resources available:
Metrics report: {metrics_report}
Content report: {content_report}
Audience report: {audience_report}
Commerce report: {commerce_report}
Debate history: {history}
Last advocate argument: {current_response}
Lessons from past analyses: {past_memory_str}

Deliver a concrete counter-offer price with clear risk reasoning. Address past lessons and learn from previous mistakes.

Keep your response under 400 words. Focus on 1-2 key points only.

IMPORTANT: Write your entire response in Chinese (Simplified)."""

        response = llm.invoke(prompt)
        argument = f"Skeptic Analyst: {response.content}"

        print("=" * 60)
        print("质疑方 (Skeptic Researcher)")
        print("=" * 60)
        print(argument)
        print()

        new_state = {
            "history": history + "\n" + argument,
            "skeptic_history": skeptic_history + "\n" + argument,
            "advocate_history": suitability_debate_state.get("advocate_history", ""),
            "current_response": argument,
            "count": suitability_debate_state["count"] + 1,
            "judge_decision": suitability_debate_state.get("judge_decision", ""),
        }

        return {"suitability_debate_state": new_state}

    return skeptic_node
