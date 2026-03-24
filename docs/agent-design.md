# Agent 设计文档

## 概述

系统包含 **13 个 Agent**，分为 5 层：数据分析层、适配度辩论层、策略层、风控辩论层、最终决策层。

每个 Agent 遵循统一的工厂模式：`create_xxx(llm, [memory])` 返回一个闭包函数 `node(state) -> dict`。

---

## 第 1 层：数据分析师 (4 个)

### Metrics Analyst — 数据指标分析师

**文件**: `agents/analysts/metrics_analyst.py`

**职责**: 量化分析达人的数据表现

**工具**:
| 工具名 | 说明 |
|--------|------|
| `get_profile_info` | 获取基础资料：粉丝、关注、获赞、认证 |
| `get_follower_growth` | 获取粉丝增长趋势 |
| `get_engagement_rates` | 计算互动率（点赞/评论/分享 vs 播放量） |
| `get_video_performance_stats` | 获取近期视频详细数据表 |

**分析维度**:
- 粉丝数据趋势和增长轨迹
- 互动率计算：(点赞+评论+分享) / 播放量
- 发布频率一致性
- **异常检测**：
  - 高粉低互动 (互动率 < 0.5%)
  - 粉丝暴增无对应内容
  - 异常的点赞/评论比 (大量点赞但几乎无评论)
  - 机器人评论模式

**输出**: `metrics_report` (Markdown 格式，含汇总表格)

**LLM**: `quick_thinking_llm`

---

### Content Analyst — 内容分析师

**文件**: `agents/analysts/content_analyst.py`

**职责**: 定性分析达人的内容质量和风格，提取视觉标签

**工具**:
| 工具名 | 说明 |
|--------|------|
| `get_recent_videos` | 获取视频元数据：标题、话题标签、音乐、时长 |
| `analyze_video_thumbnails` | **调用 Vision 模型**分析封面图，提取标签 |
| `get_content_categories` | 通过话题标签和标题分析内容领域 |

**分析维度**:
- 内容主题分类 (美妆/美食/科技/生活/育儿/时尚等)
- 视觉风格：制作质量、一致性、美感
- **视觉标签提取** (通过 Claude Vision):
  - 达人年龄估计
  - 场景 (家庭/工作室/户外)
  - 可见产品/品牌
  - 生活方式指标 (奢侈品/中产/有孩子等)
- 品牌友好度评估
- 语言分析 (字幕和文字叠层)

**输出**: `content_report` (含标签汇总)

**LLM**: `quick_thinking_llm` (视觉分析使用 `vision_llm`)

---

### Audience Analyst — 受众分析师

**文件**: `agents/analysts/audience_analyst.py`

**职责**: 分析达人的受众画像和真实性

**工具**:
| 工具名 | 说明 |
|--------|------|
| `get_audience_demographics` | 估算受众年龄/性别/地域分布 |
| `detect_fake_followers` | 检测假粉：互动比、评论质量、增长模式 |

**分析维度**:
- 受众年龄/性别/地域分布
- **假粉检测** (启发式信号):
  - 互动率 vs 粉丝数比例
  - 评论质量和多样性
  - 购买意向信号 ("哪里买"、"链接"、"价格")
- 受众与目标市场匹配度
- 评论语言 vs 目标市场语言
- 受众忠诚度：重复互动指标

**输出**: `audience_report` (含 1-10 真实性评分)

---

### Commerce Analyst — 电商分析师

**文件**: `agents/analysts/commerce_analyst.py`

**职责**: 评估达人的电商潜力和市场定价

**工具**:
| 工具名 | 说明 |
|--------|------|
| `get_ecommerce_history` | 检测过往品牌合作、赞助内容 |
| `get_competitor_pricing` | 研究同级达人的市场报价 |
| `get_tiktok_shop_data` | 获取 TikTok Shop 数据 |

**分析维度**:
- 历史合作记录频率
- TikTok Shop 使用情况
- 转化信号 (评论中的购买行为)
- 同级达人定价对比
- **产品类目适配**：美妆 / 美食 / 时尚 / 电子 / 家居 / 健身 / 母婴
- **佣金等级初步判断** (T0/T1/T2/T3)

**输出**: `commerce_report` (含定价建议)

---

## 第 2 层：适配度辩论

### Advocate Researcher — 推荐方

**文件**: `agents/researchers/advocate_researcher.py`

**职责**: 基于 4 份报告，论证推荐合作

**输入**: 4 份分析报告 + 辩论历史 + BM25 记忆

**论证重点**:
- 增长潜力和内容质量
- 受众真实性和匹配度
- 带货历史和转化证据
- 反驳质疑方的具体观点

**风格**: 对话式辩论，直接回应对方论点，不是简单罗列数据

