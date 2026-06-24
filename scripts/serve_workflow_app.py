import json
import random
import re
import secrets
import subprocess
import sys
import threading
import time
from html import unescape
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import TCPServer
from urllib.parse import parse_qs, quote, urljoin, urlparse
from urllib.request import Request, urlopen

from build_strategy_dashboard import DATA_PATH, build_rows


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "output" / "workflow_app"
VIRAL_COVER_DIR = APP_DIR / "viral_covers"
VIRAL_TRANSCRIPT_DIR = ROOT / "data" / "viral_transcripts"
VIRAL_MEDIA_DIR = ROOT / "data" / "tmp_viral_media"
CONFIG_PATH = ROOT / "data" / "workflow_server_config.json"
HOST = "0.0.0.0"
PORT = 8787


SOURCE_URL = "https://www.designkit.cn/topic/explosive-vibrato-short-video-cover"
ALLOWED_IMAGE_HOSTS = {
    "xiuxiu-pro.meitudata.com",
    "xiuxiupro-material-center.meitudata.com",
}

REFRESH_LOCK = threading.Lock()
REFRESH_STATE = {
    "running": False,
    "ok": None,
    "step": "待命",
    "message": "粘贴抖音博主主页分享链接后，会自动抓取公开作品、下载新增视频、转写并重建工作台。",
    "startedAt": "",
    "finishedAt": "",
    "logs": [],
    "mode": "app",
    "sourceUrl": "",
}


def load_config():
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    if not data.get("access_key"):
        data["access_key"] = secrets.token_urlsafe(18)
        CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


CONFIG = load_config()


class FastThreadingHTTPServer(ThreadingHTTPServer):
    def server_bind(self):
        # ThreadingHTTPServer normally calls socket.getfqdn(), which can block
        # on reverse DNS for 0.0.0.0 on some local networks.
        TCPServer.server_bind(self)
        self.server_name = HOST
        self.server_port = self.server_address[1]


def is_local_client(address):
    host = (address or ("",))[0]
    return host in {"127.0.0.1", "::1", "localhost"}


def authorized(path, headers, client_address):
    if is_local_client(client_address):
        return True
    parsed = urlparse(path)
    query_key = (parse_qs(parsed.query).get("key") or [""])[0]
    header_key = headers.get("X-Workflow-Key", "")
    return CONFIG["access_key"] in {query_key, header_key}


class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag != "img":
            return
        data = dict(attrs)
        src = data.get("src") or data.get("data-src") or data.get("data-original") or ""
        alt = data.get("alt") or data.get("title") or ""
        if src:
            self.images.append({"src": unescape(src), "alt": unescape(alt)})


def svg_data(title, sub, accent):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="960" viewBox="0 0 720 960">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#07101f"/><stop offset="1" stop-color="#18213b"/></linearGradient>
  <filter id="shadow"><feDropShadow dx="0" dy="12" stdDeviation="18" flood-color="#000" flood-opacity=".35"/></filter>
