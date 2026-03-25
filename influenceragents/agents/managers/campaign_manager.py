from influenceragents.agents.utils.agent_utils import build_influencer_context


def create_campaign_manager(llm, memory):
    def campaign_manager_node(state) -> dict:
        username = state["influencer_username"]
        market = state.get("target_market", "MY")
        influencer_context = build_influencer_context(username, market)

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        metrics_report = state["metrics_report"]
        content_report = state["content_report"]
        audience_report = state["audience_report"]
        commerce_report = state["commerce_report"]
        strategist_plan = state["evaluation_plan"]

        curr_situation = f"{metrics_report}\n\n{content_report}\n\n{audience_report}\n\n{commerce_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for rec in past_memories:
            past_memory_str += rec["recommendation"] + "\n\n"

        from influenceragents.default_config import MARKET_CONFIGS
        market_config = MARKET_CONFIGS.get(market, MARKET_CONFIGS["MY"])
        tiers = market_config["commission_tiers"]
        symbol = market_config["currency_symbol"]

        tier_table = "\n".join([f"  {k}: {v['label']}" for k, v in tiers.items()])

        prompt = f"""As the Campaign Manager, synthesize the risk analysts' debate and deliver the FINAL influencer assessment.

{influencer_context}

---

**Influencer Rating Scale** (use exactly one):
- **S** (Elite): Top-tier influencer, strongly recommend partnership
- **A** (Strong): High-quality influencer, prioritize for campaigns
- **B** (Viable): Decent influencer, suitable for test campaigns
- **C** (Caution): Below-average value, proceed only with significant negotiation
- **D** (Avoid): Not recommended for partnership

**Commission Tier Scale** ({symbol}):
{tier_table}

**Context:**
- Partnership Strategist's proposal: **{strategist_plan}**
- Lessons from past decisions: **{past_memory_str}**

**Required Output Structure:**

=== INFLUENCER ASSESSMENT REPORT ===

1. TIER RATING: [S / A / B / C / D]
2. COMMISSION TIER: [T0 / T1 / T2 / T3] — Suggested price: XXX {symbol}/video
3. VERDICT: [Highly Recommended / Recommended / Conditional / Not Recommended / Avoid]

4. PROFILE SUMMARY
   - Username, Followers, Avg Engagement Rate
   - Content Language, Authenticity Score (1-10)
   - Market: {market}

5. INFLUENCER TAGS
   - Age range, Gender, Content niche
   - Target audience type, Lifestyle tags
   - Primary language

6. E-COMMERCE POTENTIAL
   - History, Conversion ability, Suitable categories, Match score

7. COLLABORATION RECOMMENDATION
   - Format (single/multi video), Video count
   - Content direction, Commission tier rationale

8. RISK ASSESSMENT
   - Brand Safety, Audience Authenticity, ROI Confidence

9. EXECUTIVE SUMMARY
   (2-3 paragraphs grounded in the debate evidence)

---

**Risk Analysts Debate History:**
{history}

---

Be decisive and ground every conclusion in specific evidence from the analysts.

IMPORTANT: Write your entire response in Chinese (Simplified). All section headers, analysis, and summaries must be in Chinese."""

        response = llm.invoke(prompt)

        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state["history"],
            "brand_safety_history": risk_debate_state["brand_safety_history"],
            "roi_risk_history": risk_debate_state["roi_risk_history"],
            "audience_fit_history": risk_debate_state["audience_fit_history"],
            "latest_speaker": "Judge",
            "current_brand_safety_response": risk_debate_state["current_brand_safety_response"],
            "current_roi_risk_response": risk_debate_state["current_roi_risk_response"],
            "current_audience_fit_response": risk_debate_state["current_audience_fit_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_assessment": response.content,
        }

    return campaign_manager_node
