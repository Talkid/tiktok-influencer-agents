"""TikTok Influencer Analysis System - Entry Point

Usage:
    python main.py <username> [--market MY] [--debug]

Example:
    python main.py khaborney --market MY --debug
"""

import argparse
import datetime
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from influenceragents.graph.analysis_graph import InfluencerAnalysisGraph
from influenceragents.default_config import DEFAULT_CONFIG, MARKET_CONFIGS


def main():
    parser = argparse.ArgumentParser(
        description="TikTok Influencer Analysis System"
    )
    parser.add_argument(
        "username",
        type=str,
        help="TikTok username to analyze (without @)",
    )
    parser.add_argument(
        "--market",
        type=str,
        default="MY",
        choices=list(MARKET_CONFIGS.keys()),
        help="Target market (default: MY)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with streaming output",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="LLM provider (openai, anthropic, google)",
    )
    parser.add_argument(
        "--deep-model",
        type=str,
        default=None,
        help="Model for complex reasoning",
    )
    parser.add_argument(
        "--quick-model",
        type=str,
        default=None,
        help="Model for quick tasks",
    )
    parser.add_argument(
        "--debate-rounds",
        type=int,
        default=1,
        help="Number of debate rounds (default: 1)",
    )

    args = parser.parse_args()

    # Default models per provider (used when --provider is set without explicit model args)
    _PROVIDER_DEFAULT_MODELS = {
        "anthropic": ("claude-sonnet-4-6", "claude-haiku-4-5-20251001"),
        "google":    ("gemini-2.5-pro",    "gemini-2.5-flash"),
        "xai":       ("grok-4-0709",       "grok-4-fast-non-reasoning"),
        "openai":    ("gpt-4o",            "gpt-4o-mini"),
    }

    # Build config
    config = DEFAULT_CONFIG.copy()
    config["target_market"] = args.market

    if args.provider:
        config["llm_provider"] = args.provider
        # Auto-set matching default models when provider changes (unless overridden)
        if not args.deep_model and not args.quick_model:
            deep, quick = _PROVIDER_DEFAULT_MODELS.get(args.provider, ("gpt-4o", "gpt-4o-mini"))
            config["deep_think_llm"] = deep
            config["quick_think_llm"] = quick
    if args.deep_model:
        config["deep_think_llm"] = args.deep_model
    if args.quick_model:
        config["quick_think_llm"] = args.quick_model
    config["max_debate_rounds"] = args.debate_rounds
    config["max_risk_discuss_rounds"] = args.debate_rounds

    print(f"\n{'='*60}")
    print(f"  TikTok Influencer Analysis System")
    print(f"{'='*60}")
    print(f"  Username:  @{args.username}")
    print(f"  Market:    {args.market} ({MARKET_CONFIGS[args.market]['currency']})")
    print(f"  Provider:  {config['llm_provider']}")
    print(f"  Models:    {config['deep_think_llm']} / {config['quick_think_llm']}")
    print(f"  Rounds:    {args.debate_rounds}")
    print(f"{'='*60}\n")

    # Create and run the graph
    graph = InfluencerAnalysisGraph(
        debug=args.debug,
        config=config,
    )

    analysis_date = str(datetime.date.today())
    final_state, signal = graph.propagate(
        args.username,
        analysis_date=analysis_date,
        target_market=args.market,
    )

    # Output results
    print(f"\n{'='*60}")
    print(f"  ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"  Tier Rating:     {signal['tier']}")
    print(f"  Commission Tier: {signal['commission_tier']}")
    print(f"{'='*60}\n")
    print(final_state["final_assessment"])

    # Save report
    report_dir = Path(f"results/{args.username}/")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"report_{analysis_date}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_state["final_assessment"])
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