</defs>
<rect width="720" height="960" fill="url(#g)"/>
<rect x="54" y="68" width="612" height="824" rx="34" fill="#0d1424" stroke="{accent}" stroke-width="4"/>
<rect x="88" y="112" width="220" height="42" rx="21" fill="{accent}" opacity=".9"/>
<text x="108" y="141" fill="#fff" font-size="24" font-family="Arial, sans-serif" font-weight="700">爆款封面案例</text>
<text x="92" y="334" fill="#fff" font-size="72" font-family="Arial, sans-serif" font-weight="900" filter="url(#shadow)">{title}</text>
<text x="92" y="434" fill="#fff" font-size="72" font-family="Arial, sans-serif" font-weight="900" filter="url(#shadow)">{sub}</text>
<text x="92" y="540" fill="{accent}" font-size="46" font-family="Arial, sans-serif" font-weight="900">痛点 + 反常识 + 标签</text>
<rect x="92" y="670" width="536" height="3" fill="{accent}"/>
<text x="92" y="738" fill="#b9c6d6" font-size="30" font-family="Arial, sans-serif">大字、强冲突、少信息</text>
</svg>"""
    return "data:image/svg+xml;charset=utf-8," + quote(svg)


def fallback_examples(theme):
    base = [
        ("你越懂事", "越没人心疼", "#fb5f87", "真人口播"),
        ("别再讨好", "你不是来交房租的", "#f6c453", "口播干货"),
        ("太敏感不是错", "这是你的天赋", "#22d3ee", "真人讲述"),
        ("你追的不是他", "是不敢活的自己", "#a78bfa", "出镜口播"),
        ("别等准备好", "先开始再说", "#34d399", "老师口播"),
        ("把自己活回来", "从停止内耗开始", "#4f7bff", "人物封面"),
    ]
    random.shuffle(base)
    return [
        {
            "title": title,
            "subtitle": sub,
            "tag": tag,
            "image": svg_data(title, sub, color),
            "source": "本地真人口播版式",
            "sourceUrl": "",
            "pattern": "真人出镜口播：半身人物 + 大字冲突 + 栏目标签",
        }
        for title, sub, color, tag in base
    ]


def fetch_designkit_examples():
    req = Request(
        SOURCE_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(req, timeout=12) as resp:
        html = resp.read().decode("utf-8", "ignore")
    parser = ImageParser()
    parser.feed(html)
    examples = []
    seen = set()
    person_keywords = ("实景人物", "真人", "口播", "老师", "主播", "讲解", "人物")
    soft_person_keywords = ("实景风", "实景")
    exclude_keywords = ("插画", "卡通", "纯文字", "产品", "美妆", "口红", "旅游", "鞋服", "箱包", "电商", "保险", "穿搭", "宝妈", "剪辑", "APP")
    for item in parser.images:
        src = urljoin(SOURCE_URL, item["src"])
        host = urlparse(src).netloc
        alt = re.sub(r"\s+", " ", item["alt"]).strip()
        if host not in ALLOWED_IMAGE_HOSTS:
            continue
        if any(k in alt for k in exclude_keywords):
            continue
        has_person_signal = any(k in alt for k in person_keywords) or any(k in alt for k in soft_person_keywords)
        if not has_person_signal:
            continue
        clean_src = src.replace("&amp;", "&")
        if clean_src in seen:
            continue
        seen.add(clean_src)
        examples.append(
            {
                "title": alt[:28] or "热门封面模板",
                "subtitle": "真人出镜口播案例",
                "tag": "口播案例",
                "image": clean_src,
                "source": "美图设计室",
                "sourceUrl": SOURCE_URL,
                "pattern": "参考重点：真人半身/近景 + 大标题 + 强冲突 + 少文字",
            }
        )
    random.shuffle(examples)
    return examples[:9]


def cover_examples(theme):
    try:
        live = fetch_designkit_examples()
    except Exception:
        live = []
    examples = live + fallback_examples(theme)
    return {
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sourceNote": "只筛选真人出镜口播倾向的公开封面案例；网络不可用时显示本地口播版式。",
        "examples": examples[:9],
    }


DOUYIN_HOT_SEARCH_URLS = [
    "https://aweme.snssdk.com/aweme/v1/hot/search/list/?aid=1128&version_code=130200&device_platform=android",
    "https://aweme-hl.snssdk.com/aweme/v1/hot/search/list/?aid=1128&version_code=130200&device_platform=android",
    "https://aweme-lq.snssdk.com/aweme/v1/hot/search/list/?aid=1128&version_code=130200&device_platform=android",
]


def clean_hot_text(raw):
    text = unescape(str(raw or "")).strip()
    try:
        text = json.loads(f'"{text}"')
    except Exception:
        pass
    return re.sub(r"\s+", " ", text).strip()


def compact_hot_value(raw):
    try:
        value = int(float(raw))
    except Exception:
        return ""
    if value >= 100000000:
        return f"{value / 100000000:.1f}亿"
    if value >= 10000:
        return f"{value / 10000:.1f}万"
    return str(value)


def douyin_label_name(label):
    labels = {
        0: "热",
        1: "热",
        2: "新",
        3: "爆",
        4: "荐",
        5: "沸",
    }
    try:
        return labels.get(int(label), "")
    except Exception:
        return ""


def douyin_hot_lists(payload):
    data = payload.get("data") if isinstance(payload, dict) else None
    candidates = []
    if isinstance(data, dict):
        candidates.extend(data.get(key) for key in ("word_list", "trending_list", "recommend_list"))
    if isinstance(payload, dict):
        candidates.extend(payload.get(key) for key in ("word_list", "hot_search_list", "list"))
    return [item for group in candidates if isinstance(group, list) for item in group if isinstance(item, dict)]


def normalize_douyin_hot_item(item, idx):
    title = clean_hot_text(
        item.get("word")
        or item.get("sentence")
        or item.get("hot_word")
        or item.get("query")
        or item.get("title")
    )
    if not title:
        return None
    rank = item.get("position") or item.get("rank") or idx
    hot_value = item.get("hot_value") or item.get("hotValue") or item.get("view_count") or item.get("score")
    hot_value_text = compact_hot_value(hot_value)
    video_count = item.get("video_count") or item.get("discuss_video_count") or item.get("aweme_count") or ""
    label = douyin_label_name(item.get("label") or item.get("word_type"))
    cover = ""
    cover_info = item.get("word_cover") or item.get("cover") or {}
    if isinstance(cover_info, dict):
        cover_list = cover_info.get("url_list") or cover_info.get("urls") or []
        if cover_list:
            cover = cover_list[0]
    detail_parts = [f"抖音热榜第{rank}名"]
    if hot_value_text:
        detail_parts.append(f"热度{hot_value_text}")
    if video_count:
        detail_parts.append(f"相关视频/讨论约{video_count}条")
    if label:
        detail_parts.append(f"榜单标记「{label}」")
    summary = f"热搜词「{title}」；" + "，".join(detail_parts) + "。"
    return {
        "title": title,
        "summary": summary,
        "source": "抖音热搜",
        "sourceUrl": f"https://www.douyin.com/search/{quote(title)}",
        "rank": rank,
        "hotValue": hot_value or "",
        "hotValueText": hot_value_text,
        "videoCount": video_count,
        "label": label,
        "cover": cover,
        "angle": f"把抖音正在集中搜索的「{title}」转成用户当下关心的问题入口，再接到你的选题方向和痛点。",
    }


def fetch_douyin_hot_topics(limit=24):
    last_error = None
    for url in DOUYIN_HOT_SEARCH_URLS:
        req = Request(
            url,
            headers={
                "User-Agent": "okhttp3",
                "Accept": "application/json,text/plain,*/*",
                "Referer": "https://www.douyin.com/",
            },
        )
        try:
            with urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8", "ignore"))
        except Exception as exc:
            last_error = exc
            continue
        topics = []
        seen = set()
        for idx, item in enumerate(douyin_hot_lists(data), 1):
            topic = normalize_douyin_hot_item(item, idx)
            if not topic or topic["title"] in seen:
                continue
            seen.add(topic["title"])
            topics.append(topic)
            if len(topics) >= limit:
                break
        if topics:
            return topics
    if last_error:
        raise last_error
    return []


def fallback_douyin_hot_topics():
    fallback = [
        ("AI 工具进入日常办公", "抖音热点兜底", "用 AI 办公、智能体和效率工具做具体案例切入。"),
        ("高考查分与选择焦虑", "抖音热点兜底", "用升学选择、分数线和家庭决策讲规划与行动。"),
        ("普通人做个人品牌", "抖音热点兜底", "用个人品牌、信任内容和成交路径讲清楚普通人如何被看见。"),
        ("极端天气与生活规划", "抖音热点兜底", "用突发变化讲风险意识、提前准备和确定感。"),
        ("暑期出行与消费选择", "抖音热点兜底", "用出行、消费和避坑场景切入实际决策方法。"),
    ]
    return [
        {
            "title": title,
            "summary": summary,
            "source": source,
            "sourceUrl": "",
            "rank": idx,
            "hotValue": "",
            "hotValueText": "",
            "videoCount": "",
            "label": "",
            "cover": "",
            "angle": f"把「{title}」作为抖音热点方向入口，连接用户正在关心的现实问题。",
        }
        for idx, (title, source, summary) in enumerate(fallback, 1)
    ]


def hot_topics(theme="", pain=""):
    try:
        topics = fetch_douyin_hot_topics(24)
        source_note = "已读取抖音实时热搜；生成口播会引用热搜标题、排名、热度和讨论数据，再结合当前主题方向与用户痛点。"
    except Exception:
        topics = fallback_douyin_hot_topics()
        source_note = "抖音热搜读取失败，暂用本地抖音热点方向兜底；可点刷新或手动输入热点继续生成。"
    return {
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sourceNote": source_note,
        "topics": topics[:24],
    }


def read_json_body(handler):
    try:
        length = int(handler.headers.get("Content-Length", "0") or "0")
    except ValueError:
        length = 0
    if not length:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def extract_share_url(text):
    match = re.search(r"https?://[^\s，。；,;]+", text or "")
    if not match:
        return ""
    return match.group(0).rstrip(")）]}>\"'")


def resolve_douyin_url(url):
    url = extract_share_url(url) or (url or "").strip()
    if not url:
        return ""
    if "v.douyin.com" not in url:
        return url
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=8) as resp:
            return resp.geturl() or url
    except Exception:
        return url


def extract_aweme_id(url):
    text = url or ""
    for pattern in (r"/video/(\d+)", r"aweme_id=(\d+)", r"modal_id=(\d+)", r"(\d{16,})"):
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return ""


def pick_url(obj):
    if not isinstance(obj, dict):
        return ""
    urls = obj.get("url_list") or []
    return urls[0] if urls else ""


def complete_play_url(video):
    if not isinstance(video, dict):
        return ""
    for key in ("play_addr", "download_addr"):
        url = pick_url(video.get(key))
        if url:
            return url
    bit_rates = video.get("bit_rate") or []
    for item in bit_rates:
        url = pick_url((item or {}).get("play_addr"))
        if url:
            return url
    return ""


def complete_cover_url(video):
    if not isinstance(video, dict):
        return ""
    # cover_original_scale is the portrait version of the cover shown before
    # opening the video. The plain cover is often center-cropped, while
    # origin_cover can be a different frame from the playback detail page.
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


def safe_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def save_viral_cover(url, aweme_id):
    if not url or not aweme_id:
        return ""
    VIRAL_COVER_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^0-9A-Za-z_-]", "", str(aweme_id)) or "cover"
    path = VIRAL_COVER_DIR / f"{safe_id}.jpg"
    try:
        req = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.douyin.com/",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            },
        )
        with urlopen(req, timeout=15) as resp:
            data = resp.read()
        if data:
            path.write_bytes(data)
            return f"/viral_covers/{path.name}"
    except Exception:
        return ""
    return ""


def download_viral_media(url, aweme_id, referer="https://www.douyin.com/"):
    if not url or not aweme_id:
        return ""
    VIRAL_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^0-9A-Za-z_-]", "", str(aweme_id)) or "viral"
    path = VIRAL_MEDIA_DIR / f"{safe_id}.mp4"
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            "Referer": referer,
            "Accept": "*/*",
        },
    )
    try:
        with urlopen(req, timeout=75) as resp:
            with path.open("wb") as f:
                while True:
                    chunk = resp.read(1024 * 512)
                    if not chunk:
                        break
                    f.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if path.stat().st_size < 100000:
        path.unlink(missing_ok=True)
        return ""
    return str(path)


def download_viral_media_ytdlp(source_url, aweme_id):
    source_url = extract_share_url(source_url) or (source_url or "").strip()
    if not source_url or not aweme_id:
        return ""
    try:
        import yt_dlp
    except Exception:
        return ""
    VIRAL_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^0-9A-Za-z_-]", "", str(aweme_id)) or "viral"
    outtmpl = str(VIRAL_MEDIA_DIR / f"{safe_id}-%(id)s.%(ext)s")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "best[ext=mp4]/best",
        "outtmpl": outtmpl,
        "socket_timeout": 45,
        "retries": 2,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(source_url, download=True) or {}
    except Exception:
        return ""
    candidates = []
    for item in info.get("requested_downloads") or []:
        path = item.get("filepath") or item.get("_filename") or ""
        if path:
            candidates.append(Path(path))
    prepared = info.get("_filename") or ""
    if prepared:
        candidates.append(Path(prepared))
    candidates.extend(VIRAL_MEDIA_DIR.glob(f"{safe_id}-*.*"))
    valid = [p for p in candidates if p.exists() and p.stat().st_size > 100000]
    if not valid:
        return ""
    return str(max(valid, key=lambda p: p.stat().st_mtime))


def transcribe_viral_media(media_path, aweme_id):
    if not media_path or not Path(media_path).exists():
        return ""
    VIRAL_TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^0-9A-Za-z_-]", "", str(aweme_id)) or "viral"
    out_path = VIRAL_TRANSCRIPT_DIR / f"{safe_id}.txt"
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel("small", device="cpu", compute_type="int8")
        segments, _info = model.transcribe(
            media_path,
            language="zh",
            vad_filter=True,
            beam_size=5,
            condition_on_previous_text=False,
        )
        parts = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                parts.append(text)
        transcript = "\n".join(parts).strip()
        if transcript:
            out_path.write_text(transcript, encoding="utf-8")
        return transcript
    finally:
        try:
            Path(media_path).unlink(missing_ok=True)
        except Exception:
            pass


def cached_viral_transcript(aweme_id):
    safe_id = re.sub(r"[^0-9A-Za-z_-]", "", str(aweme_id)) or "viral"
    out_path = VIRAL_TRANSCRIPT_DIR / f"{safe_id}.txt"
    try:
        return out_path.read_text(encoding="utf-8").strip() if out_path.exists() else ""
    except Exception:
        return ""


def enrich_with_video_transcript(result, play_url, aweme_id, referer, original_url=""):
    if result.get("transcriptSource") == "本地 Whisper 转写稿" and (result.get("fullText") or "").strip():
        result["videoTranscriptStatus"] = "done"
        return result
    if not result.get("ok") or not aweme_id:
        result["transcriptSource"] = result.get("transcriptSource") or "页面文案"
        return result
    transcript = cached_viral_transcript(aweme_id)
    if transcript:
        result["videoTranscriptStatus"] = "done"
        result["transcriptSource"] = "已保存的 Whisper 逐字转写稿"
        result["transcriptPreview"] = transcript[:900]
        result["fullText"] = transcript
        result["elements"] = [
            "已读取该视频上次生成的 Whisper 逐字转写稿，不重复保存原始视频。",
            "以下二创优先基于真实口播转写稿，而不是页面简介或标题。",
            *(result.get("elements") or []),
        ][:7]
        return result
    media_path = ""
    errors = []
    try:
        if play_url:
            media_path = download_viral_media(play_url, aweme_id, referer=referer)
    except Exception as exc:
        errors.append(f"直连下载失败：{exc}")
    if not media_path and original_url:
        media_path = download_viral_media_ytdlp(original_url, aweme_id)
        if not media_path:
            errors.append("yt-dlp 兜底下载未拿到有效视频文件")
    try:
        transcript = transcribe_viral_media(media_path, aweme_id) if media_path else ""
    except Exception as exc:
        transcript = ""
        errors.append(f"Whisper 转写失败：{exc}")
    if transcript:
        result["videoTranscriptStatus"] = "done"
        result["transcriptSource"] = "下载视频后 Whisper 逐字转写"
        result["transcriptPreview"] = transcript[:900]
        result["fullText"] = transcript
        result["elements"] = [
            "已临时下载短视频并完成 Whisper 逐字转写，原视频已自动删除，只保存文字稿和分析结果。",
            "以下二创优先基于真实口播转写稿，而不是页面简介或标题。",
            *(result.get("elements") or []),
        ][:7]
    else:
        result["videoTranscriptStatus"] = "failed" if errors else "empty"
        if errors:
            result["videoTranscriptError"] = "；".join(errors[-3:])
        result["transcriptSource"] = result.get("transcriptSource") or "页面文案"
    return result


def ytdlp_info_url(info):
    if not isinstance(info, dict):
        return ""
    if info.get("url") and str(info.get("url")).startswith("http"):
        return info.get("url")
    for item in info.get("requested_formats") or []:
        url = item.get("url") or ""
        if url and item.get("vcodec") != "none":
            return url
    for item in info.get("formats") or []:
        url = item.get("url") or ""
        if url and item.get("vcodec") != "none":
            return url
    for item in info.get("formats") or []:
        url = item.get("url") or ""
        if url:
            return url
    return ""


def ytdlp_thumb(info):
    if not isinstance(info, dict):
        return ""
    if info.get("thumbnail"):
        return info.get("thumbnail")
    thumbs = info.get("thumbnails") or []
    return (thumbs[-1] or {}).get("url", "") if thumbs else ""


def analyze_external_with_ytdlp(original_url):
    source_url = extract_share_url(original_url) or (original_url or "").strip()
    if not source_url:
        return {"error": "没有识别到单条视频链接"}
    try:
        import yt_dlp
    except Exception as exc:
        return {"error": f"yt-dlp 不可用：{exc}"}
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noplaylist": True, "socket_timeout": 35, "retries": 2}) as ydl:
            info = ydl.extract_info(source_url, download=False) or {}
    except Exception as exc:
        return {"error": str(exc)}
    aweme_id = str(info.get("id") or extract_aweme_id(info.get("webpage_url") or source_url) or "")
    title = (info.get("title") or info.get("description") or f"抖音作品 {aweme_id}").strip()
    desc = (info.get("description") or "").strip()
    text = desc or title
    cover_url = ytdlp_thumb(info)
    play_url = ytdlp_info_url(info)
    if not aweme_id and not (text or cover_url or play_url):
        return {"error": "yt-dlp 未返回作品信息"}
    local_cover = save_viral_cover(cover_url, aweme_id) or cover_url
    result = {
        "ok": True,
        "matched": False,
        "source": "yt-dlp 已从单条视频链接提取作品信息",
        "url": info.get("webpage_url") or source_url,
        "resolvedUrl": info.get("webpage_url") or source_url,
        "awemeId": aweme_id,
        "title": re.sub(r"#\S+", "", title).strip() or f"抖音作品 {aweme_id}",
        "theme": "外部爆款拆解",
        "transcriptPreview": text[:900],
        "fullText": text,
        "scores": {
            "hook": 78 if any(w in text[:80] for w in ["你", "为什么", "其实", "不是", "别"]) else 66,
            "conflict": 82 if any(w in text for w in ["不是", "而是", "其实", "真正", "别再"]) else 70,
            "structure": 78 if len(text) >= 160 else 62,
            "action": 76 if any(w in text for w in ["评论", "收藏", "关注", "做", "试试", "方法"]) else 64,
            "cover": 82 if cover_url else 62,
        },
        "stats": {
            "play": safe_int(info.get("view_count")),
            "likes": safe_int(info.get("like_count")),
            "comments": safe_int(info.get("comment_count")),
            "collects": 0,
            "shares": safe_int(info.get("repost_count")),
        },
        "cover": ["对照原封面", "提炼痛点大字", "重做三行标题"],
        "coverImage": local_cover,
        "coverSource": cover_url,
        "playUrl": play_url,
        "transcriptSource": "yt-dlp 标题/简介，优先尝试视频转写",
        "elements": [
            "接口和浏览器提取不稳定时，已启用 yt-dlp 单条视频兜底。",
            "系统会临时下载视频做 Whisper 逐字转写，完成后删除原始视频。",
            "以下拆解只基于当前链接，不调用历史账号主题。",
        ],
    }
    return enrich_with_video_transcript(result, play_url, aweme_id or "viral", info.get("webpage_url") or source_url, original_url=source_url)


def fetch_aweme_detail(aweme_id):
    if not aweme_id:
        return {}
    url = (
        "https://www.douyin.com/aweme/v1/web/aweme/detail/"
        f"?aweme_id={aweme_id}&aid=6383&device_platform=webapp"
    )
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Referer": f"https://www.douyin.com/video/{aweme_id}",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8", "ignore"))


def analyze_external_aweme(original_url, resolved_url, aweme_id):
    try:
        data = fetch_aweme_detail(aweme_id)
    except Exception as exc:
        return {"error": str(exc)}
    item = data.get("aweme_detail") or {}
    if not item:
        return {"error": "详情接口未返回作品内容"}
    video = item.get("video") or {}
    stats = item.get("statistics") or {}
    title = item.get("item_title") or item.get("preview_title") or ""
    desc = item.get("desc") or ""
    caption = item.get("caption") or ""
    text = caption or desc or title
    has_real_text = bool((caption or desc or title or "").strip())
    cover_url = (
        complete_cover_url(video)
    )
    play_url = complete_play_url(video)
    if not has_real_text and not (cover_url or play_url):
        return {"error": "详情接口返回了作品对象，但没有标题、文案、封面或视频流"}
    local_cover = save_viral_cover(cover_url, aweme_id) or cover_url
    clean_title = re.sub(r"#\S+", "", title or desc or f"抖音作品 {aweme_id}").strip()
    if not clean_title:
        clean_title = f"抖音作品 {aweme_id}"
    result = {
        "ok": True,
        "matched": False,
        "source": "已从拆解链接提取作品详情",
        "url": f"https://www.douyin.com/video/{aweme_id}",
        "resolvedUrl": resolved_url or original_url,
        "awemeId": aweme_id,
        "title": clean_title,
        "theme": "外部爆款拆解",
        "transcriptPreview": text[:900],
        "fullText": text,
        "scores": {
            "hook": 78 if any(w in text[:80] for w in ["你", "为什么", "其实", "不是", "别"]) else 66,
            "conflict": 82 if any(w in text for w in ["不是", "而是", "其实", "真正", "别再"]) else 70,
            "structure": 78 if len(text) >= 160 else 62,
            "action": 76 if any(w in text for w in ["评论", "收藏", "关注", "做", "试试", "方法"]) else 64,
            "cover": 82 if cover_url else 62,
        },
        "stats": {
            "play": pick_count(stats, "play_count"),
            "likes": pick_count(stats, "digg_count"),
            "comments": pick_count(stats, "comment_count"),
            "collects": pick_count(stats, "collect_count"),
            "shares": pick_count(stats, "share_count"),
        },
        "cover": ["对照原封面", "提炼痛点大字", "重做三行标题"],
        "coverImage": local_cover,
        "coverSource": cover_url,
        "playUrl": play_url,
        "transcriptSource": "页面标题/简介/字幕" if has_real_text else "页面未返回文案，已改走视频转写",
        "elements": [
            "已从视频链接提取标题/简介/字幕文案，用真实内容做拆解。" if has_real_text else "页面接口没有返回文案，系统已继续临时下载视频并做 Whisper 转写。",
            "先看黄金三秒是否直接点名人群、痛点或反常识结论。",
            "中段按真实文案判断是否有“场景-冲突-观点-动作”的推进。",
            "封面图已保存到本地，用于归档后对照复盘。",
        ],
    }
    return enrich_with_video_transcript(result, play_url, aweme_id, f"https://www.douyin.com/video/{aweme_id}", original_url=original_url or resolved_url)


def analyze_external_with_browser(original_url):
    try:
        proc = subprocess.run(
            [sys.executable, "scripts/extract_douyin_video.py", original_url],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=95,
        )
    except Exception as exc:
        return {"error": f"浏览器提取失败：{exc}"}
    if proc.returncode:
        return {"error": (proc.stderr or proc.stdout or f"浏览器提取退出码 {proc.returncode}").strip()}
    try:
        data = json.loads((proc.stdout or "").strip().splitlines()[-1])
    except Exception:
        return {"error": "浏览器提取没有返回可解析数据"}
    if not data.get("ok"):
        if data.get("awemeId") and (data.get("playUrl") or data.get("coverSource")):
            data["ok"] = True
            data["fullText"] = data.get("fullText") or data.get("title") or ""
            data["transcriptPreview"] = data.get("transcriptPreview") or data.get("fullText", "")[:900]
            data["transcriptSource"] = "页面未返回文案，已改走视频转写"
        else:
            return {"error": data.get("message") or "浏览器没有捕获到详情数据", **data}
    aweme_id = data.get("awemeId") or extract_aweme_id(data.get("url", ""))
    cover_source = data.get("coverSource") or ""
    data["coverImage"] = save_viral_cover(cover_source, aweme_id) or cover_source
    data["theme"] = "外部爆款拆解"
    data["transcriptSource"] = "Playwright 页面标题/简介/字幕"
    data["scores"] = {
        "hook": 78 if any(w in (data.get("fullText") or "")[:80] for w in ["你", "为什么", "其实", "不是", "别"]) else 66,
        "conflict": 82 if any(w in (data.get("fullText") or "") for w in ["不是", "而是", "其实", "真正", "别再"]) else 70,
        "structure": 78 if len(data.get("fullText") or "") >= 160 else 62,
        "action": 76 if any(w in (data.get("fullText") or "") for w in ["评论", "收藏", "关注", "做", "试试", "方法"]) else 64,
        "cover": 82 if data.get("coverImage") else 62,
    }
    data["elements"] = [
        "已直接打开你提交的视频链接，并从页面接口提取标题、文案、封面和数据。",
        "以下拆解只基于该链接返回的真实内容，不再使用通用兜底模板。",
        "封面图已保存到本地，用于归档后对照复盘。",
    ]
    return enrich_with_video_transcript(data, data.get("playUrl") or "", aweme_id, data.get("url") or original_url, original_url=original_url)


def load_workflow_rows():
    try:
        items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    return build_rows(items)


def local_viral_analysis(url):
    pasted = (url or "").strip()
    original_url = extract_share_url(pasted) or pasted
    resolved_url = resolve_douyin_url(original_url)
    aweme_id = extract_aweme_id(resolved_url) or extract_aweme_id(original_url)
    rows = load_workflow_rows()
    match = None
    for row in rows:
        if aweme_id and row.get("id") == aweme_id:
            match = row
            break
        if original_url and original_url in {row.get("url", ""), row.get("id", "")}:
            match = row
            break
    if match:
        title = match.get("title") or "已匹配本地作品"
        text = match.get("transcript") or title
        theme = match.get("theme") or "综合清醒文案"
        score = match.get("scores", {})
        base = int(score.get("score") or 68)
        saved_cover = save_viral_cover(match.get("coverUrl") or "", aweme_id or match.get("id", ""))
        result = {
            "ok": True,
            "matched": True,
            "source": "已匹配本地作品库",
            "url": match.get("url") or resolved_url or original_url,
            "resolvedUrl": resolved_url,
            "title": title,
            "theme": theme,
            "transcriptPreview": text[:360],
            "fullText": text,
            "stats": match.get("stats") or None,
            "scores": {
                "hook": int(score.get("hook") or base),
                "conflict": min(96, base + 8),
                "structure": int(score.get("structure") or base),
                "action": min(96, int(score.get("structure") or base) + 5),
                "cover": int(score.get("cover") or base),
            },
            "cover": match.get("cover") or [],
            "coverImage": saved_cover or match.get("coverUrl") or "",
            "coverSource": match.get("coverUrl") or "",
            "transcriptSource": match.get("transcript_status") == "done" and "本地 Whisper 转写稿" or "本地作品文案",
            "elements": [
                "用已发布作品标题判断点击入口，并结合转写稿拆解停留点。",
                "重点看开头是否直接点名用户处境，避免先解释背景。",
                "中段是否形成“现象-误区-真相-行动”的递进。",
                "封面是否能在 1 秒内看懂痛点和反差。",
            ],
        }
        return enrich_with_video_transcript(result, match.get("play_url") or "", match.get("id") or aweme_id, match.get("url") or original_url)
    external = analyze_external_aweme(original_url, resolved_url, aweme_id)
    if external.get("ok"):
        return external
    browser_external = analyze_external_with_browser(original_url)
    if browser_external.get("ok"):
        return browser_external
    ytdlp_external = analyze_external_with_ytdlp(original_url)
    if ytdlp_external.get("ok"):
        return ytdlp_external
    return {
        "ok": False,
        "matched": False,
        "source": "链接内容提取失败",
        "url": original_url or pasted,
        "resolvedUrl": resolved_url,
        "message": f"没有从这个链接提取到真实视频标题、文案、封面或可转写视频。接口提取：{external.get('error') or '未知原因'}；浏览器提取：{browser_external.get('error') or '未知原因'}；yt-dlp 兜底：{ytdlp_external.get('error') or '未知原因'}。请确认复制的是单条公开视频分享链接。",
    }


def set_refresh_state(**kwargs):
    with REFRESH_LOCK:
        REFRESH_STATE.update(kwargs)


def append_refresh_log(line):
    with REFRESH_LOCK:
        logs = REFRESH_STATE.setdefault("logs", [])
        logs.append(line)
        del logs[:-80]


def refresh_snapshot():
    with REFRESH_LOCK:
        return dict(REFRESH_STATE, logs=list(REFRESH_STATE.get("logs", [])))


def load_app_capture_state():
    path = ROOT / "data" / "douyin_app_capture_state.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}


def run_step(name, command):
    set_refresh_state(step=name, message=f"正在{name}...")
    append_refresh_log(f"$ {' '.join(command)}")
    proc = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = (proc.stdout or "").strip()
    if output:
        for line in output.splitlines()[-40:]:
            append_refresh_log(line)
    if proc.returncode:
        raise RuntimeError(f"{name}失败，退出码 {proc.returncode}")


def refresh_workflow(source_url=""):
    with REFRESH_LOCK:
        if REFRESH_STATE.get("running"):
            return
        REFRESH_STATE.update(
            {
                "running": True,
                "ok": None,
                "step": "准备刷新",
                "message": "正在准备按主页链接抓取博主公开作品。" if source_url else "正在准备自动抓取账号作品信息。",
                "startedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
                "finishedAt": "",
                "logs": [],
                "mode": "profile" if source_url else "app",
                "sourceUrl": source_url,
            }
        )
    try:
        py = sys.executable
        first_step = (
            ("按主页链接抓取公开作品", [py, "scripts/capture_douyin_profile_posts.py", source_url, "--limit", "120"])
            if source_url
            else ("从抖音 App 抓取作品列表", ["/usr/bin/swift", "scripts/capture_douyin_app_posts.swift"])
        )
        if source_url:
            steps = [
                first_step,
                ("获取作品详情", [py, "scripts/fetch_douyin_details.py"]),
                ("重建工作台", [py, "scripts/build_workflow_app.py"]),
            ]
        else:
            steps = [
                first_step,
                ("获取作品详情", [py, "scripts/fetch_douyin_details.py"]),
                ("下载新增视频", [py, "scripts/download_douyin_media.py"]),
                ("自动转写视频", [py, "scripts/transcribe_douyin_media.py"]),
                ("重建工作台", [py, "scripts/build_workflow_app.py"]),
            ]
        for name, command in steps:
            run_step(name, command)
        app_state = load_app_capture_state() if not source_url else {}
        fallback_count = app_state.get("capturedCount")
        used_fallback = bool(app_state.get("fallback"))
        set_refresh_state(
            running=False,
            ok=True,
            step="刷新完成",
            message=(
                "已按主页链接抓取目标博主作品并重建工作台，页面即将刷新。"
                if source_url
                else (
                    f"当前抖音 App 页面未读到作品，已沿用上一次成功抓取的 {fallback_count or ''} 条作品继续刷新并重建工作台。"
                    if used_fallback
                    else "已抓取抖音作品信息并重建工作台；平台限制导致的原视频下载失败会自动跳过，不影响作品数据更新。"
                )
            ),
            finishedAt=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
    except Exception as exc:
        append_refresh_log(str(exc))
        set_refresh_state(
            running=False,
            ok=False,
            step="刷新失败",
            message=str(exc),
            finishedAt=time.strftime("%Y-%m-%d %H:%M:%S"),
        )


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if not authorized(self.path, self.headers, self.client_address):
            body = "未授权访问：请使用带 key 的工作台网址。".encode("utf-8")
            self.send_response(403)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/cover-examples":
            query = parse_qs(parsed.query)
            payload = cover_examples((query.get("theme") or [""])[0])
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/hot-topics":
            query = parse_qs(parsed.query)
            payload = hot_topics(
                (query.get("theme") or [""])[0],
                (query.get("pain") or [""])[0],
            )
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/refresh-status":
            body = json.dumps(refresh_snapshot(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        if not authorized(self.path, self.headers, self.client_address):
            body = json.dumps({"ok": False, "message": "未授权访问"}, ensure_ascii=False).encode("utf-8")
            self.send_response(403)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/refresh":
            snapshot = refresh_snapshot()
            if not snapshot.get("running"):
                threading.Thread(target=refresh_workflow, daemon=True).start()
                snapshot = refresh_snapshot()
            body = json.dumps(snapshot, ensure_ascii=False).encode("utf-8")
            self.send_response(202)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/refresh-profile":
            payload = read_json_body(self)
            source_url = (payload.get("url") or "").strip()
            if not source_url:
                body = json.dumps({"ok": False, "message": "请先输入抖音博主主页分享链接。"}, ensure_ascii=False).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            snapshot = refresh_snapshot()
            if not snapshot.get("running"):
                threading.Thread(target=refresh_workflow, args=(source_url,), daemon=True).start()
                snapshot = refresh_snapshot()
            body = json.dumps(snapshot, ensure_ascii=False).encode("utf-8")
            self.send_response(202)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/viral-analyze":
            payload = read_json_body(self)
            body = json.dumps(local_viral_analysis(payload.get("url", "")), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)


def main():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    server = FastThreadingHTTPServer((HOST, PORT), Handler)
    print(f"http://127.0.0.1:{PORT}/?key={CONFIG['access_key']}")
    print(f"Listening on {HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
