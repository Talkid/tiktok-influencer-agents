def create_audience_fit_debator(llm):
    def audience_fit_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        audience_fit_history = risk_debate_state.get("audience_fit_history", "")

        current_brand_safety_response = risk_debate_state.get("current_brand_safety_response", "")
        current_roi_response = risk_debate_state.get("current_roi_risk_response", "")

        metrics_report = state["metrics_report"]
        content_report = state["content_report"]
        audience_report = state["audience_report"]
        commerce_report = state["commerce_report"]
        strategist_plan = state["strategist_partnership_plan"]

        prompt = f"""As the Audience Fit Analyst, your role is to provide a balanced perspective, evaluating whether this influencer's actual audience matches the target market and product category.

Here is the partnership strategist's proposal:
{strategist_plan}

Your task is to objectively evaluate audience alignment:
- Does the influencer's audience match the target demographic for the product?
- Are the audience's interests aligned with the product category?
- Is the geographic distribution relevant to the target market?
- Balance the Brand Safety Analyst's overcaution with the ROI Risk Analyst's over-optimism
- Consider whether audience quality (engagement depth, purchase intent) matters more than quantity

Challenge both extremes:
- If Brand Safety is too cautious, point out manageable risks
- If ROI Risk is too optimistic, highlight audience mismatch concerns

Data sources:
Metrics Report: {metrics_report}
Content Report: {content_report}
Audience Report: {audience_report}
Commerce Report: {commerce_report}
Conversation history: {history}
Last Brand Safety response: {current_brand_safety_response}
Last ROI Risk response: {current_roi_response}

If no responses from others yet, present your own argument. Output conversationally without special formatting."""

        response = llm.invoke(prompt)
        argument = f"Audience Fit Analyst: {response.content}"

        new_state = {
            "history": history + "\n" + argument,
            "brand_safety_history": risk_debate_state.get("brand_safety_history", ""),
            "roi_risk_history": risk_debate_state.get("roi_risk_history", ""),
            "audience_fit_history": audience_fit_history + "\n" + argument,
            "latest_speaker": "Audience Fit",
            "current_brand_safety_response": risk_debate_state.get("current_brand_safety_response", ""),
            "current_roi_risk_response": risk_debate_state.get("current_roi_risk_response", ""),
            "current_audience_fit_response": argument,
            "judge_decision": risk_debate_state.get("judge_decision", ""),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_state}

    return audience_fit_node
