import json
import re
import time
from pathlib import Path

import requests


POSTS = Path("data/douyin_visible_posts.json")
OUT = Path("data/douyin_details")
MERGED = Path("data/douyin_details_merged.json")
TRANSCRIPTS = Path("output/transcripts")


def pick_url(obj):
    if not isinstance(obj, dict):
        return ""
    urls = obj.get("url_list") or []
    return urls[0] if urls else ""


def complete_cover_url(video):
    if not isinstance(video, dict):
        return ""
    for key in ("cover_original_scale", "origin_cover", "cover", "dynamic_cover"):
        url = pick_url(video.get(key))
        if url:
            return url
    return ""


def pick_count(stats, key):
    try:
        return int((stats or {}).get(key) or 0)
    except (TypeError, ValueError):
        return 0


def post_count(post, key):
    stats = post.get("stats") or {}
    return pick_count(stats, key)


def clean_platform_suffix(text):
    return re.sub(r"……版本过低，升级后可展示全部信息", "", text or "").strip()


def parse_count_token(token):
    token = (token or "").strip()
    if not token:
        return 0
    if token.endswith("万"):
        try:
            return int(float(token[:-1]) * 10000)
        except ValueError:
            return 0
    try:
        return int(token)
    except ValueError:
        return 0


def split_app_card_text(raw):
    text = (raw or "").strip()
    for prefix in ("妮可清醒局：",):
        if text.startswith(prefix):
            text = text[len(prefix):]
    text = re.sub(r"Tag:\s*置顶\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    match = re.match(r"(.+?)\s+(\d+(?:\.\d+)?万|\d{1,12})\s+(.+)$", text)
    if match:
        left = match.group(1).strip()
        count = parse_count_token(match.group(2))
        right = match.group(3).strip()
        left_prefix = left[: min(18, len(left))]
        right_prefix = right[: min(18, len(right))]
        if left_prefix and (right.startswith(left_prefix) or left.startswith(right_prefix)):
            return left, count
    return text, 0


def parse_app_play_count(post):
    direct = post_count(post, "play_count")
    if direct:
        return direct
    raw = ((post.get("raw_text_candidates") or {}).get("app_description") or "").strip()
    desc = clean_platform_suffix(post.get("desc") or "")
    if not raw or len(desc) < 8:
        return 0
    _, split_count = split_app_card_text(raw)
    if split_count:
        return split_count
    prefix = re.escape(desc[: min(18, len(desc))])
    patterns = [
        re.escape(desc) + r"\s+(\d+(?:\.\d+)?万|\d{1,12})\s+" + prefix,
        re.escape(desc) + r"\s+(\d+(?:\.\d+)?万|\d{1,12})\s*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw)
        if match:
            return parse_count_token(match.group(1))
    return 0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    posts = json.loads(POSTS.read_text(encoding="utf-8"))
    existing_by_id = {}
    if MERGED.exists():
        try:
            existing_by_id = {
                str(item.get("aweme_id")): item
                for item in json.loads(MERGED.read_text(encoding="utf-8"))
            }
        except json.JSONDecodeError:
            existing_by_id = {}
    transcript_by_id = {}
    if TRANSCRIPTS.exists():
        for transcript_path in TRANSCRIPTS.glob("*.txt"):
            parts = transcript_path.stem.split("_", 1)
            if len(parts) != 2:
                continue
            text = transcript_path.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                transcript_by_id[parts[1]] = {
                    "transcript": text,
                    "transcript_status": "done",
                    "transcript_path": str(transcript_path),
                }
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "referer": "https://www.douyin.com/",
    }
    merged = []
    for idx, post in enumerate(posts, 1):
        aweme_id = post["aweme_id"]
        app_desc, _ = split_app_card_text((post.get("raw_text_candidates") or {}).get("app_description") or "")
        url = (
            "https://www.douyin.com/aweme/v1/web/aweme/detail/"
            f"?aweme_id={aweme_id}&aid=6383&device_platform=webapp"
        )
        path = OUT / f"{idx:02d}_{aweme_id}.json"
        if path.exists() and path.stat().st_size:
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            res = requests.get(url, headers=headers, timeout=30)
            res.raise_for_status()
            data = res.json()
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(0.3)
        item = data.get("aweme_detail") or {}
        video = item.get("video") or {}
        music = item.get("music") or {}
        stats = item.get("statistics") or {}
        app_play_count = parse_app_play_count(post)
        cover_url = complete_cover_url(video)
        candidates = {}
        for key in [
            "desc",
            "item_title",
            "caption",
            "video_text",
            "interaction_stickers",
            "text_extra",
            "original_images",
            "images",
            "risk_infos",
            "suggest_words",
            "geofencing",
            "video_labels",
            "video_tag",
            "voice_modify_id_list",
        ]:
            if key in item:
                candidates[key] = item.get(key)
        previous = existing_by_id.get(str(aweme_id), {})
        row = {
            "index": idx,
            "aweme_id": aweme_id,
            "share_url": f"https://www.douyin.com/video/{aweme_id}",
            "desc": item.get("desc") or app_desc or post.get("desc", ""),
            "caption": item.get("caption") or "",
            "item_title": item.get("item_title") or item.get("preview_title") or "",
            "create_time": item.get("create_time"),
            "duration_ms": video.get("duration"),
            "play_url": pick_url(video.get("play_addr")),
            "download_url": pick_url(video.get("download_addr")),
            "music_url": pick_url(music.get("play_url")),
            "cover_url": cover_url,
            "stats": {
                "play_count": pick_count(stats, "play_count") or app_play_count,
                "digg_count": pick_count(stats, "digg_count"),
                "comment_count": pick_count(stats, "comment_count"),
                "collect_count": pick_count(stats, "collect_count"),
                "share_count": pick_count(stats, "share_count"),
            },
            "detail_path": str(path),
            "text_candidates": candidates,
        }
        transcript = transcript_by_id.get(str(aweme_id), {})
        for key in ["transcript", "transcript_status", "transcript_path"]:
            if previous.get(key):
                row[key] = previous[key]
            elif transcript.get(key):
                row[key] = transcript[key]
        if not row.get("transcript"):
            fallback_text = row.get("caption") or row.get("desc") or ""
            if fallback_text:
                row["transcript"] = fallback_text
                row["transcript_status"] = "caption" if row.get("caption") else "desc"
        merged.append(row)
        print(idx, aweme_id, "play", bool(merged[-1]["play_url"]), "music", bool(merged[-1]["music_url"]), merged[-1]["desc"][:80])
    MERGED.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {MERGED}")


if __name__ == "__main__":
    main()
