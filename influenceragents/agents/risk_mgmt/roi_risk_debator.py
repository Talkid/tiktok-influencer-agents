def create_roi_risk_debator(llm):
    def roi_risk_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        roi_risk_history = risk_debate_state.get("roi_risk_history", "")

        current_brand_safety_response = risk_debate_state.get("current_brand_safety_response", "")
        current_audience_fit_response = risk_debate_state.get("current_audience_fit_response", "")

        metrics_report = state["metrics_report"]
        content_report = state["content_report"]
        audience_report = state["audience_report"]
        commerce_report = state["commerce_report"]
        strategist_plan = state["strategist_partnership_plan"]

        prompt = f"""As the ROI Risk Analyst, your role is to champion high-reward opportunities and evaluate cost-effectiveness. Focus on whether the investment in this influencer will generate a positive return.

Here is the partnership strategist's proposal:
{strategist_plan}

Your task is to argue for the investment case:
- Highlight potential virality and reach amplification
- Emphasize engagement metrics that predict conversion
- Argue that the pricing is justified (or a bargain) given the influencer's actual performance
- Point out growth trajectory suggesting the influencer's value will increase
- Counter the Brand Safety Analyst's overcaution when risks are manageable
- Challenge the Audience Fit Analyst's narrow targeting when broader reach has value

Data sources:
Metrics Report: {metrics_report}
Content Report: {content_report}
Audience Report: {audience_report}
Commerce Report: {commerce_report}
Conversation history: {history}
Last Brand Safety response: {current_brand_safety_response}
Last Audience Fit response: {current_audience_fit_response}

If no responses from others yet, present your own argument. Output conversationally without special formatting.

Keep your response under 400 words. Focus on 1-2 key points only.

IMPORTANT: Write your entire response in Chinese (Simplified)."""

        response = llm.invoke(prompt)
        argument = f"ROI Risk Analyst: {response.content}"

        new_state = {
            "history": history + "\n" + argument,
            "brand_safety_history": risk_debate_state.get("brand_safety_history", ""),
            "roi_risk_history": roi_risk_history + "\n" + argument,
            "audience_fit_history": risk_debate_state.get("audience_fit_history", ""),
            "latest_speaker": "ROI Risk",
            "current_brand_safety_response": risk_debate_state.get("current_brand_safety_response", ""),
            "current_roi_risk_response": argument,
            "current_audience_fit_response": risk_debate_state.get("current_audience_fit_response", ""),
            "judge_decision": risk_debate_state.get("judge_decision", ""),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_state}

    return roi_risk_node
