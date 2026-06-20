import html
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "douyin_details_merged.json"
OUT_DIR = ROOT / "output" / "dashboard"
OUT_FILE = OUT_DIR / "index.html"


THEMES = {
    "追星心理/理想自我": ["王一博", "追星", "偶像", "喜欢谁", "代偿", "投射", "粉"],
    "边界感/反讨好": ["讨好", "顺从", "害怕", "关系", "主动权", "失去"],
    "女性成长/自我觉醒": ["女性", "成长", "自己", "人生", "自由", "觉醒", "行动"],
    "情绪管理/内核稳定": ["情绪", "稳定", "敏感", "内耗", "治愈", "反PUA"],
    "行动力/破碎重建": ["行动", "打碎", "重建", "苦", "闪闪发光", "最佳时机", "替换"],
    "文学哲思/独处": ["木心", "独处", "日月", "百转柔肠", "读懂"],
}

HOOK_WORDS = ["你", "为什么", "有没有", "其实", "不是", "才是", "别", "总被", "恭喜", "藏着"]
EMOTION_WORDS = ["害怕", "自由", "勇敢", "清醒", "委屈", "值得", "破碎", "热烈", "孤独", "稳定", "内耗", "治愈"]
CTA_WORDS = ["点赞", "收藏", "转给", "评论", "关注", "保存"]
PROBLEM_WORDS = ["不是", "其实", "你以为", "答案", "所以", "真正", "因为", "第一", "第二", "第三"]


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def parse_tags(desc):
    return re.findall(r"#([^#\s]+)", desc or "")


def strip_tags(desc):
    return re.sub(r"#\S+", "", desc or "").strip()


def clean_platform_suffix(text):
    return clean_text(re.sub(r"……版本过低，升级后可展示全部信息", "", text or ""))


def text_candidate(item, key):
    value = item.get(key)
    if value:
        return value
    candidates = item.get("text_candidates") or {}
    return candidates.get(key) or ""


def title_text(item, idx=0):
    title = text_candidate(item, "item_title") or text_candidate(item, "preview_title")
    if title:
        return clean_platform_suffix(strip_tags(title))
    desc_title = strip_tags(clean_platform_suffix(item.get("desc") or ""))
    if desc_title:
        return desc_title
    return f"作品 {idx}" if idx else "作品"


def script_text(item):
    transcript = clean_text(item.get("transcript") or "")
    if transcript:
        return transcript, "本地转写稿"
    caption = clean_platform_suffix(text_candidate(item, "caption"))
    if caption:
        return caption, "抖音 caption"
    desc = clean_platform_suffix(item.get("desc") or "")
    if desc:
        return strip_tags(desc), "作品简介"
    return "", "暂无文字稿"


def created_at(item):
    ts = item.get("create_time")
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
    except Exception:
        return ""


def pick_theme(text):
    scores = {}
    for theme, keys in THEMES.items():
        scores[theme] = sum(text.count(k) for k in keys)
    theme, score = max(scores.items(), key=lambda kv: kv[1])
    return theme if score else "综合清醒文案"


def count_words(text, words):
    return sum(text.count(w) for w in words)


