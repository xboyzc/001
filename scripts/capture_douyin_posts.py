import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright


USER_URL = "https://www.douyin.com/user/MS4wLjABAAAAQmGbiT0FbECpVmqHhMABtBg7jb28ndamY5R3YMGa6xU"
OUT = Path("data/douyin_capture")
PROFILE = Path("data/browser_profile").resolve()
PAGE_STATE = Path("data/douyin_page_state.json")


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("response_*.json"):
        old.unlink()
    captured = []

    async with async_playwright() as p:
        if PROFILE.exists():
            context = await p.chromium.launch_persistent_context(
                str(PROFILE),
                headless=True,
                viewport={"width": 1440, "height": 1200},
                locale="zh-CN",
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            )
            browser = None
        else:
            browser = await p.chromium.launch(headless=True)
            storage_state = "data/douyin_storage_state.json"
            context = await browser.new_context(
            viewport={"width": 1440, "height": 1200},
            locale="zh-CN",
            storage_state=storage_state if Path(storage_state).exists() else None,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            )
        page = context.pages[0] if context.pages else await context.new_page()

        requests_seen = []

        def on_request(request):
            url = request.url
            if "aweme" in url or "user" in url or "post" in url:
                requests_seen.append(url)

        async def on_response(response):
            url = response.url
            is_post = "/aweme/v1/web/aweme/post/" in url
            if "aweme" not in url and "post" not in url and "douyin" not in url:
                return
            try:
                ctype = response.headers.get("content-type", "")
                if not is_post and "json" not in ctype and "text" not in ctype:
                    return
                text = await response.text()
                if is_post and not text.strip():
                    retry = await context.request.get(url, headers={"referer": USER_URL})
                    text = await retry.text()
                    ctype = retry.headers.get("content-type", ctype)
            except Exception:
                return
            if is_post or "aweme_list" in text or "aweme_id" in text or "status_code" in text:
                idx = len(captured) + 1
                path = OUT / f"response_{idx:02d}.json"
                path.write_text(text, encoding="utf-8")
                captured.append({
                    "url": url,
                    "path": str(path),
                    "status": response.status,
                    "content_type": ctype,
                })

        page.on("request", on_request)
        page.on("response", on_response)
        await page.goto(USER_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(12000)
        stable_rounds = 0
        last_height = 0
        last_count = 0
        for _ in range(28):
            page_text = await page.locator("body").inner_text(timeout=5000)
            visible_count = len(set(re.findall(r"/video/(\d+)", page_text)))
            height = await page.evaluate("document.documentElement.scrollHeight")
            if visible_count == last_count and height == last_height:
                stable_rounds += 1
            else:
                stable_rounds = 0
            last_count = visible_count
            last_height = height
            if stable_rounds >= 5 and captured:
                break
            await page.mouse.wheel(0, 1800)
            await page.wait_for_timeout(1800)

        state = {
            "url": page.url,
            "title": await page.title(),
            "text": (await page.locator("body").inner_text(timeout=5000))[:4000],
            "html_ids": sorted(set(re.findall(r"/video/(\d+)", await page.content()))),
            "captured": captured,
            "requests_seen": requests_seen,
        }
        if "扫码登录" in state["text"] or "验证码登录" in state["text"]:
            state["error"] = "当前抓取浏览器未登录抖音，无法保证抓取完整作品。"
        if "服务异常" in state["text"]:
            state["error"] = "抖音作品列表服务异常，未返回完整作品列表。"
        PAGE_STATE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if state.get("error"):
            raise SystemExit(state["error"])
        await context.close()
        if browser:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