**记忆**: 使用 `advocate_memory` 回顾过去类似达人的分析经验

---

### Skeptic Researcher — 质疑方

**文件**: `agents/researchers/skeptic_researcher.py`

**职责**: 论证不推荐合作，揭示风险

**论证重点**:
- 刷量嫌疑和假粉信号
- 受众不匹配
- 品牌风险和争议内容
- 性价比质疑
- 反驳推荐方的乐观假设

**记忆**: 使用 `skeptic_memory` 回顾过去表现不佳的类似达人

---

### Evaluation Manager — 评估经理

**文件**: `agents/managers/evaluation_manager.py`

**职责**: 综合辩论结果，做出初步决策

**决策选项**: 推荐 / 有条件推荐 / 不推荐

**输出**: `evaluation_plan` — 包含决策、理由和策略方向

**LLM**: `deep_thinking_llm` (需要复杂推理)

**记忆**: 使用 `evaluation_judge_memory`

---

## 第 3 层：策略层

### Partnership Strategist — 合作策略师

**文件**: `agents/strategist/partnership_strategist.py`

**职责**: 制定具体的合作方案

**输出** `strategist_partnership_plan`:
1. **合作形式**: 单条视频 / 多条视频系列
2. **佣金等级**: T0 / T1 / T2 / T3 (读取市场配置)
3. **建议视频数量**
4. **内容方向建议**
5. **关键卖点**

**佣金判定逻辑** (以马来西亚为例):

| 等级 | 报价 (RM) | 判定依据 |
|------|-----------|---------|
| T0 | 600+ | 100万+粉丝，互动率>5%，成熟带货记录 |
| T1 | 400-500 | 50万-100万粉丝，互动率3-5%，有合作经验 |
| T2 | 200-350 | 10万-50万粉丝，互动率可接受，潜力型 |
| T3 | 50-150 | <10万粉丝或新起步，适合批量测试 |

---

## 第 4 层：风控辩论 (3 方)

### Brand Safety Analyst — 品牌安全分析师 (保守派)

**文件**: `agents/risk_mgmt/brand_safety_debator.py`

**视角**: 保护品牌声誉，最小化风险

**关注点**:
- 争议内容、过往丑闻、NSFW 内容
- 假粉损害品牌信誉
- 合同保障建议
- 文化敏感性

---

### ROI Risk Analyst — 投入回报分析师 (激进派)

**文件**: `agents/risk_mgmt/roi_risk_debator.py`

**视角**: 追求高回报，论证投入值得

**关注点**:
- 潜在爆发力和传播扩散
- 互动数据预示转化能力
- 定价合理性
- 增长轨迹暗示价值上升

---

### Audience Fit Analyst — 受众匹配分析师 (中立派)

**文件**: `agents/risk_mgmt/audience_fit_debator.py`

**视角**: 平衡评估，关注受众是否匹配

**关注点**:
- 受众画像 vs 产品目标人群
- 受众兴趣 vs 产品类目
- 地理分布 vs 目标市场
- 挑战两个极端观点

---

## 第 5 层：最终决策

### Campaign Manager — 战役经理

**文件**: `agents/managers/campaign_manager.py`

**职责**: 综合所有分析和辩论，输出最终结构化报告

**LLM**: `deep_thinking_llm`

**输出**: `final_assessment` — 包含完整评估报告:

```
1. TIER RATING: S/A/B/C/D
2. COMMISSION TIER: T0/T1/T2/T3
3. VERDICT
4. PROFILE SUMMARY
5. INFLUENCER TAGS
6. E-COMMERCE POTENTIAL
7. COLLABORATION RECOMMENDATION
8. RISK ASSESSMENT
9. EXECUTIVE SUMMARY
```

**记忆**: 使用 `campaign_manager_memory`

---

## Agent 工厂模式参考

所有 Agent 遵循统一模式：

```python
# 分析师模式 (带工具)
def create_xxx_analyst(llm):
    def analyst_node(state):
        tools = [...]
        prompt = ChatPromptTemplate.from_messages([...])
        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        report = result.content if not result.tool_calls else ""
        return {"messages": [result], "xxx_report": report}
    return analyst_node

# 研究员模式 (辩论)
def create_xxx_researcher(llm, memory):
    def researcher_node(state):
        # 读取辩论状态和报告
        # 查询 BM25 记忆
        # 生成论点
        # 更新辩论状态 (history + count)
        return {"suitability_debate_state": new_state}
    return researcher_node

# 经理模式 (决策)
def create_xxx_manager(llm, memory):
    def manager_node(state):
        # 综合辩论历史和报告
        # 查询记忆
        # 做出决策
        return {"xxx_state": new_state, "xxx_plan": response}
    return manager_node
```
