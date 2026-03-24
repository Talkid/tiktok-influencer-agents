# 开发指南

## 1. 本地开发环境搭建

### 前置要求

- Python >= 3.10
- pip 或 uv 包管理器

### 安装

```bash
cd tiktok-influencer-agents

# 安装依赖 (开发模式)
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env:
#   APIFY_TOKEN=your_token
#   OPENAI_API_KEY=your_key
```

### 验证安装

```bash
# 验证基础导入
python -c "from influenceragents.default_config import DEFAULT_CONFIG; print('OK')"

# 验证 Graph 编译 (需要 OPENAI_API_KEY)
python -c "
from influenceragents.graph.analysis_graph import InfluencerAnalysisGraph
g = InfluencerAnalysisGraph()
print(f'Nodes: {len(g.graph.nodes)}')
"
```

## 2. 项目结构导航

```
influenceragents/
├── default_config.py        # 起点: 所有配置和市场定义
│
├── agents/                  # Agent 层
│   ├── __init__.py          # 所有 create_xxx 的统一导出
│   ├── utils/
│   │   ├── agent_states.py  # 状态 TypedDict 定义
│   │   ├── agent_utils.py   # build_influencer_context + create_msg_delete + 工具导入
│   │   ├── memory.py        # BM25 记忆系统
│   │   ├── profile_tools.py # Metrics 分析师的工具
│   │   ├── content_tools.py # Content 分析师的工具
│   │   ├── audience_tools.py # Audience 分析师的工具
│   │   └── commerce_tools.py # Commerce 分析师的工具
│   ├── analysts/            # 4 个分析师: 每个有 tools 和 system prompt
│   ├── researchers/         # Advocate + Skeptic: 辩论对
│   ├── risk_mgmt/           # Brand Safety + ROI + Audience Fit: 三方辩论
│   ├── strategist/          # Partnership Strategist: 合作方案
│   └── managers/            # Evaluation Manager + Campaign Manager: 决策层
│
├── dataflows/               # 数据层
│   ├── config.py            # get_config/set_config 运行时配置
│   ├── interface.py         # VENDOR_METHODS + route_to_vendor() 路由
│   ├── apify_tiktok.py      # Apify 实现 (所有 get_apify_xxx 函数)
│   └── vision_analysis.py   # Claude Vision / GPT-4V 视觉分析
│
├── graph/                   # 图编排层
│   ├── analysis_graph.py    # 主类 InfluencerAnalysisGraph
│   ├── setup.py             # StateGraph 节点/边构建
│   ├── conditional_logic.py # 条件路由
│   ├── propagation.py       # 初始状态创建
│   ├── signal_processing.py # 提取 S/A/B/C/D + T0/T1/T2/T3
│   └── reflection.py        # 反思学习
│
└── llm_clients/             # LLM 抽象层
    ├── factory.py           # create_llm_client() 统一工厂
    ├── base_client.py       # 基类 + normalize_content()
    ├── openai_client.py     # OpenAI/xAI/OpenRouter/Ollama
    ├── anthropic_client.py  # Anthropic Claude
    ├── google_client.py     # Google Gemini
    └── validators.py        # 模型名验证
```

## 3. 常见开发任务

### 3.1 新增数据源

1. 创建 `dataflows/new_vendor.py`
2. 实现函数，签名与 `apify_tiktok.py` 一致
3. 在 `dataflows/interface.py` 中:
   - 导入新函数
   - 在 `VENDOR_METHODS` 对应方法中添加新 vendor
   - 在 `VENDOR_LIST` 中添加
4. 在 `default_config.py` 的 `data_vendors` 注释中标注新选项

### 3.2 新增分析师

1. 创建 `agents/analysts/new_analyst.py`
2. 遵循工厂模式: `create_new_analyst(llm)` → 返回闭包
3. 定义工具集 (新建 `agents/utils/new_tools.py`)
4. 在 `agents/__init__.py` 中导出
5. 在 `graph/setup.py` 中添加节点和边
6. 在 `graph/conditional_logic.py` 中添加 `should_continue_new`
7. 在 `graph/analysis_graph.py` 中:
   - 导入新工具
   - 在 `_create_tool_nodes` 中添加
   - 更新 `selected_analysts` 默认值
8. 在 `agents/utils/agent_states.py` 中添加对应的 report 字段

### 3.3 修改辩论轮数

```python
config = DEFAULT_CONFIG.copy()
config["max_debate_rounds"] = 3        # Advocate/Skeptic 辩论 3 轮
config["max_risk_discuss_rounds"] = 2  # 风控三方辩论 2 轮
```

### 3.4 切换 LLM 提供商

```python
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "anthropic"
config["deep_think_llm"] = "claude-sonnet-4-6"
config["quick_think_llm"] = "claude-haiku-4-5"
```

### 3.5 只运行部分分析师

```python
graph = InfluencerAnalysisGraph(
    selected_analysts=["metrics", "content"],  # 只运行 Metrics 和 Content
    config=config,
)
```

## 4. 调试技巧

### 开启 Debug 模式

```python
graph = InfluencerAnalysisGraph(debug=True)
# 每个节点的输出会实时打印到终端
```

### 查看完整状态日志

分析完成后检查 `results/<username>/analysis_log_<date>.json`，包含:
- 所有分析师报告
- 完整辩论历史
- 策略方案
- 最终评估

### 单独测试数据工具

```python
from influenceragents.dataflows.apify_tiktok import get_apify_profile_info
print(get_apify_profile_info("some_username"))
```

### 测试 Graph 编译

```python
import os
os.environ["OPENAI_API_KEY"] = "sk-test"

from influenceragents.graph.analysis_graph import InfluencerAnalysisGraph
graph = InfluencerAnalysisGraph()
print(list(graph.graph.nodes.keys()))  # 应输出 21 个节点
```

## 5. 测试

### 运行测试

```bash
python -m pytest tests/ -v
```

### 测试覆盖建议

| 测试类型 | 目标 |
|---------|------|
| 单元测试 | 每个数据工具的返回格式 |
| 单元测试 | BM25 记忆的增删查 |
| 单元测试 | SignalProcessor 的评级提取 |
| 集成测试 | Graph 编译成功 |
| 集成测试 | 状态初始化正确 |
| E2E 测试 | 完整分析流水线 (需 API Key) |

## 6. 生产部署注意事项

- 设置 `APIFY_TOKEN` 和至少一个 LLM API Key
- 考虑为 Apify 设置更高的 rate limit plan
- 视觉分析消耗较多 Token，可通过减少分析图片数量控制成本
- 建议在首次运行后检查 `data_cache/` 目录，确认缓存正常工作
- `results/` 目录会持续增长，建议定期归档
