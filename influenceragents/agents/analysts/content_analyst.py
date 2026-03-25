from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from influenceragents.agents.utils.agent_utils import (
    build_influencer_context,
    get_recent_videos,
    analyze_video_thumbnails,
    get_content_categories,
)


def create_content_analyst(llm):

    def content_analyst_node(state):
        username = state["influencer_username"]
        market = state.get("target_market", "MY")
        influencer_context = build_influencer_context(username, market)

        tools = [
            get_recent_videos,
            analyze_video_thumbnails,
            get_content_categories,
        ]

        system_message = """You are an influencer content analyst specializing in visual and thematic analysis. Your task is to deeply analyze the TikTok influencer's content to extract meaningful tags and categorizations.

Analyze the following aspects:
1. **Content Themes**: Dominant topics (beauty, food, tech, lifestyle, parenting, fashion, comedy, education, etc.)
2. **Visual Style**: Production quality, consistency, aesthetic appeal
3. **Visual Tags** (from thumbnail analysis): Estimated age of influencer, setting (home/studio/outdoor), visible products/brands, lifestyle indicators
4. **Content Consistency**: Whether the influencer sticks to a niche or posts varied content
5. **Brand Friendliness**: Is the content suitable for brand partnerships? Any controversial themes?
6. **Language Analysis**: What languages are used in captions and text overlays?
7. **Influencer Tags**: Based on all analysis, assign tags:
   - Age range: [18-24 / 25-34 / 35-44 / 45+]
   - Content niche: [Beauty, Food, Tech, Lifestyle, Parenting, Fashion, ...]
   - Target audience: [Gen Z, Young Professionals, Parents, ...]
   - Lifestyle: [Has kids, Pet owner, Fitness, Middle class, Luxury, ...]

First call get_recent_videos for video metadata, then analyze_video_thumbnails for visual analysis, and get_content_categories for hashtag analysis.

Output format — use bullet points for each section and end with a compact tag summary block. Be concise: 2-4 bullets per section, no verbose paragraphs. Total report must stay under 500 words.

IMPORTANT: Write your entire report in Chinese (Simplified). All analysis, labels, and summaries must be in Chinese."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant analyzing TikTok influencer content."
                    " Use the provided tools to gather data and produce a detailed analysis."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "\n{influencer_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(influencer_context=influencer_context)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "content_report": report,
        }

    return content_analyst_node
