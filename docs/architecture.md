# 系统架构设计

## 1. 架构概述

本系统是一套基于 **LangGraph** 的多 Agent 辩论式 TikTok 达人分析系统。核心思想是通过多个专业化 Agent 的协作与辩论，产生比单一 Agent 更全面、更可靠的分析结果。

### 设计原则

- **辩论驱动决策**: 不依赖单一 Agent 的判断，通过正反方辩论产生更平衡的结论
- **多市场可配置**: 通过配置切换市场（马来西亚/菲律宾/越南/巴西），无需改代码
- **数据源可插拔**: 通过 vendor 路由机制，可随时替换或新增数据源
- **记忆与学习**: BM25 记忆系统让 Agent 从历史决策中学习

## 2. 分层架构

```
┌─────────────────────────────────────────────────┐
│                  入口层 (Entry)                   │
│  main.py / cli/main.py                          │
│  解析参数 → 初始化配置 → 调用 Graph              │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              图编排层 (Graph Layer)               │
│  analysis_graph.py — 主协调器                    │
│  setup.py — StateGraph 构建                      │
│  conditional_logic.py — 条件路由                  │
│  propagation.py — 初始状态                       │
│  signal_processing.py — 提取评级                  │
│  reflection.py — 反思学习                        │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              Agent 层 (Agent Layer)              │
│                                                  │
│  analysts/     4 个数据分析师 (带工具调用)         │
│  researchers/  Advocate + Skeptic 辩论           │
│  managers/     Evaluation Manager + Campaign Mgr │
│  strategist/   Partnership Strategist            │
│  risk_mgmt/    Brand Safety + ROI + Audience Fit │
│                                                  │
│  utils/        状态定义 / BM25 记忆 / 工具封装    │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              数据层 (Dataflow Layer)              │
│  interface.py — vendor 路由 (route_to_vendor)    │
│  apify_tiktok.py — Apify TikTok 数据获取         │
│  vision_analysis.py — Claude Vision 视觉分析     │
│  config.py — 运行时配置管理                      │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              LLM 客户端层 (LLM Layer)             │
│  factory.py — 统一工厂 create_llm_client()       │
│  openai_client.py / anthropic_client.py /        │
│  google_client.py — 提供商适配器                  │
│  base_client.py — 抽象基类 + 内容归一化           │
└─────────────────────────────────────────────────┘
```

## 3. LangGraph 节点与边

### 节点清单 (共 21 个)

| 节点名 | 类型 | 文件 | 说明 |
|--------|------|------|------|
| `Metrics Analyst` | 分析师 | `analysts/metrics_analyst.py` | 数据指标分析 |
| `tools_metrics` | ToolNode | 自动生成 | Metrics 工具执行 |
| `Msg Clear Metrics` | 辅助 | `agent_utils.py` | 清理消息 |
| `Content Analyst` | 分析师 | `analysts/content_analyst.py` | 内容+视觉分析 |
| `tools_content` | ToolNode | 自动生成 | Content 工具执行 |
| `Msg Clear Content` | 辅助 | `agent_utils.py` | 清理消息 |
| `Audience Analyst` | 分析师 | `analysts/audience_analyst.py` | 受众分析 |
| `tools_audience` | ToolNode | 自动生成 | Audience 工具执行 |
| `Msg Clear Audience` | 辅助 | `agent_utils.py` | 清理消息 |
| `Commerce Analyst` | 分析师 | `analysts/commerce_analyst.py` | 电商分析 |
| `tools_commerce` | ToolNode | 自动生成 | Commerce 工具执行 |
| `Msg Clear Commerce` | 辅助 | `agent_utils.py` | 清理消息 |
| `Advocate Researcher` | 研究员 | `researchers/advocate_researcher.py` | 推荐方辩论 |
| `Skeptic Researcher` | 研究员 | `researchers/skeptic_researcher.py` | 质疑方辩论 |
| `Evaluation Manager` | 经理 | `managers/evaluation_manager.py` | 综合辩论结果 |
| `Partnership Strategist` | 策略师 | `strategist/partnership_strategist.py` | 合作方案+佣金 |
| `Brand Safety Analyst` | 风控 | `risk_mgmt/brand_safety_debator.py` | 品牌安全 |
| `ROI Risk Analyst` | 风控 | `risk_mgmt/roi_risk_debator.py` | 投入回报 |
| `Audience Fit Analyst` | 风控 | `risk_mgmt/audience_fit_debator.py` | 受众匹配 |
| `Campaign Manager` | 最终决策 | `managers/campaign_manager.py` | 最终评级报告 |

### 边的连接逻辑

```
START
  → Metrics Analyst ←→ tools_metrics (循环至无工具调用)
  → Msg Clear Metrics
  → Content Analyst ←→ tools_content
  → Msg Clear Content
  → Audience Analyst ←→ tools_audience
  → Msg Clear Audience
  → Commerce Analyst ←→ tools_commerce
  → Msg Clear Commerce
  → Advocate Researcher
     ←→ Skeptic Researcher (count < 2 * max_debate_rounds)
  → Evaluation Manager
  → Partnership Strategist
  → Brand Safety Analyst
     → ROI Risk Analyst
     → Audience Fit Analyst
     (循环: count < 3 * max_risk_discuss_rounds)
  → Campaign Manager
  → END
```

