# TikTok Influencer Analysis System — 项目索引

基于 **LangGraph** 的多 Agent 辩论式 TikTok 达人分析系统。13 个专业 Agent 协作分析达人数据，通过正反辩论产出等级评定 (S-D) 和佣金建议 (T0-T3)。

---

## 文档导航

| 文档 | 说明 |
|------|------|
| [架构总览](docs/architecture.md) | 分层架构、21 节点 LangGraph、状态管理、记忆系统、配置体系 |
| [Agent 设计](docs/agent-design.md) | 13 个 Agent 的职责、工具、Prompt 策略、工厂模式 |
| [数据层设计](docs/dataflow-design.md) | vendor 路由、Apify 数据采集、Vision 分析管线、缓存机制 |
| [评级与佣金体系](docs/rating-system.md) | S/A/B/C/D 评级标准 + T0-T3 佣金等级 + 组合矩阵 |
| [多市场配置](docs/multi-market.md) | MY/PH/VN/BR 市场切换、佣金定价、新增市场指南 |
| [开发指南](docs/development.md) | 本地搭建、新增数据源/分析师、调试技巧、测试 |

---

## 项目结构

```
tiktok-influencer-agents/
├── main.py                              # CLI 入口 (argparse)
├── pyproject.toml                       # 项目依赖 (Python 3.10+)
├── .env                                 # 环境变量配置
│
├── cli/main.py                          # Typer CLI 入口
│
├── influenceragents/                    # 核心包
│   ├── default_config.py                # 全局配置 + 4 市场佣金表
│   │
│   ├── agents/                          # 13 个 Agent
│   │   ├── analysts/                    # 数据分析层 (4 个, 带工具调用)
│   │   │   ├── metrics_analyst.py       #   粉丝/互动/增长/异常检测
│   │   │   ├── content_analyst.py       #   内容质量/视觉标签/Vision
│   │   │   ├── audience_analyst.py      #   受众画像/假粉检测
│   │   │   └── commerce_analyst.py      #   电商潜力/定价/TikTok Shop
│   │   ├── researchers/                 # 适配度辩论 (2 个)
│   │   │   ├── advocate_researcher.py   #   推荐方论证
│   │   │   └── skeptic_researcher.py    #   质疑方论证
│   │   ├── managers/                    # 决策层 (2 个)
│   │   │   ├── evaluation_manager.py    #   辩论综合 → 推荐/有条件/不推荐
│   │   │   └── campaign_manager.py      #   最终评级报告 S-D + T0-T3
│   │   ├── strategist/
│   │   │   └── partnership_strategist.py #  合作方案 + 佣金等级判定
│   │   ├── risk_mgmt/                   # 风控三方辩论 (3 个)
│   │   │   ├── brand_safety_debator.py  #   品牌安全 (保守派)
│   │   │   ├── roi_risk_debator.py      #   投入回报 (激进派)
│   │   │   └── audience_fit_debator.py  #   受众匹配 (中立派)
│   │   └── utils/
│   │       ├── agent_states.py          #   AgentState / DebateState 定义
│   │       ├── agent_utils.py           #   上下文构建 / 消息清理
│   │       ├── memory.py                #   BM25 记忆系统
│   │       ├── profile_tools.py         #   Metrics 分析师工具
│   │       ├── content_tools.py         #   Content 分析师工具
│   │       ├── audience_tools.py        #   Audience 分析师工具
│   │       └── commerce_tools.py        #   Commerce 分析师工具
│   │
│   ├── dataflows/                       # 数据层
│   │   ├── interface.py                 #   vendor 路由 (route_to_vendor)
│   │   ├── apify_tiktok.py              #   Apify TikTok 数据采集 + 缓存
│   │   ├── vision_analysis.py           #   Claude/OpenAI Vision 视觉分析
│   │   └── config.py                    #   运行时配置管理
│   │
│   ├── graph/                           # LangGraph 编排层
│   │   ├── analysis_graph.py            #   主协调器 InfluencerAnalysisGraph
│   │   ├── setup.py                     #   StateGraph 21 节点 + 边构建
│   │   ├── conditional_logic.py         #   条件路由逻辑
│   │   ├── propagation.py               #   初始状态创建 + 调用
│   │   ├── signal_processing.py         #   提取 tier + commission_tier
│   │   └── reflection.py                #   反思学习 + 记忆更新
│   │
│   └── llm_clients/                     # LLM 抽象层
│       ├── factory.py                   #   create_llm_client() 统一工厂
│       ├── base_client.py               #   基类 + 内容归一化
│       ├── openai_client.py             #   OpenAI / xAI / OpenRouter / Ollama
│       ├── anthropic_client.py          #   Anthropic Claude (支持自定义 base_url)
│       ├── google_client.py             #   Google Gemini
│       └── validators.py                #   模型名验证
│
├── tests/                               # 测试目录
├── results/                             # 分析报告输出
└── docs/                                # 详细文档
```

---

## 快速开始

```bash
# 1. 安装依赖
pip install -e .

# 2. 配置 .env
#    必填: APIFY_TOKEN + 至少一个 LLM API Key
#    示例: 使用 Anthropic 中转
APIFY_TOKEN=your_token
ANTHROPIC_BASE_URL=https://your-proxy.com
ANTHROPIC_AUTH_TOKEN=your_token

# 3. 运行分析
python main.py <tiktok_username> --market MY --provider anthropic --debug
```

