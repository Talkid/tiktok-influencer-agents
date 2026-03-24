# 数据层设计文档

## 1. 数据架构概览

```
Agent 工具调用
    ↓
@tool 装饰器函数 (agents/utils/*_tools.py)
    ↓
route_to_vendor() (dataflows/interface.py)
    ↓ (根据配置选择 vendor)
Vendor 实现 (dataflows/apify_tiktok.py / vision_analysis.py)
    ↓
外部 API (Apify / Claude Vision / TikTok API)
    ↓ (结果缓存)
data_cache/ (JSON 文件缓存)
```

## 2. 工具定义

### 分类与映射

| 类别 | 工具名 | 所属分析师 | 文件 |
|------|--------|-----------|------|
| **profile_data** | `get_profile_info` | Metrics | `profile_tools.py` |
| | `get_follower_growth` | Metrics | `profile_tools.py` |
| | `get_engagement_rates` | Metrics | `profile_tools.py` |
| | `get_video_performance_stats` | Metrics | `profile_tools.py` |
| **content_data** | `get_recent_videos` | Content | `content_tools.py` |
| | `analyze_video_thumbnails` | Content | `content_tools.py` |
| | `get_content_categories` | Content | `content_tools.py` |
| **audience_data** | `get_audience_demographics` | Audience | `audience_tools.py` |
| | `detect_fake_followers` | Audience | `audience_tools.py` |
| **commerce_data** | `get_ecommerce_history` | Commerce | `commerce_tools.py` |
| | `get_competitor_pricing` | Commerce | `commerce_tools.py` |
| | `get_tiktok_shop_data` | Commerce | `commerce_tools.py` |

### 工具签名规范

所有工具使用 LangChain `@tool` 装饰器，参数使用 `Annotated` 类型标注：

```python
@tool
def get_profile_info(
    username: Annotated[str, "TikTok username (without @)"],
) -> str:
    """获取 TikTok 用户基本资料。"""
    return route_to_vendor("get_profile_info", username)
```

## 3. Vendor 路由机制

### 路由配置

```python
# default_config.py
"data_vendors": {
    "profile_data": "apify",        # 类别级别默认
    "content_data": "apify",
    "audience_data": "apify",
    "commerce_data": "apify",
    "vision_analysis": "claude_vision",
},
"tool_vendors": {
    # "get_profile_info": "tiktok_api",  # 工具级别覆盖
},
```

### 路由优先级

1. `tool_vendors[method]` — 工具级别 (最高优先级)
2. `data_vendors[category]` — 类别级别
3. 自动 fallback — 尝试所有已注册 vendor

### 路由流程

```python
def route_to_vendor(method, *args, **kwargs):
    category = get_category_for_method(method)  # 通过 TOOLS_CATEGORIES 查找
    vendor = get_vendor(category, method)        # 按优先级获取 vendor
    impl = VENDOR_METHODS[method][vendor]         # 获取实现函数
    return impl(*args, **kwargs)                  # 执行并返回
```

## 4. Apify 数据源实现

**文件**: `dataflows/apify_tiktok.py`

### 使用的 Apify Actor

| Actor | 用途 | 数据点 |
|-------|------|--------|
| `clockworks/tiktok-profile-scraper` | 用户资料 | 粉丝数、关注、获赞、简介、认证 |
| `clockworks/tiktok-scraper` | 视频数据 | 播放量、点赞、评论、分享、封面URL、标题、话题标签 |

### 缓存策略

- 缓存路径: `dataflows/data_cache/{md5_hash}.json`
- 缓存键: `{类型}_{username}_{参数}`
- 缓存粒度: 每个 API 调用独立缓存
- 无过期机制 (适合分析场景，同一达人不需要重复抓取)

### 实现的函数

| 函数 | 说明 | 返回格式 |
|------|------|---------|
| `get_apify_profile_info` | 基础资料 | 文本 (key: value 格式) |
| `get_apify_follower_growth` | 增长数据 | 文本 + 当前快照 |
| `get_apify_engagement_rates` | 互动率 | 文本 (含互动率计算) |
| `get_apify_video_performance_stats` | 视频数据表 | Markdown 表格 |
| `get_apify_recent_videos` | 视频元数据 | 结构化文本 |
| `get_apify_video_thumbnails` | 封面 URL | JSON 数组 |
| `get_apify_content_categories` | 话题标签 | 排序统计 |
| `get_apify_audience_demographics` | 受众估算 | 文本 + 比率 |
| `get_apify_fake_followers` | 假粉检测 | 文本 + 异常信号 |
| `get_apify_ecommerce_history` | 带货历史 | 文本 + 匹配列表 |
| `get_apify_competitor_pricing` | 定价估算 | 文本 + 等级表 |
| `get_apify_tiktok_shop_data` | TikTok Shop | 占位 (待实现) |

### 假粉检测启发式规则

```python
signals = []
if followers > 10000 and engagement_rate < 0.5:
    signals.append("LOW ENGAGEMENT")          # 高粉低互动
if view_to_follower < 1:
    signals.append("LOW REACH")               # 播放量不足粉丝的 1%
if followers > 50000 and avg_comments < 5:
    signals.append("LOW COMMENTS")            # 几乎无评论
```

### 带货检测关键词

```python
ad_keywords = [
    "#ad", "#sponsored", "#gifted", "#collab", "#partnership",
    "#tiktokshop", "#affiliate", "link in bio", "use my code",
    "#iklan", "#kerjasama",  # 马来语商业标签
]
```

## 5. Vision 分析管线

**文件**: `dataflows/vision_analysis.py`

### 流程

```
1. 从 Apify 缓存获取视频封面 URL
2. 下载封面图 → Base64 编码 (内存中，不写磁盘)
3. 构建 Vision Prompt (含市场上下文)
4. 发送到 Claude Vision / GPT-4V
5. 返回结构化标签分析
```

### Vision Prompt 要求 Agent 识别

| 维度 | 提取内容 |
|------|---------|
| 年龄估计 | 视频中人物的年龄段 |
| 内容类别 | 美妆、美食、科技、生活方式等 |
| 制作质量 | 专业/业余/家庭场景/户外 |
| 生活方式 | 奢侈品、孩子、宠物、家装风格 |
| 文字叠层 | 语言识别 (马来语/中文/英语/泰米尔语) |

### 成本控制

- 每次分析最多 5 张封面 (可配置)
- 使用 `claude-sonnet` 而非 `opus` 降低成本

## 6. 新增数据源指南

### 步骤

1. 在 `dataflows/` 创建新文件 (如 `ensemble_data.py`)
2. 实现与已有函数签名一致的函数
3. 在 `interface.py` 的 `VENDOR_METHODS` 中注册
4. 在 `VENDOR_LIST` 中添加 vendor 名称
5. 更新 `DEFAULT_CONFIG` 的 `data_vendors` 选项

### 示例: 添加 EnsembleData

```python
# dataflows/ensemble_data.py
def get_ensemble_profile_info(username: str) -> str:
    # 调用 EnsembleData API
    ...

# dataflows/interface.py — 在 VENDOR_METHODS 中添加
"get_profile_info": {
    "apify": get_apify_profile_info,
    "ensemble": get_ensemble_profile_info,  # 新增
},
```