### 条件路由规则

| 方法 | 条件 | 下一节点 |
|------|------|---------|
| `should_continue_[analyst]` | `last_message.tool_calls` 存在 | `tools_[analyst]` |
| `should_continue_[analyst]` | 无工具调用 | `Msg Clear [Analyst]` |
| `should_continue_debate` | `count >= 2 * max_rounds` | `Evaluation Manager` |
| `should_continue_debate` | 最后发言者是 Advocate | `Skeptic Researcher` |
| `should_continue_debate` | 最后发言者是 Skeptic | `Advocate Researcher` |
| `should_continue_risk_analysis` | `count >= 3 * max_rounds` | `Campaign Manager` |
| `should_continue_risk_analysis` | Brand Safety 发言后 | `ROI Risk Analyst` |
| `should_continue_risk_analysis` | ROI Risk 发言后 | `Audience Fit Analyst` |
| `should_continue_risk_analysis` | Audience Fit 发言后 | `Brand Safety Analyst` |

## 4. 状态管理 (State)

### AgentState (主状态)

```python
class AgentState(MessagesState):
    influencer_username: str   # TikTok 用户名
    analysis_date: str         # 分析日期
    target_market: str         # 目标市场 (MY/PH/VN/BR)
    sender: str                # 当前发言 Agent

    # 4 份分析师报告
    metrics_report: str
    content_report: str
    audience_report: str
    commerce_report: str

    # 适配度辩论
    suitability_debate_state: SuitabilityDebateState
    evaluation_plan: str

    # 合作策略
    strategist_partnership_plan: str

    # 风控辩论
    risk_debate_state: RiskDebateState
    final_assessment: str      # 最终报告
```

### SuitabilityDebateState

```python
class SuitabilityDebateState(TypedDict):
    advocate_history: str      # 推荐方历史
    skeptic_history: str       # 质疑方历史
    history: str               # 完整辩论历史
    current_response: str      # 最新回复
    judge_decision: str        # 评估经理决定
    count: int                 # 辩论轮次计数
```

### RiskDebateState

```python
class RiskDebateState(TypedDict):
    brand_safety_history: str
    roi_risk_history: str
    audience_fit_history: str
    history: str
    latest_speaker: str
    current_brand_safety_response: str
    current_roi_risk_response: str
    current_audience_fit_response: str
    judge_decision: str
    count: int
```

## 5. 记忆系统

### BM25 记忆架构

每个需要从历史中学习的 Agent 拥有独立的记忆实例：

| 记忆实例 | 对应 Agent | 存储内容 |
|----------|-----------|---------|
| `advocate_memory` | Advocate Researcher | 过去推荐方的论点和反思 |
| `skeptic_memory` | Skeptic Researcher | 过去质疑方的论点和反思 |
| `strategist_memory` | Partnership Strategist | 过去的合作方案和效果 |
| `evaluation_judge_memory` | Evaluation Manager | 过去的评估决策和反思 |
| `campaign_manager_memory` | Campaign Manager | 过去的最终评级和反思 |

### 记忆流程

```
分析完成 → 活动执行 → 获取实际效果 → reflect_and_remember()
    ↓
反思 Agent 分析正确/错误决策 → 生成反思总结 → 存入 BM25 索引
    ↓
下次分析 → Agent 查询相似情境 → 获取 top-2 历史反思 → 融入 Prompt
```

## 6. 配置系统

### 配置层次 (优先级从高到低)

1. **tool_vendors** — 工具级别覆盖
2. **data_vendors** — 类别级别默认
3. **DEFAULT_CONFIG** — 全局默认

### 关键配置项

```python
DEFAULT_CONFIG = {
    # LLM
    "llm_provider": "openai",
    "deep_think_llm": "gpt-4o",          # 复杂推理 (辩论综合、最终决策)
    "quick_think_llm": "gpt-4o-mini",    # 快速任务 (分析师、数据处理)
    "vision_llm_provider": "anthropic",   # 视觉分析提供商
    "vision_llm_model": "claude-sonnet-4-20250514",

    # 辩论轮次
    "max_debate_rounds": 1,               # Advocate/Skeptic 辩论轮数
    "max_risk_discuss_rounds": 1,         # 风控三方辩论轮数

    # 数据源
    "data_vendors": {
        "profile_data": "apify",
        "content_data": "apify",
        "audience_data": "apify",
        "commerce_data": "apify",
        "vision_analysis": "claude_vision",
    },

    # 市场
    "target_market": "MY",
}
```

## 7. 输出结构

### 最终报告格式

```
=== INFLUENCER ASSESSMENT REPORT ===

1. TIER RATING: [S / A / B / C / D]
2. COMMISSION TIER: [T0 / T1 / T2 / T3] — 建议报价
3. VERDICT: [Highly Recommended / ... / Avoid]
4. PROFILE SUMMARY
5. INFLUENCER TAGS
6. E-COMMERCE POTENTIAL
7. COLLABORATION RECOMMENDATION
8. RISK ASSESSMENT
9. EXECUTIVE SUMMARY
```

### 输出文件

- `results/<username>/analysis_log_<date>.json` — 完整状态日志
- `results/<username>/report_<date>.md` — Markdown 报告
