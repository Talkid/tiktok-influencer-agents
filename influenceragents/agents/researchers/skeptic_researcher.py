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

        curr_situation = f"{metrics_report}\n\n{content_report}\n\n{audience_report}\n\n{commerce_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for rec in past_memories:
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""You are the Skeptic Analyst making the case AGAINST partnering with this TikTok influencer. Your goal is to present a well-reasoned argument emphasizing risks, red flags, and potential downsides.

Key points to focus on:
- Fake Engagement Risks: Highlight any signs of purchased followers, bot activity, or artificially inflated metrics.
- Audience Mismatch: Point out where the influencer's actual audience doesn't align with the target market demographics.
- Content Risks: Identify inconsistent content quality, controversial themes, or brand-unfriendly material.
- Overpriced for Value: Argue whether the influencer's actual reach and conversion potential justifies the expected pricing.
- Limited Commerce Track Record: Highlight lack of proven e-commerce success or conversion data.
- Advocate Counterpoints: Critically analyze the advocate's arguments, exposing over-optimistic assumptions.
- Engagement: Present your argument conversationally, directly engaging with the advocate's points.

Resources available:
Metrics report: {metrics_report}
Content report: {content_report}
Audience report: {audience_report}
Commerce report: {commerce_report}
Debate history: {history}
Last advocate argument: {current_response}
Lessons from past analyses: {past_memory_str}

Deliver a compelling case for caution. Address past lessons and learn from previous mistakes.

Keep your response under 400 words. Focus on 1-2 key points only.

IMPORTANT: Write your entire response in Chinese (Simplified)."""

        response = llm.invoke(prompt)
        argument = f"Skeptic Analyst: {response.content}"

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
