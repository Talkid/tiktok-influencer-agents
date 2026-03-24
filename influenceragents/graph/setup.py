from typing import Dict, Any
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from influenceragents.agents import *
from influenceragents.agents.utils.agent_states import AgentState

from .conditional_logic import ConditionalLogic


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm,
        deep_thinking_llm,
        tool_nodes: Dict[str, ToolNode],
        advocate_memory,
        skeptic_memory,
        strategist_memory,
        evaluation_judge_memory,
        campaign_manager_memory,
        conditional_logic: ConditionalLogic,
    ):
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.advocate_memory = advocate_memory
        self.skeptic_memory = skeptic_memory
        self.strategist_memory = strategist_memory
        self.evaluation_judge_memory = evaluation_judge_memory
        self.campaign_manager_memory = campaign_manager_memory
        self.conditional_logic = conditional_logic

    def setup_graph(
        self, selected_analysts=["metrics", "content", "audience", "commerce"]
    ):
        if len(selected_analysts) == 0:
            raise ValueError("Influencer Agents Graph Setup Error: no analysts selected!")

        # Create analyst nodes
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        if "metrics" in selected_analysts:
            analyst_nodes["metrics"] = create_metrics_analyst(self.quick_thinking_llm)
            delete_nodes["metrics"] = create_msg_delete()
            tool_nodes["metrics"] = self.tool_nodes["metrics"]

        if "content" in selected_analysts:
            analyst_nodes["content"] = create_content_analyst(self.quick_thinking_llm)
            delete_nodes["content"] = create_msg_delete()
            tool_nodes["content"] = self.tool_nodes["content"]

        if "audience" in selected_analysts:
            analyst_nodes["audience"] = create_audience_analyst(self.quick_thinking_llm)
            delete_nodes["audience"] = create_msg_delete()
            tool_nodes["audience"] = self.tool_nodes["audience"]

        if "commerce" in selected_analysts:
            analyst_nodes["commerce"] = create_commerce_analyst(self.quick_thinking_llm)
            delete_nodes["commerce"] = create_msg_delete()
            tool_nodes["commerce"] = self.tool_nodes["commerce"]

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

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(f"{analyst_type.capitalize()} Analyst", node)
            workflow.add_node(
                f"Msg Clear {analyst_type.capitalize()}", delete_nodes[analyst_type]
            )
            workflow.add_node(f"tools_{analyst_type}", tool_nodes[analyst_type])

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
        first_analyst = selected_analysts[0]
        workflow.add_edge(START, f"{first_analyst.capitalize()} Analyst")

        # Connect analysts in sequence
        for i, analyst_type in enumerate(selected_analysts):
            current_analyst = f"{analyst_type.capitalize()} Analyst"
            current_tools = f"tools_{analyst_type}"
            current_clear = f"Msg Clear {analyst_type.capitalize()}"

            workflow.add_conditional_edges(
                current_analyst,
                getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current_analyst)

            if i < len(selected_analysts) - 1:
                next_analyst = f"{selected_analysts[i+1].capitalize()} Analyst"
                workflow.add_edge(current_clear, next_analyst)
            else:
                workflow.add_edge(current_clear, "Advocate Researcher")

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
