from influenceragents.agents.utils.agent_utils import build_influencer_context


def create_evaluation_manager(llm, memory):
    def evaluation_manager_node(state) -> dict:
        influencer_context = build_influencer_context(
            state["influencer_username"], state.get("target_market", "MY")
        )
        history = state["suitability_debate_state"].get("history", "")
        suitability_debate_state = state["suitability_debate_state"]

        metrics_report = state["metrics_report"]
        content_report = state["content_report"]
        audience_report = state["audience_report"]
        commerce_report = state["commerce_report"]

        curr_situation = f"{metrics_report}\n\n{content_report}\n\n{audience_report}\n\n{commerce_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for rec in past_memories:
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""As the Evaluation Manager and debate facilitator, critically evaluate the advocate vs skeptic debate and make a definitive decision: Recommend, Conditionally Recommend, or Not Recommend this influencer for partnership.

Summarize the key points from both sides concisely, focusing on the most compelling evidence. Your recommendation must be clear and actionable. Avoid defaulting to "Conditional" simply because both sides have valid points; commit to a stance grounded in the debate's strongest arguments.

Additionally, develop a preliminary partnership strategy direction:
1. Your Recommendation: A decisive stance supported by the strongest arguments.
2. Rationale: Why these arguments lead to your conclusion.
3. Strategic Direction: Initial thoughts on collaboration format, content direction, and pricing tier.

Consider your past decisions on similar influencers. Use these insights to refine your judgment.

Past reflections on similar situations:
\"{past_memory_str}\"

{influencer_context}

Debate History:
{history}"""

        response = llm.invoke(prompt)

        new_state = {
            "judge_decision": response.content,
            "history": suitability_debate_state.get("history", ""),
            "skeptic_history": suitability_debate_state.get("skeptic_history", ""),
            "advocate_history": suitability_debate_state.get("advocate_history", ""),
            "current_response": response.content,
            "count": suitability_debate_state["count"],
        }

        return {
            "suitability_debate_state": new_state,
            "evaluation_plan": response.content,
        }

    return evaluation_manager_node
