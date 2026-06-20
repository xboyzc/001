import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


PROFILE = Path("data/browser_profile").resolve()
USER_URL = "https://www.douyin.com/user/MS4wLjABAAAAQmGbiT0FbECpVmqHhMABtBg7jb28ndamY5R3YMGa6xU"


async def main():
    PROFILE.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(PROFILE),
            headless=False,
            viewport={"width": 1440, "height": 1100},
            locale="zh-CN",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(USER_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        try:
            await page.get_by_text("登录", exact=True).first.click(timeout=5000)
        except Exception:
            pass
        print("Opened Douyin login window. Scan the QR code if prompted.")
        try:
            await page.wait_for_function(
                "() => !document.body.innerText.includes('扫码登录') "
                "&& !document.body.innerText.includes('请输入手机号') "
                "&& !document.body.innerText.includes('登录后免费') "
                "&& !document.body.innerText.match(/\\n登录\\n/)",
                timeout=180000,
            )
            print("Login prompt disappeared.")
        except Exception:
            print("Timed out waiting for login; leaving profile saved.")
        await context.storage_state(path="data/douyin_storage_state.json")
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
