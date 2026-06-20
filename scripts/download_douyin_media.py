import json
from pathlib import Path

import requests


DETAILS = Path("data/douyin_details_merged.json")
OUT = Path("data/tmp_media")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    items = json.loads(DETAILS.read_text(encoding="utf-8"))
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "referer": "https://www.douyin.com/",
    }
    for item in items:
        url = item.get("play_url")
        if not url:
            print(item["index"], item["aweme_id"], "SKIP no play_url")
            continue
        path = OUT / f"{item['index']:02d}_{item['aweme_id']}.mp4"
        if path.exists() and path.stat().st_size > 100000:
            print(item["index"], item["aweme_id"], "EXISTS", path.stat().st_size)
            item["media_path"] = str(path)
            continue
        try:
            with requests.get(url, headers=headers, stream=True, timeout=60) as res:
                res.raise_for_status()
                with path.open("wb") as f:
                    for chunk in res.iter_content(chunk_size=1024 * 512):
                        if chunk:
                            f.write(chunk)
        except requests.RequestException as exc:
            item.pop("media_path", None)
            item["media_download_status"] = "failed"
            item["media_download_error"] = str(exc)
            status = getattr(getattr(exc, "response", None), "status_code", "")
            reason = f"HTTP {status}" if status else exc.__class__.__name__
            print(item["index"], item["aweme_id"], "SKIP download failed", reason)
            if path.exists() and path.stat().st_size < 100000:
                path.unlink()
            continue
        item["media_path"] = str(path)
        item["media_download_status"] = "done"
        print(item["index"], item["aweme_id"], "DOWNLOADED", path.stat().st_size)
    DETAILS.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
