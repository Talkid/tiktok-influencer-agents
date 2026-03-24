import os
from pathlib import Path
import json
from typing import Dict, Any, List, Optional

from langgraph.prebuilt import ToolNode

from influenceragents.llm_clients import create_llm_client

from influenceragents.agents import *
from influenceragents.default_config import DEFAULT_CONFIG
from influenceragents.agents.utils.memory import InfluencerSituationMemory
from influenceragents.agents.utils.agent_states import (
    AgentState,
    SuitabilityDebateState,
    RiskDebateState,
)
from influenceragents.dataflows.config import set_config

from influenceragents.agents.utils.agent_utils import (
    get_profile_info,
    get_follower_growth,
    get_engagement_rates,
    get_video_performance_stats,
    get_recent_videos,
    analyze_video_thumbnails,
    get_content_categories,
    get_audience_demographics,
    detect_fake_followers,
    get_ecommerce_history,
    get_competitor_pricing,
    get_tiktok_shop_data,
)

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


class InfluencerAnalysisGraph:
    """Main class that orchestrates the influencer analysis framework."""

    def __init__(
        self,
        selected_analysts=["metrics", "content", "audience", "commerce"],
        debug=False,
        config: Dict[str, Any] = None,
        callbacks: Optional[List] = None,
    ):
        self.debug = debug
        self.config = config or DEFAULT_CONFIG.copy()
        self.callbacks = callbacks or []

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs
        llm_kwargs = self._get_provider_kwargs()
        if self.callbacks:
            llm_kwargs["callbacks"] = self.callbacks

        # Only OpenAI-compatible providers use backend_url; others (anthropic, google)
        # rely on their own env vars (ANTHROPIC_BASE_URL, etc.)
        _OPENAI_COMPAT = {"openai", "ollama", "openrouter", "xai"}
        provider = self.config["llm_provider"].lower()
        backend_url = self.config.get("backend_url") if provider in _OPENAI_COMPAT else None

        deep_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["deep_think_llm"],
            base_url=backend_url,
            **llm_kwargs,
        )
        quick_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["quick_think_llm"],
            base_url=backend_url,
            **llm_kwargs,
        )

        self.deep_thinking_llm = deep_client.get_llm()
        self.quick_thinking_llm = quick_client.get_llm()

        # Initialize memories
        self.advocate_memory = InfluencerSituationMemory("advocate_memory", self.config)
        self.skeptic_memory = InfluencerSituationMemory("skeptic_memory", self.config)
        self.strategist_memory = InfluencerSituationMemory("strategist_memory", self.config)
        self.evaluation_judge_memory = InfluencerSituationMemory("evaluation_judge_memory", self.config)
        self.campaign_manager_memory = InfluencerSituationMemory("campaign_manager_memory", self.config)

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=self.config["max_debate_rounds"],
            max_risk_discuss_rounds=self.config["max_risk_discuss_rounds"],
        )
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.advocate_memory,
            self.skeptic_memory,
            self.strategist_memory,
            self.evaluation_judge_memory,
            self.campaign_manager_memory,
            self.conditional_logic,
        )

        self.propagator = Propagator(self.config.get("max_recur_limit", 100))
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.username = None
        self.log_states_dict = {}

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _get_provider_kwargs(self) -> Dict[str, Any]:
        kwargs = {}
        provider = self.config.get("llm_provider", "").lower()

        if provider == "google":
            thinking_level = self.config.get("google_thinking_level")
            if thinking_level:
                kwargs["thinking_level"] = thinking_level
        elif provider == "openai":
            reasoning_effort = self.config.get("openai_reasoning_effort")
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort
        elif provider == "anthropic":
            effort = self.config.get("anthropic_effort")
            if effort:
                kwargs["effort"] = effort

        return kwargs

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        return {
            "metrics": ToolNode([get_profile_info, get_follower_growth, get_engagement_rates, get_video_performance_stats]),
            "content": ToolNode([get_recent_videos, analyze_video_thumbnails, get_content_categories]),
            "audience": ToolNode([get_audience_demographics, detect_fake_followers]),
            "commerce": ToolNode([get_ecommerce_history, get_competitor_pricing, get_tiktok_shop_data]),
        }

    def propagate(self, username: str, analysis_date: str = None, target_market: str = None):
        """Run the influencer analysis graph for a TikTok username.

        Args:
            username: TikTok username (without @)
            analysis_date: Date of analysis (defaults to today)
            target_market: Market code (defaults to config's target_market)

        Returns:
            Tuple of (final_state, processed_signal)
        """
        import datetime

        self.username = username
        if analysis_date is None:
            analysis_date = str(datetime.date.today())
        if target_market is None:
            target_market = self.config.get("target_market", "MY")

        # Initialize state
        init_state = self.propagator.create_initial_state(
            username, analysis_date, target_market
        )
        args = self.propagator.get_graph_args()

        if self.debug:
            trace = []
            for chunk in self.graph.stream(init_state, **args):
                if len(chunk["messages"]) == 0:
                    pass
                else:
                    try:
                        chunk["messages"][-1].pretty_print()
                    except UnicodeEncodeError:
                        content = chunk["messages"][-1].content
                        print(content.encode("utf-8", errors="replace").decode("utf-8"))
                    trace.append(chunk)
            final_state = trace[-1]
        else:
            final_state = self.graph.invoke(init_state, **args)

        self.curr_state = final_state
        self._log_state(analysis_date, final_state)

        return final_state, self.process_signal(final_state["final_assessment"])

    def _log_state(self, analysis_date, final_state):
        self.log_states_dict[str(analysis_date)] = {
            "influencer_username": final_state["influencer_username"],
            "analysis_date": final_state["analysis_date"],
            "target_market": final_state.get("target_market", "MY"),
            "metrics_report": final_state["metrics_report"],
            "content_report": final_state["content_report"],
            "audience_report": final_state["audience_report"],
            "commerce_report": final_state["commerce_report"],
            "suitability_debate_state": {
                "advocate_history": final_state["suitability_debate_state"]["advocate_history"],
                "skeptic_history": final_state["suitability_debate_state"]["skeptic_history"],
                "history": final_state["suitability_debate_state"]["history"],
                "judge_decision": final_state["suitability_debate_state"]["judge_decision"],
            },
            "strategist_partnership_plan": final_state["strategist_partnership_plan"],
            "risk_debate_state": {
                "brand_safety_history": final_state["risk_debate_state"]["brand_safety_history"],
                "roi_risk_history": final_state["risk_debate_state"]["roi_risk_history"],
                "audience_fit_history": final_state["risk_debate_state"]["audience_fit_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "evaluation_plan": final_state["evaluation_plan"],
            "final_assessment": final_state["final_assessment"],
        }

        directory = Path(f"results/{self.username}/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            directory / f"analysis_log_{analysis_date}.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4, ensure_ascii=False)

    def reflect_and_remember(self, campaign_results):
        """Reflect on decisions and update memory based on campaign results."""
        self.reflector.reflect_advocate(self.curr_state, campaign_results, self.advocate_memory)
        self.reflector.reflect_skeptic(self.curr_state, campaign_results, self.skeptic_memory)
        self.reflector.reflect_strategist(self.curr_state, campaign_results, self.strategist_memory)
        self.reflector.reflect_evaluation_judge(self.curr_state, campaign_results, self.evaluation_judge_memory)
        self.reflector.reflect_campaign_manager(self.curr_state, campaign_results, self.campaign_manager_memory)

    def process_signal(self, full_signal):
        return self.signal_processor.process_signal(full_signal)
