"""CLI entry point for the TikTok Influencer Analysis System."""

from dotenv import load_dotenv
load_dotenv()

import typer
from rich.console import Console

app = typer.Typer(
    name="influenceragents",
    help="TikTok Influencer Analysis: Multi-Agent Framework for Creator Evaluation",
)
console = Console()


@app.command()
def analyze(
    username: str = typer.Argument(..., help="TikTok username to analyze"),
    market: str = typer.Option("MY", help="Target market code (MY, PH, VN, BR)"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
    provider: str = typer.Option("openai", help="LLM provider"),
    debate_rounds: int = typer.Option(1, help="Number of debate rounds"),
):
    """Analyze a TikTok influencer and generate an assessment report."""
    from influenceragents.graph.analysis_graph import InfluencerAnalysisGraph
    from influenceragents.default_config import DEFAULT_CONFIG, MARKET_CONFIGS
    import datetime

    _PROVIDER_DEFAULT_MODELS = {
        "anthropic": ("claude-sonnet-4-6", "claude-haiku-4-5-20251001"),
        "google":    ("gemini-2.5-pro",    "gemini-2.5-flash"),
        "xai":       ("grok-4-0709",       "grok-4-fast-non-reasoning"),
        "openai":    ("gpt-4o",            "gpt-4o-mini"),
    }

    config = DEFAULT_CONFIG.copy()
    config["target_market"] = market
    config["llm_provider"] = provider
    deep, quick = _PROVIDER_DEFAULT_MODELS.get(provider, ("gpt-4o", "gpt-4o-mini"))
    config["deep_think_llm"] = deep
    config["quick_think_llm"] = quick
    config["max_debate_rounds"] = debate_rounds
    config["max_risk_discuss_rounds"] = debate_rounds

    market_config = MARKET_CONFIGS.get(market, MARKET_CONFIGS["MY"])

    console.print(f"\n[bold]TikTok Influencer Analysis System[/bold]")
    console.print(f"  Username:  @{username}")
    console.print(f"  Market:    {market} ({market_config['currency']})")
    console.print(f"  Provider:  {config['llm_provider']}")
    console.print()

    graph = InfluencerAnalysisGraph(debug=debug, config=config)
    analysis_date = str(datetime.date.today())
    final_state, signal = graph.propagate(username, analysis_date, market)

    console.print(f"\n[bold green]ANALYSIS COMPLETE[/bold green]")
    console.print(f"  Tier Rating:     [bold]{signal['tier']}[/bold]")
    console.print(f"  Commission Tier: [bold]{signal['commission_tier']}[/bold]")
    console.print()
    console.print(final_state["final_assessment"])


if __name__ == "__main__":
    app()
