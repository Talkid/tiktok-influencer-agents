# 多市场配置指南

## 1. 配置结构

市场配置定义在 `influenceragents/default_config.py` 的 `MARKET_CONFIGS` 字典中。

```python
MARKET_CONFIGS = {
    "MY": {
        "currency": "MYR",
        "currency_symbol": "RM",
        "languages": ["ms", "zh", "en"],
        "commission_tiers": {
            "T0": {"min": 1000, "label": "600+ RM"},
            "T1": {"min": 500, "max": 1000, "label": "400-500 RM"},
            "T2": {"min": 100, "max": 500, "label": "200-350 RM"},
            "T3": {"min": 50, "max": 100, "label": "50-150 RM"},
        },
    },
    # ... 其他市场
}
```

## 2. 已支持市场

| 市场代码 | 国家 | 货币 | 语言 | 状态 |
|----------|------|------|------|------|
| **MY** | 马来西亚 | MYR (RM) | 马来语、中文、英语 | 首发市场 |
| **PH** | 菲律宾 | PHP (₱) | 他加禄语、英语 | 预配置 |
| **VN** | 越南 | VND (₫) | 越南语 | 预配置 |
| **BR** | 巴西 | BRL (R$) | 葡萄牙语 | 预配置 |

## 3. 市场配置如何影响系统

### 3.1 Agent Prompt 中的市场上下文

`build_influencer_context()` 会将市场信息注入到所有 Agent 的 Prompt 中：

```python
"The TikTok influencer to analyze is @{username}. Target market: MY."
```

### 3.2 佣金等级判定

Partnership Strategist 和 Campaign Manager 会读取当前市场的佣金配置：

```python
from influenceragents.default_config import MARKET_CONFIGS
market_config = MARKET_CONFIGS[state["target_market"]]
tiers = market_config["commission_tiers"]
```

### 3.3 定价估算

Commerce Analyst 的 `get_competitor_pricing` 工具根据市场配置返回对应货币的报价：

```
Pricing Estimation for @xxx (50,000 followers):
Estimated Tier: T2
Market Rate Range: 200-350 RM
Market: MY
```

### 3.4 语言分析

Content Analyst 在分析内容语言时参考市场的主要语言列表。

## 4. 切换市场

### 命令行

```bash
python main.py username --market PH  # 切换到菲律宾市场
```

### API 调用

```python
from influenceragents.graph.analysis_graph import InfluencerAnalysisGraph
from influenceragents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["target_market"] = "VN"  # 切换到越南市场

graph = InfluencerAnalysisGraph(config=config)
state, signal = graph.propagate("username", target_market="VN")
```

## 5. 新增市场

### 步骤

1. 在 `MARKET_CONFIGS` 中添加新市场配置：

```python
"TH": {  # 泰国
    "currency": "THB",
    "currency_symbol": "฿",
    "languages": ["th", "en"],
    "commission_tiers": {
        "T0": {"min": 10000, "label": "10,000+ THB"},
        "T1": {"min": 6000, "max": 9000, "label": "6,000-9,000 THB"},
        "T2": {"min": 3000, "max": 5500, "label": "3,000-5,500 THB"},
        "T3": {"min": 500, "max": 2500, "label": "500-2,500 THB"},
    },
},
```

2. 如有需要，在 CLI 的 `--market` choices 中添加新选项

3. 如需特殊的带货检测关键词，在 `apify_tiktok.py` 的 `ad_keywords` 中添加当地语言标签

### 佣金定价参考

为新市场设定佣金时，建议：

- 参考当地 KOL 平台的市场报价
- T0 对标当地头部达人的平均报价
- T3 设为当地最低合理合作价
- T1/T2 在两端之间均匀分布