def score_item(item):
    desc = clean_platform_suffix(item.get("desc") or "")
    title = title_text(item)
    transcript, transcript_source = script_text(item)
    text = title + " " + transcript
    tags = parse_tags(desc)

    if not transcript:
        return {
            "score": 42,
            "hook": 40,
            "structure": 30,
            "emotion": 35,
            "cover": 45,
            "status_note": "缺少文字稿，暂按标题做方向判断。",
        }

    title_len = len(title)
    transcript_len = len(transcript)
    hook = 45 + min(30, count_words(title[:35] + transcript[:70], HOOK_WORDS) * 8)
    if "？" in title or "?" in title:
        hook += 8
    if title_len <= 24:
        hook += 8
    elif title_len > 44:
        hook -= 8

    structure = 45 + min(28, count_words(transcript, PROBLEM_WORDS) * 4)
    if count_words(transcript, CTA_WORDS):
        structure += 8
    if transcript_len < 120:
        structure -= 10
    elif 180 <= transcript_len <= 520:
        structure += 8

    emotion = 42 + min(34, count_words(text, EMOTION_WORDS) * 6)
    if len(tags) >= 3:
        emotion += 5

    cover = 50
    if 8 <= title_len <= 24:
        cover += 22
    if any(w in title for w in ["你", "别", "不是", "恭喜", "为什么"]):
        cover += 12
    if title_len > 36:
        cover -= 10

    raw = hook * 0.28 + structure * 0.30 + emotion * 0.24 + cover * 0.18
    score = max(35, min(96, round(raw)))
    return {
        "score": score,
        "hook": max(0, min(100, round(hook))),
        "structure": max(0, min(100, round(structure))),
        "emotion": max(0, min(100, round(emotion))),
        "cover": max(0, min(100, round(cover))),
        "status_note": f"已基于{transcript_source}分析。",
    }


def cover_suggestion(title, theme):
    title = title or "清醒成长"
    if "王一博" in title or "追" in title:
        return ["你追的不是他", "是不敢活的自己", "追星心理"]
    if "讨好" in title:
        return ["别再讨好", "你不是来交房租的", "边界感"]
    if "敏感" in title:
        return ["太敏感不是错", "这是你的天赋", "高敏感自救"]
    if "苦" in title or "行动" in title:
        return ["别没苦硬吃", "支棱起来", "行动力"]
    if "情绪" in title:
        return ["不被带节奏", "才是真稳定", "内核稳定"]
    if theme == "文学哲思/独处":
        return ["人都逃不过", "这四步", "文学清醒"]
    return [title[:8], "把自己活回来", theme.split("/")[0]]


def copy_advice(item, score):
    title = title_text(item)
    transcript, transcript_source = script_text(item)
    advice = []
    if score["hook"] < 70:
        advice.append("前 3 秒需要更尖锐：先抛“你正在付出的代价”，再解释原因。")
    else:
        advice.append("开头具备停留点，适合保留“你/不是/其实”这类直指用户的句式。")
    if score["structure"] < 70:
        advice.append("中段建议固定成“现象-误区-真相-行动”四步，减少散文式漂移。")
    else:
        advice.append("结构有递进感，可以在结尾增加一句可评论的问题放大互动。")
    if len(transcript) < 160 and transcript_source != "暂无文字稿":
        advice.append("内容偏短，可扩展一个真实场景或反差例子，提升可信度。")
    if "王一博" in title:
        advice.append("明星话题是流量入口，但结尾一定回到“普通女性如何改变自己”，避免只停在追星。")
    return advice


def optimization_tips(item, score, theme):
    title = title_text(item)
    transcript, transcript_source = script_text(item)
    tips = {
        "hook": "前 3 秒先抛结果或代价，少铺垫；用“你以为/其实/别再/为什么”直接点名用户。",
        "structure": "中段固定成“痛点场景-错误理解-真正原因-今天动作”，每 5 到 8 秒推进一次。",
        "emotion": "把抽象清醒落到具体感受，加入“委屈、害怕、松一口气、站回自己”等可共鸣词。",
        "cover": "封面三行控制在 12 到 18 个大字：痛点人群 + 反常识判断 + 栏目标签。",
    }
    if score["hook"] >= 75:
        tips["hook"] = "开头已有停留点，保留直指用户的句式，再把第一句话压缩到更短。"
    if score["structure"] >= 75:
        tips["structure"] = "结构有递进感，下一步在结尾加一个能让用户评论自身经历的问题。"
    if score["emotion"] >= 75:
        tips["emotion"] = "情绪共鸣够强，注意补一个具体动作，把“被说中”转成“愿意关注”。"
    if score["cover"] >= 75:
        tips["cover"] = "封面点击条件较好，保持大字冲突和明确栏目，不要塞太多副标题。"
    if len(transcript) < 160 and transcript_source != "暂无文字稿":
        tips["structure"] += " 当前文字稿偏短，建议补一个真实场景，增强信任感。"
    if "王一博" in title or "追星" in title or theme.startswith("追星"):
        tips["emotion"] += " 追星主题结尾要回到“我想成为怎样的人”，不要只停留在偶像本身。"
        tips["cover"] = "封面建议：你追的不是他 / 是不敢活的自己 / 追星心理。"
    return tips


