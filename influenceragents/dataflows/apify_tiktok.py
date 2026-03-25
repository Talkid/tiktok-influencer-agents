"""Apify TikTok data fetching implementation.

Uses Apify actors to scrape TikTok profile data, videos, and comments.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Optional

from influenceragents.dataflows.config import get_config

try:
    from apify_client import ApifyClient
except ImportError:
    ApifyClient = None


def _get_cache_path(key: str) -> Path:
    config = get_config()
    cache_dir = Path(config.get("data_cache_dir", "./dataflows/data_cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    hashed = hashlib.md5(key.encode()).hexdigest()
    return cache_dir / f"{hashed}.json"


def _load_cache(key: str) -> Optional[dict]:
    path = _get_cache_path(key)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_cache(key: str, data: dict):
    path = _get_cache_path(key)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_apify_client() -> "ApifyClient":
    if ApifyClient is None:
        raise ImportError("apify-client is required. Install with: pip install apify-client")
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise ValueError("APIFY_TOKEN environment variable is required")
    return ApifyClient(token)


def _run_actor(actor_id: str, run_input: dict, cache_key: str) -> list:
    """Run an Apify actor with caching."""
    cached = _load_cache(cache_key)
    if cached is not None:
        return cached

    client = _get_apify_client()
    run = client.actor(actor_id).call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

    _save_cache(cache_key, items)
    return items


def get_apify_profile_info(username: str) -> str:
    """Fetch TikTok user profile information via Apify."""
    cache_key = f"profile_{username}"
    try:
        items = _run_actor(
            "clockworks/tiktok-profile-scraper",
            {"profiles": [username], "resultsPerPage": 1},
            cache_key,
        )
        if not items:
            return f"No profile data found for @{username}"

        profile = items[0]
        meta = profile.get("authorMeta", profile)  # profile data is nested in authorMeta
        lines = [
            f"Username: @{meta.get('name', username)}",
            f"Display Name: {meta.get('nickName', 'N/A')}",
            f"Bio: {meta.get('signature', 'N/A')}",
            f"Followers: {meta.get('fans', 'N/A')}",
            f"Following: {meta.get('following', 'N/A')}",
            f"Total Likes: {meta.get('heart', 'N/A')}",
            f"Total Videos: {meta.get('video', 'N/A')}",
            f"Verified: {meta.get('verified', False)}",
            f"User ID: {meta.get('id', 'N/A')}",
            f"Sec UID: {meta.get('secUid', 'N/A')}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching profile for @{username}: {e}"


def get_apify_follower_growth(username: str, days: int = 30) -> str:
    """Estimate follower growth based on available data."""
    cache_key = f"follower_growth_{username}_{days}"
    try:
        items = _run_actor(
            "clockworks/tiktok-profile-scraper",
            {"profiles": [username], "resultsPerPage": 1},
            cache_key,
        )
        if not items:
            return f"No data found for @{username}"

        profile = items[0]
        meta = profile.get("authorMeta", profile)
        followers = meta.get("fans", 0)
        videos = meta.get("video", 0)
        hearts = meta.get("heart", 0)

        return (
            f"Current Followers: {followers}\n"
            f"Total Videos: {videos}\n"
            f"Total Likes: {hearts}\n"
            f"Avg Likes per Video: {hearts // max(videos, 1)}\n"
            f"Note: Historical growth data requires premium API access. "
            f"Current snapshot shows {followers} followers with {videos} videos."
        )
    except Exception as e:
        return f"Error fetching follower growth for @{username}: {e}"


def get_apify_engagement_rates(username: str) -> str:
    """Calculate engagement rates from recent videos."""
    cache_key = f"engagement_{username}"
    try:
        items = _run_actor(
            "clockworks/tiktok-scraper",
            {"profiles": [username], "resultsPerPage": 30, "shouldDownloadVideos": False},
            cache_key,
        )
        if not items:
            return f"No video data found for @{username}"

        total_views = 0
        total_likes = 0
        total_comments = 0
        total_shares = 0
        count = len(items)

        for video in items:
            total_views += video.get("playCount", 0)
            total_likes += video.get("diggCount", 0)
            total_comments += video.get("commentCount", 0)
            total_shares += video.get("shareCount", 0)

        avg_views = total_views / max(count, 1)
        avg_likes = total_likes / max(count, 1)
        avg_comments = total_comments / max(count, 1)
        avg_shares = total_shares / max(count, 1)
        engagement_rate = (avg_likes + avg_comments + avg_shares) / max(avg_views, 1) * 100

        return (
            f"Videos Analyzed: {count}\n"
            f"Total Views: {total_views:,}\n"
            f"Avg Views/Video: {avg_views:,.0f}\n"
            f"Avg Likes/Video: {avg_likes:,.0f}\n"
            f"Avg Comments/Video: {avg_comments:,.0f}\n"
            f"Avg Shares/Video: {avg_shares:,.0f}\n"
            f"Engagement Rate: {engagement_rate:.2f}%\n"
            f"Like-to-View Ratio: {(avg_likes / max(avg_views, 1) * 100):.2f}%\n"
            f"Comment-to-View Ratio: {(avg_comments / max(avg_views, 1) * 100):.4f}%"
        )
    except Exception as e:
        return f"Error calculating engagement for @{username}: {e}"


def get_apify_video_performance_stats(username: str, limit: int = 30) -> str:
    """Get detailed performance stats for recent videos."""
    cache_key = f"video_stats_{username}_{limit}"
    try:
        items = _run_actor(
            "clockworks/tiktok-scraper",
            {"profiles": [username], "resultsPerPage": limit, "shouldDownloadVideos": False},
            cache_key,
        )
        if not items:
            return f"No video data found for @{username}"

        lines = [f"Video Performance Stats for @{username} (Last {len(items)} videos):\n"]
        lines.append("| # | Views | Likes | Comments | Shares | Duration | Caption |")
        lines.append("|---|-------|-------|----------|--------|----------|---------|")

        for i, video in enumerate(items[:20], 1):
            views = video.get("playCount", 0)
            likes = video.get("diggCount", 0)
            comments = video.get("commentCount", 0)
            shares = video.get("shareCount", 0)
            duration = video.get("videoMeta", {}).get("duration", 0) if isinstance(video.get("videoMeta"), dict) else 0
            caption = (video.get("text", "") or "")[:50]
            lines.append(f"| {i} | {views:,} | {likes:,} | {comments:,} | {shares:,} | {duration}s | {caption} |")

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching video stats for @{username}: {e}"


def get_apify_recent_videos(username: str, limit: int = 20) -> str:
    """Get recent video metadata: captions, hashtags, music, duration."""
    cache_key = f"recent_videos_{username}_{limit}"
    try:
        items = _run_actor(
            "clockworks/tiktok-scraper",
            {"profiles": [username], "resultsPerPage": limit, "shouldDownloadVideos": False},
            cache_key,
        )
        if not items:
            return f"No videos found for @{username}"

        lines = [f"Recent Videos for @{username}:\n"]
        for i, video in enumerate(items, 1):
            hashtags = " ".join([f"#{h.get('name', '')}" for h in video.get("hashtags", [])])
            music = video.get("musicMeta", {}).get("musicName", "N/A") if isinstance(video.get("musicMeta"), dict) else "N/A"
            lines.append(
                f"Video {i}:\n"
                f"  Caption: {video.get('text', 'N/A')}\n"
                f"  Hashtags: {hashtags or 'None'}\n"
                f"  Music: {music}\n"
                f"  Views: {video.get('playCount', 0):,}\n"
                f"  Posted: {video.get('createTimeISO', 'N/A')}\n"
            )

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching recent videos for @{username}: {e}"


def get_apify_video_thumbnails(username: str, limit: int = 10) -> str:
    """Get video thumbnail/cover URLs for visual analysis."""
    cache_key = f"thumbnails_{username}_{limit}"
    try:
        items = _run_actor(
            "clockworks/tiktok-scraper",
            {"profiles": [username], "resultsPerPage": limit, "shouldDownloadVideos": False},
            cache_key,
        )
        if not items:
            return f"No videos found for @{username}"

        covers = []
        for video in items:
            cover_url = video.get("videoMeta", {}).get("coverUrl", "") if isinstance(video.get("videoMeta"), dict) else ""
            if not cover_url:
                cover_url = video.get("covers", {}).get("default", "") if isinstance(video.get("covers"), dict) else ""
            if cover_url:
                covers.append({
                    "url": cover_url,
                    "caption": video.get("text", ""),
                    "views": video.get("playCount", 0),
                })

        return json.dumps(covers, ensure_ascii=False)
    except Exception as e:
        return f"Error fetching thumbnails for @{username}: {e}"


def get_apify_content_categories(username: str) -> str:
    """Analyze hashtags and captions to categorize content niche."""
    cache_key = f"categories_{username}"
    try:
        items = _run_actor(
            "clockworks/tiktok-scraper",
            {"profiles": [username], "resultsPerPage": 30, "shouldDownloadVideos": False},
            cache_key,
        )
        if not items:
            return f"No video data found for @{username}"

        all_hashtags = {}
        all_captions = []

        for video in items:
            for h in video.get("hashtags", []):
                name = h.get("name", "").lower()
                if name:
                    all_hashtags[name] = all_hashtags.get(name, 0) + 1
            caption = video.get("text", "")
            if caption:
                all_captions.append(caption)

        sorted_tags = sorted(all_hashtags.items(), key=lambda x: x[1], reverse=True)[:20]

        lines = [f"Content Category Analysis for @{username}:\n"]
        lines.append("Top Hashtags:")
        for tag, count in sorted_tags:
            lines.append(f"  #{tag}: {count} times")
        lines.append(f"\nTotal videos analyzed: {len(items)}")
        lines.append(f"Unique hashtags: {len(all_hashtags)}")
        lines.append(f"\nSample Captions:")
        for cap in all_captions[:5]:
            lines.append(f"  - {cap[:100]}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error analyzing content for @{username}: {e}"


def get_apify_audience_demographics(username: str) -> str:
    """Estimate audience demographics from comment analysis."""
    cache_key = f"demographics_{username}"
    try:
        items = _run_actor(
            "clockworks/tiktok-scraper",
            {"profiles": [username], "resultsPerPage": 10, "shouldDownloadVideos": False,
             "shouldDownloadCovers": False},
            cache_key,
        )
        if not items:
            return f"No data found for @{username}"

        total_comments = sum(v.get("commentCount", 0) for v in items)
        total_views = sum(v.get("playCount", 0) for v in items)
        total_likes = sum(v.get("diggCount", 0) for v in items)

        return (
            f"Audience Estimation for @{username}:\n"
            f"Total Comments (last {len(items)} videos): {total_comments:,}\n"
            f"Total Views: {total_views:,}\n"
            f"Comment-to-View Ratio: {(total_comments / max(total_views, 1) * 100):.4f}%\n"
            f"Like-to-View Ratio: {(total_likes / max(total_views, 1) * 100):.2f}%\n"
            f"Note: Detailed demographics (age, gender, location) require TikTok Creator API access. "
            f"Use comment analysis and content themes to infer audience characteristics."
        )
    except Exception as e:
        return f"Error fetching demographics for @{username}: {e}"


def get_apify_fake_followers(username: str) -> str:
    """Detect fake followers by analyzing engagement patterns."""
    cache_key = f"fake_detection_{username}"
    try:
        # Get profile data
        profile_items = _run_actor(
            "clockworks/tiktok-profile-scraper",
            {"profiles": [username], "resultsPerPage": 1},
            f"profile_{username}",
        )
        # Get video data
        video_items = _run_actor(
            "clockworks/tiktok-scraper",
            {"profiles": [username], "resultsPerPage": 30, "shouldDownloadVideos": False},
            f"engagement_{username}",
        )

        if not profile_items or not video_items:
            return f"Insufficient data for fake follower analysis of @{username}"

        followers = profile_items[0].get("authorMeta", profile_items[0]).get("fans", 0)
        total_views = sum(v.get("playCount", 0) for v in video_items)
        total_likes = sum(v.get("diggCount", 0) for v in video_items)
        total_comments = sum(v.get("commentCount", 0) for v in video_items)
        video_count = len(video_items)

        avg_views = total_views / max(video_count, 1)
        avg_likes = total_likes / max(video_count, 1)
        avg_comments = total_comments / max(video_count, 1)
        engagement_rate = (avg_likes + avg_comments) / max(avg_views, 1) * 100
        view_to_follower = avg_views / max(followers, 1) * 100

        # Heuristic signals
        signals = []
        if followers > 10000 and engagement_rate < 0.5:
            signals.append("LOW ENGAGEMENT: High followers but very low engagement rate")
        if view_to_follower < 1:
            signals.append("LOW REACH: Average views are less than 1% of follower count")
        if followers > 50000 and avg_comments < 5:
            signals.append("LOW COMMENTS: Very few comments relative to follower count")
        if not signals:
            signals.append("No major anomalies detected")

        return (
            f"Fake Follower Analysis for @{username}:\n"
            f"Followers: {followers:,}\n"
            f"Avg Views/Video: {avg_views:,.0f}\n"
            f"Avg Likes/Video: {avg_likes:,.0f}\n"
            f"Engagement Rate: {engagement_rate:.2f}%\n"
            f"View-to-Follower Ratio: {view_to_follower:.1f}%\n\n"
            f"Anomaly Signals:\n" + "\n".join(f"  - {s}" for s in signals)
        )
    except Exception as e:
        return f"Error analyzing fake followers for @{username}: {e}"


def get_apify_ecommerce_history(username: str) -> str:
    """Detect past brand collaborations and product mentions."""
    cache_key = f"ecommerce_{username}"
    try:
        items = _run_actor(
            "clockworks/tiktok-scraper",
            {"profiles": [username], "resultsPerPage": 30, "shouldDownloadVideos": False},
            cache_key,
        )
        if not items:
            return f"No video data found for @{username}"

        commerce_signals = []
        ad_keywords = ["#ad", "#sponsored", "#gifted", "#collab", "#partnership",
                       "#tiktokshop", "#affiliate", "link in bio", "use my code",
                       "#iklan", "#kerjasama"]  # Include Malay terms

        for video in items:
            text = (video.get("text", "") or "").lower()
            hashtags = [f"#{h.get('name', '').lower()}" for h in video.get("hashtags", [])]
            all_text = text + " " + " ".join(hashtags)

            matched = [kw for kw in ad_keywords if kw in all_text]
            if matched:
                commerce_signals.append({
                    "caption": video.get("text", "")[:100],
                    "signals": matched,
                    "views": video.get("playCount", 0),
                })

        lines = [f"E-commerce History for @{username}:\n"]
        lines.append(f"Videos analyzed: {len(items)}")
        lines.append(f"Commerce-related videos found: {len(commerce_signals)}\n")

        if commerce_signals:
            for i, sig in enumerate(commerce_signals[:10], 1):
                lines.append(f"  {i}. [{', '.join(sig['signals'])}] Views: {sig['views']:,}")
                lines.append(f"     Caption: {sig['caption']}")
        else:
            lines.append("  No clear sponsored/commerce content detected.")

        return "\n".join(lines)
    except Exception as e:
        return f"Error analyzing e-commerce history for @{username}: {e}"


def get_apify_competitor_pricing(username: str) -> str:
    """Research pricing of comparable influencers."""
    # This would ideally query a pricing database; for now provide market context
    cache_key = f"pricing_{username}"
    try:
        profile_items = _run_actor(
            "clockworks/tiktok-profile-scraper",
            {"profiles": [username], "resultsPerPage": 1},
            f"profile_{username}",
        )

        if not profile_items:
            return f"No profile data for @{username}"

        followers = profile_items[0].get("authorMeta", profile_items[0]).get("fans", 0)

        config = get_config()
        from influenceragents.default_config import MARKET_CONFIGS
        market = config.get("target_market", "MY")
        market_config = MARKET_CONFIGS.get(market, MARKET_CONFIGS["MY"])
        tiers = market_config["commission_tiers"]
        symbol = market_config["currency_symbol"]

        if followers >= 1000000:
            tier = "T0"
        elif followers >= 500000:
            tier = "T1"
        elif followers >= 100000:
            tier = "T2"
        else:
            tier = "T3"

        tier_info = tiers[tier]

        return (
            f"Pricing Estimation for @{username} ({followers:,} followers):\n"
            f"Estimated Tier: {tier}\n"
            f"Market Rate Range: {tier_info['label']}\n"
            f"Market: {market}\n\n"
            f"Reference Tiers ({symbol}):\n"
            f"  T0 (1M+ followers): {tiers['T0']['label']}\n"
            f"  T1 (500K-1M followers): {tiers['T1']['label']}\n"
            f"  T2 (100K-500K followers): {tiers['T2']['label']}\n"
            f"  T3 (<100K followers): {tiers['T3']['label']}\n"
            f"\nNote: Actual pricing depends on engagement rate, content quality, and niche."
        )
    except Exception as e:
        return f"Error researching pricing for @{username}: {e}"


def get_apify_tiktok_shop_data(username: str) -> str:
    """Retrieve TikTok Shop带货商品列表 via EchoTik API."""
    import requests as _requests

    cache_key = f"echotik_shop_{username}"
    cached = _load_cache(cache_key)
    if cached is not None:
        products = cached
    else:
        # 从已缓存的 profile 获取 user_id
        try:
            profile_items = _run_actor(
                "clockworks/tiktok-profile-scraper",
                {"profiles": [username], "resultsPerPage": 1},
                f"profile_{username}",
            )
        except Exception as e:
            return f"Error fetching profile for @{username}: {e}"

        if not profile_items:
            return f"No profile data found for @{username}, cannot fetch TikTok Shop data."

        meta = profile_items[0].get("authorMeta", profile_items[0])
        user_id = str(meta.get("id", ""))
        if not user_id:
            return f"User ID not available for @{username}, cannot fetch TikTok Shop data."

        base_url = os.environ.get("ECHOTIK_BASE_URL", "https://open.echotik.live")
        echotik_user = os.environ.get("ECHOTIK_USERNAME", "")
        echotik_pass = os.environ.get("ECHOTIK_PASSWORD", "")
        if not echotik_user or not echotik_pass:
            return (
                f"EchoTik credentials not configured. "
                f"Set ECHOTIK_USERNAME and ECHOTIK_PASSWORD in environment."
            )

        try:
            resp = _requests.get(
                f"{base_url}/api/v3/echotik/influencer/product/list",
                params={
                    "user_id": user_id,
                    "page_num": 1,
                    "page_size": 10,
                    "influencer_product_sort_field": 1,  # 按总销量排序
                    "sort_type": 1,  # desc
                },
                auth=(echotik_user, echotik_pass),
                timeout=30,
            )
            resp.raise_for_status()
        except Exception as e:
            return f"Error calling EchoTik API for @{username}: {e}"

        result = resp.json()
        if result.get("code") != 0:
            return f"EchoTik API error for @{username}: {result.get('message', 'Unknown error')}"

        products = result.get("data", [])
        _save_cache(cache_key, products)

    if not products:
        return f"TikTok Shop data for @{username}: 该达人无带货商品记录。"

    meta = None  # user_id already embedded in products
    uid = products[0].get("user_id", "N/A") if products else "N/A"
    lines = [
        f"TikTok Shop带货商品 — @{username} (User ID: {uid})",
        f"共 {len(products)} 件商品（按总销量降序）:",
        "",
    ]
    for i, p in enumerate(products, 1):
        lines.append(f"{i}. {p.get('product_name', 'N/A')}")
        lines.append(f"   商品ID: {p.get('product_id', 'N/A')}")
        lines.append(f"   均价: {p.get('spu_avg_price', 'N/A')}")
        lines.append(f"   总销量: {p.get('total_sale_cnt', 0):,}")
        lines.append(f"   总销售额: {p.get('total_sale_gmv_amt', 0):,.2f}")
        lines.append(
            f"   直播带货: {p.get('total_live_cnt', 0)} 场, "
            f"直播销量: {p.get('total_live_sale_cnt', 0):,}"
        )
        lines.append(
            f"   视频带货: {p.get('total_video_cnt', 0)} 条, "
            f"视频销量: {p.get('total_video_sale_cnt', 0):,}"
        )
        lines.append("")
    return "\n".join(lines)
