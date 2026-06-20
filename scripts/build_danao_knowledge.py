import json
import re
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DANAO_DIR = ROOT / "danao"
OUT = ROOT / "data" / "danao_knowledge.json"


MODULES = [
    {
        "id": "super_individual_mindset",
        "name": "超级个体心态",
        "keywords": ["心态", "超级个体"],
        "principles": [
            "先把内容当成长期资产，而不是单条流量。",
            "用稳定输出建立信任，用复盘迭代建立能力。",
            "每条内容都要回答：我是谁、我帮谁、解决什么问题。",
        ],
        "useFor": ["发布规划", "选题生成器"],
    },
    {
        "id": "platform_traffic_monetization",
        "name": "平台流量机制与变现",
        "keywords": ["流量机制", "变现模式", "投效果"],
        "principles": [
            "短视频先解决停留、完播、互动，再谈转化。",
            "内容要分层：拉新内容负责破圈，信任内容负责转粉，转化内容负责成交。",
            "选题要同时考虑平台推荐信号和用户当下需求。",
        ],
        "useFor": ["发布复盘", "发布规划", "爆款短视频拆解"],
    },
    {
        "id": "personal_ip_positioning",
        "name": "个人 IP 定位",
        "keywords": ["个人IP", "人设", "IP人设", "标签"],
        "principles": [
            "人设不是包装，而是用户能持续识别的能力、态度和场景。",
            "内容标签要固定出现：人群标签、问题标签、方法标签、风格标签。",
            "选题不要只追热点，要把热点翻译成自己的 IP 主张。",
        ],
        "useFor": ["选题生成器", "标题封面文案优化", "发布规划"],
    },
    {
        "id": "content_labeling",
        "name": "内容给 IP 打标签",
        "keywords": ["拍什么", "标签", "内容给IP"],
        "principles": [
            "每条内容只强化一个主要标签，避免一条视频承载太多任务。",
            "封面和标题要让用户先记住你的栏目感，再进入文案细节。",
            "同一主张连续做 3 到 5 条，才容易形成账号记忆点。",
        ],
        "useFor": ["发布复盘", "选题生成器", "标题封面文案优化"],
    },
    {
        "id": "oral_video_workflow",
        "name": "一个人口播从 0 到 1",
        "keywords": ["口播", "表现力", "直播间话术"],
        "principles": [
            "口播脚本先写给耳朵听，不要写成文章。",
            "前 3 秒先给结果、冲突或代价，中段每 5 到 8 秒推进一次。",
            "表现力优先练眼神、停顿、重音和情绪落点。",
        ],
        "useFor": ["标题封面文案优化", "爆款短视频拆解"],
    },
    {
        "id": "ai_copywriting",
        "name": "AI 爆款文案",
        "keywords": ["AI写出爆款文案", "AI的基础认知", "智能体"],
        "principles": [
            "AI 负责扩展选题和结构，人负责判断真实痛点与账号立场。",
            "爆款文案要同时具备：强钩子、具体场景、反常识、可执行动作。",
            "生成结果不能停在漂亮话，要落到标题、封面、脚本和互动问题。",
        ],
        "useFor": ["选题生成器", "标题封面文案优化", "爆款短视频拆解"],
    },
    {
        "id": "ai_editing",
        "name": "AI 辅助剪辑",
        "keywords": ["AI辅助剪辑"],
        "principles": [
            "剪辑要服务信息密度：删废话、留重音、强化情绪转折。",
            "用字幕、停顿、画面切换配合文案结构，提升完播。",
            "复盘时关注用户在哪个段落可能滑走，再反推脚本节奏。",
        ],
        "useFor": ["发布复盘", "爆款短视频拆解", "发布规划"],
    },
    {
        "id": "side_business",
        "name": "副业与商业闭环",
        "keywords": ["副业", "企业IP", "获客", "直播间话术"],
        "principles": [
            "内容不只是曝光，还要逐步建立可信任的产品入口。",
            "免费流量内容负责筛选人群，私域或直播负责加深关系。",
            "规划时要安排信任内容和转化内容，不能只做情绪共鸣。",
        ],
        "useFor": ["发布规划", "选题生成器"],
    },
]


def clean_text(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    # Many slide PDFs use custom embedded fonts. Keep only snippets that look
    # readable enough; file titles still preserve the course source.
    readable = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff" or ch.isascii())
    if not text or readable / max(len(text), 1) < 0.45:
        return ""
    return text[:1200]


def module_for_name(name):
    hits = []
    for mod in MODULES:
        score = sum(1 for kw in mod["keywords"] if kw in name)
        if score:
            hits.append((score, mod["id"]))
    return sorted(hits, reverse=True)[0][1] if hits else "personal_ip_positioning"


def read_pdf(path):
    try:
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        raw = "\n".join((page.extract_text() or "") for page in reader.pages[:6])
        return pages, clean_text(raw)
    except Exception:
        return 0, ""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sources = []
    for path in sorted(DANAO_DIR.glob("*.pdf")):
        pages, snippet = read_pdf(path)
        sources.append(
            {
                "file": path.name,
                "path": str(path),
                "pages": pages,
                "moduleId": module_for_name(path.name),
                "snippet": snippet,
            }
        )

    by_module = {mod["id"]: [] for mod in MODULES}
    for source in sources:
        by_module.setdefault(source["moduleId"], []).append(source["file"])

    payload = {
        "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "sourceDir": str(DANAO_DIR),
        "sourceCount": len(sources),
        "sources": sources,
        "modules": [{**mod, "sources": by_module.get(mod["id"], [])} for mod in MODULES],
        "workflowRules": [
            "发布复盘：先看作品数据和转写稿，再用平台流量、内容标签、AI剪辑三类方法判断优化点。",
            "选题生成器：先参考个人IP定位、内容标签和AI爆款文案，再结合手动主题和痛点生成标题、封面、脚本。",
            "标题封面文案优化：先参考口播流程、表现力和AI爆款文案，输出能直接拍摄的口播稿。",
            "爆款短视频拆解：先参考平台机制、黄金三秒、脚本结构和封面标签，拆出可归档复用模板。",
            "发布规划：先参考超级个体心态、变现路径和账号信任资产，安排拉新、信任、转化、复盘内容。",
        ],
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} with {len(sources)} sources")


if __name__ == "__main__":
    main()
