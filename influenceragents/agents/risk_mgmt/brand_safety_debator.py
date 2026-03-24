def create_brand_safety_debator(llm):
    def brand_safety_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        brand_safety_history = risk_debate_state.get("brand_safety_history", "")

        current_roi_response = risk_debate_state.get("current_roi_risk_response", "")
        current_audience_fit_response = risk_debate_state.get("current_audience_fit_response", "")

        metrics_report = state["metrics_report"]
        content_report = state["content_report"]
        audience_report = state["audience_report"]
        commerce_report = state["commerce_report"]
        strategist_plan = state["strategist_partnership_plan"]

        prompt = f"""As the Brand Safety Analyst, your primary objective is to protect brand reputation and minimize reputational risk. You prioritize safety, content quality, and long-term brand value when evaluating this influencer partnership.

Here is the partnership strategist's proposal:
{strategist_plan}

Your task is to critically examine potential brand risks:
- Content that could embarrass or damage the brand
- Controversial opinions, past scandals, or NSFW content patterns
- Audience authenticity concerns (fake followers damage brand credibility)
- Contract protection recommendations
- Cultural sensitivity issues in the target market

Counter the ROI Risk Analyst's focus on returns by emphasizing that brand damage is often irreversible. Counter the Audience Fit Analyst where their assumptions about audience quality may be too optimistic.

Data sources:
Metrics Report: {metrics_report}
Content Report: {content_report}
Audience Report: {audience_report}
Commerce Report: {commerce_report}
Conversation history: {history}
Last ROI Risk response: {current_roi_response}
Last Audience Fit response: {current_audience_fit_response}

If no responses from others yet, present your own argument. Output conversationally without special formatting."""

        response = llm.invoke(prompt)
        argument = f"Brand Safety Analyst: {response.content}"

        new_state = {
            "history": history + "\n" + argument,
            "brand_safety_history": brand_safety_history + "\n" + argument,
            "roi_risk_history": risk_debate_state.get("roi_risk_history", ""),
            "audience_fit_history": risk_debate_state.get("audience_fit_history", ""),
            "latest_speaker": "Brand Safety",
            "current_brand_safety_response": argument,
            "current_roi_risk_response": risk_debate_state.get("current_roi_risk_response", ""),
            "current_audience_fit_response": risk_debate_state.get("current_audience_fit_response", ""),
            "judge_decision": risk_debate_state.get("judge_decision", ""),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_state}

    return brand_safety_node
