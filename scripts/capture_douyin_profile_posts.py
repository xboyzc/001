import argparse
import asyncio
import json
import platform
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parents[1]
PROFILE = (ROOT / "data" / "browser_profile").resolve()
OUT = ROOT / "data" / "douyin_posts.json"
VISIBLE_OUT = ROOT / "data" / "douyin_visible_posts.json"
STATE = ROOT / "data" / "douyin_profile_capture_state.json"
CAPTURE_DIR = ROOT / "data" / "douyin_profile_capture"


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
        with urlopen(req, timeout=12) as resp:
            return resp.geturl() or url
    except Exception:
        return url


def extract_sec_uid(*urls):
    for url in urls:
        if not url:
            continue
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        for key in ("sec_uid", "sec_user_id"):
            value = (query.get(key) or [""])[0]
            if value:
                return value
        match = re.search(r"/user/([^/?#]+)", url)
        if match:
            return match.group(1)
    return ""


def best_url(obj):
    if not isinstance(obj, dict):
        return ""
    urls = obj.get("url_list") or []
    return urls[0] if urls else ""


def post_from_aweme(item):
    aweme_id = str(item.get("aweme_id") or "")
    video = item.get("video") or {}
    music = item.get("music") or {}
    images = item.get("images") or []
    raw = {}
    for key in (
        "author",
        "statistics",
        "item_title",
        "interaction_stickers",
        "text_extra",
        "video_text",
        "caption",
        "subtitle",
        "suggest_words",
    ):
        if key in item:
            raw[key] = item.get(key)
    return {
        "aweme_id": aweme_id,
        "desc": item.get("desc") or item.get("item_title") or "",
        "create_time": item.get("create_time"),
        "share_url": f"https://www.douyin.com/video/{aweme_id}",
        "duration_ms": video.get("duration"),
        "play_url": best_url(video.get("play_addr")),
        "download_url": best_url(video.get("download_addr")),
        "music_url": best_url(music.get("play_url")),
        "image_urls": [best_url(img) for img in images if isinstance(img, dict)],
        "raw_text_candidates": raw,
    }


def write_state(**kwargs):
    payload = {
        "capturedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        **kwargs,
    }
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


