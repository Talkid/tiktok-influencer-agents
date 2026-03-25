"""Parallel analyst runner — runs all selected analyst nodes concurrently."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.messages import HumanMessage

from .metrics_analyst import create_metrics_analyst
from .content_analyst import create_content_analyst
from .audience_analyst import create_audience_analyst
from .commerce_analyst import create_commerce_analyst

_ANALYST_FACTORIES = {
    "metrics": create_metrics_analyst,
    "content": create_content_analyst,
    "audience": create_audience_analyst,
    "commerce": create_commerce_analyst,
}

_ANALYST_LABELS = {
    "metrics": "指标分析师",
    "content": "内容分析师",
    "audience": "受众分析师",
    "commerce": "电商分析师",
}


def create_parallel_analysts(llm, selected_analysts, debug=False):
    """Return a single LangGraph node that runs all selected analysts in parallel."""
    analyst_nodes = {
        name: _ANALYST_FACTORIES[name](llm)
        for name in selected_analysts
        if name in _ANALYST_FACTORIES
    }

    def parallel_analysts_node(state):
        username = state.get("influencer_username", "")
        print(f"\n[并行分析] 开始同时运行 {len(analyst_nodes)} 个分析师 (@{username})...")

        future_to_name = {}
        with ThreadPoolExecutor(max_workers=len(analyst_nodes)) as executor:
            for name, fn in analyst_nodes.items():
                future = executor.submit(fn, state)
                future_to_name[future] = name

            results = {}
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                label = _ANALYST_LABELS.get(name, name)
                try:
                    results[name] = future.result()
                    report = results[name].get(f"{name}_report", "")
                    print(f"  [完成] {label}")
                    if debug and report:
                        sep = "=" * 60
                        print(f"\n{sep}")
                        print(f"  {label} 报告")
                        print(sep)
                        print(report)
                        print(f"{sep}\n")
                except Exception as e:
                    results[name] = {f"{name}_report": f"分析失败: {e}"}
                    print(f"  [失败] {label}: {e}")

        print("[并行分析] 全部分析师完成，进入辩论阶段\n")

        return {
            "metrics_report": results.get("metrics", {}).get("metrics_report", ""),
            "content_report": results.get("content", {}).get("content_report", ""),
            "audience_report": results.get("audience", {}).get("audience_report", ""),
            "commerce_report": results.get("commerce", {}).get("commerce_report", ""),
            "messages": [HumanMessage(content="Continue")],
        }

    return parallel_analysts_node