def opportunity(item, theme):
    title = title_text(item)
    if "王一博" in title:
        return "把明星热度转译为“理想自我投射”系列，既吃热点，又沉淀账号方法论。"
    if theme == "边界感/反讨好":
        return "强痛点主题，适合做连续剧：讨好型人格、边界感、关系主动权、拒绝练习。"
    if theme == "情绪管理/内核稳定":
        return "容易形成收藏价值，建议增加可执行练习，比如一句自救话术或一个当天动作。"
    if theme == "行动力/破碎重建":
        return "适合做燃向封面和快节奏剪辑，补足故事案例后更容易转发。"
    return "适合沉淀为账号价值观资产，用更清晰的封面词提高点击。"


def build_rows(items):
    rows = []
    for idx, item in enumerate(items, 1):
        desc = clean_platform_suffix(item.get("desc") or "")
        title = title_text(item, idx)
        transcript, transcript_source = script_text(item)
        theme = pick_theme(desc + " " + transcript)
        scores = score_item(item)
        stats = item.get("stats") or {}
        rows.append(
            {
                "idx": idx,
                "id": item.get("aweme_id", ""),
                "title": title,
                "tags": parse_tags(desc),
                "date": created_at(item),
                "status": item.get("transcript_status", ""),
                "theme": theme,
                "transcript": transcript,
                "transcriptSource": transcript_source,
                "scores": scores,
                "cover": cover_suggestion(title, theme),
                "advice": copy_advice(item, scores),
                "optimizationTips": optimization_tips(item, scores, theme),
                "opportunity": opportunity(item, theme),
                "stats": {
                    "play": int(stats.get("play_count") or 0),
                    "likes": int(stats.get("digg_count") or 0),
                    "comments": int(stats.get("comment_count") or 0),
                    "collects": int(stats.get("collect_count") or 0),
                    "shares": int(stats.get("share_count") or 0),
                },
                "coverUrl": item.get("cover_url") or "",
                "url": f"https://www.douyin.com/video/{item.get('aweme_id','')}",
            }
        )
    return rows


def trend_data(rows):
    themes = Counter(r["theme"] for r in rows)
    avg = round(sum(r["scores"]["score"] for r in rows) / max(1, len(rows)), 1)
    done = sum(1 for r in rows if r["status"] == "done")
    high = sorted(rows, key=lambda r: r["scores"]["score"], reverse=True)[:5]
    return themes, avg, done, high


def make_theme_ideas():
    return [
        {
            "pillar": "追星心理变自我成长",
            "why": "已有王一博相关内容形成连续入口，适合把热点流量转成账号心智。",
            "ideas": [
                "你喜欢的偶像，暴露了你最缺的能力",
                "为什么越清醒的人，越不需要神化任何人",
                "你不是在追星，你是在找一个更勇敢的自己",
                "把追星变成自我管理：普通人可以偷学的 3 件事",
            ],
        },
        {
            "pillar": "关系里的边界感",
            "why": "讨好、敏感、内耗是高共鸣痛点，容易收藏和转发。",
            "ideas": [
                "你越懂事，别人越敢亏待你",
                "别把好脾气用在消耗你的人身上",
                "高敏感的人最该练的不是钝感，是边界",
                "真正的关系稳定，是你敢说不",
            ],
        },
        {
            "pillar": "女性自我重建",
            "why": "账号核心气质是温柔但有锋芒，适合做长期 IP。",
            "ideas": [
                "女人最该戒掉的不是恋爱脑，是低配感",
                "你不是来吃苦的，你是来长本事的",
                "破碎不是失败，是旧版本卸载",
                "别等状态好了再开始，开始本身就是状态",
            ],
        },
        {
            "pillar": "情绪稳定方法论",
            "why": "从金句走向方法，能提升账号信任和复看率。",
            "ideas": [
                "被带节奏时，先问自己这 3 个问题",
                "情绪上头的 10 分钟，决定你会不会后悔",
                "内核稳定不是冷漠，是不把方向盘交出去",
                "把内耗停掉的一个小动作",
            ],
        },
    ]


