from typing import Dict, Any
from langgraph.graph import END, StateGraph, START

from influenceragents.agents import *
from influenceragents.agents.analysts.parallel_runner import create_parallel_analysts
from influenceragents.agents.utils.agent_states import AgentState

from .conditional_logic import ConditionalLogic


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm,
        deep_thinking_llm,
        advocate_memory,
        skeptic_memory,
        strategist_memory,
        evaluation_judge_memory,
        campaign_manager_memory,
        conditional_logic: ConditionalLogic,
    ):
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.advocate_memory = advocate_memory
        self.skeptic_memory = skeptic_memory
        self.strategist_memory = strategist_memory
        self.evaluation_judge_memory = evaluation_judge_memory
        self.campaign_manager_memory = campaign_manager_memory
        self.conditional_logic = conditional_logic

    def setup_graph(
        self, selected_analysts=["metrics", "content", "audience", "commerce"], debug=False
    ):
        if len(selected_analysts) == 0:
            raise ValueError("Influencer Agents Graph Setup Error: no analysts selected!")

        # Create researcher and manager nodes
        advocate_node = create_advocate_researcher(
            self.quick_thinking_llm, self.advocate_memory
        )
        skeptic_node = create_skeptic_researcher(
            self.quick_thinking_llm, self.skeptic_memory
        )
        evaluation_manager_node = create_evaluation_manager(
            self.deep_thinking_llm, self.evaluation_judge_memory
        )
        strategist_node = create_partnership_strategist(
            self.quick_thinking_llm, self.strategist_memory
        )

        # Create risk analysis nodes
        brand_safety_node = create_brand_safety_debator(self.quick_thinking_llm)
        roi_risk_node = create_roi_risk_debator(self.quick_thinking_llm)
        audience_fit_node = create_audience_fit_debator(self.quick_thinking_llm)
        campaign_manager_node = create_campaign_manager(
            self.deep_thinking_llm, self.campaign_manager_memory
        )

        # Parallel analysts node (replaces 4 sequential analyst chains)
        parallel_analysts_node = create_parallel_analysts(
            self.quick_thinking_llm, selected_analysts, debug=debug
        )

        # Create workflow
        workflow = StateGraph(AgentState)

        # Single parallel node for all analysts
        workflow.add_node("Parallel Analysts", parallel_analysts_node)

        # Add other nodes
        workflow.add_node("Advocate Researcher", advocate_node)
        workflow.add_node("Skeptic Researcher", skeptic_node)
        workflow.add_node("Evaluation Manager", evaluation_manager_node)
        workflow.add_node("Partnership Strategist", strategist_node)
        workflow.add_node("Brand Safety Analyst", brand_safety_node)
        workflow.add_node("ROI Risk Analyst", roi_risk_node)
        workflow.add_node("Audience Fit Analyst", audience_fit_node)
        workflow.add_node("Campaign Manager", campaign_manager_node)

        # Define edges
        workflow.add_edge(START, "Parallel Analysts")
        workflow.add_edge("Parallel Analysts", "Advocate Researcher")

        # Suitability debate edges
        workflow.add_conditional_edges(
            "Advocate Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Skeptic Researcher": "Skeptic Researcher",
                "Evaluation Manager": "Evaluation Manager",
            },
        )
        workflow.add_conditional_edges(
            "Skeptic Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Advocate Researcher": "Advocate Researcher",
                "Evaluation Manager": "Evaluation Manager",
            },
        )

        # Evaluation → Strategist → Risk debate
        workflow.add_edge("Evaluation Manager", "Partnership Strategist")
        workflow.add_edge("Partnership Strategist", "Brand Safety Analyst")

        # Risk debate edges
        workflow.add_conditional_edges(
            "Brand Safety Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "ROI Risk Analyst": "ROI Risk Analyst",
                "Campaign Manager": "Campaign Manager",
            },
        )
        workflow.add_conditional_edges(
            "ROI Risk Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Audience Fit Analyst": "Audience Fit Analyst",
                "Campaign Manager": "Campaign Manager",
            },
        )
        workflow.add_conditional_edges(
            "Audience Fit Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Brand Safety Analyst": "Brand Safety Analyst",
                "Campaign Manager": "Campaign Manager",
            },
        )

        workflow.add_edge("Campaign Manager", END)

        return workflow.compile()
