import json
import re
from pathlib import Path


CAPTURE_DIR = Path("data/douyin_capture")
OUT = Path("data/douyin_posts.json")
VISIBLE_OUT = Path("data/douyin_visible_posts.json")
PAGE_STATE = Path("data/douyin_page_state.json")


def best_url(url_obj):
    if not isinstance(url_obj, dict):
        return ""
    urls = url_obj.get("url_list") or []
    return urls[0] if urls else ""


def main():
    payloads = []
    for path in sorted(CAPTURE_DIR.glob("response_*.json")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if '"aweme_list"' in text and text.strip():
            try:
                payloads.append(json.loads(text))
            except json.JSONDecodeError:
                continue
    if not payloads:
        if PAGE_STATE.exists():
            try:
                page_state = json.loads(PAGE_STATE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                page_state = {}
            if page_state.get("error"):
                raise SystemExit(f"No fresh aweme_list response found: {page_state['error']}")
        if OUT.exists():
            VISIBLE_OUT.write_text(OUT.read_text(encoding="utf-8"), encoding="utf-8")
            print("No fresh aweme_list response found; reused existing post list.")
            return
        raise SystemExit("No aweme_list response found")

    posts = []
    seen_payload_ids = set()
    for payload in payloads:
        for item in payload.get("aweme_list", []):
            aweme_id = str(item.get("aweme_id") or "")
            if not aweme_id or aweme_id in seen_payload_ids:
                continue
            seen_payload_ids.add(aweme_id)
            video = item.get("video") or {}
            music = item.get("music") or {}
            images = item.get("images") or []
            post = {
                "aweme_id": aweme_id,
                "desc": item.get("desc") or "",
                "create_time": item.get("create_time"),
                "share_url": f"https://www.douyin.com/video/{item.get('aweme_id')}",
                "duration_ms": video.get("duration"),
                "play_url": best_url(video.get("play_addr")),
                "download_url": best_url(video.get("download_addr")),
                "music_url": best_url(music.get("play_url")),
                "image_urls": [best_url(i.get("url_list") if False else i) for i in images],
                "raw_text_candidates": {},
            }
            for key in (
                "item_title",
                "interaction_stickers",
                "text_extra",
                "video_text",
                "voice_modify_id_list",
                "geofencing",
                "desc_language",
                "caption",
                "subtitle",
            ):
                if key in item:
                    post["raw_text_candidates"][key] = item.get(key)
            posts.append(post)
    if PAGE_STATE.exists():
        try:
            page_state = json.loads(PAGE_STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            page_state = {}
        page_ids = set(page_state.get("html_ids") or [])
        page_text = PAGE_STATE.read_text(encoding="utf-8", errors="ignore")
        page_ids |= set(re.findall(r"https?://www\\.douyin\\.com/video/(\\d+)", page_text))
        known = {str(p.get("aweme_id") or "") for p in posts}
        for aweme_id in sorted(page_ids - known, reverse=True):
            posts.append({
                "aweme_id": aweme_id,
                "desc": "",
                "create_time": None,
                "share_url": f"https://www.douyin.com/video/{aweme_id}",
                "duration_ms": None,
                "play_url": "",
                "download_url": "",
                "music_url": "",
                "image_urls": [],
                "raw_text_candidates": {"source": "page_dom_fallback"},
            })

    text = json.dumps(posts, ensure_ascii=False, indent=2)
    existing = []
    for existing_path in (VISIBLE_OUT, OUT):
        if existing_path.exists():
            try:
                existing.extend(json.loads(existing_path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass
    merged = []
    seen = set()
    for post in [*posts, *existing]:
        aweme_id = str(post.get("aweme_id") or "")
        if not aweme_id or aweme_id in seen:
            continue
        seen.add(aweme_id)
        merged.append(post)
    text = json.dumps(merged, ensure_ascii=False, indent=2)
    OUT.write_text(text, encoding="utf-8")
    VISIBLE_OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {len(merged)} posts to {OUT}")
    print(f"Wrote {len(merged)} posts to {VISIBLE_OUT}")
    for i, p in enumerate(posts, 1):
        print(i, p["aweme_id"], p["desc"][:80], "play", bool(p["play_url"]), "music", bool(p["music_url"]))


if __name__ == "__main__":
    main()