def json_for_html(data):
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def h(text):
    return html.escape(str(text), quote=True)


def render_html(rows):
    themes, avg, done, high = trend_data(rows)
    top_theme = themes.most_common(1)[0][0] if themes else "综合清醒文案"
    chart_items = themes.most_common()
    source_notes = [
        {
            "name": "巨量引擎 2026 营销 IP 通案摘要",
            "url": "https://www.fxbaogao.com/detail/5201755",
            "note": "平台强调多元生活场景、强情感共鸣、内容趋势事件和互动营销。",
        },
        {
            "name": "2026 抖音旋律营销趋势白皮书报道",
            "url": "https://finance.sina.cn/tech/2026-01-30/detail-inhizxrn0297442.d.html?vt=4",
            "note": "爆款声音可按记忆点、情绪值、传播性三项管理。",
        },
        {
            "name": "抖音电商 2026 春夏趋势报告摘要",
            "url": "https://www.fxbaogao.com/detail/5224642",
            "note": "年轻女性消费决策中，场景、风格和情绪价值是关键因子。",
        },
        {
            "name": "抖音精选创作者出版计划 2.0",
            "url": "https://www.news.cn/tech/20260108/0f61ba6b538443d0965970d4aef17456/c.html",
            "note": "知识型短视频有机会沉淀为图文、课程、书稿等长内容资产。",
        },
    ]
    page_data = {
        "rows": rows,
        "themeChart": chart_items,
        "ideas": make_theme_ideas(),
        "sources": source_notes,
    }

    cards = []
    for r in rows:
        score = r["scores"]["score"]
        tone = "good" if score >= 78 else "mid" if score >= 65 else "low"
        cards.append(
            f"""
            <article class="video-card {tone}" data-theme="{h(r['theme'])}" data-status="{h(r['status'])}">
              <div class="card-top">
                <div>
                  <div class="eyebrow">#{r['idx']} · {h(r['theme'])}</div>
                  <h3>{h(r['title'])}</h3>
                </div>
                <div class="score">{score}</div>
              </div>
              <div class="metrics">
                <span>钩子 {r['scores']['hook']}</span>
                <span>结构 {r['scores']['structure']}</span>
                <span>情绪 {r['scores']['emotion']}</span>
                <span>封面 {r['scores']['cover']}</span>
              </div>
              <p class="opportunity">{h(r['opportunity'])}</p>
              <div class="cover-lines">
                <b>封面三行</b>
                <span>{h(' / '.join(r['cover']))}</span>
              </div>
              <ul>
                {''.join(f'<li>{h(a)}</li>' for a in r['advice'])}
              </ul>
              <details>
                <summary>查看文字稿</summary>
                <p>{h(r['transcript'] or r['scores']['status_note'])}</p>
              </details>
            </article>
            """
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>抖音工作流 · 本地分析看板</title>
  <style>
    :root {{
      --ink:#172026; --muted:#64707d; --line:#d9e0e7; --paper:#fbfaf7;
      --blue:#2454ff; --teal:#0f9b8e; --rose:#c23b58; --gold:#b7791f; --green:#247a50;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif; color:var(--ink); background:var(--paper); }}
    header {{ padding:28px 32px 18px; border-bottom:1px solid var(--line); background:#fff; position:sticky; top:0; z-index:5; }}
    .title-row {{ display:flex; justify-content:space-between; gap:20px; align-items:flex-start; }}
    h1 {{ margin:0; font-size:30px; letter-spacing:0; }}
    .subtitle {{ margin:8px 0 0; color:var(--muted); max-width:820px; line-height:1.6; }}
    .date {{ font-size:13px; color:var(--muted); white-space:nowrap; }}
    main {{ padding:24px 32px 48px; }}
    .grid {{ display:grid; gap:16px; }}
    .kpis {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
    .panel {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:18px; box-shadow:0 1px 0 rgba(20,30,40,.03); }}
    .kpi b {{ display:block; font-size:30px; margin-bottom:4px; }}
    .kpi span, .small {{ color:var(--muted); font-size:13px; line-height:1.5; }}
    .section-title {{ display:flex; align-items:end; justify-content:space-between; gap:18px; margin:28px 0 12px; }}
    h2 {{ font-size:20px; margin:0; }}
    .strategy {{ grid-template-columns:1.1fr .9fr; align-items:stretch; }}
    .bars {{ display:grid; gap:10px; }}
    .bar {{ display:grid; grid-template-columns:130px 1fr 36px; gap:10px; align-items:center; font-size:13px; }}
    .track {{ height:10px; background:#edf1f4; border-radius:99px; overflow:hidden; }}
    .fill {{ height:100%; background:linear-gradient(90deg,var(--teal),var(--blue)); }}
    .filters {{ display:flex; flex-wrap:wrap; gap:8px; }}
    button {{ border:1px solid var(--line); background:#fff; border-radius:6px; padding:8px 11px; color:var(--ink); cursor:pointer; }}
    button.active {{ background:var(--ink); color:#fff; border-color:var(--ink); }}
    .cards {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
    .video-card {{ border-top:4px solid var(--blue); }}
    .video-card.mid {{ border-top-color:var(--gold); }}
    .video-card.low {{ border-top-color:var(--rose); }}
    .card-top {{ display:flex; justify-content:space-between; gap:14px; align-items:flex-start; }}
    .eyebrow {{ color:var(--muted); font-size:12px; margin-bottom:7px; }}
    h3 {{ margin:0; font-size:17px; line-height:1.45; }}
    .score {{ min-width:48px; height:48px; display:grid; place-items:center; border-radius:50%; background:#eff4ff; color:var(--blue); font-weight:800; }}
    .metrics {{ display:flex; flex-wrap:wrap; gap:8px; margin:14px 0; }}
    .metrics span {{ background:#f1f4f6; border-radius:6px; padding:5px 8px; font-size:12px; color:#3a4650; }}
    .opportunity {{ line-height:1.65; margin:0 0 12px; }}
    .cover-lines {{ border:1px dashed #bfc8d1; border-radius:8px; padding:10px 12px; margin:10px 0; display:grid; gap:4px; }}
    .cover-lines span {{ color:var(--rose); font-weight:700; }}
    ul {{ padding-left:18px; margin:12px 0 0; line-height:1.7; }}
    details {{ margin-top:12px; color:var(--muted); }}
    details p {{ line-height:1.7; color:#3f4a54; }}
    .ideas {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
    .idea h3 {{ font-size:15px; margin-bottom:8px; }}
    .idea ol {{ padding-left:18px; line-height:1.65; }}
    .roadmap {{ grid-template-columns:repeat(3,minmax(0,1fr)); }}
    .roadmap h3 {{ color:var(--teal); }}
    .sources a {{ color:var(--blue); text-decoration:none; }}
    .sources li {{ margin:8px 0; }}
    @media (max-width: 980px) {{
      header, main {{ padding-left:18px; padding-right:18px; }}
      .kpis, .strategy, .cards, .ideas, .roadmap {{ grid-template-columns:1fr; }}
      .title-row {{ display:block; }}
      .date {{ margin-top:8px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="title-row">
      <div>
        <h1>抖音工作流 · 本地分析看板</h1>
        <p class="subtitle">基于账号「妮可清醒局」17 条公开作品、14 条本地转写稿生成。目标不是只存档，而是把内容变成可复盘、可迭代、可批量产出选题的工作台。</p>
      </div>
      <div class="date">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
  </header>
  <main>
    <section class="grid kpis">
      <div class="panel kpi"><b>{len(rows)}</b><span>已纳入作品</span></div>
      <div class="panel kpi"><b>{done}</b><span>完成本地转写</span></div>
      <div class="panel kpi"><b>{avg}</b><span>平均内容潜力分</span></div>
      <div class="panel kpi"><b>{h(top_theme)}</b><span>当前最强内容簇</span></div>
    </section>

    <div class="section-title"><h2>账号判断</h2><span class="small">定位、优势、短板和下一阶段打法</span></div>
    <section class="grid strategy">
      <div class="panel">
        <h2>一句话定位</h2>
        <p class="opportunity">「温柔但锋利的女性清醒局」：用心理洞察、关系边界和自我成长，把用户从情绪共鸣带到行动改变。</p>
        <ul>
          <li>优势：金句密度高，直指女性情绪、自我价值和关系痛点。</li>
          <li>机会：王一博/追星主题可以作为热点入口，但要长期沉淀成“理想自我投射”方法论。</li>
          <li>短板：部分作品偏散文化，封面词和 3 秒钩子还可以更明确、更有冲突。</li>
          <li>建议：每条视频固定输出一个“可带走的动作”，让用户不仅觉得被说中，还知道下一步怎么做。</li>
        </ul>
      </div>
      <div class="panel">
        <h2>主题分布</h2>
        <div class="bars">
          {''.join(f'<div class="bar"><span>{h(k)}</span><div class="track"><div class="fill" style="width:{v / max(themes.values()) * 100:.0f}%"></div></div><b>{v}</b></div>' for k, v in chart_items)}
        </div>
      </div>
    </section>

    <div class="section-title">
      <h2>逐条视频复盘</h2>
      <div class="filters" id="filters"><button class="active" data-filter="all">全部</button>{''.join(f'<button data-filter="{h(k)}">{h(k)}</button>' for k,_ in chart_items)}</div>
    </div>
    <section class="grid cards" id="cards">{''.join(cards)}</section>

    <div class="section-title"><h2>未来主题灵感</h2><span class="small">按长期栏目来做，降低每天想选题的成本</span></div>
    <section class="grid ideas">
      {''.join(f'<div class="panel idea"><h3>{h(x["pillar"])}</h3><p class="small">{h(x["why"])}</p><ol>{"".join(f"<li>{h(i)}</li>" for i in x["ideas"])}</ol></div>' for x in make_theme_ideas())}
    </section>

    <div class="section-title"><h2>发展路线</h2><span class="small">从短视频到个人 IP 资产</span></div>
    <section class="grid roadmap">
      <div class="panel"><h3>1. 内容产品化</h3><p>把“清醒金句”升级成固定栏目：追星心理局、反讨好练习、情绪稳定急救、女性重建日课。</p></div>
      <div class="panel"><h3>2. 视觉统一化</h3><p>封面统一三行：痛点词 + 反常识判断 + 栏目标签。字号大、词少、每条只打一个核心冲突。</p></div>
      <div class="panel"><h3>3. 长内容沉淀</h3><p>把高分视频扩写成图文、小红书笔记、直播提纲或电子手册，形成“短视频引流，长内容建立信任”。</p></div>
    </section>

    <div class="section-title"><h2>趋势依据</h2><span class="small">结合 2026 年公开趋势信息与账号现有内容推断</span></div>
    <section class="panel sources">
      <ul>
        {''.join(f'<li><a href="{h(s["url"])}">{h(s["name"])}</a>：{h(s["note"])}</li>' for s in source_notes)}
      </ul>
    </section>
  </main>
  <script>
    const dashboardData = {json_for_html(page_data)};
    document.querySelectorAll('#filters button').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('#filters button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.dataset.filter;
        document.querySelectorAll('.video-card').forEach(card => {{
          card.style.display = filter === 'all' || card.dataset.theme === filter ? '' : 'none';
        }});
      }});
    }});
  </script>
</body>
</html>
"""


def main():
    items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    rows = build_rows(items)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(render_html(rows), encoding="utf-8")
    print(OUT_FILE)


if __name__ == "__main__":
    main()
