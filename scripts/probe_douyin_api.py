import asyncio
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.async_api import async_playwright


STATE = Path("data/douyin_page_state.json")


def get_post_url():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    for url in state.get("requests_seen", []):
        if "/aweme/v1/web/aweme/post/" in url:
            return url
    for cap in state.get("captured", []):
        if "/aweme/v1/web/aweme/post/" in cap.get("url", ""):
            return cap["url"]
    raise SystemExit("No post URL found")


def mutate_url(url, **updates):
    parts = urlsplit(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    q.pop("a_bogus", None)
    q.pop("x-secsdk-web-signature", None)
    q.update({k: str(v) for k, v in updates.items()})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


async def main():
    base = get_post_url()
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(Path("data/browser_profile").resolve()),
            headless=True,
            viewport={"width": 1440, "height": 1200},
            locale="zh-CN",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://www.douyin.com/", wait_until="domcontentloaded")
        tests = [
            {},
            {"max_cursor": 1779818603000},
            {"time_list_query": 1779818603000, "max_cursor": 0},
            {"time_list_query": "2026·05", "max_cursor": 0},
            {"time_list_query": "2026-05", "max_cursor": 0},
            {"count": 50, "max_cursor": 0},
        ]
        results = []
        for i, upd in enumerate(tests):
            url = mutate_url(base, **upd)
            data = await page.evaluate(
                """async (url) => {
                    const res = await fetch(url, {credentials: 'include'});
                    const text = await res.text();
                    return {status: res.status, url: res.url, text};
                }""",
                url,
            )
            path = Path(f"data/probe_{i}.json")
            path.write_text(data["text"], encoding="utf-8")
            try:
                j = json.loads(data["text"]) if data["text"] else {}
                summary = {
                    "status_code": j.get("status_code"),
                    "count": len(j.get("aweme_list") or []),
                    "has_more": j.get("has_more"),
                    "not_login": bool(j.get("not_login_module")),
                    "time_list": j.get("time_list"),
                    "ids": [a.get("aweme_id") for a in (j.get("aweme_list") or [])],
                }
            except Exception:
                summary = {"raw": data["text"][:300]}
            results.append({"updates": upd, "http_status": data["status"], "path": str(path), "summary": summary})
        Path("data/probe_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
