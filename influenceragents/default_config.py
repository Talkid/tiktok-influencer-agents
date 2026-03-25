import os

# Market-specific commission tiers and configuration
MARKET_CONFIGS = {
    "MY": {
        "currency": "MYR",
        "currency_symbol": "RM",
        "languages": ["ms", "zh", "en"],
        "commission_tiers": {
            "T0": {"min": 600, "label": "600+ RM"},
            "T1": {"min": 400, "max": 500, "label": "400-500 RM"},
            "T2": {"min": 200, "max": 350, "label": "200-350 RM"},
            "T3": {"min": 50, "max": 150, "label": "50-150 RM"},
        },
    },
    "PH": {
        "currency": "PHP",
        "currency_symbol": "₱",
        "languages": ["tl", "en"],
        "commission_tiers": {
            "T0": {"min": 8000, "label": "8000+ PHP"},
            "T1": {"min": 5000, "max": 7000, "label": "5000-7000 PHP"},
            "T2": {"min": 2500, "max": 4500, "label": "2500-4500 PHP"},
            "T3": {"min": 500, "max": 2000, "label": "500-2000 PHP"},
        },
    },
    "VN": {
        "currency": "VND",
        "currency_symbol": "₫",
        "languages": ["vi"],
        "commission_tiers": {
            "T0": {"min": 3500000, "label": "3,500,000+ VND"},
            "T1": {"min": 2000000, "max": 3000000, "label": "2,000,000-3,000,000 VND"},
            "T2": {"min": 1000000, "max": 1800000, "label": "1,000,000-1,800,000 VND"},
            "T3": {"min": 250000, "max": 800000, "label": "250,000-800,000 VND"},
        },
    },
    "BR": {
        "currency": "BRL",
        "currency_symbol": "R$",
        "languages": ["pt"],
        "commission_tiers": {
            "T0": {"min": 1500, "label": "1500+ BRL"},
            "T1": {"min": 1000, "max": 1400, "label": "1000-1400 BRL"},
            "T2": {"min": 500, "max": 900, "label": "500-900 BRL"},
            "T3": {"min": 100, "max": 400, "label": "100-400 BRL"},
        },
    },
}

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("INFLUENCER_RESULTS_DIR", "./results"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "gpt-4o",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "https://api.openai.com/v1",
    # Vision model settings (for thumbnail/video analysis)
    "vision_llm_provider": "anthropic",
    "vision_llm_model": "claude-sonnet-4-20250514",
    # Provider-specific thinking configuration
    "google_thinking_level": None,
    "openai_reasoning_effort": None,
    "anthropic_effort": None,
    # Debate and discussion settings
    "max_debate_rounds": 3,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Data vendor configuration
    "data_vendors": {
        "profile_data": "apify",
        "content_data": "apify",
        "audience_data": "apify",
        "commerce_data": "apify",
        "vision_analysis": "claude_vision",
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {},
    # Market configuration
    "target_market": "MY",
}
