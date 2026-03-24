# TikTok Influencer Analysis System

基于 **LangGraph** 的多 Agent 辩论式 TikTok 达人评估系统。13 个专业 AI Agent 协作分析达人数据，通过正反辩论产出等级评定（S-D）和佣金建议（T0-T3）。

## 特性

- **多 Agent 辩论** — Advocate vs Skeptic 对抗辩论，Brand Safety / ROI / Audience Fit 三方风控
- **真实 TikTok 数据** — 通过 Apify 抓取粉丝、互动率、视频、电商历史
- **Vision 分析** — Claude Vision 分析视频封面，提取年龄/场景/生活方式标签
- **BM25 记忆** — Agent 从历史分析中学习，提升决策一致性
- **多市场支持** — 马来西亚、菲律宾、越南、巴西，独立佣金定价体系
- **多 LLM 支持** — OpenAI、Anthropic（支持中转）、Google、xAI、OpenRouter、Ollama

## 快速开始

### 1. 安装

```bash
pip install -e .
```

### 2. 配置环境变量

复制并编辑 `.env`：

```bash
# 必填：Apify TikTok 数据抓取
APIFY_TOKEN=your_apify_token

# LLM：至少配置一个
# Anthropic（支持自定义中转地址）
ANTHROPIC_BASE_URL=https://your-proxy.com
ANTHROPIC_AUTH_TOKEN=your_token

# 或使用 OpenAI
OPENAI_API_KEY=your_openai_key
```

### 3. 运行分析

```bash
python main.py <tiktok_username> --market MY --provider anthropic
```

## 命令行参数

```
python main.py <username> [选项]

参数:
  username              TikTok 用户名（不含 @）

选项:
  --market {MY,PH,VN,BR}    目标市场 (默认: MY)
  --provider TEXT           LLM 提供商: openai | anthropic | google | xai (默认: openai)
  --deep-model TEXT         复杂推理模型（辩论/决策）
  --quick-model TEXT        快速任务模型（数据分析）
  --debate-rounds INT       辩论轮数 (默认: 1)
  --debug                   实时打印每个 Agent 的输出
```

**示例：**

```bash
# 使用 Anthropic 分析马来西亚市场
python main.py fasterbabyy --market MY --provider anthropic --debug

# 使用 OpenAI，增加辩论轮数
python main.py username --provider openai --debate-rounds 3

# 指定具体模型
python main.py username --provider anthropic \
  --deep-model claude-sonnet-4-6 \
  --quick-model claude-haiku-4-5-20251001
```

## 各 LLM 提供商默认模型

| 提供商 | 深度推理模型 | 快速模型 | 环境变量 |
|--------|------------|---------|---------|
| `anthropic` | claude-sonnet-4-6 | claude-haiku-4-5-20251001 | `ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL` |
| `openai` | gpt-4o | gpt-4o-mini | `OPENAI_API_KEY` |
| `google` | gemini-2.5-pro | gemini-2.5-flash | `GOOGLE_API_KEY` |
| `xai` | grok-4-0709 | grok-4-fast-non-reasoning | `XAI_API_KEY` |
| `openrouter` | 自定义 | 自定义 | `OPENROUTER_API_KEY` |

## 分析流程

```
TikTok 用户名
    ↓
数据分析层（4 个 Agent）
  Metrics Analyst    → 粉丝/互动率/增长/异常检测
  Content Analyst    → 内容质量/Vision 视觉标签
  Audience Analyst   → 受众画像/假粉检测
  Commerce Analyst   → 电商历史/市场定价
    ↓
适配度辩论（2 个 Agent）
  Advocate ←→ Skeptic（多轮辩论）
  → Evaluation Manager（推荐 / 有条件 / 不推荐）
    ↓
合作策略（1 个 Agent）
  Partnership Strategist → 佣金等级 + 合作方案
    ↓
风控辩论（3 个 Agent）
  Brand Safety ←→ ROI Risk ←→ Audience Fit
    ↓
最终决策（1 个 Agent）
  Campaign Manager → 等级(S-D) + 佣金(T0-T3) + 完整报告
```

## 评级体系

### 达人等级（S/A/B/C/D）

| 等级 | 含义 | 互动率 | 建议行动 |
|------|------|--------|---------|
| S | Elite 顶级 | >5% | 强烈推荐，优先锁定 |
| A | Strong 优质 | 3-5% | 优先合作 |
| B | Viable 可用 | 1-3% | 测试性合作 |
| C | Caution 谨慎 | <1% | 大幅议价后考虑 |
| D | Avoid 避免 | 异常 | 不合作 |

### 佣金等级（T0-T3）— 马来西亚市场

| 等级 | 单条报价 | 粉丝量参考 |
|------|---------|-----------|
| T0 | 600+ RM | 100万+ |
| T1 | 400-500 RM | 50万-100万 |
| T2 | 200-350 RM | 10万-50万 |
| T3 | 50-150 RM | <10万 |

> 其他市场（PH/VN/BR）使用对应货币定价，见 [多市场配置文档](docs/multi-market.md)。

## 输出文件

分析完成后在 `results/<username>/` 目录下生成：

- `report_<date>.md` — 结构化 Markdown 报告（含等级、标签、合作建议）
- `analysis_log_<date>.json` — 完整状态日志（含所有辩论历史、中间报告）

## 项目结构

```
tiktok-influencer-agents/
├── main.py                          # CLI 入口
├── cli/main.py                      # Typer CLI 入口
├── influenceragents/
│   ├── default_config.py            # 全局配置 + 市场佣金表
│   ├── agents/                      # 13 个 Agent
│   │   ├── analysts/                # 数据分析层（4 个）
│   │   ├── researchers/             # 适配度辩论（2 个）
│   │   ├── risk_mgmt/               # 风控辩论（3 个）
│   │   ├── strategist/              # 合作策略师
│   │   ├── managers/                # 决策层（2 个）
│   │   └── utils/                   # 状态/记忆/工具定义
│   ├── dataflows/                   # 数据采集层（Apify + Vision）
│   ├── graph/                       # LangGraph 编排
│   └── llm_clients/                 # 多 LLM 提供商抽象
├── docs/                            # 详细设计文档
└── results/                         # 分析报告输出
```

## 详细文档

| 文档 | 内容 |
|------|------|
| [架构总览](docs/architecture.md) | 分层架构、LangGraph 节点、状态管理 |
| [Agent 设计](docs/agent-design.md) | 13 个 Agent 的职责与 Prompt 策略 |
| [数据层设计](docs/dataflow-design.md) | Apify 接入、vendor 路由、Vision 管线 |
| [评级与佣金](docs/rating-system.md) | S-D 评级标准 + T0-T3 佣金矩阵 |
| [多市场配置](docs/multi-market.md) | 4 个市场配置与新增市场指南 |
| [开发指南](docs/development.md) | 新增数据源、Agent、调试技巧 |

## 依赖

- Python >= 3.10
- LangGraph >= 0.4.8
- LangChain (anthropic / openai / google-genai)
- Apify Client >= 1.8.0
- Rank-BM25（记忆检索）
- python-dotenv
