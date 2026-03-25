from influenceragents.agents.utils.agent_states import AgentState


class ConditionalLogic:
    """Handles conditional logic for determining graph flow."""

    def __init__(self, max_debate_rounds=1, max_risk_discuss_rounds=1):
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds

    def should_continue_debate(self, state: AgentState) -> str:
        if state["suitability_debate_state"]["count"] >= 2 * self.max_debate_rounds:
            return "Evaluation Manager"
        if state["suitability_debate_state"]["current_response"].startswith("Advocate"):
            return "Skeptic Researcher"
        return "Advocate Researcher"

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        if state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds:
            return "Campaign Manager"
        if state["risk_debate_state"]["latest_speaker"].startswith("Brand Safety"):
            return "ROI Risk Analyst"
        if state["risk_debate_state"]["latest_speaker"].startswith("ROI Risk"):
            return "Audience Fit Analyst"
        return "Brand Safety Analyst"
