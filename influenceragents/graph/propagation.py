from typing import Dict, Any, List, Optional
from influenceragents.agents.utils.agent_states import (
    AgentState,
    SuitabilityDebateState,
    RiskDebateState,
)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100):
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self, username: str, analysis_date: str, target_market: str = "MY"
    ) -> Dict[str, Any]:
        return {
            "messages": [("human", username)],
            "influencer_username": username,
            "analysis_date": str(analysis_date),
            "target_market": target_market,
            "suitability_debate_state": SuitabilityDebateState(
                {
                    "advocate_history": "",
                    "skeptic_history": "",
                    "history": "",
                    "current_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
            ),
            "risk_debate_state": RiskDebateState(
                {
                    "brand_safety_history": "",
                    "roi_risk_history": "",
                    "audience_fit_history": "",
                    "history": "",
                    "latest_speaker": "",
                    "current_brand_safety_response": "",
                    "current_roi_risk_response": "",
                    "current_audience_fit_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
            ),
            "metrics_report": "",
            "content_report": "",
            "audience_report": "",
            "commerce_report": "",
        }

    def get_graph_args(self, callbacks: Optional[List] = None) -> Dict[str, Any]:
        config = {"recursion_limit": self.max_recur_limit}
        if callbacks:
            config["callbacks"] = callbacks
        return {
            "stream_mode": "values",
            "config": config,
        }
