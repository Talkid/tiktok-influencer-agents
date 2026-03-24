from typing import Dict, Any


class Reflector:
    """Handles reflection on decisions and updating memory."""

    def __init__(self, quick_thinking_llm):
        self.quick_thinking_llm = quick_thinking_llm
        self.reflection_system_prompt = self._get_reflection_prompt()

    def _get_reflection_prompt(self) -> str:
        return """You are an expert influencer marketing analyst tasked with reviewing partnership decisions and providing comprehensive analysis.
Your goal is to deliver detailed insights into influencer evaluation decisions and highlight opportunities for improvement:

1. Reasoning:
   - Determine whether the partnership recommendation was correct based on campaign performance.
   - Analyze contributing factors: metrics accuracy, content analysis quality, audience assessment, commerce evaluation.
   - Weight the importance of each factor in the decision-making process.

2. Improvement:
   - For incorrect recommendations, propose revisions.
   - Provide corrective actions: better metric thresholds, content analysis improvements, audience authenticity detection.

3. Summary:
   - Summarize lessons learned from successes and mistakes.
   - Highlight how these lessons apply to future influencer evaluations.

4. Query:
   - Extract key insights into a concise sentence of no more than 1000 tokens."""

    def _extract_current_situation(self, current_state: Dict[str, Any]) -> str:
        return (
            f"{current_state['metrics_report']}\n\n"
            f"{current_state['content_report']}\n\n"
            f"{current_state['audience_report']}\n\n"
            f"{current_state['commerce_report']}"
        )

    def _reflect_on_component(self, component_type: str, report: str, situation: str, campaign_results) -> str:
        messages = [
            ("system", self.reflection_system_prompt),
            (
                "human",
                f"Campaign Results: {campaign_results}\n\nAnalysis/Decision: {report}\n\nInfluencer Reports: {situation}",
            ),
        ]
        return self.quick_thinking_llm.invoke(messages).content

    def reflect_advocate(self, current_state, campaign_results, advocate_memory):
        situation = self._extract_current_situation(current_state)
        debate_history = current_state["suitability_debate_state"]["advocate_history"]
        result = self._reflect_on_component("ADVOCATE", debate_history, situation, campaign_results)
        advocate_memory.add_situations([(situation, result)])

    def reflect_skeptic(self, current_state, campaign_results, skeptic_memory):
        situation = self._extract_current_situation(current_state)
        debate_history = current_state["suitability_debate_state"]["skeptic_history"]
        result = self._reflect_on_component("SKEPTIC", debate_history, situation, campaign_results)
        skeptic_memory.add_situations([(situation, result)])

    def reflect_strategist(self, current_state, campaign_results, strategist_memory):
        situation = self._extract_current_situation(current_state)
        strategist_plan = current_state["strategist_partnership_plan"]
        result = self._reflect_on_component("STRATEGIST", strategist_plan, situation, campaign_results)
        strategist_memory.add_situations([(situation, result)])

    def reflect_evaluation_judge(self, current_state, campaign_results, judge_memory):
        situation = self._extract_current_situation(current_state)
        judge_decision = current_state["suitability_debate_state"]["judge_decision"]
        result = self._reflect_on_component("EVALUATION JUDGE", judge_decision, situation, campaign_results)
        judge_memory.add_situations([(situation, result)])

    def reflect_campaign_manager(self, current_state, campaign_results, campaign_memory):
        situation = self._extract_current_situation(current_state)
        judge_decision = current_state["risk_debate_state"]["judge_decision"]
        result = self._reflect_on_component("CAMPAIGN MANAGER", judge_decision, situation, campaign_results)
        campaign_memory.add_situations([(situation, result)])
