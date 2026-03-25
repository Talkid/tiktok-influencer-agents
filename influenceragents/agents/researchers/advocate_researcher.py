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

        curr_situation = f"{metrics_report}\n\n{content_report}\n\n{audience_report}\n\n{commerce_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for rec in past_memories:
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""You are the Advocate Analyst making the case FOR partnering with this TikTok influencer. Your task is to build a strong, evidence-based case emphasizing the influencer's value for brand collaborations.

Key points to focus on:
- Growth Potential: Highlight follower growth trends, increasing engagement, and content virality potential.
- Content Quality: Emphasize content consistency, production value, and brand-friendly themes.
- Audience Value: Point to authentic engagement, relevant demographics, and purchase intent signals.
- Commerce Track Record: Highlight past successful collaborations, TikTok Shop activity, and conversion evidence.
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

Deliver a compelling case for why this influencer is worth partnering with. Address past lessons and learn from previous mistakes.

IMPORTANT: Write your entire response in Chinese (Simplified)."""

        response = llm.invoke(prompt)
        argument = f"Advocate Analyst: {response.content}"

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
