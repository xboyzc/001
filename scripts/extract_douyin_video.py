import argparse
import asyncio
import json
import re
import time
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parents[1]
PROFILE = (ROOT / "data" / "browser_profile").resolve()


def extract_url(text):
    match = re.search(r"https?://[^\s，。；,;]+", text or "")
    if not match:
        return ""
    return match.group(0).rstrip(")）]")


def resolve_url(url):
    if not url:
        return ""
    try:
        req = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                )
            },
        )
        with urlopen(req, timeout=10) as resp:
            return resp.geturl() or url
    except Exception:
        return url


def best_url(obj):
    if not isinstance(obj, dict):
        return ""
    urls = obj.get("url_list") or []
    return urls[0] if urls else ""


def complete_cover_url(video):
    if not isinstance(video, dict):
        return ""
    for key in ("cover_original_scale", "origin_cover", "cover", "dynamic_cover"):
        url = best_url(video.get(key))
        if url:
            return url
    return ""


def complete_play_url(video):
    if not isinstance(video, dict):
        return ""
    for key in ("play_addr", "download_addr"):
        url = best_url(video.get(key))
        if url:
            return url
    for item in video.get("bit_rate") or []:
        url = best_url((item or {}).get("play_addr"))
        if url:
            return url
    return ""


def pick_count(stats, key):
    try:
        return int((stats or {}).get(key) or 0)
    except (TypeError, ValueError):
        return 0


def normalize(item, original_url, resolved_url):
    aweme_id = str(item.get("aweme_id") or item.get("group_id") or "")
    video = item.get("video") or {}
    stats = item.get("statistics") or {}
    title = item.get("item_title") or item.get("preview_title") or ""
    desc = item.get("desc") or ""
    caption = item.get("caption") or ""
    text = caption or desc or title
    cover_url = complete_cover_url(video)
    play_url = complete_play_url(video)
    clean_title = re.sub(r"#\S+", "", title or desc or f"抖音作品 {aweme_id}").strip()
    has_real_text = bool((caption or desc or title or "").strip())
    return {
        "ok": bool(aweme_id and has_real_text),
        "source": "Playwright 已从视频链接提取作品详情",
        "url": f"https://www.douyin.com/video/{aweme_id}" if aweme_id else resolved_url or original_url,
        "resolvedUrl": resolved_url or original_url,
        "awemeId": aweme_id,
        "title": clean_title or f"抖音作品 {aweme_id}",
        "fullText": text,
        "transcriptPreview": text[:900],
        "stats": {
            "play": pick_count(stats, "play_count"),
            "likes": pick_count(stats, "digg_count"),
            "comments": pick_count(stats, "comment_count"),
            "collects": pick_count(stats, "collect_count"),
            "shares": pick_count(stats, "share_count"),
        },
        "coverSource": cover_url,
        "playUrl": play_url,
        "cover": ["对照原封面", "提炼痛点大字", "重做三行标题"],
        **({} if has_real_text else {"message": "已打开视频页并拿到封面，但该链接没有返回可分析的标题或文案。"}),
    }


async def extract_video(input_url):
    original_url = extract_url(input_url) or input_url.strip()
    if not original_url:
        return {"ok": False, "message": "没有识别到视频链接。"}

    resolved_url = resolve_url(original_url)
    payloads = []

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(PROFILE),
            headless=True,
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        for old_page in list(context.pages):
            try:
                await old_page.close()
            except Exception:
                pass
        page = await context.new_page()

        async def on_response(response):
            url = response.url
            if not any(key in url for key in ("/aweme/v1/web/aweme/detail/", "/aweme/v1/web/aweme/post/")):
                return
            try:
                text = await response.text()
            except Exception:
                return
            if "aweme_detail" not in text and "aweme_list" not in text:
                return
            try:
                payloads.append(json.loads(text))
            except json.JSONDecodeError:
                return

        page.on("response", on_response)
        await page.goto(resolved_url or original_url, wait_until="domcontentloaded", timeout=70000)
        await page.wait_for_timeout(7000)
        html = ""
        try:
            html = await page.content()
        except Exception:
            html = ""
        final_url = page.url
        await context.close()

    for payload in payloads:
        if isinstance(payload, dict) and isinstance(payload.get("aweme_detail"), dict):
            return normalize(payload["aweme_detail"], original_url, final_url or resolved_url)
        if isinstance(payload, dict):
            for item in payload.get("aweme_list") or []:
                if isinstance(item, dict):
                    return normalize(item, original_url, final_url or resolved_url)

    # A small last resort for pages that embed JSON but do not expose the network
    # response to Playwright in time.
    match = re.search(r'"aweme_id"\s*:\s*"?(?P<id>\d{16,})"?', html)
    if match:
        return {
            "ok": False,
            "awemeId": match.group("id"),
            "resolvedUrl": final_url or resolved_url,
            "message": "页面打开成功，但没有捕获到包含标题、文案、封面的详情数据。",
        }
    return {
        "ok": False,
        "resolvedUrl": final_url or resolved_url,
        "message": "没有从该公开视频链接捕获到详情数据。请复制单条视频分享链接，不要复制主页或合集链接。",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    result = asyncio.run(extract_video(args.url))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