---

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `APIFY_TOKEN` | 是 | Apify API Token (TikTok 数据抓取) |
| `OPENAI_API_KEY` | 至少一个 | OpenAI API Key |
| `ANTHROPIC_AUTH_TOKEN` | 至少一个 | Anthropic API Token (优先级高于 ANTHROPIC_API_KEY) |
| `ANTHROPIC_API_KEY` | 至少一个 | Anthropic API Key (备选) |
| `ANTHROPIC_BASE_URL` | 否 | Anthropic 自定义 Base URL (代理/中转) |
| `GOOGLE_API_KEY` | 至少一个 | Google Gemini API Key |
| `XAI_API_KEY` | 至少一个 | X AI (Grok) API Key |
| `OPENROUTER_API_KEY` | 至少一个 | OpenRouter API Key |
| `INFLUENCER_RESULTS_DIR` | 否 | 自定义结果输出目录 (默认 `./results`) |

---

## CLI 用法

```bash
# 基础分析
python main.py username --market MY

# 指定 LLM 提供商和模型
python main.py username --provider anthropic --deep-model claude-sonnet-4-6 --quick-model claude-haiku-4-5

# 增加辩论轮数
python main.py username --debate-rounds 3

# Debug 模式 (实时打印节点输出)
python main.py username --debug
```

---

## 系统流水线

```
输入: TikTok 用户名 + 目标市场
  │
  ▼
┌──────────────────────────────────┐
│  第 1 层: 数据分析 (4 个分析师)     │
│  Metrics → Content → Audience    │
│  → Commerce (各自调用工具采集数据)   │
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  第 2 层: 适配度辩论                │
│  Advocate ←→ Skeptic (多轮辩论)   │
│  → Evaluation Manager (综合裁决)  │
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  第 3 层: 合作策略                  │
│  Partnership Strategist           │
│  (佣金等级 T0-T3 + 合作方案)       │
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  第 4 层: 风控辩论 (三方)           │
│  Brand Safety ←→ ROI Risk        │
│  ←→ Audience Fit (循环辩论)       │
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  第 5 层: 最终决策                  │
│  Campaign Manager                 │
│  → 等级(S-D) + 佣金(T0-T3)       │
│  → 标签 + 结构化报告              │
└───────────────┬──────────────────┘
                ▼
输出: results/<username>/report_<date>.md
      results/<username>/analysis_log_<date>.json
```

---

## 核心技术栈

| 技术 | 用途 |
|------|------|
| LangGraph 0.4.8+ | Agent 工作流编排 |
| LangChain | LLM 抽象和 Prompt 管理 |
| Apify Client | TikTok 数据采集 |
| Claude Vision | 视频封面视觉分析 |
| Rank-BM25 | Agent 记忆检索 (无需 embedding) |
| Typer + Rich | CLI 界面 |
| Pandas | 数据处理 |

---

## LLM 提供商支持

| 提供商 | 配置方式 | 推荐模型 |
|--------|---------|---------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o / gpt-4o-mini |
| Anthropic | `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` | claude-sonnet-4-6 / claude-haiku-4-5 |
| Google | `GOOGLE_API_KEY` | gemini-2.5-flash |
| xAI | `XAI_API_KEY` | grok 系列 |
| OpenRouter | `OPENROUTER_API_KEY` | 任意 OpenRouter 模型 |
| Ollama | `backend_url` 指向本地 | 本地模型 |

---

## 评级速查

**达人等级 (S/A/B/C/D)**

| 等级 | 互动率 | 受众 | 带货 | 建议 |
|------|--------|------|------|------|
| S | >5% | 真实 | 实绩突出 | 强烈推荐 |
| A | 3-5% | 较真实 | 有经验 | 优先合作 |
| B | 1-3% | 可接受 | 有限 | 测试合作 |
| C | <1% | 有疑虑 | 无 | 大幅议价 |
| D | 异常 | 假粉 | — | 不合作 |

**佣金等级 (T0-T3)** — 以马来西亚为例

| 等级 | 报价 (RM) | 粉丝量参考 |
|------|-----------|-----------|
| T0 | 600+ | 100万+ |
| T1 | 400-500 | 50万-100万 |
| T2 | 200-350 | 10万-50万 |
| T3 | 50-150 | <10万 |

---

## 关键扩展点

| 扩展需求 | 涉及文件 | 参考文档 |
|---------|---------|---------|
| 新增 LLM 提供商 | `llm_clients/` 新建 + `factory.py` 注册 | [开发指南](docs/development.md) §3.4 |
| 新增数据源 | `dataflows/` 新建 + `interface.py` 注册 | [数据层设计](docs/dataflow-design.md) §6 |
| 新增分析师 Agent | `agents/analysts/` + `graph/setup.py` | [开发指南](docs/development.md) §3.2 |
| 新增市场 | `default_config.py` MARKET_CONFIGS | [多市场配置](docs/multi-market.md) §5 |
| 调整辩论轮数 | config `max_debate_rounds` | [开发指南](docs/development.md) §3.3 |