async def capture(profile_url, limit):
    original_url = extract_url(profile_url) or profile_url.strip()
    if not original_url:
        raise SystemExit("请提供抖音博主主页分享链接。")

    resolved = resolve_url(original_url)
    if "douyin.com" not in resolved:
        raise SystemExit("链接不是有效的抖音页面链接。")

    target_sec_uid = extract_sec_uid(resolved, original_url)
    app_url = f"https://www.douyin.com/user/{target_sec_uid}" if target_sec_uid else resolved
    app_fallback_error = ""
    swift_script = ROOT / "scripts" / "capture_douyin_app_profile_posts.swift"
    if platform.system() == "Darwin" and swift_script.exists():
        try:
            app_capture = subprocess.run(
                [
                    "/usr/bin/swift",
                    "scripts/capture_douyin_app_profile_posts.swift",
                    app_url,
                    "--limit",
                    str(limit),
                ],
                cwd=str(ROOT),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=45,
            )
            if app_capture.returncode == 0:
                app_state_path = ROOT / "data" / "douyin_app_profile_capture_state.json"
                try:
                    app_state = json.loads(app_state_path.read_text(encoding="utf-8"))
                except Exception:
                    app_state = {}
                write_state(
                    ok=True,
                    inputUrl=original_url,
                    resolvedUrl=resolved,
                    finalUrl=app_state.get("profileURL") or app_url,
                    title=app_state.get("authorName") or "",
                    targetSecUid=target_sec_uid,
                    capturedCount=app_state.get("capturedCount") or 0,
                    capturedIds=app_state.get("capturedIds") or [],
                    source="douyin_desktop_app_accessibility_profile",
                    message="已通过已登录抖音 App 抓取目标博主公开作品。",
                    appOutput=app_capture.stdout.strip().splitlines()[-20:],
                )
                print(app_capture.stdout.strip())
                return
            app_fallback_error = app_capture.stdout.strip()
        except Exception as exc:
            app_fallback_error = f"抖音 App 抓取不可用，已切换网页版抓取：{exc}"
    else:
        app_fallback_error = "当前系统不支持 macOS 抖音 App 辅助功能抓取，已切换网页版抓取。"

    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    for old in CAPTURE_DIR.glob("response_*.json"):
        old.unlink()

    captured_payloads = []
    response_meta = []

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(PROFILE),
            headless=True,
            viewport={"width": 1440, "height": 1300},
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
            if "/aweme/v1/web/aweme/post/" not in url:
                return
            try:
                ctype = response.headers.get("content-type", "")
                text = await response.text()
            except Exception:
                return
            if "aweme_list" not in text:
                return
            idx = len(response_meta) + 1
            path = CAPTURE_DIR / f"response_{idx:02d}.json"
            path.write_text(text, encoding="utf-8")
            response_meta.append({"url": url, "status": response.status, "path": str(path), "content_type": ctype})
            try:
                captured_payloads.append(json.loads(text))
            except json.JSONDecodeError:
                pass

        page.on("response", on_response)
        await page.goto(resolved, wait_until="domcontentloaded", timeout=70000)
        await page.wait_for_timeout(6000)

        stable_rounds = 0
        last_ids = set()
        page_text = ""
        html = ""
        max_rounds = 36 if limit > 60 else 24
        for _ in range(max_rounds):
            try:
                page_text = await page.locator("body").inner_text(timeout=6000)
                html = await page.content()
            except Exception:
                page_text = ""
                html = ""
            ids = set(re.findall(r"/video/(\d{16,})", html + "\n" + page_text))
            ids |= {
                str(item.get("aweme_id") or "")
                for payload in captured_payloads
                for item in payload.get("aweme_list", [])
                if isinstance(payload, dict)
            }
            ids.discard("")
            if len(ids) >= limit:
                break
            stable_rounds = stable_rounds + 1 if ids == last_ids else 0
            if stable_rounds >= 6 and ids:
                break
            last_ids = ids
            await page.mouse.wheel(0, 2200)
            await page.wait_for_timeout(1800)

        final_url = page.url
        title = await page.title()
        await context.close()

    target_sec_uid = extract_sec_uid(resolved, final_url)
    posts = []
    seen = set()
    rejected = []
    for payload in captured_payloads:
        if not isinstance(payload, dict):
            continue
        for item in payload.get("aweme_list", []):
            if not isinstance(item, dict):
                continue
            aweme_id = str(item.get("aweme_id") or "")
            if not aweme_id or aweme_id in seen:
                continue
            author = item.get("author") or {}
            item_sec_uid = str(author.get("sec_uid") or "")
            if target_sec_uid and item_sec_uid and item_sec_uid != target_sec_uid:
                rejected.append(
                    {
                        "aweme_id": aweme_id,
                        "nickname": author.get("nickname") or "",
                        "sec_uid": item_sec_uid,
                    }
                )
                continue
            if target_sec_uid and not item_sec_uid:
                rejected.append({"aweme_id": aweme_id, "reason": "missing_author_sec_uid"})
                continue
            seen.add(aweme_id)
            posts.append(post_from_aweme(item))

    if not posts:
        write_state(
            ok=False,
            inputUrl=original_url,
            resolvedUrl=resolved,
            finalUrl=final_url if "final_url" in locals() else resolved,
            title=title if "title" in locals() else "",
            targetSecUid=target_sec_uid,
            capturedCount=0,
            rejectedCount=len(rejected),
            rejected=rejected[:20],
            appFallbackError=app_fallback_error,
            message="没有抓到已通过作者归属校验的公开作品。为避免误抓推荐流，未更新作品库。请确认主页作品公开可见，或登录后重试。",
            responses=response_meta,
        )
        raise SystemExit("没有抓到已通过作者归属校验的公开作品。为避免误抓推荐流，未更新作品库。")

    posts = posts[:limit]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(posts, ensure_ascii=False, indent=2)
    OUT.write_text(text, encoding="utf-8")
    VISIBLE_OUT.write_text(text, encoding="utf-8")
    write_state(
        ok=True,
        inputUrl=original_url,
        resolvedUrl=resolved,
        finalUrl=final_url,
        title=title,
        targetSecUid=target_sec_uid,
        capturedCount=len(posts),
        capturedIds=[p["aweme_id"] for p in posts],
        rejectedCount=len(rejected),
        message="已按博主主页公开展示作品抓取，并通过作者归属校验后更新作品库。",
        responses=response_meta[-20:],
    )
    print(f"Wrote {len(posts)} profile posts to {VISIBLE_OUT}")
    print(f"Profile: {title} {final_url}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="抖音博主主页分享链接，也支持包含链接的一整段分享文案")
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()
    asyncio.run(capture(args.url, max(1, args.limit)))


if __name__ == "__main__":
    main()
