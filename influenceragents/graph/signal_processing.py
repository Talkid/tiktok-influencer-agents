class SignalProcessor:
    """Processes influencer assessment signals to extract tier and commission ratings."""

    def __init__(self, quick_thinking_llm):
        self.quick_thinking_llm = quick_thinking_llm

    def process_signal(self, full_signal: str) -> dict:
        """Extract tier rating and commission tier from the full assessment.

        Returns:
            dict with 'tier' (S/A/B/C/D) and 'commission_tier' (T0/T1/T2/T3)
        """
        tier_messages = [
            (
                "system",
                "You are an assistant that extracts the influencer tier rating from assessment reports. "
                "Extract exactly one of: S, A, B, C, D. Output only the single letter, nothing else.",
            ),
            ("human", full_signal),
        ]

        commission_messages = [
            (
                "system",
                "You are an assistant that extracts the commission tier from assessment reports. "
                "Extract exactly one of: T0, T1, T2, T3. Output only the tier code, nothing else.",
            ),
            ("human", full_signal),
        ]

        tier = self.quick_thinking_llm.invoke(tier_messages).content.strip()
        commission = self.quick_thinking_llm.invoke(commission_messages).content.strip()

        return {
            "tier": tier,
            "commission_tier": commission,
        }
