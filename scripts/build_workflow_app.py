import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from build_strategy_dashboard import (
    DATA_PATH,
    ROOT,
    build_rows,
    json_for_html,
)


OUT_DIR = ROOT / "output" / "workflow_app"
OUT_FILE = OUT_DIR / "index.html"
DANAO_PATH = ROOT / "data" / "danao_knowledge.json"


def load_danao():
    if not DANAO_PATH.exists():
        return {
            "updatedAt": "",
            "sourceCount": 0,
            "sources": [],
            "modules": [],
            "workflowRules": [],
        }
    try:
        data = json.loads(DANAO_PATH.read_text(encoding="utf-8"))
        for source in data.get("sources", []):
            source.pop("snippet", None)
        return data
    except json.JSONDecodeError:
        return {
            "updatedAt": "",
            "sourceCount": 0,
            "sources": [],
            "modules": [],
            "workflowRules": [],
        }


def render(rows):
    data = {
        "videos": rows,
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "pillars": [
            "AI超级个体内容管理",
            "AI内容工作台/短视频工作流",
            "智能体提效/内容自动化",
            "追星心理/理想自我",
            "边界感/反讨好",
            "女性成长/自我觉醒",
            "情绪管理/内核稳定",
            "行动力/破碎重建",
            "文学哲思/独处",
        ],
        "painPoints": [
            "内容越做越乱，不知道怎么把热点、选题、文案和复盘连成一套流程",
            "每天临时想选题，发完作品也不知道下一条怎么优化",
            "采集了很多作品和热点，却不会变成自己的口播文案",
            "想用 AI 做内容管理，但不知道该让 AI 先处理哪一步",
            "有工具、有素材、有想法，但发布节奏一直不稳定",
            "讨好别人却丢了自己",
            "太敏感导致情绪内耗",
            "追星背后的理想自我投射",
            "不敢改变的人生停滞",
            "关系里没有边界感",
            "清醒但做不到行动",
            "破碎后如何重新开始",
            "把自己活成别人期待的样子",
        ],
        "danao": load_danao(),
    }

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI 超级个体工作台 · AI 超级个体内容管理</title>
  <style>
    :root {{
      --bg:#070b16; --panel:rgba(13,20,36,.78); --panel-strong:rgba(18,28,50,.92);
      --ink:#edf6ff; --muted:#91a3ba; --line:rgba(140,170,220,.20);
      --blue:#4f7bff; --cyan:#22d3ee; --green:#34d399; --rose:#fb5f87; --amber:#f6c453; --violet:#9b7cff;
      --home:#22d3ee; --library:#4f7bff; --optimizer:#fb5f87; --viral:#ff7aa8; --ideas:#a78bfa; --planner:#34d399; --update:#f6c453;
      --active:var(--home); --active-soft:rgba(34,211,238,.14); --active-line:rgba(34,211,238,.34);
      --glow:0 0 36px rgba(34,211,238,.18), 0 18px 80px rgba(0,0,0,.38);
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;
      background:
        radial-gradient(circle at 20% -10%, rgba(79,123,255,.36), transparent 34%),
        radial-gradient(circle at 84% 8%, rgba(34,211,238,.22), transparent 28%),
        linear-gradient(145deg,#050812 0%,#0b1020 48%,#070b16 100%);
      color:var(--ink);
    }}
    body:before {{
      content:""; position:fixed; inset:0; pointer-events:none; opacity:.42;
      background-image:linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
      background-size:32px 32px;
      mask-image:linear-gradient(to bottom, black, transparent 82%);
    }}
    body[data-view="home"] {{ --active:var(--home); --active-soft:rgba(34,211,238,.14); --active-line:rgba(34,211,238,.34); }}
    body[data-view="library"] {{ --active:var(--library); --active-soft:rgba(79,123,255,.15); --active-line:rgba(79,123,255,.38); }}
    body[data-view="optimizer"] {{ --active:var(--optimizer); --active-soft:rgba(251,95,135,.14); --active-line:rgba(251,95,135,.38); }}
    body[data-view="viral"] {{ --active:var(--viral); --active-soft:rgba(255,122,168,.15); --active-line:rgba(255,122,168,.40); }}
    body[data-view="ideas"] {{ --active:var(--ideas); --active-soft:rgba(167,139,250,.15); --active-line:rgba(167,139,250,.38); }}
    body[data-view="planner"] {{ --active:var(--planner); --active-soft:rgba(52,211,153,.13); --active-line:rgba(52,211,153,.36); }}
    body[data-view="update"] {{ --active:var(--update); --active-soft:rgba(246,196,83,.14); --active-line:rgba(246,196,83,.38); }}
    .app {{ display:grid; grid-template-columns:288px minmax(0,1fr); min-height:100vh; position:relative; }}
    aside {{
      background:linear-gradient(180deg, rgba(11,17,31,.94), rgba(8,12,22,.82));
      color:#eaf0f7; padding:24px 16px; position:sticky; top:0; height:100vh;
      border-right:1px solid var(--line); box-shadow:18px 0 70px rgba(0,0,0,.24); backdrop-filter:blur(18px);
    }}
    .brand {{ font-size:22px; font-weight:900; margin-bottom:6px; letter-spacing:.02em; }}
    .brand:after {{ content:""; display:block; width:54px; height:3px; margin-top:12px; border-radius:99px; background:linear-gradient(90deg,var(--cyan),var(--blue),var(--violet)); box-shadow:0 0 18px rgba(34,211,238,.6); }}
    .aside-note {{ color:#9dadbd; font-size:13px; line-height:1.6; margin:18px 0 24px; }}
    nav button {{
      --nav-color:var(--cyan); width:100%; text-align:left; margin:6px 0; background:transparent; color:#cdd9e7; border:1px solid transparent;
      border-radius:10px; padding:12px 13px; cursor:pointer; font-size:14px; transition:.18s ease; display:flex; align-items:center; gap:10px;
    }}
    nav button:before {{ content:""; width:9px; height:9px; border-radius:50%; background:var(--nav-color); box-shadow:0 0 16px var(--nav-color); flex:0 0 auto; }}
    nav button[data-view="home"] {{ --nav-color:var(--home); }}
    nav button[data-view="library"] {{ --nav-color:var(--library); }}
    nav button[data-view="optimizer"] {{ --nav-color:var(--optimizer); }}
    nav button[data-view="viral"] {{ --nav-color:var(--viral); }}
    nav button[data-view="ideas"] {{ --nav-color:var(--ideas); }}
    nav button[data-view="planner"] {{ --nav-color:var(--planner); }}
    nav button[data-view="update"] {{ --nav-color:var(--update); }}
    nav button:hover {{ border-color:var(--active-line); background:var(--active-soft); }}
    nav button.active {{ background:linear-gradient(90deg, var(--active-soft), rgba(255,255,255,.035)); color:#fff; border-color:var(--active-line); box-shadow:inset 0 0 24px var(--active-soft); }}
    main {{ padding:28px 32px 46px; position:relative; }}
    header {{
      display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin-bottom:20px;
      padding:22px; border:1px solid var(--active-line); border-radius:18px; background:linear-gradient(135deg, var(--active-soft), rgba(14,23,42,.76) 42%, rgba(11,18,34,.58)); box-shadow:var(--glow);
    }}
    h1 {{ margin:0; font-size:32px; letter-spacing:0; line-height:1.15; }}
    .sub {{ color:var(--muted); line-height:1.7; margin:10px 0 0; max-width:880px; }}
    .status-pill {{
      background:var(--active-soft); color:#f3fbff; border:1px solid var(--active-line);
      border-radius:999px; padding:9px 13px; font-size:13px; white-space:nowrap; box-shadow:0 0 24px var(--active-soft);
    }}
    .view {{ display:none; }}
    .view.active {{ display:block; }}
    .grid {{ display:grid; gap:14px; }}
    .kpis {{ grid-template-columns:repeat(4,minmax(0,1fr)); margin-bottom:18px; }}
    .panel {{
      background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:18px;
      box-shadow:0 18px 70px rgba(0,0,0,.22); backdrop-filter:blur(18px);
    }}
    .view.active > .panel, .view.active > .grid > .panel {{ border-color:var(--active-line); }}
    .module-label {{ display:inline-flex; align-items:center; gap:8px; margin:0 0 10px; color:#dfeaff; font-size:12px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }}
    .module-label:before {{ content:""; width:22px; height:3px; border-radius:99px; background:var(--active); box-shadow:0 0 18px var(--active); }}
    .kpi {{ position:relative; overflow:hidden; }}
    .kpi:before {{ content:""; position:absolute; inset:0 0 auto 0; height:3px; background:var(--kpi-color, var(--cyan)); opacity:.95; }}
    .kpi-total {{ --kpi-color:var(--library); }}
    .kpi-avg {{ --kpi-color:var(--planner); }}
    .kpi-best {{ --kpi-color:var(--ideas); }}
    .kpi-need {{ --kpi-color:var(--optimizer); }}
    .kpi b {{ display:block; font-size:32px; margin-bottom:4px; color:#fff; }}
    .kpi span, .muted {{ color:var(--muted); font-size:13px; line-height:1.55; }}
    .kpi-action {{ margin-top:12px; width:100%; border-radius:10px; padding:9px 10px; cursor:pointer; color:#fff; font-weight:800; border:1px solid rgba(251,95,135,.45); background:linear-gradient(135deg, rgba(251,95,135,.75), rgba(167,139,250,.58)); box-shadow:0 0 22px rgba(251,95,135,.18); }}
    .kpi-action:hover {{ transform:translateY(-1px); filter:saturate(1.08); }}
    .toolbar {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin:12px 0 16px; }}
    input, textarea, select {{ width:100%; border:1px solid var(--line); border-radius:10px; padding:11px 12px; background:rgba(6,10,20,.72); color:var(--ink); font:inherit; outline:none; }}
    input:focus, textarea:focus, select:focus {{ border-color:rgba(34,211,238,.58); box-shadow:0 0 0 3px rgba(34,211,238,.12); }}
    option {{ background:#101827; color:#edf6ff; }}
    textarea {{ min-height:150px; resize:vertical; line-height:1.65; }}
    .small-input {{ max-width:260px; }}
    button.primary {{ background:linear-gradient(135deg,var(--active),var(--blue)); color:#fff; border:1px solid var(--active-line); border-radius:10px; padding:10px 14px; cursor:pointer; box-shadow:0 0 22px var(--active-soft); }}
    button.secondary {{ background:rgba(255,255,255,.06); color:var(--ink); border:1px solid var(--line); border-radius:10px; padding:10px 14px; cursor:pointer; }}
    button.primary:disabled, button.secondary:disabled {{ opacity:.48; cursor:not-allowed; transform:none; }}
    button.secondary.active-filter {{ border-color:rgba(251,95,135,.55); background:rgba(251,95,135,.16); color:#ffdbe5; box-shadow:0 0 20px rgba(251,95,135,.12); }}
    button.primary:hover, button.secondary:hover {{ transform:translateY(-1px); }}
    .videos {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
    .video {{ border-top:4px solid var(--theme-color, var(--blue)); }}
    .video.theme-star {{ --theme-color:var(--amber); }}
    .video.theme-boundary {{ --theme-color:var(--optimizer); }}
    .video.theme-growth {{ --theme-color:var(--planner); }}
    .video.theme-emotion {{ --theme-color:var(--cyan); }}
    .video.theme-action {{ --theme-color:var(--blue); }}
    .video.theme-literary {{ --theme-color:var(--ideas); }}
    .video.warn {{ border-top-color:var(--amber); }}
    .video.low {{ border-top-color:var(--rose); }}
    .row {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }}
    h2 {{ margin:0 0 12px; font-size:20px; }}
    h3 {{ margin:0; font-size:16px; line-height:1.45; }}
    .score {{ min-width:48px; height:48px; display:grid; place-items:center; border-radius:50%; background:rgba(79,123,255,.14); color:#bcd0ff; border:1px solid rgba(79,123,255,.35); font-weight:900; box-shadow:0 0 24px rgba(79,123,255,.18); }}
    .chips {{ display:flex; flex-wrap:wrap; gap:7px; margin:12px 0; }}
    .chip {{ font-size:12px; padding:5px 9px; border-radius:99px; background:rgba(145,163,186,.13); color:#c8d5e3; border:1px solid rgba(145,163,186,.16); }}
    .theme-chip {{ background:rgba(255,255,255,.06); border-color:var(--theme-color, var(--line)); color:#fff; }}
    .cover {{ background:rgba(251,95,135,.10); border:1px dashed rgba(251,95,135,.38); color:#ffadc1; padding:11px; border-radius:10px; font-weight:800; }}
    .stats-grid {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:8px; margin:12px 0; }}
    .stat-pill {{ border:1px solid var(--line); border-radius:10px; padding:9px 8px; background:rgba(255,255,255,.045); }}
    .stat-pill b {{ display:block; font-size:16px; color:#fff; margin-bottom:2px; }}
    .stat-pill span {{ color:var(--muted); font-size:12px; }}
    .review-sections {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; margin-top:12px; }}
    .review-tip {{ border:1px solid var(--line); border-radius:12px; padding:11px; background:rgba(255,255,255,.04); line-height:1.6; }}
    .review-tip b {{ color:var(--active); }}
    details.transcript-box {{ margin-top:12px; border:1px solid var(--line); border-radius:12px; background:rgba(6,10,20,.42); overflow:hidden; }}
    details.transcript-box summary {{ cursor:pointer; padding:11px 12px; color:#fff; font-weight:800; }}
    .transcript-content {{ padding:0 12px 12px; color:#d9e5f3; max-height:220px; overflow:auto; white-space:pre-wrap; line-height:1.75; font-size:13px; }}
    .cover-trends {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-top:12px; }}
    .cover-example {{ border:1px solid var(--line); border-radius:14px; overflow:hidden; background:rgba(255,255,255,.045); }}
    .cover-example img {{ width:100%; aspect-ratio:3/4; object-fit:cover; display:block; background:#0b1120; }}
    .cover-example-body {{ padding:10px; display:grid; gap:6px; }}
    .cover-example-title {{ font-size:13px; line-height:1.45; color:#fff; font-weight:800; }}
    .cover-example-meta {{ color:var(--muted); font-size:12px; line-height:1.45; }}
    .actions {{ display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }}
    .split {{ grid-template-columns:1fr 1fr; }}
    .three {{ grid-template-columns:repeat(3,minmax(0,1fr)); }}
    .result-list {{ display:grid; gap:10px; margin-top:12px; }}
    .result {{ border:1px solid var(--line); background:rgba(255,255,255,.045); border-radius:12px; padding:13px; line-height:1.65; }}
    .danao-ref {{ border-color:rgba(34,211,238,.34); background:linear-gradient(135deg, rgba(34,211,238,.10), rgba(167,139,250,.08)); }}
    .result b {{ color:var(--active); }}
    .teleprompter-pack {{
      border:1px solid rgba(52,211,153,.46); border-radius:16px; padding:16px;
      background:linear-gradient(180deg, rgba(52,211,153,.12), rgba(6,10,20,.55));
      box-shadow:0 0 34px rgba(52,211,153,.10);
    }}
    .teleprompter-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:12px; }}
    .teleprompter-label {{ display:inline-flex; align-items:center; gap:7px; color:#bfffe6; font-size:12px; font-weight:900; letter-spacing:.08em; }}
    .teleprompter-label:before {{ content:""; width:9px; height:9px; border-radius:50%; background:var(--green); box-shadow:0 0 16px var(--green); }}
    .teleprompter-title {{ margin-top:6px; color:#fff; font-size:18px; font-weight:950; line-height:1.35; }}
    .teleprompter-copy {{ white-space:nowrap; font-weight:900; }}
    .teleprompter-box {{
      min-height:240px; max-height:520px; overflow:auto; white-space:pre-wrap; line-height:1.9;
      color:#f8fffb; font-size:16px; padding:18px; border-radius:14px;
      border:1px solid rgba(52,211,153,.34); background:rgba(3,10,12,.70);
    }}
    .reference-pack {{
      margin-top:14px; border:1px solid rgba(145,163,186,.22); border-radius:16px; padding:14px;
      background:rgba(255,255,255,.028);
    }}
    .reference-head {{ display:flex; justify-content:space-between; gap:12px; align-items:center; margin-bottom:10px; }}
    .reference-head b {{ color:#dbeafe; }}
    .reference-grid {{ display:grid; gap:10px; }}
    .formula-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }}
    .formula-card {{ border:1px solid var(--line); background:rgba(255,255,255,.045); border-radius:12px; padding:12px; }}
    .formula-card strong {{ display:block; color:#fff; margin-bottom:6px; }}
    .formula-card code {{ color:#ffe66d; white-space:normal; line-height:1.6; }}
    .metric-row {{ display:grid; grid-template-columns:120px minmax(0,1fr); gap:10px; align-items:center; }}
    .meter {{ height:9px; border-radius:99px; background:rgba(255,255,255,.08); overflow:hidden; }}
    .meter span {{ display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,var(--rose),var(--amber),var(--cyan)); }}
    .idea-results {{ grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; max-height:560px; overflow:auto; padding-right:3px; }}
    .idea-card {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; align-items:center; border-left:3px solid var(--ideas); padding:10px 11px; }}
    .idea-card strong {{ display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; margin-bottom:5px; color:#fff; font-size:14px; line-height:1.42; }}
    .idea-card button {{ white-space:nowrap; padding:8px 10px; }}
    .idea-meta {{ display:flex; gap:6px; flex-wrap:wrap; }}
    .idea-card.active {{ border-color:var(--ideas); background:rgba(167,139,250,.12); box-shadow:0 0 28px rgba(167,139,250,.12); }}
    .link-analyzer {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; align-items:center; }}
    .link-analyzer input {{ min-height:52px; font-size:15px; border-color:rgba(255,122,168,.34); box-shadow:0 0 24px rgba(255,122,168,.08); }}
    .link-analyzer button {{ min-height:52px; min-width:146px; font-weight:900; }}
    .home-profile-sync {{ align-items:start; margin-top:12px; }}
    .home-profile-sync input {{ min-height:58px; }}
    .home-profile-sync .sync-cta {{
      min-width:146px; min-height:54px; height:54px; padding:0 20px; margin-top:0;
      display:flex; align-items:center; justify-content:center; text-align:center; font-size:18px; line-height:1; white-space:nowrap;
    }}
    .archive-list {{ display:grid; gap:8px; margin-top:12px; max-height:420px; overflow:auto; }}
    .archive-item {{ border:1px solid var(--line); border-radius:12px; padding:10px; background:rgba(255,255,255,.04); }}
    .archive-item strong {{ display:block; color:#fff; line-height:1.4; margin-bottom:4px; }}
    .archive-details {{ margin-top:10px; border-top:1px solid var(--line); padding-top:10px; display:grid; gap:8px; }}
    .archive-details .copybox {{ max-height:180px; overflow:auto; background:rgba(6,10,20,.42); border:1px solid var(--line); border-radius:10px; padding:10px; }}
    .viral-cover-compare {{ display:grid; grid-template-columns:180px minmax(0,1fr); gap:12px; align-items:start; }}
    .viral-cover-compare img {{ width:100%; aspect-ratio:9/16; object-fit:contain; border-radius:12px; border:1px solid var(--line); background:#07101f; }}
    .cover-advice-list {{ display:grid; gap:8px; }}
    .cover-advice-list div {{ border:1px solid var(--line); border-radius:10px; padding:9px 10px; background:rgba(255,255,255,.04); line-height:1.6; }}
    .viral-deep-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-top:10px; }}
    .viral-deep-card {{ border:1px solid var(--line); border-radius:12px; padding:12px; background:rgba(255,255,255,.045); line-height:1.65; }}
    .viral-deep-card strong {{ display:block; color:#fff; margin-bottom:7px; }}
    .viral-deep-card ul {{ margin:0; padding-left:18px; color:#d5e1ef; }}
    .viral-deep-card li {{ margin:3px 0; }}
    .script-pack {{ margin-top:14px; border-color:var(--active-line); }}
    .script-title {{ font-size:18px; color:#fff; font-weight:900; margin-bottom:8px; }}
    .recreate-pack {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px; }}
    .recreate-pack .copybox {{ max-height:260px; overflow:auto; }}
    .qd-card {{ border:1px solid var(--active-line); border-radius:16px; background:linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.035)); overflow:hidden; }}
    .qd-head {{ display:flex; align-items:center; justify-content:space-between; gap:12px; padding:12px 14px; border-bottom:1px solid var(--line); background:rgba(255,255,255,.045); }}
    .qd-tabs {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
    .qd-tab {{ border:1px solid var(--line); border-radius:999px; padding:6px 10px; color:#cbd7e6; background:rgba(255,255,255,.045); font-size:12px; }}
    .qd-tab.active {{ color:#06111e; background:linear-gradient(135deg,var(--active),#fff07d); border-color:rgba(255,255,255,.55); font-weight:900; }}
    .qd-actions {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
    .qd-actions button {{ padding:8px 10px; font-size:12px; }}
    .qd-table {{ width:100%; border-collapse:collapse; table-layout:fixed; }}
    .qd-table th, .qd-table td {{ border-bottom:1px solid var(--line); padding:12px; text-align:left; vertical-align:top; }}
    .qd-table th {{ color:#aebed2; font-size:12px; font-weight:900; background:rgba(6,10,20,.30); }}
    .qd-video-cell {{ display:grid; grid-template-columns:68px minmax(0,1fr); gap:10px; align-items:start; }}
    .qd-thumb {{ width:68px; aspect-ratio:3/4; border-radius:9px; border:1px solid var(--line); object-fit:cover; background:linear-gradient(145deg, rgba(255,122,168,.28), rgba(34,211,238,.20)); display:grid; place-items:center; color:#fff; font-size:12px; font-weight:900; overflow:hidden; }}
    .qd-thumb img {{ width:100%; height:100%; object-fit:cover; display:block; }}
    .qd-video-title {{ color:#fff; font-weight:900; line-height:1.45; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
    .qd-video-meta {{ margin-top:6px; color:var(--muted); font-size:12px; line-height:1.5; }}
    .qd-copy-preview {{ max-height:118px; overflow:auto; white-space:pre-wrap; line-height:1.7; color:#dbe7f5; }}
    .qd-summary-list {{ margin:0; padding-left:18px; color:#d5e1ef; line-height:1.65; }}
    .qd-summary-list li {{ margin:2px 0; }}
    .qd-more {{ margin-top:8px; }}
    .qd-ai-layout {{ display:grid; grid-template-columns:360px minmax(0,1fr); gap:14px; align-items:stretch; }}
    .qd-ai-input, .qd-ai-output {{ border:1px solid var(--line); border-radius:14px; padding:14px; background:rgba(6,10,20,.38); }}
    .qd-template-title {{ display:flex; align-items:center; gap:8px; color:#fff; font-weight:900; margin-bottom:12px; }}
    .qd-template-title:before {{ content:""; width:24px; height:24px; border-radius:8px; background:linear-gradient(135deg,#ffe66d,var(--active)); box-shadow:0 0 20px var(--active-soft); }}
    .qd-textarea {{ min-height:230px; max-height:330px; overflow:auto; border:1px solid var(--line); border-radius:12px; padding:12px; background:rgba(255,255,255,.035); white-space:pre-wrap; line-height:1.7; color:#dbe7f5; }}
    .qd-char-row {{ display:flex; justify-content:space-between; gap:10px; margin-top:10px; color:var(--muted); font-size:12px; }}
    .qd-generate {{ width:100%; margin-top:14px; min-height:50px; font-weight:950; }}
    .qd-output-paper {{ min-height:260px; max-height:390px; overflow:auto; white-space:pre-wrap; line-height:1.85; color:#edf6ff; padding:14px; border:1px solid var(--line); border-radius:12px; background:rgba(255,255,255,.045); }}
    .qd-output-label {{ margin:10px 0; color:var(--muted); font-size:12px; }}
    .qd-output-actions {{ display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; margin-top:12px; }}
    .qd-output-actions button {{ padding:9px 11px; }}
    .qd-agent-bar {{ display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom:10px; color:var(--muted); font-size:12px; }}
    .qd-agent-bar b {{ color:var(--active); }}
    .qd-mode-row {{ display:flex; gap:8px; flex-wrap:wrap; margin:10px 0 12px; }}
    .qd-mode {{ border:1px solid var(--line); border-radius:999px; padding:8px 11px; background:rgba(255,255,255,.055); color:#dce8f5; cursor:pointer; font-size:12px; font-weight:800; }}
    .qd-mode.active {{ color:#06111e; border-color:rgba(255,255,255,.66); background:linear-gradient(135deg,var(--active),#fff07d); box-shadow:0 0 18px var(--active-soft); }}
    .calendar {{ grid-template-columns:repeat(7,minmax(0,1fr)); }}
    .day {{ min-height:120px; border-top:4px solid var(--day-color, var(--planner)); }}
    .day:nth-child(1) {{ --day-color:var(--optimizer); }}
    .day:nth-child(2) {{ --day-color:var(--amber); }}
    .day:nth-child(3) {{ --day-color:var(--cyan); }}
    .day:nth-child(4) {{ --day-color:var(--planner); }}
    .day:nth-child(5) {{ --day-color:var(--rose); }}
    .day:nth-child(6) {{ --day-color:var(--ideas); }}
    .day:nth-child(7) {{ --day-color:var(--blue); }}
    .day strong {{ color:var(--day-color); }}
    .planner-summary {{ grid-template-columns:repeat(3,minmax(0,1fr)); margin-bottom:14px; }}
    .planner-summary .result {{ min-height:116px; }}
    .planner-actions {{ grid-template-columns:repeat(2,minmax(0,1fr)); margin-top:14px; }}
    .plan-card h3 {{ margin:8px 0 10px; }}
    .plan-card ul, .trust-card ul {{ margin:10px 0 0; padding-left:18px; color:#cbd7e6; line-height:1.65; }}
    .plan-card li, .trust-card li {{ margin:4px 0; }}
    .day-goal {{ color:#fff; font-weight:900; margin-top:8px; }}
    .day-cover {{ display:inline-block; margin-top:8px; padding:7px 9px; border-radius:9px; background:rgba(251,95,135,.12); color:#ffb4c7; border:1px dashed rgba(251,95,135,.36); font-size:12px; line-height:1.45; }}
    .copybox {{ white-space:pre-wrap; line-height:1.7; }}
    .progress-log {{ max-height:260px; overflow:auto; white-space:pre-wrap; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; line-height:1.6; color:#b8c7da; }}
    .refresh-state {{ border-color:var(--active-line); background:var(--active-soft); }}
    .hero-sync {{
      position:relative; overflow:hidden; margin-bottom:18px; padding:22px; border-radius:18px;
      border:1px solid rgba(246,196,83,.48);
      background:
        linear-gradient(135deg, rgba(246,196,83,.20), rgba(251,95,135,.15) 42%, rgba(79,123,255,.14)),
        rgba(13,20,36,.82);
      box-shadow:0 24px 90px rgba(246,196,83,.16), 0 0 60px rgba(251,95,135,.10);
    }}
    .hero-sync:before {{
      content:""; position:absolute; inset:-1px; pointer-events:none;
      background:linear-gradient(90deg, transparent, rgba(255,255,255,.18), transparent);
      transform:translateX(-64%); animation:shine 5s ease-in-out infinite;
    }}
    @keyframes shine {{ 0%, 58% {{ transform:translateX(-64%); }} 100% {{ transform:translateX(64%); }} }}
    .hero-sync-inner {{ position:relative; display:grid; grid-template-columns:minmax(0,1fr) 178px; gap:18px; align-items:stretch; }}
    .hero-sync h2 {{ font-size:24px; margin-bottom:8px; }}
    .hero-sync p {{ margin:0; max-width:760px; }}
    .sync-cta {{
      min-width:230px; min-height:58px; border-radius:14px; padding:15px 20px; cursor:pointer;
      color:#07101f; font-weight:950; font-size:16px; border:1px solid rgba(255,255,255,.72);
      background:linear-gradient(135deg,#ffe66d 0%,#ff7aa8 48%,#6ee7ff 100%);
      box-shadow:0 18px 48px rgba(255,122,168,.28), 0 0 34px rgba(255,230,109,.28);
    }}
    .sync-cta:hover {{ transform:translateY(-2px); filter:saturate(1.12); }}
    .sync-cta:disabled {{ cursor:not-allowed; opacity:.72; transform:none; }}
    .self-sync-card {{
      width:178px; min-width:178px; height:178px; min-height:0; align-self:center; display:flex; flex-direction:column; align-items:flex-start; justify-content:space-between;
      text-align:left; color:#06111e; border-radius:18px; padding:18px; line-height:1.25;
      background:linear-gradient(135deg,#6ee7ff 0%,#ffe66d 48%,#ff7aa8 100%);
      box-shadow:0 24px 70px rgba(34,211,238,.24), 0 0 42px rgba(255,122,168,.22);
    }}
    .self-sync-card span:first-child {{ font-size:13px; letter-spacing:.08em; text-transform:uppercase; opacity:.72; }}
    .self-sync-card span:last-child {{ font-size:22px; font-weight:950; }}
    .home-refresh-status {{ margin-top:12px; width:100%; min-height:48px; border-color:rgba(246,196,83,.34); background:rgba(246,196,83,.10); }}
    .hidden {{ display:none !important; }}
    @media (max-width:1080px) {{
      .app {{ grid-template-columns:1fr; }}
      aside {{ position:relative; height:auto; }}
      nav {{ display:flex; overflow:auto; gap:6px; }}
      nav button {{ width:auto; white-space:nowrap; }}
      .kpis,.videos,.split,.three,.calendar,.planner-summary,.planner-actions {{ grid-template-columns:1fr; }}
      .cover-trends {{ grid-template-columns:1fr; }}
      .stats-grid,.review-sections {{ grid-template-columns:1fr; }}
      main {{ padding:18px; }}
      header {{ display:block; }}
      .status-pill {{ display:inline-block; margin-top:10px; }}
      .hero-sync-inner {{ grid-template-columns:1fr; }}
      .sync-cta {{ width:100%; }}
      .self-sync-card {{ width:100%; min-width:0; height:auto; aspect-ratio:auto; min-height:118px; }}
      .home-refresh-status {{ width:100%; }}
      .formula-grid,.metric-row,.idea-results,.link-analyzer {{ grid-template-columns:1fr; }}
      .viral-cover-compare {{ grid-template-columns:1fr; }}
      .viral-deep-grid {{ grid-template-columns:1fr; }}
      .recreate-pack {{ grid-template-columns:1fr; }}
      .qd-ai-layout {{ grid-template-columns:1fr; }}
      .qd-table {{ min-width:760px; }}
      .qd-card {{ overflow:auto; }}
    }}
  </style>
</head>
<body data-view="home">
  <div class="app">
    <aside>
      <div class="brand">AI 超级个体工作台</div>
      <div class="aside-note">AI 超级个体内容管理：发完作品后复盘，发布前优化标题、封面、文案，并持续生成下一批选题。</div>
      <nav>
        <button class="active" data-view="home">工作台首页</button>
        <button data-view="library">已发布复盘</button>
        <button data-view="ideas">选题生成器</button>
        <button data-view="optimizer">标题/封面/文案优化</button>
        <button data-view="viral">爆款短视频拆解</button>
        <button data-view="planner">发布规划</button>
        <button data-view="update">抖音数据抓取</button>
      </nav>
    </aside>
    <main>
      <header>
        <div>
          <h1>AI 超级个体内容管理</h1>
          <p class="sub">这是你的本地短视频指挥舱：直接使用从抖音账号抓取的作品信息和转写稿，帮助你复盘已发布内容，并随时生成标题、封面、文案结构和下一批选题。</p>
        </div>
        <div class="status-pill">本地数据：{len(rows)} 条 · 生成于 {data['generatedAt']}</div>
      </header>

      <section id="home" class="view active">
        <div class="hero-sync">
          <div class="hero-sync-inner">
            <div>
              <div class="module-label">douyin data sync</div>
              <h2>输入博主主页链接，抓取公开作品并自动分析</h2>
              <p class="muted">粘贴任意抖音博主主页分享链接，工作台会抓取该主页公开展示的短视频作品；只有通过目标作者归属校验后，才会更新作品库并快速生成分析。</p>
              <div class="link-analyzer home-profile-sync">
                <input id="homeProfileUrl" placeholder="粘贴博主主页分享链接，例如 https://v.douyin.com/... 或 douyin.com/user/...">
                <button class="sync-cta" id="homeRefreshProfile">抓取抖音作品</button>
              </div>
              <div id="homeRefreshStatus" class="result home-refresh-status"><b>状态：</b>待命</div>
            </div>
            <button class="sync-cta self-sync-card" id="homeRefreshDouyin"><span>My Account</span><span>抓取我的抖音</span></button>
          </div>
        </div>
        <div class="grid kpis">
          <div class="panel kpi kpi-total"><b id="kpiTotal">0</b><span>作品库</span></div>
          <div class="panel kpi kpi-avg"><b id="kpiAvg">0</b><span>平均潜力分</span></div>
          <div class="panel kpi kpi-best"><b id="kpiBest">-</b><span>最强主题</span></div>
          <div class="panel kpi kpi-need"><b id="kpiNeed">0</b><span>待优化作品</span><button class="kpi-action" id="viewNeedVideos">查看待优化内容</button></div>
        </div>
        <div class="grid split">
          <div class="panel">
            <div class="module-label">action center</div>
            <h2>今天先做什么</h2>
            <div id="todayActions" class="result-list"></div>
          </div>
          <div class="panel">
            <div class="module-label">growth map</div>
            <h2>账号下一步方向</h2>
            <div class="result-list">
              <div class="result"><b>主线：</b>女性清醒成长，语气保持“温柔但锋利”。</div>
              <div class="result"><b>流量入口：</b>追星心理、关系边界、高敏感、行动重建。</div>
              <div class="result"><b>升级点：</b>每条视频从“被说中”再往前一步，给用户一个可执行动作。</div>
              <div class="result"><b>封面策略：</b>三行字固定为“痛点 + 反常识 + 栏目标签”。</div>
            </div>
          </div>
        </div>
      </section>

      <section id="library" class="view">
        <div class="module-label">content library</div>
        <h2>已发布作品复盘</h2>
        <div class="toolbar">
          <input class="small-input" id="searchVideo" placeholder="搜索标题、主题、标签">
          <select class="small-input" id="themeFilter"><option value="">全部主题</option></select>
          <button class="secondary" id="filterNeeds">只看待优化作品</button>
          <button class="secondary" id="sortScore">按潜力分排序</button>
        </div>
        <div class="grid videos" id="videoList"></div>
      </section>

      <section id="optimizer" class="view">
        <div class="grid split">
          <div class="panel">
            <div class="module-label">copy lab</div>
            <h2>发布前优化</h2>
            <label class="muted">标题/简介</label>
            <input id="draftTitle" placeholder="例如：你追的不是他，是你不敢活的人生">
            <div style="height:10px"></div>
            <label class="muted">口播稿/转写稿</label>
            <textarea id="draftText" placeholder="把你准备发布的文案或视频转写稿粘贴到这里"></textarea>
            <div class="toolbar">
              <select id="draftTheme">
                <option value="">自动判断主题</option>
              </select>
              <select id="draftHook"></select>
              <button class="primary" id="analyzeDraft">生成优化建议</button>
              <button class="secondary" id="plainRewrite">原文案大白话洗稿</button>
              <button class="secondary" id="useBestVideo">用最高分作品试填</button>
            </div>
          </div>
          <div class="panel">
            <div class="module-label">output radar</div>
            <h2>优化结果</h2>
            <div id="draftResult" class="result-list">
              <div class="result muted">粘贴文案后点击“生成优化建议”。</div>
            </div>
          </div>
        </div>
      </section>

      <section id="viral" class="view">
        <div class="panel">
          <div class="module-label">viral lab</div>
          <h2>爆款短视频拆解</h2>
          <label class="muted">短视频链接</label>
          <div class="link-analyzer">
            <input id="viralUrl" placeholder="粘贴抖音短视频链接，例如 https://v.douyin.com/... 或 https://www.douyin.com/video/...">
            <button class="primary" id="analyzeViral">分析链接</button>
          </div>
          <div class="result muted">这是独立的链接拆解工作台：粘贴一条短视频链接，系统会先像“提文案”一样生成视频、文案内容、全文摘要和复制操作；再像“AI文案-智能二创”一样生成可直接复制使用的二创成品。</div>
        </div>
        <div class="panel script-pack">
          <div class="module-label">growth pattern</div>
          <h2>拆解结果</h2>
          <div id="viralResult" class="result-list">
            <div class="result muted">粘贴短视频链接后点击“分析链接”，这里会生成提取文案表格、深度拆解、封面对照和 AI 二创文案。</div>
          </div>
        </div>
        <div class="panel script-pack">
          <div class="module-label">case archive</div>
          <h2>已归档爆款拆解</h2>
          <div id="viralArchiveList" class="archive-list">
            <div class="result muted">归档后的拆解会出现在选题生成器里，可选择套用。</div>
          </div>
        </div>
      </section>

      <section id="ideas" class="view">
        <div class="grid split">
          <div class="panel">
            <div class="module-label">topic engine</div>
            <h2>选题生成器</h2>
            <label class="muted">主题方向</label>
            <select id="ideaTheme"></select>
            <div style="height:8px"></div>
            <input id="ideaThemeCustom" placeholder="也可以手动输入主题方向，例如：AI 时代个人品牌 / 成交型信任内容">
            <div style="height:10px"></div>
            <label class="muted">用户痛点</label>
            <select id="ideaPain"></select>
            <div style="height:8px"></div>
            <input id="ideaPainCustom" placeholder="也可以手动输入用户痛点，例如：想做账号但不知道怎么让别人信任">
            <div style="height:10px"></div>
            <label class="muted">默认开场钩子公式</label>
            <select id="ideaHook"></select>
            <div style="height:10px"></div>
            <label class="muted">套用爆款拆解案例</label>
            <select id="ideaViralCase"></select>
            <div style="height:10px"></div>
            <label class="muted">抖音新闻热点</label>
            <select id="ideaHotTopic"><option value="">不结合热点</option></select>
            <div style="height:8px"></div>
            <input id="ideaHotCustom" placeholder="也可以手动输入抖音热点，例如：某条热搜词 / 某个新闻事件">
            <div class="toolbar">
              <button class="secondary" id="refreshHotTopics">刷新抖音热搜</button>
              <span class="muted" id="hotTopicStatus">可结合当前抖音新闻热点做口播</span>
            </div>
            <div class="toolbar">
              <button class="secondary" id="checkDedaoBrain">检查得到大脑</button>
              <span class="muted" id="dedaoBrainStatus">生成前会自动检索得到大脑记忆、成果和知识库</span>
            </div>
            <div style="height:10px"></div>
            <label class="muted">生成数量</label>
            <select id="ideaCount">
              <option>12</option><option selected>24</option><option>36</option>
            </select>
            <div class="toolbar">
              <button class="primary" id="generateIdeas">生成选题</button>
              <button class="secondary" id="copyIdeas">复制选题</button>
            </div>
          </div>
          <div class="panel">
            <div class="module-label">idea bank</div>
            <h2>选题结果</h2>
            <div id="ideasResult" class="result-list idea-results"></div>
          </div>
        </div>
        <div class="panel script-pack">
          <div class="module-label">script package</div>
          <h2>确定选题后的标题 / 文字稿 / 封面</h2>
          <div id="ideaPackage" class="result-list">
            <div class="result muted">点击任意选题右侧的“确定并生成”，这里会自动生成可发布素材。</div>
          </div>
        </div>
      </section>

      <section id="planner" class="view">
        <div class="module-label">weekly route</div>
        <h2>基于已抓取作品的 7 天发布规划</h2>
        <p class="muted">先点击“抓取我的抖音 App”同步你自己的作品库，系统会根据主题分布、潜力分、钩子/结构/封面短板，生成未来 7 天的发布指导、涨粉动作和信任感建设清单。</p>
        <div class="grid planner-summary" id="plannerSummary"></div>
        <div class="grid calendar" id="calendar"></div>
        <div class="grid planner-actions" id="trustActions"></div>
      </section>

      <section id="update" class="view">
        <div class="grid split">
          <div class="panel">
            <div class="module-label">data sync</div>
            <h2>按博主主页链接抓取作品并分析</h2>
            <div class="result-list">
              <div class="result"><b>主流程：</b>粘贴抖音博主主页分享链接，系统会抓取该主页公开展示的短视频作品、校验目标作者、获取详情、快速分析并重建工作台。</div>
              <div class="result"><b>准确性保护：</b>不会再把推荐流、热门链接或页面缓存里的视频当成目标博主作品；没有通过作者归属校验时会失败并保留原作品库。</div>
              <div class="result"><b>无需手动保存：</b>视频转写稿会自动保存到本地，工作台读取最新分析结果。</div>
              <div class="result"><b>完成后：</b>页面会自动刷新，你会看到新的作品库、复盘、标题封面建议和选题方向。</div>
              <label class="muted">博主主页分享链接</label>
              <div class="link-analyzer">
                <input id="profileUrl" placeholder="粘贴博主主页分享链接，例如 https://v.douyin.com/... 或 https://www.douyin.com/user/...">
                <button class="primary" id="refreshProfile">抓取这个博主</button>
              </div>
              <div class="actions">
                <button class="secondary" id="refreshDouyin">备用：抓取我的抖音 App（macOS）</button>
                <button class="secondary" id="checkRefresh">查看刷新状态</button>
              </div>
              <div id="refreshStatus" class="result refresh-state"><b>状态：</b>待命</div>
              <div id="refreshLog" class="result progress-log hidden"></div>
            </div>
          </div>
          <div class="panel">
            <div class="module-label">local files</div>
            <h2>本地文件</h2>
            <div class="copybox result">管理地址：
http://127.0.0.1:8787/

本地数据：
data/douyin_visible_posts.json
data/douyin_details_merged.json
output/transcripts/

如果管理地址打不开，启动：
cd /Users/a001/Documents/抖音工作流
.venv/bin/python scripts/serve_workflow_app.py</div>
          </div>
        </div>
      </section>
    </main>
  </div>

  <script>
    const state = {json_for_html(data)};

    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => [...document.querySelectorAll(sel)];
    const esc = (s) => String(s ?? '').replace(/[&<>"']/g, m => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[m]));
    const fmt = (n) => {{
      const num = Number(n || 0);
      if (num >= 100000000) return (num / 100000000).toFixed(1).replace(/\\.0$/,'') + '亿';
      if (num >= 10000) return (num / 10000).toFixed(1).replace(/\\.0$/,'') + '万';
      return String(num);
    }};
    const accessKey = new URLSearchParams(location.search).get('key') || '';
    const apiUrl = (path) => `${{path}}${{path.includes('?') ? '&' : '?'}}key=${{encodeURIComponent(accessKey)}}`;
    const apiOptions = (options={{}}) => ({{
      ...options,
      headers: {{ ...(options.headers || {{}}), ...(accessKey ? {{ 'X-Workflow-Key': accessKey }} : {{}}) }}
    }});
    state.dedaoBrain = {{ status:null, current:null, busy:false, cache:{{}} }};

    const hookFormulas = [
      {{ id:'pain_reverse', name:'痛点反转', pattern:'你以为{{pain}}，其实真正的问题是{{truth}}', use:'适合清醒观点、反常识选题' }},
      {{ id:'result_warning', name:'结果预警', pattern:'如果你还在{{pain}}，最后最容易失去的是{{loss}}', use:'适合关系、边界、内耗类内容' }},
      {{ id:'identity_call', name:'身份点名', pattern:'总是{{pain}}的人，先别急着怪自己', use:'适合高共鸣口播开头' }},
      {{ id:'three_seconds', name:'三秒扎心', pattern:'先说结论：{{truth}}，不是{{wrong}}', use:'适合需要快速停留的短视频' }},
      {{ id:'story_scene', name:'具体场景', pattern:'你有没有遇到过这种时刻：{{scene}}', use:'适合增强真实感和代入感' }},
      {{ id:'celebrity_projection', name:'追星投射', pattern:'你喜欢的不是他，是他替你活出了{{desire}}', use:'适合追星心理系列' }}
    ];

    function hookById(id) {{
      return hookFormulas.find(x=>x.id===id) || hookFormulas[0];
    }}

    function danaoModulesFor(area) {{
      const modules = state.danao?.modules || [];
      return modules.filter(mod => (mod.useFor || []).includes(area));
    }}

    function danaoPrinciples(area, limit=3) {{
      const modules = danaoModulesFor(area);
      const items = modules
        .map(mod => (mod.principles || [])[0] ? {{ module: mod.name, principle: mod.principles[0], sources: mod.sources || [] }} : null)
        .filter(Boolean);
      modules.forEach(mod => {{
        (mod.principles || []).slice(1).forEach(principle => items.push({{ module: mod.name, principle, sources: mod.sources || [] }}));
      }});
      return items.slice(0, limit);
    }}

    function renderDanaoReference(area, limit=3) {{
      const refs = danaoPrinciples(area, limit);
      if (!refs.length) return '';
      const sourceCount = state.danao?.sourceCount || 0;
      return `
        <div class="result danao-ref">
          <b>外部大脑参考：</b><span class="muted">已接入 danao 文件夹 ${{sourceCount}} 份课件，输出前先参考相关方法论。</span><br>
          ${{refs.map((x,i)=>`${{i+1}}. 【${{esc(x.module)}}】${{esc(x.principle)}}`).join('<br>')}}
        </div>`;
    }}

    function dedaoItems(memory) {{
      return (memory?.results || state.dedaoBrain?.current?.results || []).filter(x => x && (x.title || x.content));
    }}

    function renderDedaoBrainReference(area, memory, limit=4) {{
      const items = dedaoItems(memory).slice(0, limit);
      const status = state.dedaoBrain?.status;
      if (!items.length) {{
        const note = status?.configured === false
          ? '得到大脑 API 尚未配置，当前只使用本地 danao 课件。'
          : (memory?.message || '本次没有召回到足够相关的得到大脑笔记，已使用本地 danao 课件兜底。');
        return `<div class="result danao-ref"><b>得到大脑实时记忆：</b><span class="muted">${{esc(note)}}</span></div>`;
      }}
      return `
        <div class="result danao-ref">
          <b>得到大脑实时记忆：</b><span class="muted">已在“${{esc(area)}}”生成前召回 ${{items.length}} 条相关笔记/成果。</span><br>
          ${{items.map((x,i)=>`${{i+1}}. 【${{esc(x.title || '得到大脑笔记')}}】${{esc((x.content || '').slice(0, 118))}}`).join('<br>')}}
        </div>`;
    }}

    function dedaoCleanPoint(item) {{
      const raw = `${{item?.title || ''}}。${{item?.content || ''}}`
        .replace(/#[^\\s#]+/g, '')
        .replace(/[📌🔑✅⚠️]/g, '')
        .replace(/核心内容概览|核心工具模块|实战版|指南|方法论/g, '')
        .replace(/\\s+/g, ' ')
        .trim();
      const parts = raw.split(/[。！？!?；;\\n]/).map(x=>x.trim()).filter(x=>x.length >= 10);
      return safeClip(parts.find(x=>!/^(一|二|三|四|五|六|七|八|九|十|\\d+)[)、.]/.test(x)) || parts[0] || raw, 118);
    }}

    async function loadDedaoStatus() {{
      const target = $('#dedaoBrainStatus');
      if (target) target.textContent = '正在检查得到大脑连接...';
      try {{
        const res = await fetch(apiUrl('/api/dedao/status'), apiOptions({{ cache:'no-store' }}));
        const data = await res.json();
        state.dedaoBrain.status = data;
        if (target) {{
          if (!data.configured) target.textContent = '得到大脑未配置，当前使用本地 danao 课件';
          else if (data.reachable === false) target.textContent = data.message || '得到大脑连接失败';
          else target.textContent = `得到大脑已连接：${{data.label || '得到大脑'}}，知识库 ${{data.knowledgeCount || 0}} 个`;
        }}
        return data;
      }} catch (err) {{
        if (target) target.textContent = '无法连接得到大脑接口，当前使用本地 danao 课件';
        return {{ configured:false, reachable:false, message:String(err?.message || err) }};
      }}
    }}

    async function recallDedaoBrain(area, query, topK=6) {{
      const clean = String(query || '').replace(/\\s+/g, ' ').trim();
      if (!clean) return {{ ok:false, results:[], message:'检索词为空' }};
      const cacheKey = `${{area}}|${{clean}}|${{topK}}`;
      if (state.dedaoBrain.cache[cacheKey]) {{
        state.dedaoBrain.current = state.dedaoBrain.cache[cacheKey];
        return state.dedaoBrain.current;
      }}
      const target = $('#dedaoBrainStatus');
      if (target) target.textContent = `正在检索得到大脑：${{clean.slice(0, 26)}}...`;
      try {{
        const res = await fetch(apiUrl('/api/dedao-recall'), apiOptions({{
          method:'POST',
          headers: {{ 'Content-Type':'application/json' }},
          body: JSON.stringify({{ query:clean, top_k:topK }})
        }}));
        const data = await res.json();
        state.dedaoBrain.status = data.status || state.dedaoBrain.status;
        state.dedaoBrain.current = data;
        state.dedaoBrain.cache[cacheKey] = data;
        if (target) {{
          target.textContent = data.ok
            ? `已召回得到大脑 ${{(data.results || []).length}} 条记忆，生成将优先使用这些素材`
            : (data.message || '得到大脑检索失败，已用本地 danao 兜底');
        }}
        return data;
      }} catch (err) {{
        const data = {{ ok:false, results:[], message:String(err?.message || err) }};
        state.dedaoBrain.current = data;
        if (target) target.textContent = '得到大脑检索失败，已用本地 danao 兜底';
        return data;
      }}
    }}

    function dedaoBrainLine(memory, theme, pain, clean, careerMode=false) {{
      const items = dedaoItems(memory);
      if (!items.length) return '';
      const first = items[0];
      const second = items[1];
      const point = dedaoCleanPoint(first);
      const support = second ? dedaoCleanPoint(second) : '';
      if (careerMode) {{
        return `这里有一个很关键的素材判断：${{point || '先把能力、对象和结果说清楚'}}。所以这一条不能只讲观点，要把用户能看见的入口、动作和结果一起讲出来。${{support ? `再补一句：${{support}}。` : ''}}`;
      }}
      return `这里有一个很关键的素材判断：${{point || '先把问题放进真实场景，再给一个能马上做的小动作'}}。所以这一条不要停在道理上，要把场景、原因和今天能做的小动作讲清楚。${{support ? `再补一句：${{support}}。` : ''}}`;
    }}

    function dedaoTopicBase(theme, pain, memory, index) {{
      const items = dedaoItems(memory);
      if (!items.length || index % 3 !== 0) return '';
      const item = items[Math.floor(index / 3) % items.length];
      const title = safeClip(item.title || item.content || pain, 18);
      if (!title) return '';
      return `${{theme.split('/')[0]}}：从得到大脑「${{title}}」延伸出的短视频选题`;
    }}

    function currentHookId() {{
      return localStorage.getItem('workflowHookFormula') || 'pain_reverse';
    }}

    function syncHookSelects(id) {{
      const hookId = hookById(id).id;
      localStorage.setItem('workflowHookFormula', hookId);
      ['draftHook','ideaHook'].forEach(sel => {{
        const el = $('#' + sel);
        if (el) el.value = hookId;
      }});
    }}

    function viralArchives() {{
      try {{
        return JSON.parse(localStorage.getItem('workflowViralArchives') || '[]');
      }} catch (err) {{
        return [];
      }}
    }}

    function saveViralArchives(items) {{
      localStorage.setItem('workflowViralArchives', JSON.stringify(items.slice(0,30)));
    }}

    function currentViralArchive() {{
      const id = $('#ideaViralCase')?.value || '';
      return viralArchives().find(x=>x.id === id) || null;
    }}

    function coverDisplaySrc(src, seed='') {{
      if (!src) return '';
      if (!src.startsWith('/viral_covers/')) return src;
      const sep = src.includes('?') ? '&' : '?';
      return `${{src}}${{sep}}v=${{encodeURIComponent(seed || Date.now())}}`;
    }}

    function viralCoverAdvice(x) {{
      const title = x.title || '待拆解短视频';
      const theme = x.theme || '爆款拆解';
      const pain = x.pain || inferCorePain(title, x.template || '', theme);
      const cover = Array.isArray(x.cover) ? x.cover : [];
      if (theme === '当前链接拆解') {{
        const topic = linkTopic(title, x.fullText || x.transcriptPreview || '');
        const lines = [
          cover[0] || safeClip(topic, 10),
          cover[1] || '这点最关键',
          cover[2] || '看完再决定'
        ];
        return [
          `三行字建议：${{lines.join(' / ')}}。封面只承接当前链接主题「${{topic}}」，不套用历史账号栏目词。`,
          `人物画面建议：优先保留原视频封面的主体关系和视线方向，重新强化大字信息。`,
          `视觉重点：第一行给主题，第二行给判断，第三行给继续看的理由。`,
          `对照检查：封面必须让用户在点开前知道这条视频讲的是「${{topic}}」，不要混入旧账号的心理、情感或女性成长标签。`
        ];
      }}
      const themeName = theme.split('/')[0] || theme;
      const lineOne = cover[0] || (title.includes('追') ? '你追的不是他' : pain.slice(0, 10) || '别再委屈自己');
      const lineTwo = cover[1] || (theme.includes('追星') ? '是不敢活的自己' : '真正问题在这里');
      const lineThree = cover[2] || themeName;
      const emotion = theme.includes('追星') ? '向往感 + 自我投射' : theme.includes('边界') || pain.includes('讨好') ? '委屈感 + 清醒反击' : theme.includes('情绪') ? '压抑感 + 稳定感' : '被说中 + 可改变';
      return [
        `三行字建议：${{lineOne}} / ${{lineTwo}} / ${{lineThree}}。这组字要直接承接标题「${{title.slice(0, 24)}}」，不要换成泛泛的“成长/清醒”。`,
        `人物画面建议：真人近景看镜头，表情贴合「${{emotion}}」；如果原封面表情不明显，优先换成更强的眼神和半身口播姿态。`,
        `视觉重点：第一行打痛点人群，第二行打反常识，第三行做栏目标签；字数控制在 14 到 20 个大字，避免把正文塞进封面。`,
        `对照检查：这条内容的爆点是「${{pain}}」，封面必须让用户一眼知道“这说的是我”，否则再好的文案也会输在点击。`
      ];
    }}

    function renderCoverCompare(x) {{
      const tips = x.coverAdvice || viralCoverAdvice(x);
      const displaySrc = coverDisplaySrc(x.coverImage, x.coverSource || x.url || x.createdAt || '');
      const image = displaySrc ? `<img src="${{esc(displaySrc)}}" alt="点开短视频前看到的完整封面图" referrerpolicy="no-referrer">` : `<div class="result muted">当前链接未拿到封面图。匹配到本地作品或详情接口返回封面后，会自动展示封面对照。</div>`;
      return `
        <div class="viral-cover-compare">
          <div>${{image}}</div>
          <div class="cover-advice-list">${{tips.map(t=>`<div>${{esc(t)}}</div>`).join('')}}</div>
        </div>`;
    }}

    function viralDeepSections(x) {{
      const title = x.title || '待拆解短视频';
      const theme = x.theme || '爆款拆解';
      const pain = x.pain || inferCorePain(title, x.template || '', theme);
      const scores = x.scores || {{}};
      const scoreRows = [
        ['黄金三秒', scores.hook || 76],
        ['冲突反差', scores.conflict || 78],
        ['结构递进', scores.structure || 72],
        ['行动价值', scores.action || 68],
        ['封面点击', scores.cover || 76]
      ];
      const weakest = scoreRows.slice().sort((a,b)=>a[1]-b[1])[0];
      if (theme === '当前链接拆解') {{
        const topic = linkTopic(title, x.fullText || x.transcriptPreview || '');
        const first = safeClip(splitSentences(x.fullText || x.transcriptPreview || title, 1)[0] || title, 42);
        return [
          {{ title:'爆款短视频底层逻辑', items:[`当前链接核心主题：${{topic}}。`, '只拆这条链接的标题、转写稿、封面和数据，不调用历史账号主题。', '复用的是信息推进方式，不复用原句。'] }},
          {{ title:'黄金三秒开场', items:[`原链接开场抓手：${{first}}。`, '二创时第一句话仍然先给判断或结果。', '不要加旧账号的心理、女性成长、情感类解释。'] }},
          {{ title:'内容结构', items:['0-3秒：抛出当前链接的核心判断。', '4-12秒：补一个新场景，让主题更具体。', '13-28秒：解释原因或步骤。', '结尾：围绕当前主题设计互动问题。'] }},
          {{ title:'爆款脚本框架', items:[`开头：${{first}}`, `场景：围绕「${{topic}}」换一个新例子。`, '推进：讲清原因，不照搬原视频句子。', '方法：给一个马上能执行的动作。', `互动：你对「${{topic}}」最想先解决哪一步？`] }},
          {{ title:'完播与转化关键动作', items:['每 5-8 秒推进一个信息点。', '用画面、字幕和停顿强调当前链接最强的一句话。', '结尾问题只围绕当前链接主题，不带旧栏目口号。'] }},
          {{ title:'爆款短视频数据分析', items:[...scoreRows.map(([name,value])=>`${{name}}：${{value}}分`), `优先优化短板：${{weakest[0]}}。`] }}
        ];
      }}
      const hook = title.includes('为什么') ? title : `为什么${{pain}}，会让用户第一眼停下来`;
      const solution = theme.includes('追星')
        ? '把对人物的喜欢转成“我想成为什么样的人”，给用户一个自我升级动作。'
        : theme.includes('边界') || pain.includes('讨好')
          ? '先承认委屈，再给一句能马上用的拒绝话术，让用户觉得有出口。'
          : theme.includes('情绪')
            ? '把情绪问题拆成一个身体动作或十分钟缓冲方法，降低执行门槛。'
            : '把抽象观点落到一个今天能做的小动作，让用户从共鸣走向关注。';
      return [
        {{
          title:'爆款短视频底层逻辑',
          items:[`用户入口不是“内容好”，而是「${{pain}}」被点名。`, `这条内容要完成：被说中 -> 重新理解 -> 有一个动作可做。`, `账号承接点：${{theme}}，要让新用户知道你持续解决同一类问题。`]
        }},
        {{
          title:'黄金三秒开场',
          items:[`第一句话：${{hook}}。`, '不要先介绍背景，先说结论、代价或反常识。', `画面第一秒配合封面大字：${{(x.cover || [title]).slice(0,2).join(' / ')}}。`]
        }},
        {{
          title:'高吸引力开头',
          items:[`身份点名：总是${{pain}}的人，先别急着怪自己。`, `结果预警：继续这样，最容易丢掉的是自己的主动权。`, `反常识：问题不在你想太多，而在你太久没有站回自己。`]
        }},
        {{
          title:'内容结构',
          items:['0-3秒：痛点/结论直接抛出。', '4-12秒：给一个具体场景，让用户确认“这说的是我”。', '13-28秒：误区反转，讲清真正原因。', '最后8秒：给动作 + 评论问题。']
        }},
        {{
          title:'爆款脚本框架',
          items:[`开头：${{hook}}`, `场景：把「${{pain}}」放进一个真实生活瞬间。`, `反转：这不是你不够好，而是你的边界/理想自我/情绪出口没有被看见。`, `方法：${{solution}}`, '互动：评论区留一句“我先站回自己”。']
        }},
        {{
          title:'痛点挖掘与解决方案',
          items:[`表层痛点：${{pain}}。`, '深层动机：用户想被理解，也想知道自己下一步怎么变好。', `解决方案：${{solution}}`, '输出方式：少讲大道理，多给一句话术、一个动作、一个判断标准。']
        }},
        {{
          title:'完播与转化关键动作',
          items:['每 5-8 秒给一个新信息点，避免连续金句但没有推进。', '中段插入“你可能以为...但真正...”制造继续看的理由。', '结尾不要只说点赞关注，要问一个能让用户暴露处境的问题。', '归档复用时，把互动问题同步改成选题生成器的结尾。']
        }},
        {{
          title:'爆款短视频数据分析',
          items:[...scoreRows.map(([name,value])=>`${{name}}：${{value}}分`), `优先优化短板：${{weakest[0]}}。`, weakest[1] < 72 ? '判断：这条更适合先优化开头/封面，再复刻结构。' : '判断：整体可复用，适合沉淀成选题模板。']
        }}
      ];
    }}

    function renderViralDeepDive(x) {{
      const sections = x.deepDive || viralDeepSections(x);
      return `<div class="viral-deep-grid">${{sections.map(sec=>`
        <div class="viral-deep-card">
          <strong>${{esc(sec.title)}}</strong>
          <ul>${{(sec.items || []).map(item=>`<li>${{esc(item)}}</li>`).join('')}}</ul>
        </div>`).join('')}}</div>`;
    }}

    function splitSentences(text, limit=5) {{
      return String(text || '')
        .replace(/\\s+/g, ' ')
        .split(/(?<=[。！？!?；;])|\\n+/)
        .map(x=>x.trim())
        .filter(Boolean)
        .slice(0, limit);
    }}

    function cleanLinkText(text) {{
      return String(text || '')
        .replace(/#\\S+/g, '')
        .replace(/[\\u{{1F300}}-\\u{{1FAFF}}]/gu, '')
        .replace(/\\s+/g, ' ')
        .trim();
    }}

    function safeClip(text, max=28) {{
      const clean = cleanLinkText(text);
      return clean.length > max ? clean.slice(0, max) : clean;
    }}

    function linkTopic(title, original) {{
      const titleClean = cleanLinkText(title).replace(/^抖音作品\\s*\\d+$/, '').trim();
      if (titleClean) return safeClip(titleClean, 18);
      const sentence = splitSentences(original, 1)[0] || '';
      return safeClip(sentence, 18) || '这条内容';
    }}

    function legacySafe(text) {{
      return String(text || '')
        .replace(/心理学/g, '内容逻辑')
        .replace(/心理/g, '内容')
        .replace(/女性成长/g, '内容成长')
        .replace(/追星/g, '兴趣话题')
        .replace(/王一博/g, '原视频人物')
        .replace(/太敏感/g, '想法没有讲清楚')
        .replace(/委屈/g, '卡点')
        .replace(/被爱/g, '被看见')
        .replace(/讨好/g, '迎合')
        .replace(/内耗/g, '反复消耗')
        .replace(/把自己活回来/g, '把表达讲清楚');
    }}

    function polishSentence(sentence) {{
      return legacySafe(cleanLinkText(sentence))
        .replace(/[。！？!?；;]+$/g, '')
        .replace(/^(然后|所以|但是|因为|其实|而且|还有)[，,\\s]*/g, '')
        .trim();
    }}

    function deepItems(x, keyword) {{
      const sections = x.deepDive || viralDeepSections(x);
      const section = sections.find(sec => String(sec.title || '').includes(keyword));
      return section ? (section.items || []).map(item => legacySafe(cleanLinkText(item))) : [];
    }}

    function extractAfterLabel(text) {{
      return legacySafe(cleanLinkText(text))
        .replace(/^[^：:]{1,12}[：:]/, '')
        .replace(/[。；;]+$/g, '')
        .trim();
    }}

    function deepTopic(x) {{
      const logic = deepItems(x, '底层逻辑');
      const fromLogic = logic.find(item => item.includes('核心主题'));
      if (fromLogic) return safeClip(extractAfterLabel(fromLogic), 10);
      return safeClip(linkTopic(x.title || '', x.fullText || x.transcriptPreview || ''), 10);
    }}

    function finalDeepScriptGuard(script, source) {{
      let out = String(script || '')
        .replace(/这条内容/g, '这个问题')
        .replace(/原视频/g, '这个案例')
        .replace(/二创/g, '这版表达')
        .replace(/爆款逻辑/g, '关键判断')
        .replace(/黄金三秒/g, '开头')
        .replace(/脚本框架/g, '表达顺序')
        .replace(/底层逻辑[：:]/g, '')
        .replace(/内容结构[：:]/g, '')
        .replace(/传播动作[：:]/g, '')
        .replace(/转化动作[：:]/g, '');
      if (!/(情感|心理|女性成长|追星|王一博)/.test(source || '')) {{
        out = out
          .replace(/心理/g, '判断')
          .replace(/情感/g, '表达')
          .replace(/女性成长/g, '个人成长')
          .replace(/追星/g, '兴趣表达')
          .replace(/王一博/g, '这个人物')
          .replace(/追星心理/g, '内容洞察')
          .replace(/关系边界/g, '关键边界')
          .replace(/高敏感/g, '高关注度')
          .replace(/清醒局/g, '内容栏目')
          .replace(/我先站回自己/g, '我先开始行动')
          .replace(/把自己活回来/g, '把这件事做明白')
          .replace(/被爱/g, '被理解')
          .replace(/讨好/g, '迎合')
          .replace(/内耗/g, '反复消耗');
      }}
      return out.replace(/\\n{3,}/g, '\\n\\n').trim();
    }}

    function makeDeepDrivenScript(x, topic) {{
      const topicName = safeClip(topic, 10) || '这件事';
      const logic = deepItems(x, '底层逻辑');
      const hookRules = deepItems(x, '黄金三秒');
      const structure = deepItems(x, '内容结构');
      const framework = deepItems(x, '脚本框架');
      const conversion = deepItems(x, '转化');
      const openingRule = hookRules.find(item => item.includes('判断') || item.includes('结果') || item.includes('抓手')) || '第一句话先给判断或结果';
      const sceneRule = framework.find(item => item.includes('场景')) || structure.find(item => item.includes('4-12秒')) || '补一个新场景，让主题更具体';
      const pushRule = framework.find(item => item.includes('推进')) || structure.find(item => item.includes('13-28秒')) || '讲清原因，不照搬原视频句子';
      const methodRule = framework.find(item => item.includes('方法')) || '给一个马上能执行的动作';
      const interactRule = framework.find(item => item.includes('互动')) || conversion.find(item => item.includes('结尾')) || `围绕「${{topicName}}」设计互动问题`;
      const rhythmRule = conversion.find(item => item.includes('5-8') || item.includes('推进')) || '每 5-8 秒推进一个信息点';
      const logicRule = logic.find(item => item.includes('信息推进') || item.includes('复用')) || '复用信息推进方式，不复用原句';

      const source = `${{topicName}} ${{[...logic, ...hookRules, ...structure, ...framework, ...conversion].join(' ')}}`;
      const has = (words) => words.some(word => source.includes(word));
      let pain = '你一直停在知道这件事很重要，却没有把它变成一个具体动作';
      let value = '把判断落到行动里';
      let scene = `你刷到「${{topicName}}」的时候，觉得有道理，收藏了，转发了，但真正回到自己的问题里，还是不知道第一步该怎么做`;
      let actionA = `先把「${{topicName}}」里最关键的一个问题写清楚`;
      let actionB = '再把它拆成一个今天就能完成的小动作';
      let actionC = '最后用一个结果来验证，而不是只停留在想法里';
      let outcome = '你会从看懂一条内容，变成真的能把它用到自己身上';

      if (has(['账号','内容','自媒体','流量','粉丝','变现','客户','成交','IP','个人品牌','直播','获客'])) {{
        pain = '你一直在发作品、追热点、学爆款，却没有让用户明白你到底能帮他解决什么';
        value = '先建立信任，再放大流量';
        scene = '你辛辛苦苦发了很多条，播放有起有落，但用户看完只觉得热闹，不知道为什么要关注你，更不知道为什么要相信你';
        actionA = '先用一句话说清楚你帮谁解决什么问题';
        actionB = '再连续发三条内容：一条讲误区，一条讲方法，一条讲案例';
        actionC = '最后把每条作品结尾都落到一个明确行动，让用户知道下一步怎么做';
        outcome = '用户才会从刷到你，变成记住你，再到愿意信任你';
      }} else if (has(['学习','考试','课程','读书','技能','训练','练习','方法','效率','复习'])) {{
        pain = '你一直在找资料、听方法、换计划，但真正动手练的次数太少';
        value = '把信息变成练习，把练习变成反馈';
        scene = '你看完很多经验，当下很有动力，第二天又回到原来的状态，因为你没有把它拆成一个可以重复执行的动作';
        actionA = '先只选一个最重要的知识点';
        actionB = '用自己的话讲出来，或者马上做一遍';
        actionC = '当天就做一次反馈，别等完全准备好';
        outcome = '你会从“我懂了”，变成“我真的会用了”';
      }} else if (has(['职场','老板','工资','同事','工作','副业','简历','面试','公司','创业'])) {{
        pain = '你一直在等别人看见你的努力，却没有主动把自己的价值讲清楚';
        value = '把被动等待变成主动证明';
        scene = '你做了很多事，但汇报时说不出结果，谈机会时拿不出证据，最后只能继续等别人评价你';
        actionA = '先把最近做出的三个结果列出来';
        actionB = '把每个结果对应到对方真正关心的收益';
        actionC = '下一次沟通时直接讲事实、数据和下一步';
        outcome = '你会从被动等机会，变成主动争取空间';
      }} else if (has(['店','产品','买','卖','价格','装修','房子','汽车','品牌','服务','体验','消费'])) {{
        pain = '你容易被表面的价格、颜值或者卖点带着走，却忽略了真正影响使用体验的细节';
        value = '先判断真实需求，再判断值不值得';
        scene = '你当下觉得很心动，真正用起来才发现有些地方根本不适合自己，最后为冲动买单';
        actionA = '先写下你最在意的三个使用场景';
        actionB = '把每个选择放进真实场景里比较';
        actionC = '只为长期会用到的价值买单';
        outcome = '你会少花冤枉钱，也少做后悔的选择';
      }}

      const hook = `如果你正在为「${{topicName}}」反复纠结，先记住一句话：${{value}}。`;
      const draft = [
        hook,
        `真正卡住你的不是信息不够，而是${{pain}}。`,
        `你看，${{scene}}。很多人就是卡在这里：知道问题存在，但没有把判断说清楚，也没有把下一步讲明白。`,
        `接下来别急着讲一堆道理，先给一个具体画面，再把原因讲透。用户先看见自己，才愿意继续听你往下说。`,
        `中段只做一件事：把问题拆开讲，让用户知道自己不是差一点热情，而是少了一个可以照着走的步骤。`,
        `所以方法很简单。第一，${{actionA}}。第二，${{actionB}}。第三，${{actionC}}。`,
        `你不要一口气把所有信息都倒出来，每一步只讲一个重点：先让人停下来，再让人听懂，最后让人知道该怎么做。`,
        `当你把这几步跑通，${{outcome}}。`,
        `${{interactRule.includes('？') ? interactRule.replace(/^.*?[:：]/, '') : `如果你也卡在「${{topicName}}」，评论区告诉我你现在最卡的是哪一步，我下一条直接拆给你看。`}}`
      ].join('\\n\\n');
      return finalDeepScriptGuard(draft, source);
    }}

    function makeConcreteScript(topic, rawSentences) {{
      const lines = rawSentences.map(polishSentence).filter(Boolean);
      const source = `${{topic}} ${{lines.join(' ')}}`;
      const has = (words) => words.some(word => source.includes(word));
      const topicName = safeClip(topic, 16) || '这件事';
      let frame = {{
        audience: `正在关注「${{topicName}}」的人`,
        trap: '只看到了表面的结果，却没有把它变成自己的行动',
        shift: '先抓住关键判断，再把判断落到一个具体动作里',
        scene: '你收藏了很多信息，真正要用的时候却还是不知道从哪一步开始',
        action1: '把你现在最卡的一步写下来',
        action2: '删掉那些暂时用不上的干扰信息',
        action3: '今天只完成一个最小动作',
        result: '你会从被信息推着走，变成自己能做决定的人'
      }};
      if (has(['账号','内容','自媒体','流量','粉丝','变现','客户','成交','IP','个人品牌','直播','获客'])) {{
        frame = {{
          audience: `想把「${{topicName}}」做出结果的人`,
          trap: '一上来就追热点、学形式、拼更新频率，却没有让别人看懂你能解决什么问题',
          shift: '先把信任搭起来，再去谈流量和转化',
          scene: '你每天都在发，可用户看完只觉得热闹，不知道为什么要关注你、相信你、继续等你下一条',
          action1: '用一句话写清楚你帮谁解决什么问题',
          action2: '连续发三条内容证明你的判断、方法和案例',
          action3: '把每条作品的结尾都落到一个明确行动',
          result: '用户会从刷到你，变成记住你，再到愿意信任你'
        }};
      }} else if (has(['学习','考试','课程','读书','技能','训练','练习','方法','效率','复习'])) {{
        frame = {{
          audience: `想把「${{topicName}}」真正学会的人`,
          trap: '一直在找资料、换方法、听建议，却没有形成自己的练习节奏',
          shift: '不要再把学习当成收集信息，要把它变成每天能重复的动作',
          scene: '你看完一堆经验，当下很有动力，第二天又回到原来的状态',
          action1: '只选一个最重要的知识点',
          action2: '用自己的话讲出来或者写出来',
          action3: '当天立刻做一次反馈，不要等完全准备好',
          result: '你会从“看懂了”，变成真的会用'
        }};
      }} else if (has(['职场','老板','工资','同事','工作','副业','简历','面试','公司','创业'])) {{
        frame = {{
          audience: `正在处理「${{topicName}}」这类职场问题的人`,
          trap: '只想着忍一忍、等一等，却没有主动整理自己的筹码',
          shift: '别把希望都放在别人评价上，要把选择权一点点拿回来',
          scene: '你明明做了很多事，但汇报时讲不清价值，谈机会时又拿不出证据',
          action1: '把你最近做出的结果列出来',
          action2: '把结果对应到对方真正关心的收益',
          action3: '下一次沟通时直接讲事实、数据和下一步',
          result: '你会从被动等待机会，变成主动争取空间'
        }};
      }} else if (has(['店','产品','买','卖','价格','装修','房子','汽车','品牌','服务','体验','消费'])) {{
        frame = {{
          audience: `正在考虑「${{topicName}}」的人`,
          trap: '只盯着表面的价格、颜值或者卖点，忽略了后面真正影响体验的细节',
          shift: '先判断自己的真实需求，再看这个选择值不值得',
          scene: '你当下觉得很心动，真正用起来才发现有些地方根本不适合自己',
          action1: '先写下你最在意的三个使用场景',
          action2: '把每个选择放到真实场景里比较',
          action3: '只为长期会用到的价值买单',
          result: '你会少花冤枉钱，也少为冲动选择后悔'
        }};
      }} else if (has(['孩子','父母','家庭','教育','妈妈','爸爸','亲子','婚姻','关系'])) {{
        frame = {{
          audience: `正在面对「${{topicName}}」的人`,
          trap: '一着急就想控制结果，却忘了先看见对方真正需要什么',
          shift: '先把沟通从情绪里拿出来，再去解决具体问题',
          scene: '你越想把事情讲清楚，对方越抗拒，最后两个人都只记住了不舒服',
          action1: '先停十秒，不急着下判断',
          action2: '把指责换成一个具体请求',
          action3: '只讨论下一步怎么做，不翻旧账',
          result: '关系会从互相消耗，慢慢变成可以一起解决问题'
        }};
      }}
      return [
        `${{frame.audience}}，先别急着照着别人做。`,
        `真正让你卡住的，往往不是你不知道这件事重要，而是你一直陷在一个误区里：${{frame.trap}}。`,
        `换个角度看，关键不是多知道一点，而是${{frame.shift}}。`,
        `你可以想象一个很具体的画面：${{frame.scene}}。这时候，再多道理都不如一个清晰动作有用。`,
        `所以从今天开始，先做三件事。第一，${{frame.action1}}。第二，${{frame.action2}}。第三，${{frame.action3}}。`,
        `当你能把这三步跑通，${{frame.result}}。`,
        `如果你现在也卡在「${{topicName}}」这里，评论区告诉我你最卡的是哪一步，我下一条直接给你拆做法。`
      ].join('\\n\\n');
    }}

    const viralCopyModes = [
      {{ id:'standard', name:'智能二创', desc:'保留原意和结构，重写成可直接发布的成品稿。' }},
      {{ id:'official', name:'官方', desc:'表达更正式、清楚、可信，适合品牌号和知识型内容。' }},
      {{ id:'spoken', name:'口播式文案', desc:'更像真人出镜讲出来，有停顿、有推进、有互动。' }},
      {{ id:'colloquial', name:'口语化方式', desc:'更大白话、更顺嘴，减少书面感和抽象词。' }}
    ];

    function viralModeById(mode) {{
      return viralCopyModes.find(x=>x.id === mode) || viralCopyModes[0];
    }}

    function normalizeCurrentSourceText(text) {{
      return cleanLinkText(String(text || ''))
        .replace(/复制此链接.*$/g, '')
        .replace(/打开.{0,4}搜索.*$/g, '')
        .replace(/https?:\\/\\/\\S+/g, '')
        .trim();
    }}

    function detectViralDomain(source) {{
      const hay = String(source || '').toLowerCase();
      const has = (words) => words.some(word => hay.includes(String(word).toLowerCase()));
      if (has(['cloud code','claude','codex','ai','人工智能','智能体','大模型','编程','自动化','工具','产品','软件'])) return 'ai_tool';
      if (has(['账号','内容','自媒体','短视频','流量','粉丝','变现','成交','客户','个人品牌','ip','获客','直播','投流'])) return 'content_business';
      if (has(['学习','考试','课程','知识','读书','训练','练习','效率','复习','技能'])) return 'learning';
      if (has(['职场','工作','老板','同事','工资','副业','创业','面试','简历','公司','项目'])) return 'career';
      if (has(['产品','价格','门店','服务','装修','房子','汽车','品牌','购买','消费','体验','测评'])) return 'product_service';
      if (has(['孩子','父母','家庭','教育','妈妈','爸爸','亲子','老师','学生'])) return 'family_education';
      if (has(['健康','饮食','运动','睡眠','身体','医生','医院','减肥','营养'])) return 'health';
      return 'general';
    }}

    function makeFreshViralCopyAgent(x, mode='standard') {{
      const original = normalizeCurrentSourceText(x.fullText || x.transcriptPreview || x.title || '');
      const title = normalizeCurrentSourceText(x.title || '');
      const deep = (x.deepDive || []).flatMap(sec => sec.items || []).join(' ');
      const elements = (x.elements || []).join(' ');
      const currentSource = normalizeCurrentSourceText(`${{title}} ${{original}} ${{elements}}`);
      const guidance = normalizeCurrentSourceText(deep);
      const source = normalizeCurrentSourceText(`${{currentSource}} ${{guidance}}`);
      const topic = safeClip(linkTopic(title, original), 16) || '这个主题';
      const sentences = splitSentences(original, 10).map(normalizeCurrentSourceText).filter(Boolean);
      const modeMeta = viralModeById(mode);
      const seed = `${{Date.now().toString(36)}}-${{Math.random().toString(36).slice(2,7)}}`;
      return {{
        id:`copy-agent-${{seed}}`,
        mode:modeMeta,
        source,
        currentSource,
        guidance,
        original,
        title,
        topic,
        sentences,
        domain:detectViralDomain(source),
        sourceNote:'仅使用当前链接提取文案、当前链接深度拆解和当前封面信息，不读取历史账号主题。'
      }};
    }}

    function viralDomainLabel(domain) {{
      return ({{
        ai_tool:'AI 工具/智能体',
        content_business:'内容商业/IP',
        learning:'学习训练',
        career:'职场项目',
        product_service:'产品服务',
        family_education:'家庭教育',
        health:'健康生活',
        general:'当前链接主题'
      }})[domain] || '当前链接主题';
    }}

    function agentFrame(agent) {{
      const topic = agent.topic;
      const second = safeClip(agent.sentences[1] || '', 38);
      const frames = {{
        ai_tool: {{
          audience:'想把 AI 工具真正用起来的人',
          hook:`如果你已经开始接触「${{topic}}」，别只把它当成一个新软件。`,
          scene:`很多人看到新工具，只停在围观、收藏和转发，真正要做东西的时候，还是不知道怎么把想法拆成步骤。`,
          insight:`关键不是你要一下子懂完所有技术，而是先把目标说清楚，把任务拆明白，再让工具帮你执行和验证。`,
          method:['写清楚你想完成的结果', '把结果拆成三到五个可执行步骤', '每一步都让工具给出版本，再用真实反馈修正'],
          ending:'如果你也想把 AI 变成生产力，今天就拿一个真实需求试一次，不要只停在看懂。'
        }},
        content_business: {{
          audience:'正在做账号、内容或个人品牌的人',
          hook:`如果你正在围绕「${{topic}}」做内容，先别急着追模板。`,
          scene:`很多内容看起来很热闹，但用户看完不知道你是谁，也不知道你到底能帮他解决什么。`,
          insight:`真正要复制的不是原句，而是它先抓问题、再给判断、最后给行动的顺序。`,
          method:['用一句话说清你帮谁解决什么问题', '用一个具体场景证明你理解用户', '结尾给一个明确动作，让用户知道下一步怎么做'],
          ending:'内容的目的不是把话说满，而是让用户愿意记住你、相信你、继续看你。'
        }},
        learning: {{
          audience:'正在学习或训练一项能力的人',
          hook:`如果你也在研究「${{topic}}」，别再只收集方法。`,
          scene:`很多人收藏了很多经验，当下很有动力，但第二天回到自己身上还是不知道先做哪一步。`,
          insight:`真正拉开差距的不是信息量，而是你能不能把信息变成练习，再把练习变成反馈。`,
          method:['先选一个最关键的问题', '用自己的话讲一遍', '当天做一次最小练习并记录反馈'],
          ending:'你不用等完全准备好，先完成一次小闭环，能力才会真的开始长出来。'
        }},
        career: {{
          audience:'正在处理工作、项目或职业选择的人',
          hook:`如果你正在面对「${{topic}}」，先别只想着忍一忍或者再等等。`,
          scene:`很多人做了不少事，但表达时讲不清结果，争取机会时拿不出证据。`,
          insight:`你需要的不是把自己说得更辛苦，而是把价值、结果和下一步讲清楚。`,
          method:['列出最近做出的具体结果', '说明这个结果对别人有什么价值', '提出下一步可执行方案'],
          ending:'当你能把价值说清楚，机会就不只是等来的，而是可以主动争取的。'
        }},
        product_service: {{
          audience:'正在做选择、买产品或判断服务的人',
          hook:`关于「${{topic}}」，你最该看的不是表面卖点。`,
          scene:`很多选择一开始看着很心动，真正用起来才发现它不适合自己的真实场景。`,
          insight:`判断值不值得，先看需求是否匹配，再看长期使用成本，而不是只看当下吸不吸引人。`,
          method:['写下三个真实使用场景', '把每个选择放进场景里比较', '只为长期能用到的价值买单'],
          ending:'别为一时冲动做决定，让选择回到真实需求里。'
        }},
        family_education: {{
          audience:'正在面对家庭、亲子或教育问题的人',
          hook:`如果你正在为「${{topic}}」着急，先别急着控制结果。`,
          scene:`很多沟通越想讲清楚，越容易变成互相较劲，最后真正的问题反而被情绪盖住。`,
          insight:`有效沟通不是谁压过谁，而是先把感受放稳，再把问题拆小。`,
          method:['先停下来确认真正的问题', '把指责换成具体请求', '只讨论下一步怎么做'],
          ending:'当沟通从情绪里出来，问题才有机会被一起解决。'
        }},
        health: {{
          audience:'正在关注健康、身体或生活习惯的人',
          hook:`如果你正在关注「${{topic}}」，先别被单一结论带着走。`,
          scene:`很多人听到一个方法就马上照做，但忽略了自己的身体状态、生活节奏和长期坚持成本。`,
          insight:`真正有用的改变，一定是能被你稳定执行、能被反馈验证的。`,
          method:['先确认自己的基础情况', '只改一个最容易坚持的小习惯', '连续记录一周反馈再调整'],
          ending:'不要追求一下子改变很多，能长期做下去的动作才更有价值。'
        }},
        general: {{
          audience:`正在关注「${{topic}}」的人`,
          hook:`如果你正在关注「${{topic}}」，先抓住一个关键点。`,
          scene: second ? `表面看是在讲「${{topic}}」，真正要放大的，是用户为什么会停下来、为什么会继续听。` : `表面看这只是一个信息点，但真正能留下来的，是它能不能帮你做出一个判断。`,
          insight:`这类内容真正要讲清楚的，是问题为什么重要、误区在哪里、下一步该怎么做。`,
          method:[`先把「${{topic}}」里的核心问题说清楚`, '再换一个新例子讲明白原因', '最后给一个今天就能执行的小动作'],
          ending:`如果你也卡在「${{topic}}」这里，先从一个小动作开始，不要只停在看懂。`
        }}
      }};
      return frames[agent.domain] || frames.general;
    }}

    function composeAgentScript(agent) {{
      const frame = agentFrame(agent);
      const mode = agent.mode.id;
      const methodLine = frame.method.map((item, i)=>`${{['第一','第二','第三'][i] || `第${{i+1}}`}}，${{item}}`).join('。');
      if (mode === 'official') {{
        return [
          `针对「${{agent.topic}}」，最重要的是先建立一个清晰判断。`,
          `${{frame.scene}}`,
          `${{frame.insight}}`,
          `具体执行上，可以分为三个步骤。${{methodLine}}。`,
          `${{frame.ending}}`
        ].join('\\n\\n');
      }}
      if (mode === 'spoken') {{
        return [
          `${{frame.hook}}`,
          `你会发现，${{frame.scene}}`,
          `所以这件事不能只讲一个结论，真正要讲透的是：${{frame.insight}}`,
          `接下来你就记住三步。${{methodLine}}。`,
          `${{frame.ending}}`,
          `如果你也遇到过类似情况，评论区告诉我你现在最卡的是哪一步，我下一条继续拆。`
        ].join('\\n\\n');
      }}
      if (mode === 'colloquial') {{
        return [
          `说白了，「${{agent.topic}}」这件事，别只看表面热闹。`,
          `${{frame.scene}}`,
          `真正有用的点在这里：${{frame.insight}}`,
          `你不用一下子做很多，先按这三步来：${{methodLine}}。`,
          `${{frame.ending}}`,
          `先别收藏完就算了，今天就挑一步做。做完你再回头看，感觉会完全不一样。`
        ].join('\\n\\n');
      }}
      return [
        `${{frame.hook}}`,
        `${{frame.scene}}`,
        `${{frame.insight}}`,
        `接下来直接把它落成一个更完整的行动路径：${{methodLine}}。`,
        `${{frame.ending}}`,
        `如果你也在关注「${{agent.topic}}」，评论区告诉我你最想先解决哪一步，我继续给你拆。`
      ].join('\\n\\n');
    }}

    function removeOldCoreLeak(script, agent) {{
      let out = String(script || '');
      const source = agent?.currentSource || agent?.source || '';
      const blocked = [
        ['我先站回自己', '我先开始行动'],
        ['把自己活回来', '把这件事做明白'],
        ['你追的不是他', `你关注的是「${{agent?.topic || '这个主题'}}」背后的关键信息`],
        ['是不敢活的自己', '是还没有被你用起来的判断'],
        ['追星心理', '内容洞察'],
        ['女性成长', '能力成长'],
        ['清醒局', '内容栏目'],
        ['王一博', '当前人物'],
        ['太敏感', '过度反应'],
        ['被爱', '被理解'],
        ['内耗', '反复消耗']
      ];
      blocked.forEach(([bad, good]) => {{
        if (!source.includes(bad)) out = out.split(bad).join(good);
      }});
      return out.replace(/\\n{3,}/g, '\\n\\n').trim();
    }}

    function makeQingdouStyleScript(x, mode='standard') {{
      const agent = makeFreshViralCopyAgent(x, mode);
      const script = removeOldCoreLeak(finalDeepScriptGuard(composeAgentScript(agent), agent.currentSource || agent.source), agent);
      return {{ script, agent }};
    }}

    function makeViralRecreation(x, mode='standard') {{
      const original = (x.fullText || x.transcriptPreview || x.title || '').trim();
      const sentences = splitSentences(original, 12).map(normalizeCurrentSourceText).filter(Boolean);
      const title = x.title || sentences[0] || '爆款短视频二创';
      const topic = deepTopic(x);
      const hook = sentences[0] || normalizeCurrentSourceText(title) || `当前链接最值得看的，是它给出的判断`;
      const action = sentences.find(s=>/评论|收藏|关注|转发|点赞|方法|步骤|试试|记住|建议/.test(s)) || `最后给一个明确动作，让用户知道看完以后该做什么。`;
      const structure = [
        `开头借鉴：先用「${{hook.slice(0, 42)}}」这类强判断/强痛点停住用户。`,
        `中段借鉴：围绕「${{topic}}」保留原视频的信息顺序，但换成新的表达和例子。`,
        `结尾借鉴：把「${{action.slice(0, 42)}}」改成你账号能承接的互动问题。`
      ];
      const newTitle = removeOldCoreLeak(finalDeepScriptGuard(`${{topic}}，换个角度更容易被看完`, `${{title}} ${{original}}`), {{ source:`${{title}} ${{original}}`, topic }});
      const cover = [safeClip(topic, 10), '这点最关键', '看完再决定'];
      const generated = makeQingdouStyleScript(x, mode);
      return {{
        title: newTitle,
        cover,
        script: generated.script,
        agent: generated.agent,
        structure,
        originalHook: hook,
        note: `${{x.transcriptSource || '提取文案'}}生成智能二创：只读取当前链接，不调用历史账号主题。`
      }};
    }}

    function viralSummaryItems(x) {{
      const text = x.fullText || x.transcriptPreview || x.title || '';
      const sentences = splitSentences(text, 4).map(legacySafe);
      const topic = x.pain || linkTopic(x.title || '', text);
      const items = [
        `核心主题：${{legacySafe(topic)}}`,
        sentences[0] ? `开场信息：${{sentences[0]}}` : `识别标题：${{legacySafe(x.title || '待拆解短视频')}}`,
        sentences[1] ? `内容推进：${{sentences[1]}}` : '内容推进：先给判断，再补场景，最后给动作。',
        `可复用点：${{(x.elements || [])[0] || '强开场 + 具体场景 + 明确行动'}}`
      ];
      return items.slice(0,3);
    }}

    function viralDurationLabel(x) {{
      const raw = x.duration || x.durationSec || x.videoDuration || x.video_duration || x.stats?.duration || '';
      const num = Number(raw || 0);
      if (!num) return '未识别';
      const sec = num > 1000 ? Math.round(num / 1000) : Math.round(num);
      if (sec >= 60) return `${{Math.floor(sec / 60)}}分${{String(sec % 60).padStart(2,'0')}}秒`;
      return `${{sec}}秒`;
    }}

    function renderQingdouExtract(x) {{
      const text = x.fullText || x.transcriptPreview || '当前链接未提取到文案内容';
      const cover = coverDisplaySrc(x.coverImage || x.coverSource || '', x.id || x.title || '');
      const summary = viralSummaryItems(x);
      const source = x.source || x.transcriptSource || '链接分析';
      return `
        <div class="qd-card">
          <div class="qd-head">
            <div class="qd-tabs">
              <span class="qd-tab active">本次提取</span>
              <span class="qd-tab">历史结果</span>
              <span class="qd-tab">提取列表</span>
            </div>
            <div class="qd-actions">
              <button class="secondary" onclick="archiveViralById('${{esc(x.id || '')}}')">保存归档</button>
              <button class="secondary" onclick="copyViralTranscript('${{esc(x.id || '')}}')">复制文案</button>
              <button class="secondary" onclick="exportViralTranscript('${{esc(x.id || '')}}')">导出文案</button>
            </div>
          </div>
          <table class="qd-table">
            <thead><tr><th style="width:28%">视频</th><th style="width:34%">文案内容</th><th style="width:22%">全文摘要</th><th style="width:16%">操作</th></tr></thead>
            <tbody>
              <tr>
                <td>
                  <div class="qd-video-cell">
                    <div class="qd-thumb">${{cover ? `<img src="${{esc(cover)}}" alt="短视频封面" loading="lazy" referrerpolicy="no-referrer">` : '封面'}}</div>
                    <div>
                      <div class="qd-video-title">${{esc(x.title || '已提取短视频')}}</div>
                      <div class="qd-video-meta">${{esc(source)}}<br>视频时长：${{esc(viralDurationLabel(x))}}</div>
                    </div>
                  </div>
                </td>
                <td><div class="qd-copy-preview">${{esc(text)}}</div></td>
                <td>
                  <details open>
                    <summary>查看</summary>
                    <ul class="qd-summary-list">${{summary.map(item=>`<li>${{esc(item)}}</li>`).join('')}}</ul>
                  </details>
                </td>
                <td>
                  <div class="qd-actions">
                    <button class="secondary" onclick="copyViralTranscript('${{esc(x.id || '')}}')">复制文案</button>
                    <button class="secondary" onclick="scrollViralAi('${{esc(x.id || '')}}')">智能二创</button>
                  </div>
                  <details class="qd-more"><summary>更多</summary><div class="muted">可继续做深度拆解、封面对照、归档复用。</div></details>
                </td>
              </tr>
            </tbody>
          </table>
        </div>`;
    }}

    function getViralAiOutputText(id='') {{
      const key = id || 'current';
      return document.getElementById(`viralAiOutput-${{key}}`)?.textContent?.trim() || '';
    }}

    function renderViralRecreation(x) {{
      const recreation = makeViralRecreation(x);
      const original = x.fullText || x.transcriptPreview || '当前链接未提取到原文案。';
      const key = x.id || 'current';
      const modeButtons = viralCopyModes.map(mode=>`
        <button class="qd-mode ${{mode.id === 'standard' ? 'active' : ''}}" data-mode="${{esc(mode.id)}}" onclick="rewriteViralByMode('${{esc(key)}}','${{esc(mode.id)}}')">${{esc(mode.name)}}</button>
      `).join('');
      return `
        <div class="qd-ai-layout" id="viralAiBlock-${{esc(key)}}">
          <div class="qd-ai-input">
            <div class="qd-tabs"><span class="qd-tab">所有模板</span><span class="qd-tab active">当前模板</span></div>
            <div class="qd-template-title">智能二创</div>
            <div class="muted">内容要求（必填） · 当前链接专属智能体 · 不读取历史账号主题</div>
            <div class="qd-textarea">${{esc(original)}}</div>
            <div class="qd-char-row"><span>粘贴 · 清空</span><span>${{Math.min(original.length, 3000)}} / 3000</span></div>
            <button class="primary qd-generate" onclick="rerenderViralAi('${{esc(key)}}')">重新创作</button>
            <div class="qd-output-label">内容由 AI 生成</div>
          </div>
          <div class="qd-ai-output">
            <div class="qd-agent-bar">
              <span><b>本次智能体：</b><span id="viralAgentId-${{esc(key)}}">${{esc(recreation.agent?.id || 'copy-agent')}}</span></span>
              <span id="viralAgentDomain-${{esc(key)}}">${{esc(viralDomainLabel(recreation.agent?.domain))}} · ${{esc(recreation.agent?.mode?.name || '智能二创')}}</span>
            </div>
            <div class="qd-output-label">智能润色</div>
            <div class="qd-mode-row" id="viralModeRow-${{esc(key)}}">${{modeButtons}}</div>
            <div class="qd-output-paper" id="viralAiOutput-${{esc(key)}}">${{esc(recreation.script)}}</div>
            <div class="qd-output-label">内容由 AI 生成</div>
            <div class="qd-output-actions">
              <button class="secondary" onclick="sendViralRecreationToOptimizer('${{esc(x.id || '')}}')">编辑文案</button>
              <button class="secondary" onclick="copyViralRecreation('${{esc(x.id || '')}}')">复制文案</button>
              <button class="secondary" onclick="archiveViralById('${{esc(x.id || '')}}')">保存归档</button>
              <button class="secondary" disabled title="本地版暂未接入配音服务">AI配音</button>
            </div>
          </div>
        </div>`;
    }}

    function viralRecordById(id) {{
      if (id) return viralArchives().find(x=>x.id === id) || (state.lastViralAnalysis?.id === id ? state.lastViralAnalysis : null);
      return state.lastViralAnalysis || null;
    }}

    window.copyViralTranscript = async function(id='') {{
      const record = viralRecordById(id);
      if (!record) return;
      await navigator.clipboard.writeText(record.fullText || record.transcriptPreview || '');
    }}

    window.exportViralTranscript = function(id='') {{
      const record = viralRecordById(id);
      if (!record) return;
      const text = [
        `标题：${{record.title || ''}}`,
        `来源：${{record.source || ''}}`,
        `链接：${{record.url || ''}}`,
        '',
        record.fullText || record.transcriptPreview || ''
      ].join('\\n');
      const blob = new Blob([text], {{ type:'text/plain;charset=utf-8' }});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${{(record.title || '提取文案').slice(0,18).replace(/[\\\\/:*?"<>|]/g,'_')}}.txt`;
      a.click();
      URL.revokeObjectURL(a.href);
    }}

    window.scrollViralAi = function(id='') {{
      const key = id || 'current';
      document.getElementById(`viralAiBlock-${{key}}`)?.scrollIntoView({{ behavior:'smooth', block:'start' }});
    }}

    window.archiveViralById = function(id='') {{
      const record = viralRecordById(id);
      if (!record) return;
      const items = viralArchives().filter(x=>x.id !== record.id && x.title !== record.title);
      items.unshift(record);
      saveViralArchives(items);
      renderViralArchiveList();
    }}

    window.rerenderViralAi = function(id='') {{
      rewriteViralByMode(id, 'standard');
    }}

    window.rewriteViralByMode = function(id='', mode='standard') {{
      const record = viralRecordById(id);
      if (!record) return;
      const recreation = makeViralRecreation(record, mode);
      const key = id || 'current';
      const el = document.getElementById(`viralAiOutput-${{key}}`);
      if (el) el.textContent = recreation.script;
      const agentId = document.getElementById(`viralAgentId-${{key}}`);
      if (agentId) agentId.textContent = recreation.agent?.id || 'copy-agent';
      const agentDomain = document.getElementById(`viralAgentDomain-${{key}}`);
      if (agentDomain) agentDomain.textContent = `${{viralDomainLabel(recreation.agent?.domain)}} · ${{recreation.agent?.mode?.name || viralModeById(mode).name}}`;
      const modeRow = document.getElementById(`viralModeRow-${{key}}`);
      if (modeRow) modeRow.querySelectorAll('.qd-mode').forEach(btn => btn.classList.toggle('active', btn.dataset.mode === mode));
    }}

    window.copyViralRecreation = async function(id='') {{
      const record = viralRecordById(id);
      if (!record) return;
      const recreation = makeViralRecreation(record);
      await navigator.clipboard.writeText(getViralAiOutputText(id) || recreation.script || '');
    }}

    window.sendViralRecreationToOptimizer = function(id='') {{
      const record = viralRecordById(id);
      if (!record) return;
      const recreation = makeViralRecreation(record);
      $('#draftTitle').value = recreation.title;
      $('#draftText').value = getViralAiOutputText(id) || recreation.script;
      $('#draftTheme').value = record.theme || themeOf(recreation.title, recreation.script);
      switchView('optimizer');
      analyzeDraft();
    }}

    function renderViralArchiveList() {{
      const items = viralArchives();
      const list = $('#viralArchiveList');
      if (list) {{
        list.innerHTML = items.length ? items.map(x=>`
          <div class="archive-item">
            <strong>${{esc(x.title)}}</strong>
            <div class="muted">${{esc(x.theme)}} · 爆款潜力 ${{x.avg}} · ${{esc(x.createdAt)}}</div>
            <details class="archive-details">
              <summary>查看拆解详细内容</summary>
              <div class="result"><b>来源链接：</b>${{x.url ? `<a href="${{esc(x.url)}}" target="_blank" rel="noreferrer">${{esc(x.url)}}</a>` : '本地分析'}}</div>
              ${{x.stats ? `<div class="result"><b>链接数据：</b>播放 ${{fmt(x.stats.play)}} · 点赞 ${{fmt(x.stats.likes)}} · 评论 ${{fmt(x.stats.comments)}} · 收藏 ${{fmt(x.stats.collects)}} · 分享 ${{fmt(x.stats.shares)}}</div>` : ''}}
              <div class="result"><b>核心痛点：</b>${{esc(x.pain || '未记录')}}</div>
              <div class="result"><b>提取文案功能：</b>${{renderQingdouExtract(x)}}</div>
              <div class="result"><b>爆款元素：</b><br>${{(x.elements || []).map((item, i)=>`${{i+1}}. ${{esc(item)}}`).join('<br>') || '未记录'}}</div>
              <div class="result"><b>深度拆解：</b>${{renderViralDeepDive(x)}}</div>
              <div class="result"><b>封面图与拆解建议：</b>${{renderCoverCompare(x)}}</div>
              <div class="result"><b>提取文案并二创：</b>${{renderViralRecreation(x)}}</div>
              <div class="copybox"><b>可复用模板：</b><br>${{esc(x.template || '未记录')}}</div>
            </details>
            <div class="actions"><button class="secondary" onclick="useArchivedCaseInIdeas('${{esc(x.id)}}')">用于选题生成</button><button class="secondary" onclick="deleteViralArchive('${{esc(x.id)}}')">删除</button></div>
          </div>`).join('') : '<div class="result muted">归档后的拆解会出现在选题生成器里，可选择套用。</div>';
      }}
      const select = $('#ideaViralCase');
      if (select) {{
        const current = select.value;
        select.innerHTML = '<option value="">不套用爆款案例</option>' + items.map(x=>`<option value="${{esc(x.id)}}">${{esc(x.title.slice(0,28))}}｜${{esc(x.theme)}}｜${{x.avg}}分</option>`).join('');
        if (items.some(x=>x.id === current)) select.value = current;
      }}
    }}

    window.useArchivedCaseInIdeas = function(id) {{
      switchView('ideas');
      renderViralArchiveList();
      $('#ideaViralCase').value = id;
      generateIdeas();
    }}

    window.deleteViralArchive = function(id) {{
      saveViralArchives(viralArchives().filter(x=>x.id !== id));
      renderViralArchiveList();
      generateIdeas();
    }}

    function hookLine(formula, topic, theme, pain) {{
      const themeName = (theme || '').split('/')[0] || '清醒成长';
      const clean = cleanTopic(topic || pain || themeName);
      const careerMode = isCareerTheme(theme, pain || clean);
      const replacements = {{
        pain: pain || clean,
        truth: careerMode ? '你还没有建立让用户相信你的内容资产' : theme.includes('追星') ? '你在追一个不敢活出的自己' : theme.includes('情绪') ? '你缺的不是钝感，而是边界' : '你把自己放得太靠后',
        loss: careerMode ? '用户对你的信任和成交机会' : theme.includes('追星') ? '自己的生命力' : '你自己的边界和主动权',
        wrong: careerMode ? '只要多发作品就会自然涨粉' : theme.includes('追星') ? '单纯喜欢一个人' : '你不够好',
        scene: careerMode ? `每天都在发内容，却说不清自己帮谁解决什么问题` : `明明已经不舒服了，还要替别人找理由`,
        desire: careerMode ? '可持续被看见、被信任、被选择的个人品牌' : '你真正想要的自由和松弛'
      }};
      return formula.pattern.replace(/{{(pain|truth|loss|wrong|scene|desire)}}/g, (_, key)=>replacements[key]);
    }}

    function plainRewriteText(title, text, theme) {{
      const pain = inferCorePain(title, text, theme);
      const line = hookLine(hookById($('#draftHook')?.value), title, theme, pain);
      if (isCareerTheme(theme, pain + text + title)) {{
        return [
          line,
          '',
          `说白了，${{pain}}，不是因为你不努力，也不是因为你不会用工具，而是用户还没有在你的内容里看到足够明确的价值。`,
          '',
          '你要先让别人知道三件事：第一，你到底帮谁；第二，你解决什么具体问题；第三，为什么这件事可以相信你。',
          '',
          '所以别一上来就追热点、堆技巧、发很多看起来很努力的内容。先把你的能力拆成用户能看懂的三类内容：误区内容、方法内容、案例内容。',
          '',
          '今天你就做一个动作：写一句话，讲清楚“我帮助哪类人，用什么方法，解决什么问题”。这句话清楚了，你后面的标题、封面、文案和选题才不会散。',
          '',
          '最后直接问用户：你现在做账号，最卡的是定位、内容，还是信任？评论区告诉我，我下一条继续拆。'
        ].join('\\n');
      }}
      return [
        line,
        '',
        `说白了，${{pain}}，最难受的不是事情本身，而是你已经不舒服了，还在说服自己别计较。`,
        '',
        '你不用把话讲得很高级，也不用绕很多弯。用户真正想听的是：我为什么会这样，我到底该怎么办。',
        '',
        '所以这条视频可以这么讲：第一，先把那个扎心场景说出来。第二，告诉她这不是她太矫情，而是她的边界被碰到了。第三，给她一个今天就能做的小动作。',
        '',
        '你可以从一句话开始练：我先确认一下，我是不是真的愿意。别小看这句话，它是在帮你把选择权拿回来。',
        '',
        '最后别讲大道理，直接问她：你有没有也在关系里这样委屈过自己？'
      ].join('\\n');
    }}

    function viralScores(title, text) {{
      const hay = `${{title}} ${{text}}`;
      const countAny = (arr) => arr.reduce((n,w)=>n+(hay.includes(w)?1:0),0);
      return {{
        hook: Math.min(96, 45 + countAny(['你','为什么','其实','不是','别','总是','有没有','先说结论'])*8),
        conflict: Math.min(96, 42 + countAny(['不是','而是','其实','反而','真正','别再','失去','委屈'])*7),
        structure: Math.min(96, 40 + countAny(['第一','第二','第三','所以','因为','答案','最后'])*8 + (text.length > 180 ? 12 : 0)),
        action: Math.min(96, 40 + countAny(['做','练习','问自己','评论区','收藏','转发','今天'])*7),
        cover: Math.min(96, 48 + (title.length <= 24 ? 20 : 0) + (/[你别不]/.test(title) ? 12 : 0))
      }};
    }}

    function renderHookFormulas() {{
      if (!$('#hookFormulaList')) return;
      $('#hookFormulaList').innerHTML = hookFormulas.map(f=>`
        <div class="formula-card">
          <strong>${{esc(f.name)}}</strong>
          <code>${{esc(f.pattern)}}</code>
          <div class="muted">${{esc(f.use)}}</div>
        </div>`).join('');
    }}

    function themeOf(title, text) {{
      const hay = `${{title}} ${{text}}`;
      const rules = [
        ['AI超级个体/个人品牌', ['AI','超级个体','个人品牌','个人IP','IP','智能体','内容管理','自媒体','账号','信任','副业','获客','变现']],
        ['追星心理/理想自我', ['王一博','追星','偶像','粉','投射','代偿']],
        ['边界感/反讨好', ['讨好','顺从','边界','关系','失去','拒绝']],
        ['女性成长/自我觉醒', ['女性','成长','自己','人生','自由','觉醒']],
        ['情绪管理/内核稳定', ['情绪','稳定','敏感','内耗','治愈']],
        ['行动力/破碎重建', ['行动','打碎','重建','苦','开始','破碎']],
        ['文学哲思/独处', ['木心','独处','日月','读懂']]
      ];
      let best = ['综合清醒文案', 0];
      rules.forEach(([name, keys]) => {{
        const score = keys.reduce((n,k)=>n+(hay.includes(k)?1:0),0);
        if (score > best[1]) best = [name, score];
      }});
      return best[0];
    }}

    function isCareerTheme(theme, pain='') {{
      const hay = `${{theme}} ${{pain}}`;
      return /AI|超级个体|个人品牌|个人IP|\\bIP\\b|智能体|内容管理|自媒体|账号|定位|信任|副业|获客|变现|成交|商业|创业|流量|客户|粉丝/.test(hay);
    }}

    function scoreDraft(title, text) {{
      const hookWords = ['你','为什么','有没有','其实','不是','才是','别','总被','恭喜'];
      const emotionWords = ['害怕','自由','勇敢','清醒','委屈','值得','破碎','热烈','稳定','内耗','治愈'];
      const structureWords = ['不是','其实','你以为','答案','所以','真正','因为','第一','第二','第三'];
      const count = (arr, hay) => arr.reduce((n,w)=>n+(hay.includes(w)?1:0),0);
      const hay = title + text;
      let hook = 45 + Math.min(32, count(hookWords, title + text.slice(0,80))*8);
      if (/[？?]/.test(title)) hook += 8;
      if (title.length >= 8 && title.length <= 24) hook += 8;
      let structure = 45 + Math.min(32, count(structureWords, text)*5);
      if (text.length > 180 && text.length < 560) structure += 8;
      let emotion = 42 + Math.min(36, count(emotionWords, hay)*6);
      let cover = 52 + (title.length <= 24 ? 22 : -6) + (/[你别不]/.test(title) ? 10 : 0);
      const total = Math.max(35, Math.min(96, Math.round(hook*.28 + structure*.30 + emotion*.24 + cover*.18)));
      return {{ total, hook:Math.min(100,Math.round(hook)), structure:Math.min(100,Math.round(structure)), emotion:Math.min(100,Math.round(emotion)), cover:Math.min(100,Math.round(cover)) }};
    }}

    function titleVariants(title, theme) {{
      const core = title.replace(/#\\S+/g,'').trim() || '把自己活回来';
      const map = {{
        'AI超级个体/个人品牌': ['普通人做 AI 超级个体，先别急着发作品', '你的账号做不起来，不是不会发，是没人信你', '个人品牌变现前，先让用户知道你能解决什么'],
        '追星心理/理想自我': ['你追的不是偶像，是不敢活的自己', '越喜欢他，越暴露你想成为谁', '别只追光，把自己也点亮'],
        '边界感/反讨好': ['你越懂事，别人越敢亏待你', '别再用讨好，保护你的害怕', '真正的边界，是敢让别人不高兴'],
        '女性成长/自我觉醒': ['别急着变好，先把自己还给自己', '你不是来陪跑的，你是来改命的', '真正的成长，是不再低配自己'],
        '情绪管理/内核稳定': ['不被带节奏，才是真稳定', '情绪上头前，先把方向盘拿回来', '敏感不是错，失控才是'],
        '行动力/破碎重建': ['别等最佳时机，先从废墟里开花', '你不是没状态，是还没开始', '破碎不是失败，是旧版本卸载'],
        '文学哲思/独处': ['人都逃不过这四步', '独处不是孤独，是回到自己', '读懂这句话，你就不急了']
      }};
      return [core, ...(map[theme] || map['女性成长/自我觉醒'])].slice(0,4);
    }}

    function coverLines(title, theme) {{
      const variants = titleVariants(title, theme);
      return variants.map(v => {{
        const short = v.replace(/[，。？?]/g,' ').split(/\\s+/).filter(Boolean);
        if (isCareerTheme(theme)) return ['别急着发作品','先建立信任资产', theme.split('/')[0]];
        if (theme.includes('追星')) return ['你追的不是他','是不敢活的自己','追星心理'];
        if (theme.includes('讨好')) return ['别再讨好','你不是来交房租的','边界感'];
        if (theme.includes('情绪')) return ['不被带节奏','才是真稳定','内核稳定'];
        return [short[0] || v.slice(0,8), short.slice(1).join('') || '把自己活回来', theme.split('/')[0]];
      }});
    }}

    function themeClass(theme) {{
      if (theme.includes('追星')) return 'theme-star';
      if (theme.includes('边界') || theme.includes('讨好')) return 'theme-boundary';
      if (theme.includes('女性') || theme.includes('成长')) return 'theme-growth';
      if (theme.includes('情绪') || theme.includes('内核')) return 'theme-emotion';
      if (theme.includes('行动') || theme.includes('重建')) return 'theme-action';
      if (theme.includes('文学') || theme.includes('独处')) return 'theme-literary';
      return '';
    }}

    function scriptAdvice(title, text, theme) {{
      if (isCareerTheme(theme, title + text)) {{
        return [
          `3 秒钩子：先说“${{titleVariants(title, theme)[1]}}”，不要先介绍背景。`,
          '中段结构：用户卡点 1 句 + 常见误区 1 句 + 你的方法 3 点 + 今天动作 1 个。',
          '信任设计：必须说清楚“我帮谁、解决什么问题、凭什么相信我”。',
          text.length < 160 ? '文案偏短，建议补一个具体案例或操作步骤，否则像口号不像方法。' : '文案长度够用，下一步重点是删掉泛泛表达，让每 5 秒都有一个可执行信息点。'
        ];
      }}
      return [
        `3 秒钩子：先说“${{titleVariants(title, theme)[1]}}”，不要先铺垫。`,
        '中段结构：现象 1 句 + 误区 1 句 + 真相 2 句 + 行动建议 1 句。',
        '结尾互动：问一句“你是在讨好别人，还是在压抑自己？”这类能让用户评论自己的问题。',
        text.length < 160 ? '文案偏短，建议补一个具体场景，否则只有金句没有信任感。' : '文案长度够用，下一步重点是删掉重复表达，让每 5 秒都有一个信息点。'
      ];
    }}

    function fallbackCoverExamples() {{
      const pool = [
        ['你越懂事','越没人心疼','#fb5f87','真人口播'],
        ['别再讨好','你不是来交房租的','#f6c453','口播干货'],
        ['太敏感不是错','这是你的天赋','#22d3ee','真人讲述'],
        ['你追的不是他','是不敢活的自己','#a78bfa','出镜口播'],
        ['别等准备好','先开始再说','#34d399','老师口播'],
        ['把自己活回来','从停止内耗开始','#4f7bff','人物封面']
      ].sort(()=>Math.random()-.5);
      return pool.map(([a,b,color,tag])=>{{
        const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="720" height="960" viewBox="0 0 720 960">
          <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#07101f"/><stop offset="1" stop-color="#18213b"/></linearGradient></defs>
          <rect width="720" height="960" fill="url(#g)"/><rect x="54" y="68" width="612" height="824" rx="34" fill="#0d1424" stroke="${{color}}" stroke-width="4"/>
          <circle cx="360" cy="164" r="54" fill="${{color}}" opacity=".35"/><circle cx="360" cy="156" r="34" fill="#dfeaff"/><path d="M276 286c22-70 146-70 168 0" fill="#dfeaff" opacity=".9"/>
          <rect x="88" y="112" width="248" height="42" rx="21" fill="${{color}}" opacity=".9"/><text x="108" y="141" fill="#fff" font-size="24" font-family="Arial, sans-serif" font-weight="700">真人口播案例</text>
          <text x="92" y="334" fill="#fff" font-size="72" font-family="Arial, sans-serif" font-weight="900">${{a}}</text><text x="92" y="434" fill="#fff" font-size="72" font-family="Arial, sans-serif" font-weight="900">${{b}}</text>
          <text x="92" y="540" fill="${{color}}" font-size="42" font-family="Arial, sans-serif" font-weight="900">人物近景 + 大字冲突</text>
        </svg>`;
        return {{ title:`${{a}} / ${{b}}`, tag, source:'本地真人口播版式', image:'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg), pattern:'真人出镜口播：半身人物 + 大字冲突 + 栏目标签' }};
      }});
    }}

    function renderCoverExamples(target, data) {{
      const examples = (data?.examples?.length ? data.examples : fallbackCoverExamples()).slice(0,6);
      const note = data?.updatedAt ? `实时更新：${{esc(data.updatedAt)}}` : '本地刷新：每次打开随机更新';
      target.innerHTML = `
        <div class="result"><b>真人出镜口播热门案例图：</b><span class="muted"> ${{note}}</span><br><span class="muted">只保留真人/人物/老师/课程讲解/口播倾向案例，重点看“人物近景 + 大字冲突 + 少信息”。</span></div>
        <div class="cover-trends">
          ${{examples.map(x=>`
            <div class="cover-example">
              <img src="${{esc(x.image)}}" alt="${{esc(x.title || '封面案例')}}" loading="lazy" referrerpolicy="no-referrer">
              <div class="cover-example-body">
                <div class="cover-example-title">${{esc(x.title || x.tag || '热门封面案例')}}</div>
                <div class="cover-example-meta">${{esc(x.pattern || '大标题 + 强对比 + 明确主题')}}</div>
                <div class="cover-example-meta">${{x.sourceUrl ? `<a href="${{esc(x.sourceUrl)}}" target="_blank" rel="noreferrer">${{esc(x.source || '来源')}}</a>` : esc(x.source || '本地案例')}}</div>
              </div>
            </div>`).join('')}}
        </div>`;
    }}

    async function loadCoverExamples(theme) {{
      const target = $('#coverExamples');
      if (!target) return;
      renderCoverExamples(target, null);
      try {{
        const res = await fetch(apiUrl(`/api/cover-examples?theme=${{encodeURIComponent(theme || '')}}&t=${{Date.now()}}`), apiOptions({{ cache:'no-store' }}));
        if (!res.ok) throw new Error('cover api failed');
        const data = await res.json();
        renderCoverExamples(target, data);
      }} catch (err) {{
        renderCoverExamples(target, null);
      }}
    }}

    function inferCorePain(title, text, theme) {{
      const hay = `${{title}} ${{text}}`;
      if (isCareerTheme(theme, hay)) {{
        if (hay.includes('信任')) return '想做账号，但用户不知道为什么要相信你';
        if (hay.includes('定位') || hay.includes('人设')) return '想做个人品牌，但定位和人设不够清楚';
        if (hay.includes('变现') || hay.includes('成交') || hay.includes('获客')) return '有内容想变现，但缺少清晰的信任和成交路径';
        return '想成为 AI 超级个体，但不知道怎么把能力变成可持续内容资产';
      }}
      if (hay.includes('讨好') || theme.includes('讨好')) return '总是在关系里讨好别人，却把自己放到最后';
      if (hay.includes('敏感') || hay.includes('内耗') || theme.includes('情绪')) return '明明感受很强，却总被说太敏感';
      if (hay.includes('追星') || hay.includes('王一博') || theme.includes('追星')) return '把对偶像的喜欢，投射成自己不敢活出的样子';
      if (hay.includes('边界') || hay.includes('拒绝')) return '不敢拒绝别人，害怕一说不就失去关系';
      if (hay.includes('破碎') || hay.includes('行动') || theme.includes('行动')) return '知道该改变，却迟迟没有开始';
      if (hay.includes('独处') || theme.includes('文学')) return '在人群里消耗太久，忘了怎么回到自己';
      const source = String(text || title || '').replace(/#\\S+/g, ' ').replace(/\\s+/g, ' ').trim();
      const firstSentence = source.split(/[。！？!?\\n]/).map(x=>x.trim()).filter(Boolean)[0] || '';
      if (firstSentence.length >= 6) return firstSentence.slice(0, 42);
      return '该链接的真实文案痛点不够明确，需要先补充可读标题或字幕';
    }}

    function optimizedScript(title, text, theme, scores) {{
      const titles = titleVariants(title, theme);
      const mainTitle = titles[1] || titles[0] || title || '把自己活回来';
      const pain = inferCorePain(title, text, theme);
      const formula = hookById($('#draftHook')?.value || currentHookId());
      const opening = hookLine(formula, title || mainTitle, theme, pain);
      if (isCareerTheme(theme, pain + text + title)) {{
        const action = pain.includes('信任')
          ? '先别急着证明自己多厉害，先连续输出三个能解决具体问题的内容：一个讲误区，一个讲方法，一个讲案例。'
          : pain.includes('定位') || pain.includes('人设')
            ? '先用一句话说清楚：你帮谁、解决什么问题、凭什么是你。说不清这句话，发再多作品也很难留下记忆点。'
            : pain.includes('变现') || pain.includes('成交') || pain.includes('获客')
              ? '先把内容分成三类：拉新内容解决曝光，信任内容解决相信，转化内容解决行动。不要每条视频都只求播放。'
              : '把你的能力拆成用户能看懂的内容资产：选题讲问题，文案讲方法，案例讲结果，主页讲你是谁。';
        const bridge = scores.structure < 70
          ? '这条内容要按“问题-误区-方法-动作”的结构讲，不要只讲概念。'
          : '这条内容的核心不是喊口号，而是让用户看完以后知道下一步该做什么。';
        return [
          opening,
          '',
          `标题建议：${{mainTitle}}`,
          '',
          `很多人想做${{theme.split('/')[0] || '个人品牌'}}，第一反应就是：我要多发作品、我要追热点、我要把账号做起来。`,
          '',
          `但真正卡住你的，往往不是不会发，而是${{pain}}。用户不是因为你说得多才信你，而是因为他能在你的内容里看见三个东西：你理解他的问题，你有解决问题的方法，你能持续给他确定感。`,
          '',
          bridge,
          '',
          `所以这条视频我建议你这样讲：第一，先点出用户最焦虑的场景，比如“我想做账号，但不知道别人为什么要关注我”。第二，告诉他一个误区：不是先把自己包装得很厉害，而是先让用户知道你能帮他解决什么。第三，给出一个今天就能做的动作：${{action}}`,
          '',
          '真正的 AI 超级个体，不是工具用得多，而是能把自己的经验、方法和判断，变成别人愿意持续关注的内容资产。',
          '',
          '如果你也想把自己的能力做成一个可持续的个人品牌，评论区留一句“我要做资产”，我下一条继续拆具体步骤。'
        ].join('\\n');
      }}
      const action = theme.includes('追星')
        ? '别只问自己为什么喜欢他，也问问自己：他身上哪一种生命力，是我也想长出来的。'
        : theme.includes('边界') || theme.includes('讨好')
          ? '下一次你想立刻答应别人之前，先停三秒，问自己一句：我是真的愿意，还是害怕别人不高兴。'
          : theme.includes('情绪')
            ? '情绪上来的时候，先不要急着证明谁对谁错，先把注意力拉回身体，给自己十分钟不做决定。'
            : theme.includes('行动')
              ? '不要等状态完全好了再开始，先做一件小到不会失败的事，让自己重新拿回主动权。'
              : '每天给自己留一段不解释、不迎合、不表演的时间，慢慢把注意力收回来。';
      const bridge = scores.structure < 70
        ? '这条视频我会把它讲得更清楚：先说痛点，再说误区，最后给你一个今天就能做的小动作。'
        : '这条视频不用讲太满，只要把最刺痛的地方讲准，再给一个能落地的动作。';
      const ending = theme.includes('追星')
        ? '如果你也在某个人身上看见过理想中的自己，评论区打一个“我也想发光”。'
        : '如果你也想从今天开始把自己放回第一位，评论区留一句“我先站回自己”。';
      return [
        opening,
        '',
        `标题建议：${{mainTitle}}`,
        '',
        `你有没有发现，${{pain}}的时候，最累的不是那件事本身，而是你一边委屈，一边还要说服自己“算了，没关系”。`,
        '',
        '但我想告诉你，真正消耗你的，往往不是别人一句话、一个态度、一次忽视，而是你已经不舒服了，却还在替对方找理由。你明明感觉到了不对劲，却第一反应不是保护自己，而是怀疑自己是不是太敏感、太小题大做、太不懂事。',
        '',
        bridge,
        '',
        `第一，你要先承认自己的感受。感受出现，不代表你脆弱，它只是提醒你：这里可能有一个边界被碰到了。第二，不要急着把自己改造成更好说话的人。很多时候，你缺的不是懂事，而是允许自己不舒服。第三，${{action}}`,
        '',
        '真正的清醒，不是把自己变得很冷，也不是跟所有人对抗，而是你终于知道：关系可以重要，别人也可以重要，但你不能一直消失。',
        '',
        ending
      ].join('\\n');
    }}

    function renderKpis() {{
      const videos = state.videos;
      const avg = Math.round(videos.reduce((n,v)=>n+v.scores.score,0)/videos.length);
      const themes = {{}};
      videos.forEach(v => themes[v.theme] = (themes[v.theme]||0)+1);
      const best = Object.entries(themes).sort((a,b)=>b[1]-a[1])[0]?.[0] || '-';
      $('#kpiTotal').textContent = videos.length;
      $('#kpiAvg').textContent = avg;
      $('#kpiBest').textContent = best.replace('/','/');
      $('#kpiNeed').textContent = videos.filter(v => v.scores.score < 68).length;
      $('#todayActions').innerHTML = [
        '先优化低于 68 分的视频标题和封面，尤其是只有情绪没有具体动作的作品。',
        '把王一博相关作品整理成“追星心理”系列，连续做 5 条形成记忆点。',
        '每条新视频发布前先来这里生成 4 个标题和 4 个封面方案。',
        '每周固定产出 2 条方法论内容，提升收藏和复看。'
      ].map((x,i)=>`<div class="result"><b>${{i+1}}.</b> ${{esc(x)}}</div>`).join('') + renderDanaoReference('发布规划', 3);
    }}

    function renderVideoList() {{
      const search = $('#searchVideo').value.trim();
      const theme = $('#themeFilter').value;
      let videos = [...state.videos];
      if ($('#sortScore').dataset.sort === 'on') videos.sort((a,b)=>b.scores.score-a.scores.score);
      if (state.onlyNeeds) videos = videos.filter(v => v.scores.score < 68);
      videos = videos.filter(v => (!theme || v.theme === theme) && (!search || `${{v.title}} ${{v.theme}} ${{v.tags.join(' ')}} ${{v.transcript || ''}}`.includes(search)));
      $('#filterNeeds').classList.toggle('active-filter', !!state.onlyNeeds);
      $('#videoList').innerHTML = videos.map(v => `
        <article class="panel video ${{themeClass(v.theme)}} ${{v.scores.score<60?'low':v.scores.score<70?'warn':''}}">
          <div class="row"><div><div class="muted">#${{v.idx}} · <span class="chip theme-chip">${{esc(v.theme)}}</span> · ${{esc(v.date || '日期缺失')}}</div><h3>${{esc(v.title)}}</h3></div><div class="score">${{v.scores.score}}</div></div>
          <div class="chips"><span class="chip">钩子 ${{v.scores.hook}}</span><span class="chip">结构 ${{v.scores.structure}}</span><span class="chip">情绪 ${{v.scores.emotion}}</span><span class="chip">封面 ${{v.scores.cover}}</span></div>
          <div class="stats-grid">
            <div class="stat-pill"><b>${{fmt(v.stats?.play)}}</b><span>播放量</span></div>
            <div class="stat-pill"><b>${{fmt(v.stats?.likes)}}</b><span>点赞</span></div>
            <div class="stat-pill"><b>${{fmt(v.stats?.comments)}}</b><span>评论</span></div>
            <div class="stat-pill"><b>${{fmt(v.stats?.collects)}}</b><span>收藏</span></div>
            <div class="stat-pill"><b>${{fmt(v.stats?.shares)}}</b><span>分享</span></div>
          </div>
          <div class="cover">${{esc(v.cover.join(' / '))}}</div>
          <div class="review-sections">
            <div class="review-tip"><b>钩子优化：</b>${{esc(v.optimizationTips?.hook || '前 3 秒先点名痛点和代价。')}}</div>
            <div class="review-tip"><b>结构优化：</b>${{esc(v.optimizationTips?.structure || '按痛点、误区、真相、动作推进。')}}</div>
            <div class="review-tip"><b>情绪优化：</b>${{esc(v.optimizationTips?.emotion || '补具体场景和用户真实感受。')}}</div>
            <div class="review-tip"><b>封面优化：</b>${{esc(v.optimizationTips?.cover || '三行大字突出冲突和栏目标签。')}}</div>
          </div>
          ${{renderDanaoReference('发布复盘', 2)}}
          <details class="transcript-box" open>
            <summary>文字稿 · ${{esc(v.transcriptSource || '本地内容')}}</summary>
            <div class="transcript-content">${{esc(v.transcript || v.scores.status_note || '暂无文字稿')}}</div>
          </details>
          <div class="actions"><button class="secondary" onclick="loadVideoToOptimizer(${{v.idx}})">拿这条做改写</button><button class="secondary" onclick="makeSiblingIdeas(${{v.idx}})">生成同类选题</button></div>
        </article>`).join('');
    }}

    function showNeedVideos() {{
      state.onlyNeeds = true;
      $('#searchVideo').value = '';
      $('#themeFilter').value = '';
      $('#sortScore').dataset.sort = 'on';
      switchView('library');
      renderVideoList();
    }}

    function renderSelectors() {{
      const themes = [...new Set([...state.pillars, ...state.videos.map(v=>v.theme)])];
      $('#themeFilter').innerHTML = '<option value="">全部主题</option>' + themes.map(t=>`<option>${{esc(t)}}</option>`).join('');
      $('#draftTheme').innerHTML = '<option value="">自动判断主题</option>' + themes.map(t=>`<option>${{esc(t)}}</option>`).join('');
      $('#ideaTheme').innerHTML = '<option value="">不套用预设，使用手动输入</option>' + themes.map(t=>`<option>${{esc(t)}}</option>`).join('');
      $('#ideaPain').innerHTML = '<option value="">不套用预设，使用手动输入</option>' + state.painPoints.map(p=>`<option>${{esc(p)}}</option>`).join('');
      if ([...$('#ideaTheme').options].some(option => option.value === 'AI超级个体内容管理')) $('#ideaTheme').value = 'AI超级个体内容管理';
      if ([...$('#ideaPain').options].some(option => option.value === '内容越做越乱，不知道怎么把热点、选题、文案和复盘连成一套流程')) $('#ideaPain').value = '内容越做越乱，不知道怎么把热点、选题、文案和复盘连成一套流程';
      const hookOptions = hookFormulas.map(f=>`<option value="${{esc(f.id)}}">${{esc(f.name)}}｜${{esc(f.use)}}</option>`).join('');
      ['draftHook','ideaHook'].forEach(sel => {{
        const el = $('#' + sel);
        if (el) el.innerHTML = hookOptions;
      }});
      syncHookSelects(currentHookId());
      renderViralArchiveList();
    }}

    function selectedIdeaTheme() {{
      return ($('#ideaThemeCustom')?.value || '').trim() || $('#ideaTheme').value || 'AI超级个体内容管理';
    }}

    function selectedIdeaPain() {{
      return ($('#ideaPainCustom')?.value || '').trim() || $('#ideaPain').value || '内容越做越乱，不知道怎么把热点、选题、文案和复盘连成一套流程';
    }}

    function selectedIdeaHot() {{
      const manual = ($('#ideaHotCustom')?.value || '').trim();
      if (manual) return {{
        title: manual,
        summary: `手动输入的抖音热点：${{manual}}。`,
        source: '手动输入热点',
        angle: '按手动输入热点做具体新闻切入。'
      }};
      const raw = $('#ideaHotTopic')?.value || '';
      if (!raw) return null;
      try {{
        return JSON.parse(raw);
      }} catch {{
        return {{ title:raw, summary:`抖音热点：${{raw}}。`, source:'抖音热搜', angle:'结合当前抖音热点做具体切入。' }};
      }}
    }}

    function hotMetaLine(hot) {{
      const parts = [];
      if (hot?.rank) parts.push(`热榜第${{hot.rank}}名`);
      if (hot?.hotValueText) parts.push(`热度${{hot.hotValueText}}`);
      else if (hot?.hotValue) parts.push(`热度${{Number(hot.hotValue).toLocaleString('zh-CN')}}`);
      if (hot?.videoCount) parts.push(`相关视频/讨论${{hot.videoCount}}条`);
      if (hot?.label) parts.push(`标记${{hot.label}}`);
      return parts.join(' · ');
    }}

    function hotSummaryLine(hot) {{
      return (hot?.summary || hot?.sentence || hot?.angle || '').trim();
    }}

    async function loadHotTopics() {{
      const select = $('#ideaHotTopic');
      const status = $('#hotTopicStatus');
      if (!select) return;
      if (status) status.textContent = '正在刷新抖音热搜...';
      try {{
        const res = await fetch(apiUrl(`/api/hot-topics?theme=${{encodeURIComponent(selectedIdeaTheme())}}&pain=${{encodeURIComponent(selectedIdeaPain())}}&t=${{Date.now()}}`), apiOptions({{ cache:'no-store' }}));
        const data = await res.json();
        state.hotTopics = data.topics || [];
        select.innerHTML = '<option value="">不结合热点</option>' + state.hotTopics.map((x, i)=>{{
          const meta = hotMetaLine(x);
          return `<option value="${{esc(JSON.stringify(x))}}">${{i+1}}. ${{esc(x.title.slice(0,34))}}｜${{esc(meta || x.source || '抖音热搜')}}</option>`;
        }}).join('');
        if (status) status.textContent = data.sourceNote || `已刷新 ${{state.hotTopics.length}} 条抖音热搜`;
      }} catch (err) {{
        if (status) status.textContent = '抖音热搜刷新失败，可手动输入热点继续生成';
      }}
    }}

    function analyzeDraft() {{
      const title = $('#draftTitle').value.trim();
      const text = $('#draftText').value.trim();
      const theme = $('#draftTheme').value || themeOf(title, text);
      const formula = hookById($('#draftHook').value);
      syncHookSelects(formula.id);
      const scores = scoreDraft(title, text);
      const titles = titleVariants(title, theme);
      const covers = coverLines(title, theme);
      const advice = scriptAdvice(title, text, theme);
      const newScript = optimizedScript(title, text, theme, scores);
      state.optimizedDraft = {{ title: titles[1] || titles[0] || title, script: newScript, theme }};
      $('#draftResult').innerHTML = `
        <div class="result"><b>主题判断：</b>${{esc(theme)}}　<b>潜力分：</b>${{scores.total}}（钩子 ${{scores.hook}} / 结构 ${{scores.structure}} / 情绪 ${{scores.emotion}} / 封面 ${{scores.cover}}）</div>
        <div class="result"><b>已套用钩子公式：</b>${{esc(formula.name)}}<br><span class="muted">${{esc(formula.pattern)}} · 下次生成选题会自动沿用。</span></div>
        <div class="result"><b>标题备选：</b><br>${{titles.map((t,i)=>`${{i+1}}. ${{esc(t)}}`).join('<br>')}}</div>
        <div class="result"><b>封面三行字：</b><br>${{covers.map((c,i)=>`${{i+1}}. ${{esc(c.join(' / '))}}`).join('<br>')}}</div>
        <div id="coverExamples" class="result-list"></div>
        <div class="result"><b>文案调整：</b><br>${{advice.map((a,i)=>`${{i+1}}. ${{esc(a)}}`).join('<br>')}}</div>
        ${{renderDanaoReference('标题封面文案优化', 3)}}
        <div class="result"><b>新版文字稿：</b><div class="copybox">${{esc(newScript)}}</div></div>
        <div class="actions">
          <button class="primary" onclick="copyOptimizedDraft()">复制新版文字稿</button>
          <button class="secondary" onclick="replaceWithOptimizedDraft()">替换左侧文字稿</button>
        </div>
        <div class="result"><b>发布建议：</b>标题里保留一个强冲突词，封面不超过 14 个大字，正文结尾加一个让用户代入自己的问题。</div>`;
      loadCoverExamples(theme);
    }}

    function plainRewriteDraft() {{
      const title = $('#draftTitle').value.trim();
      const text = $('#draftText').value.trim();
      const theme = $('#draftTheme').value || themeOf(title, text);
      syncHookSelects($('#draftHook').value);
      const rewritten = plainRewriteText(title, text, theme);
      state.plainDraft = {{ title: title || '大白话改写稿', script: rewritten, theme }};
      $('#draftResult').innerHTML = `
        <div class="result"><b>大白话改写：</b><span class="muted">保留原观点，去掉绕弯和书面感，更像真人口播。</span></div>
        ${{renderDanaoReference('标题封面文案优化', 3)}}
        <div class="result"><b>新版文字稿：</b><div class="copybox">${{esc(rewritten)}}</div></div>
        <div class="actions">
          <button class="primary" onclick="copyPlainDraft()">复制大白话文字稿</button>
          <button class="secondary" onclick="replaceWithPlainDraft()">替换左侧文字稿</button>
        </div>`;
    }}

    window.copyPlainDraft = async function() {{
      await navigator.clipboard.writeText(state.plainDraft?.script || '');
    }}

    window.replaceWithPlainDraft = function() {{
      if (!state.plainDraft) return;
      $('#draftTitle').value = state.plainDraft.title;
      $('#draftText').value = state.plainDraft.script;
      $('#draftTheme').value = state.plainDraft.theme;
      analyzeDraft();
    }}

    function renderViralAnalysis(data) {{
      if (!data || data.ok === false) {{
        state.lastViralAnalysis = null;
        $('#viralResult').innerHTML = `
          <div class="result"><b>链接内容提取失败，未生成拆解。</b><br><span class="muted">${{esc(data?.message || '没有从该链接拿到真实标题、文案、封面或数据。')}}</span></div>
          <div class="result"><b>下一步：</b>请确认粘贴的是单条公开视频分享链接；系统不会要求先抓取博主主页，拿不到真实标题、文案、封面或数据时才会停止生成。</div>`;
        return;
      }}
      const title = data.title || '待拆解短视频链接';
      const text = data.fullText || data.transcriptPreview || title;
      const theme = '当前链接拆解';
      const pain = linkTopic(title, text);
      const scores = data.scores || viralScores(title, text);
      const avg = Math.round((scores.hook + scores.conflict + scores.structure + scores.action + scores.cover) / 5);
      const reusableHook = safeClip(splitSentences(text, 1)[0] || title || pain, 42);
      const metric = (name, value) => `<div class="metric-row"><span class="muted">${{esc(name)}} ${{value}}</span><div class="meter"><span style="width:${{value}}%"></span></div></div>`;
      const techniques = [
        `开头停留点来自当前链接原文：${{legacySafe(reusableHook)}}`,
        `核心主题只按当前链接判断：${{legacySafe(pain)}}。`,
        '中段拆解只保留原视频的信息推进，不套用历史账号的情感、心理或女性成长模板。',
        '每 5 到 8 秒给一个新信息点：现象、原因、例子、动作。',
        '结尾互动要围绕当前链接主题提问，不使用旧栏目口号。'
      ];
      const template = [
        `开头：${{legacySafe(reusableHook)}}`,
        `场景：围绕「${{legacySafe(pain)}}」补一个新的具体画面。`,
        '推进：解释为什么这件事重要，换一个新例子，不复述原句。',
        '方法：给用户一个能马上执行的动作。',
        `互动：围绕「${{legacySafe(pain)}}」问一个可回答的问题。`
      ].join('\\n');
      const viralRecord = {{
        id: `viral-${{Date.now()}}`,
        title,
        theme,
        pain,
        avg,
        url: data.resolvedUrl || data.url || $('#viralUrl')?.value.trim() || '',
        source: data.source || '链接分析',
        scores,
        stats: data.stats || null,
        duration: data.duration || data.durationSec || data.videoDuration || data.video_duration || '',
        transcriptPreview: data.transcriptPreview || '',
        fullText: data.fullText || data.transcriptPreview || '',
        transcriptSource: data.transcriptSource || '页面文案',
        videoTranscriptStatus: data.videoTranscriptStatus || '',
        videoTranscriptError: data.videoTranscriptError || '',
        cover: data.cover || ['痛点大字','真人口播','反常识标签'],
        coverImage: data.coverImage || data.coverUrl || '',
        coverSource: data.coverSource || data.coverUrl || '',
        elements: [...(data.elements || []), ...techniques].slice(0,7),
        template,
        createdAt: new Date().toLocaleString()
      }};
      viralRecord.coverAdvice = viralCoverAdvice(viralRecord);
      viralRecord.deepDive = viralDeepSections(viralRecord);
      viralRecord.recreation = makeViralRecreation(viralRecord);
      state.lastViralAnalysis = viralRecord;
      $('#viralResult').innerHTML = `
        <div class="result"><b>分析来源：</b>${{esc(data.source || '链接分析')}}<br><span class="muted">${{esc(data.resolvedUrl || data.url || '')}}</span></div>
        <div class="result"><b>爆款潜力：</b>${{avg}}　<span class="muted">${{esc(theme)}} · ${{esc(pain)}}</span><br><b>识别标题：</b>${{esc(title)}}</div>
        ${{data.stats ? `<div class="result"><b>链接数据：</b>播放 ${{fmt(data.stats.play)}} · 点赞 ${{fmt(data.stats.likes)}} · 评论 ${{fmt(data.stats.comments)}} · 收藏 ${{fmt(data.stats.collects)}} · 分享 ${{fmt(data.stats.shares)}}</div>` : ''}}
        <div class="result"><b>提取文案功能：</b><span class="muted"> ${{esc(viralRecord.transcriptSource)}}${{viralRecord.videoTranscriptStatus === 'failed' ? ` · 视频下载转写失败：${{esc(viralRecord.videoTranscriptError)}}` : ''}}</span>${{renderQingdouExtract(viralRecord)}}</div>
        <div class="result">${{metric('开场钩子', scores.hook)}}${{metric('冲突反差', scores.conflict)}}${{metric('结构递进', scores.structure)}}${{metric('行动价值', scores.action)}}${{metric('封面传播', scores.cover)}}</div>
        <div class="result"><b>爆款元素：</b><br>${{[...(data.elements || []), ...techniques].slice(0,7).map((x,i)=>`${{i+1}}. ${{esc(x)}}`).join('<br>')}}</div>
        ${{renderDanaoReference('爆款短视频拆解', 3)}}
        <div class="result"><b>深度拆解：</b>${{renderViralDeepDive(viralRecord)}}</div>
        <div class="result"><b>封面图与拆解建议：</b>${{renderCoverCompare(viralRecord)}}</div>
        <div class="result"><b>提取文案并二创：</b>${{renderViralRecreation(viralRecord)}}</div>
        <div class="result"><b>可复用创作模板：</b><div class="copybox">${{esc(template)}}</div></div>
        <div class="actions">
          <button class="primary" onclick="archiveCurrentViral()">归档拆解结果</button>
          <button class="secondary" onclick="archiveAndUseViral()">归档并用于选题生成</button>
        </div>`;
    }}

    window.archiveCurrentViral = function() {{
      if (!state.lastViralAnalysis) return;
      const items = viralArchives().filter(x=>x.id !== state.lastViralAnalysis.id && x.title !== state.lastViralAnalysis.title);
      items.unshift(state.lastViralAnalysis);
      saveViralArchives(items);
      renderViralArchiveList();
      $('#viralResult').insertAdjacentHTML('afterbegin', '<div class="result"><b>已归档：</b>这个爆款拆解现在可以在选题生成器里选择套用。</div>');
    }}

    window.archiveAndUseViral = function() {{
      archiveCurrentViral();
      if (!state.lastViralAnalysis) return;
      useArchivedCaseInIdeas(state.lastViralAnalysis.id);
    }}

    async function analyzeViral() {{
      const url = $('#viralUrl').value.trim();
      if (!url) {{
        $('#viralResult').innerHTML = '<div class="result"><b>请先粘贴短视频链接。</b><br><span class="muted">支持 v.douyin.com 短链接和 douyin.com/video 长链接。</span></div>';
        return;
      }}
      $('#viralResult').innerHTML = '<div class="result"><b>正在提取链接内容...</b><br><span class="muted">系统会先提取真实标题、封面和数据；拿到播放地址后会临时下载视频做逐字转写，转写完成后自动删除原视频。</span></div>';
      try {{
        const res = await fetch(apiUrl('/api/viral-analyze'), apiOptions({{
          method:'POST',
          cache:'no-store',
          headers: {{ 'Content-Type':'application/json', ...(accessKey ? {{ 'X-Workflow-Key': accessKey }} : {{}}) }},
          body: JSON.stringify({{ url }})
        }}));
        if (!res.ok) throw new Error('链接分析接口不可用');
        renderViralAnalysis(await res.json());
      }} catch (err) {{
        renderViralAnalysis({{ ok:false, message:`链接分析接口不可用：${{err.message || err}}。未提取到真实内容，所以没有生成拆解。` }});
      }}
    }}

    window.copyOptimizedDraft = async function() {{
      await navigator.clipboard.writeText(state.optimizedDraft?.script || '');
    }}

    window.replaceWithOptimizedDraft = function() {{
      if (!state.optimizedDraft) return;
      $('#draftTitle').value = state.optimizedDraft.title;
      $('#draftText').value = state.optimizedDraft.script;
      $('#draftTheme').value = state.optimizedDraft.theme;
      analyzeDraft();
    }}

    function loadVideoToOptimizer(idx) {{
      const v = state.videos.find(x=>x.idx===idx);
      $('#draftTitle').value = v.title;
      $('#draftText').value = v.transcript;
      $('#draftTheme').value = v.theme;
      switchView('optimizer');
      analyzeDraft();
    }}
    window.loadVideoToOptimizer = loadVideoToOptimizer;

    const topicTemplates = [
      '{{theme}}里最容易被忽略的问题：{{pain}}',
      '为什么你明明关注{{theme}}，却一直卡在{{pain}}',
      '{{pain}}的人，先别急着找答案',
      '把{{theme}}做出结果，先拆清这 3 个误区',
      '如果你正在{{pain}}，先从这个具体动作开始',
      '{{theme}}不是知道就行，关键是怎么开始行动',
      '普通人做{{theme}}，最该先补上的一步',
      '{{pain}}背后，其实少了一个可执行流程',
      '用一个真实场景讲清楚{{theme}}',
      '{{theme}}从想法到结果，中间差的不是热情',
      '别只看结论，{{theme}}真正有用的是这套判断',
      '今天把{{pain}}变成一个可执行动作'
    ];

    const careerTopicTemplates = [
      '为什么{{pain}}，才是{{theme}}做不起来的真正原因',
      '普通人做{{theme}}，先别急着发作品',
      '{{theme}}最该先建立的不是流量，而是信任',
      '想靠{{theme}}变现，先把这 3 件事说清楚',
      '{{pain}}的人，最需要先做一套内容资产',
      '别再乱发作品了，{{theme}}要先搭内容定位',
      '用户为什么不信你？因为你少了这条内容',
      '从今天开始，把你的能力做成可被看见的资产',
      '{{theme}}不是发朋友圈，而是持续交付确定感',
      '一个人做账号，怎样让陌生人快速相信你',
      'AI 不是替你变强，是放大你已经清楚的能力',
      '把经验变成内容，把内容变成信任，把信任变成成交'
    ];

    const aiSuperTopicTemplates = [
      '{{theme}}别再靠灵感，先搭一条内容流水线',
      '把内容混乱变成每天能执行的工作台',
      'AI 超级个体不是多发作品，而是先管好素材入口',
      '一条抖音热点，怎样变成 3 条能发的口播',
      '{{theme}}的第一步：把采集、选题、文案、复盘分开',
      '别再临时想标题，先做你的选题资产库',
      '用 AI 管内容，最该先自动化的是这一步',
      '内容越做越乱，说明你缺的不是工具，是流程',
      '一个人做账号，怎样把每天的内容生产稳定下来',
      '把爆款拆解变成自己的选题，不要再只收藏',
      '发布前 10 分钟，先用这张检查表过一遍',
      '未来 7 天怎么发，先从你的旧作品里找答案'
    ];

    function cleanTopic(topic) {{
      return String(topic || '').replace(/^\\d+[.、]\\s*/, '').replace(/｜.*/, '').trim();
    }}

    function ideaSeed(text) {{
      return Math.abs(String(text || '').split('').reduce((n, ch)=>((n * 31) + ch.charCodeAt(0)) | 0, 7));
    }}

    function pickSeed(list, seed, offset=0) {{
      return list[(seed + offset) % list.length];
    }}

    function ideaDomain(theme, pain, topic) {{
      const hay = `${{theme}} ${{pain}} ${{topic}}`;
      if (isCareerTheme(theme, hay)) return 'content_business';
      return detectViralDomain(hay);
    }}

    function isAISuperContentTheme(theme='', pain='') {{
      const hay = `${{theme}} ${{pain}}`;
      return /AI\\s*超级个体|超级个体内容管理|AI内容工作台|短视频工作流|内容工作台|内容管理|智能体提效|内容自动化|工作流/.test(hay);
    }}

    function ideaVariantPlan(clean, theme, pain, variant=0) {{
      const domain = ideaDomain(theme, pain, clean);
      const seed = ideaSeed(`${{clean}}|${{theme}}|${{pain}}|${{variant}}`);
      const plans = {{
        content_business: {{
          angles:['信任资产','内容定位','案例证明','成交路径','主页承接','AI 协作'],
          scenes:[
            `用户刷到你时，第一反应不是买不买，而是先判断你到底懂不懂他的问题`,
            `你每天都在发内容，但主页、标题和结尾没有形成同一个信任闭环`,
            `用户看完觉得有道理，却不知道下一步该找你做什么`,
            `你有能力、有经验，但内容里缺少能被截图、收藏和转发的确定感`
          ],
          mistakes:['只追热点，不解释你解决什么问题','把内容当日记发，没有给用户选择你的理由','标题讲自己很努力，正文没有证明你可信','把涨粉当目标，却忽略了成交前的信任铺垫'],
          methods:[
            ['写清楚你帮谁解决什么问题','用一个真实场景证明你理解用户','结尾给一个可评论的下一步问题'],
            ['把主页置顶改成身份说明','连续发三条误区/方法/案例内容','用同一句价值主张贯穿标题和封面'],
            ['先讲用户最卡的场景','再给一个可执行步骤','最后用案例证明这个步骤有效'],
            ['把经验拆成清单','把清单变成栏目','把栏目沉淀成用户一眼能懂的服务入口']
          ],
          proof:['拆一个客户常问的问题','拿你过去做成的一件小结果举例','用一个失败内容和一个有效内容做对比','展示从问题到方案的完整思考过程'],
          interactions:['你现在做账号最卡的是定位、内容还是信任？','如果你要做个人品牌，你最想先解决哪一步？','评论区留一个你的行业，我帮你拆第一条信任内容。','你觉得用户不信你的原因，是看不懂价值，还是看不到证据？'],
          cover:['先建立信任','别急着发作品','把能力做成资产']
        }},
        ai_tool: {{
          angles:['工具落地','任务拆解','效率提升','工作流搭建','智能体应用','真实场景'],
          scenes:[
            `很多人收藏了一堆 AI 工具，但真正打开时还是不知道第一句话该怎么说`,
            `你想让 AI 帮你干活，却没有把目标、材料和标准交代清楚`,
            `同一个工具，有人做出结果，有人只得到一堆看起来正确的废话`,
            `问题不是工具不够强，而是你还没把任务拆到 AI 能执行`
          ],
          mistakes:['把 AI 当搜索框用','只问一句大问题，不给背景和标准','收藏工具清单，却不拿真实任务验证','想做万能智能体，结果每件事都做不深'],
          methods:[
            ['先写清楚最终结果','再给 AI 角色、背景和限制','最后让它输出可检查的版本'],
            ['选一个真实任务','拆成三步流程','每一步都保存可复用提示词'],
            ['先喂资料','再让 AI 生成方案','最后用真实业务标准校验'],
            ['一个场景做一个智能体','一个智能体只干一类任务','跑通后再复制到下一个场景']
          ],
          proof:['用一个你每天重复做的任务演示','拿 AI 前后两版结果做对比','展示提示词从粗到细的变化','拆一个从输入到输出的完整工作流'],
          interactions:['你最想先用 AI 解决哪件重复工作？','评论区留一个任务，我帮你拆成 AI 工作流。','你卡在工具选择，还是卡在提示词？','如果只能先做一个智能体，你会让它干什么？'],
          cover:['AI别只收藏','先跑通一个任务','工具要落地']
        }},
        learning: {{
          angles:['最小练习','反馈闭环','知识输出','方法筛选','持续训练','复盘改进'],
          scenes:[
            `你听懂了很多方法，但第二天回到自己身上还是不知道先做哪一步`,
            `你一直在找更好的资料，却很少把一个知识点真正练到手上`,
            `收藏让你感觉自己在进步，但输出才会暴露你到底会不会`,
            `你不是学得少，而是没有把学习变成可反馈的动作`
          ],
          mistakes:['把收藏当学习','只看方法不做练习','追求一次学完，反而迟迟不开始','没有记录反馈，所以每次都像从零开始'],
          methods:[
            ['选一个最关键的问题','用自己的话讲一遍','当天做一次最小练习'],
            ['把知识点改成一道题','做完马上对照结果','记录下一次要改什么'],
            ['只学一条方法','用一个真实场景验证','把反馈写成下一条内容'],
            ['先输出半成品','再补缺口','最后形成自己的模板']
          ],
          proof:['展示一次练习前后的变化','用一个失败例子说明误区','把复杂方法拆成一张清单','记录 7 天连续练习的反馈'],
          interactions:['你现在最想学会的能力是什么？','你卡在开始、坚持，还是复盘？','评论区留一个目标，我帮你拆最小练习。','你收藏最多但一直没做的是什么？'],
          cover:['别只收藏','先做一次小练习','学习要闭环']
        }},
        product_service: {{
          angles:['真实需求','使用场景','避坑判断','长期成本','选择标准','体验对比'],
          scenes:[
            `很多选择一开始看着很心动，真正用起来才发现不适合自己的场景`,
            `你以为自己在比价格，其实是在比长期使用成本和真实体验`,
            `卖点写得越热闹，用户越需要一个简单的判断标准`,
            `用户不是不想买，而是不确定这个选择到底适不适合自己`
          ],
          mistakes:['只看表面卖点','被低价或颜值带着走','没有把选择放进真实场景','忽略长期维护和使用成本'],
          methods:[
            ['写下三个真实使用场景','把每个方案放进去比较','只选长期会用到的价值'],
            ['先判断必要需求','再看加分功能','最后算长期成本'],
            ['列出不能接受的坑','对照产品细节检查','保留一个备选方案'],
            ['先问谁会用','再问用多久','最后问坏了怎么办']
          ],
          proof:['做一次真实场景对比','展示一个容易忽略的细节','用用户真实问题反推选择标准','把买前买后的体验差异讲清楚'],
          interactions:['你做选择时最容易踩哪个坑？','评论区留你的场景，我帮你判断该怎么看。','你更在意价格、效果还是长期省心？','这类产品你最怕买错哪一点？'],
          cover:['别只看卖点','先看真实场景','这样选不后悔']
        }},
        general: {{
          angles:['误区纠偏','具体场景','三步行动','反差判断','自我检查','连续练习'],
          scenes:[
            `很多人不是不想做${{theme.split('/')[0] || '这个主题'}}，而是卡在「${{pain}}」以后，不知道第一步该先动哪里`,
            `你看过很多方法，但一回到自己的场景里，最难的还是把「${{pain}}」变成一个当天能做的小动作`,
            `真正让人停下来的，不是一个漂亮观点，而是你把${{theme.split('/')[0] || '这个主题'}}里的真实卡点说得足够具体`,
            `如果一个选题只停在结论层面，用户听完会觉得对；但只有把「${{pain}}」放进真实场景里，他才会觉得这和自己有关`
          ],
          mistakes:['只给结论，不给场景','只说应该改变，不说从哪一步开始','把问题讲得太大，用户不知道怎么照做','开头很有情绪，中段没有具体动作'],
          methods:[
            ['把问题缩小到一个具体场景','只选一个今天能完成的小动作','做完以后记录一次真实反馈'],
            ['先停下找完美答案','把问题换成一个具体选择','用十分钟先试一次'],
            ['列出你已经知道的做法','删掉今天做不到的部分','保留一个最小动作'],
            ['先说清楚现在的问题','再定一个能检查的结果','最后安排下一次复盘']
          ],
          proof:['拿一个今天就会遇到的场景举例','把复杂问题拆成一个小动作','用前后对比说明动作为什么有效','把常见误区换成一句更好懂的话'],
          interactions:['你现在最卡的是理解、开始，还是坚持？','如果只改一步，你最想先改哪一步？','评论区留一个你的场景，我帮你拆成一个小动作。','这个问题你遇到过吗？你当时是怎么处理的？'],
          cover:['别只听道理','先做这一步','今天就能用']
        }}
      }};
      const config = plans[domain] || plans.general;
      const method = pickSeed(config.methods, seed, 3);
      return {{
        domain,
        angle: pickSeed(config.angles, seed, 0),
        scene: pickSeed(config.scenes, seed, 1),
        mistake: pickSeed(config.mistakes, seed, 2),
        method,
        proof: pickSeed(config.proof, seed, 4),
        interaction: pickSeed(config.interactions, seed, 5),
        cover: config.cover,
        seed
      }};
    }}

    function oralVariantProfile(clean, theme, pain, plan, variant=0, careerMode=false) {{
      const themeName = theme.split('/')[0] || theme;
      const variantIndex = Math.abs(Number(variant) || 0);
      const careerProfiles = [
        {{
          hook:`先说一个很现实的判断：做${{themeName}}，别急着多发，先让别人一眼看懂你到底能帮他解决什么。`,
          scene:`你是不是也有这种感觉：每天都在发内容，标题也改了，热点也追了，可别人听完以后，还是不知道为什么要关注你。`,
          conflict:`问题不在于你不努力，而在于你的内容没有形成一个连续的判断。今天讲一个观点，明天追一个热点，后天又换一个方向，用户很难在你身上形成稳定印象。`,
          turn:`所以「${{clean}}」这件事，真正要解决的不是多发一条，而是让每一条都承担一个清楚的任务。`,
          proof:`你可以想象一个新用户第一次看到你，他不会研究你以前发过什么，他只会在当下判断：你是谁，你懂什么，你能不能帮我省掉一段弯路。`,
          close:`如果你的账号现在也卡住了，评论区告诉我：你最缺的是定位、选题、文案，还是复盘？`
        }},
        {{
          hook:`很多账号不是死在没流量，而是流量来了以后，别人看不出你值得被留下。`,
          scene:`很多人做账号，一上来就想要爆款。可爆款最怕的不是没流量，而是流量来了以后，用户不知道你到底值不值得留下。`,
          conflict:`你越着急证明自己，内容越容易变成自我介绍；你越想把所有能力都讲出来，用户越抓不到重点。`,
          turn:`所以「${{clean}}」不能只当成一个标题，它要变成一个入口，让别人一秒知道你正在解决什么问题。`,
          proof:`比如同样讲一个方法，有的人只说“我很专业”，有的人直接说“你现在卡住，是因为少了这一步”。后者更容易被记住，因为它先把用户的处境说出来了。`,
          close:`你现在发内容最想让别人记住你哪一个能力？把那句话写出来，越具体越好。`
        }},
        {{
          hook:`如果你的内容总是散，先别怪表达能力，先看你有没有把能力放进固定场景里。`,
          scene:`如果你做内容做久了，一定会遇到一个阶段：你明明有经验，也有想法，但写出来总像一堆散点。`,
          conflict:`散点内容最大的问题，是每一条都像重新开始。用户看一条觉得还行，看两条还是不知道你到底围绕什么在持续输出。`,
          turn:`所以「${{clean}}」这类选题，最重要的是把你的能力放进一个固定场景里，让用户知道你不是随便聊聊。`,
          proof:`一个很简单的判断：这次表达结束以后，别人能不能说出你帮哪类人解决哪类问题？如果说不出来，它就还不够聚焦。`,
          close:`如果你愿意，我下一条可以继续拆：一条内容怎么从散点变成栏目。`
        }},
        {{
          hook:`用户愿意听你，不是因为你说得多，而是因为你第一句话就说中了他的麻烦。`,
          scene:`很多时候，账号做不起来，不是因为你没有方法，而是你把方法讲得离用户太远。`,
          conflict:`用户不想先听一整套理论，他想先确认：我现在的麻烦，你到底懂不懂。只有他觉得你懂，后面的方法才有重量。`,
          turn:`所以「${{clean}}」要先从用户正在经历的那一刻讲起，再把你的方法放进去。`,
          proof:`比如不要一上来讲“内容定位很重要”，而是先说“你发了很多条，别人还是不知道为什么要信你”。这一句话出来，用户才会愿意继续听。`,
          close:`你可以在评论区留一句：你现在最想让用户相信你的是什么？`
        }},
        {{
          hook:`一个人做账号，最值钱的不是每天都有灵感，而是每次表达都能积累信任。`,
          scene:`你可能也经历过：今天想讲定位，明天想讲热点，后天又想讲工具，结果每一条都没错，但放在一起就是没有主线。`,
          conflict:`没有主线的时候，用户不会觉得你全面，只会觉得不知道该从哪里理解你。`,
          turn:`所以「${{clean}}」要承担一个很具体的角色：把你的能力、用户的卡点和下一步行动连起来。`,
          proof:`当用户能听懂“你帮谁、解决什么、怎么开始”，他才会把你从普通账号里单独记住。`,
          close:`你现在最想建立哪一种信任：专业、结果、陪跑，还是工具能力？`
        }},
        {{
          hook:`别把个人品牌做成自我介绍，真正有效的是让别人从你的内容里看见自己的下一步。`,
          scene:`很多人介绍自己很认真，经历、能力、证书都说了，可用户听完还是没有行动，因为他没有找到自己的入口。`,
          conflict:`用户不是不相信你，他是不知道这件事和他今天的困难有什么关系。`,
          turn:`所以「${{clean}}」要先把用户的问题摆在前面，再把你的经验变成可执行的路径。`,
          proof:`你每次能帮用户省掉一次试错，他对你的信任就会多一层。内容不是展示你有多厉害，而是证明你真的能把问题往前推。`,
          close:`评论区说一个你最想解决的用户问题，我帮你把它拆成一条能发的口播。`
        }}
      ];
      const generalProfiles = [
        {{
          hook:`先说结果：做${{themeName}}，不要从大道理开始，先把「${{pain}}」放进一个具体场景里。`,
          scene:`很多人遇到「${{clean}}」这种问题，第一反应是继续找方法，可真正卡住的往往不是方法少，而是不知道现在该先处理哪一个动作。`,
          conflict:`如果你只停在“我应该改变”，很容易越想越累。因为这句话太大了，大到你今天根本不知道从哪里下手。`,
          turn:`所以这一次别把问题讲大，直接把它缩到今天能发生的一件小事里。`,
          proof:`比如把「${{pain}}」换成一个画面：你正在犹豫、正在拖延、正在反复比较，或者正在因为一个选择迟迟不敢开始。画面一具体，行动才会跟上。`,
          close:`你现在最卡住的那个具体场景是什么？把它写出来，答案会清楚很多。`
        }},
        {{
          hook:`如果你一直在${{pain}}，先别急着否定自己，先换一个更小的入口。`,
          scene:`你可能已经听过很多关于${{themeName}}的建议，可一回到现实里，还是会卡在同一个地方：想做，但不知道先从哪一步开始。`,
          conflict:`这不是你执行力差，而是目标太大、动作太虚。一个动作只要不能在今天完成，它就很容易变成压力。`,
          turn:`所以「${{clean}}」最有用的地方，是把一个模糊问题变成三个能落地的小步骤。`,
          proof:`第一步，先把问题说成一句人话；第二步，找到今天能验证的小动作；第三步，做完以后记录一次反馈。你不需要一次解决全部，只要先让事情动起来。`,
          close:`如果今天只允许你先做一步，你会先做哪一步？`
        }},
        {{
          hook:`很多人以为${{themeName}}难，是因为自己懂得不够多，其实更常见的问题是：懂了以后没有形成动作。`,
          scene:`你看完一个观点，觉得有道理；刷到一个案例，也觉得可以学。可第二天回到自己身上，又不知道该怎么用。`,
          conflict:`原因很简单：信息没有经过筛选，经验没有变成流程，行动没有得到反馈。`,
          turn:`所以「${{clean}}」不要再停在结论里，今天先完成一个小动作。`,
          proof:`你可以拿一个真实问题来试，先写下现状，再写下你想要的结果，最后只选一个最小动作去做。只要这个动作能完成，后面就有复盘的基础。`,
          close:`你最近收藏最多、但一直没真正开始的是哪一件事？`
        }},
        {{
          hook:`今天不讲复杂理论，就讲「${{clean}}」到底怎么从一句话变成一个能用的方法。`,
          scene:`很多问题看起来很复杂，其实一开始不需要完整方案，只需要先找到一个能马上试的入口。`,
          conflict:`如果没有入口，你会一直在脑子里想，越想越觉得应该准备充分，最后反而什么都没动。`,
          turn:`所以你要先抓住一个当下：我现在在哪个场景里卡住了，我能先做哪一个动作。`,
          proof:`比如先问自己“我现在是不是卡在这一步”，再告诉自己“别急，先做这个动作”，做完以后再看结果。这样事情就不会一直停在想法里。`,
          close:`你想先把哪个问题拆成一个今天能做的动作？`
        }},
        {{
          hook:`如果你一想到${{themeName}}就觉得复杂，先别急着一次做好，先找到今天最容易开始的那一步。`,
          scene:`真正让人坚持不下去的，往往不是方向错，而是第一步太重。你一开始就要求自己完整、标准、长期，很容易还没开始就累了。`,
          conflict:`但如果你把「${{pain}}」缩小到一个很小的动作，事情就会变得可控。`,
          turn:`所以「${{clean}}」的关键不是马上解决全部，而是先让你从停住的状态里动一下。`,
          proof:`你可以先做一个最小版本：不追求完美，只看今天能不能完成一次。完成一次，下一次就有了参考。`,
          close:`你现在最容易开始的那一步是什么？别想太远，先做这一小步。`
        }},
        {{
          hook:`别再把${{themeName}}做成空泛观点，真正有传播力的是：一句话说中问题，一分钟给到做法。`,
          scene:`很多建议听起来很有气势，越听越虚。因为它一直在说重要、应该、必须，却没有告诉你：从哪里开始。`,
          conflict:`你不是不愿意改变，你是怕自己又听懂了，但生活没有任何变化。`,
          turn:`所以「${{clean}}」要把重点放在“开始”上，不是讲全，而是讲准。`,
          proof:`你可以先给自己一个判断，再找一个具体例子，最后只保留三个动作。动作够具体，你就不用反复猜到底该怎么办。`,
          close:`如果你也想把这个问题变成行动，今天先选一个动作做完。`
        }},
        {{
          hook:`我更建议你把「${{clean}}」当成一次现场沟通，而不是一段标准答案。`,
          scene:`当你已经被「${{pain}}」困住时，你不需要再听一堆正确的话，你需要的是把眼前这一步说清楚。`,
          conflict:`标准答案最大的问题，是它离现实太远。听完好像都对，但你还是不知道今天该怎么接住。`,
          turn:`所以先别追求标准，先把你正在经历的那一下说出来。`,
          proof:`比如不要只说“要提高认知”，而是说“你现在卡住，是因为手里有很多选择，但没有一个判断标准”。这句话一出来，后面的动作才自然。`,
          close:`你现在最需要的不是更多答案，而是一个能马上开始的判断标准。`
        }},
        {{
          hook:`「${{clean}}」这件事，别从完美方案开始，先从一个最容易被忽略的小动作开始。`,
          scene:`很多变化失败，不是因为方向错，而是第一步太重。你一开始就想做完整、做漂亮、做长期，最后反而迟迟没开始。`,
          conflict:`真正可持续的改变，一定先小到你今天就能完成。完成以后，你才有信心继续往下走。`,
          turn:`所以今天把${{themeName}}里的「${{pain}}」缩小，缩小到你能在十分钟里试一次。`,
          proof:`十分钟写一个问题，十分钟做一次尝试，十分钟记录一次结果。只要你开始留下反馈，下一次就不是从零开始。`,
          close:`现在就选一个十分钟能完成的动作，先把它做完。`
        }}
      ];
      const profile = careerMode ? careerProfiles[variantIndex % careerProfiles.length] : generalProfiles[variantIndex % generalProfiles.length];
      const careerMethodLeads = [
        '这件事可以直接落到三个动作里',
        '你下一条内容就按这个顺序来',
        '先别追复杂技巧，就做这三步',
        '把它变成可执行流程，其实只需要三步'
      ];
      const generalMethodLeads = [
        '你现在可以先这样做',
        '这件事先不用做大，先做这三步',
        '今天就从一个小流程开始',
        '如果你想马上动起来，可以按这个顺序'
      ];
      const methodLead = careerMode ? careerMethodLeads[variantIndex % careerMethodLeads.length] : generalMethodLeads[variantIndex % generalMethodLeads.length];
      const methodLine = `${{methodLead}}：${{plan.method[0]}}；${{plan.method[1]}}；${{plan.method[2]}}。`;
      return {{ ...profile, methodLine }};
    }}

    function aiSuperWorkflowPlan(clean, theme, pain, variant=0) {{
      const seed = ideaSeed(`${{clean}}|${{theme}}|${{pain}}|ai-super|${{variant}}`);
      const plans = [
        {{
          angle:'素材入口',
          title:'别再临时找选题，先把素材入口管起来',
          scene:'你刷到热点、同行作品、评论区问题，第一反应都是先收藏，可真正要发的时候，素材散在截图、收藏夹和脑子里，根本拿不出来',
          first:'把所有素材先分进三个盒子：正在被讨论、用户原话、我能给的方法',
          steps:['把抖音热点放进“正在被讨论”','把评论和私信放进“用户原话”','把你的经验放进“我能给的方法”'],
          proof:'比如你今天看到一个热点，不要马上写标题，先问自己：这个热点里用户正在担心什么，我能不能给他一个更省力的做法',
          closer:'今天先别急着写新稿，先把最近 20 条素材按这三个盒子分好，你会立刻发现选题不再是凭感觉硬憋出来的',
          cover:['先管素材','别靠灵感','三盒分类']
        }},
        {{
          angle:'选题库',
          title:'你的选题库不能只存标题，要存用户下一步',
          scene:'很多人做了一个选题表，里面全是标题，可一到写文案就卡住，因为标题后面没有场景、痛点和行动',
          first:'每个选题都要补齐四列：谁在焦虑、卡在哪一步、我给什么动作、看完怎么互动',
          steps:['写具体人群，不写泛泛的大众','写他当下卡住的真实动作','写你能给他的一个小步骤'],
          proof:'比如“AI 内容管理”这个方向，不要只写“怎么做内容”，要写“每天临时想选题的人，先用一张表把热点、痛点和旧作品连起来”',
          closer:'你把这四列补齐以后，AI 才不是替你乱写，而是在你的规则里帮你把半成品变成成品',
          cover:['选题别空','补齐四列','直接能写']
        }},
        {{
          angle:'脚本工厂',
          title:'口播稿不要从空白页开始，要从固定工位开始',
          scene:'你打开文档准备写稿，脑子里一片空白，最后不是写得很散，就是又回到老一套表达',
          first:'把口播工位固定成四步：一句判断、一个场景、三个动作、一个问题',
          steps:['直接给判断，不铺垫','放一个用户正在经历的画面','给三个马上能做的动作'],
          proof:'你要写“发布节奏不稳定”，就别先讲理论，先说：你不是没素材，是没有把素材排进明天、后天和下周的内容位置里',
          closer:'以后每次写稿都先过这四步，AI 只负责扩写和润色，主线必须由你的工作流决定',
          cover:['别空白写','四步成稿','马上能念']
        }},
        {{
          angle:'封面标题',
          title:'封面和标题不能分开想，要一起过同一个承诺',
          scene:'有些作品文案很好，但封面像情绪口号，标题像随手一写，用户点开前根本不知道能得到什么',
          first:'先写一句内容承诺，再把它拆成封面三行字和标题关键词',
          steps:['封面第一行写用户正在卡住的动作','第二行写你给的结果','第三行写今天照做的入口'],
          proof:'比如“内容越做越乱”，封面可以写“内容太乱了 / 先建工作台 / 今天就能分好”，标题再承接具体做法',
          closer:'这样做的好处是，用户没点开之前就知道你要解决什么，点开以后也不会觉得标题和正文断开',
          cover:['封面先承诺','标题接结果','别各写各的']
        }},
        {{
          angle:'复盘表',
          title:'复盘不是看播放量高不高，是找下一条怎么改',
          scene:'很多人发完就盯着播放量，数据一低就焦虑，数据一高也不知道为什么高，下一条还是从零开始',
          first:'每条作品发完只看四个问题：开头有没有停住人，中段有没有推进，评论有没有暴露痛点，下一条接什么',
          steps:['把播放量当成入口信号，不当成情绪判决','把评论区原话复制进痛点库','把表现好的句子存进标题和封面库'],
          proof:'如果一条作品评论里反复出现“我就是不知道怎么开始”，下一条就不要再讲大方向，直接做“第一步怎么做”',
          closer:'你这样复盘 7 天，工作台里就会长出自己的内容地图，而不是每天被数据牵着情绪走',
          cover:['别只看播放','复盘找下一条','数据变选题']
        }},
        {{
          angle:'发布日历',
          title:'未来 7 天不要随便发，要让每一条接住上一条',
          scene:'你今天发热点，明天发感悟，后天发工具，用户看了三天还是不知道你到底在帮他完成什么',
          first:'把 7 天内容排成一条线：问题、误区、方法、案例、工具、清单、复盘',
          steps:['第一天只讲用户最痛的场景','第二天拆一个常见误区','第三天给一个能照做的方法'],
          proof:'比如你做 AI 内容管理，第一天讲素材太乱，第二天讲为什么收藏没用，第三天教三盒分类法，后面再接脚本、封面和复盘',
          closer:'这样用户不是随机刷到你，而是连续看见你在帮他把一个问题往前推',
          cover:['7天别乱发','一条线推进','越看越清楚']
        }},
        {{
          angle:'AI分工',
          title:'AI 不是替你想方向，是替你处理重复工序',
          scene:'你把所有问题都丢给 AI，让它直接给选题、标题、文案、封面，结果看起来完整，但一点都不像你的账号',
          first:'先把 AI 分成三个岗位：资料整理员、口播助理、复盘记录员',
          steps:['资料整理员只负责把素材分类','口播助理只负责把你的观点扩成口语稿','复盘记录员只负责从数据里提下一条选题'],
          proof:'你给 AI 的任务越具体，它越像团队；你给它一个大而空的问题，它就只能给你一堆看起来正确的套话',
          closer:'从今天开始，别再问 AI “帮我写一个爆款”，改成“把这 5 条素材整理成 3 个可发布选题”',
          cover:['AI先分工','别问大问题','一岗一任务']
        }},
        {{
          angle:'旧作品再生产',
          title:'你的旧作品不是过去式，是下一轮选题原料',
          scene:'很多人一条作品发完就放过去了，其实真正值钱的东西在旧作品里：哪句话有人停留，哪类评论最多，哪个封面没人点',
          first:'把旧作品拆成三类：能复刻、要重写、该淘汰',
          steps:['能复刻的作品保留开头和选题方向','要重写的作品换标题、封面和前 3 秒','该淘汰的作品只留下用户问题'],
          proof:'如果旧作品观点不错但播放低，不要马上否定主题，先检查是不是封面没有说清结果，或者开头太慢',
          closer:'旧作品复盘一次，往往能生出三条新内容，这比每天盲目找热点稳定得多',
          cover:['旧作品别扔','一条变三条','复盘再生产']
        }}
      ];
      const base = plans[variant % plans.length];
      return {{ ...base, seed, badge: pickSeed(['采集台','选题库','脚本工厂','封面库','复盘表','发布日历','AI分工','旧作品库'], seed, 0) }};
    }}

    function aiSuperTopicPackage(idea, rawTopic, baseClean, suffixLabel, theme, pain) {{
      const clean = suffixLabel ? `${{baseClean}}（${{suffixLabel}}）` : baseClean;
      const themeName = theme.split('/')[0] || 'AI超级个体内容管理';
      const variant = Number(idea.variant || 0);
      const hot = idea.hot || selectedIdeaHot();
      const hotTitle = hot?.title || '';
      const hotSummary = hotSummaryLine(hot);
      const hotMeta = hotMetaLine(hot);
      const viralCase = currentViralArchive();
      const plan = aiSuperWorkflowPlan(clean, theme, pain, variant);
      const memory = idea.memory || state.dedaoBrain?.current || null;
      const formula = {{
        id:'ai-workbench-direct',
        name:'AI工作台口播开场',
        pattern:'真实卡点 + 当前场景 + 立刻能做的工作流'
      }};
      const openings = [
        `如果你想做${{themeName}}，先别再问今天发什么。真正拖住你的，是${{pain}}。`,
        `我越来越确定，一人做内容最怕的不是没工具，而是${{pain}}。`,
        `你以为做${{themeName}}靠的是灵感，其实靠的是一套每天能跑起来的流程。`,
        `今天这段话，送给所有素材很多、工具很多，但发内容还是很乱的人。`
      ];
      const aiHotSource = hot?.source === '手动输入热点' ? '你输入的抖音热点' : '今天抖音热榜';
      const aiHotSummary = hotSummary && !hotSummary.includes('手动输入') ? `可以顺手带一句：${{hotSummary}}。` : '';
      const hotLine = hotTitle
        ? `拿${{aiHotSource}}「${{hotTitle}}」举例。${{hotMeta ? `它现在是${{hotMeta}}。` : ''}}${{aiHotSummary}}你别急着把它塞进标题，先看它背后用户正在关心什么，再决定它能不能进入你的选题库。`
        : '';
      const caseLine = viralCase
        ? `很多爆款表面看是标题厉害，其实背后都有同一个东西：它知道用户此刻最卡在哪里，也知道下一句该把人带到哪里。`
        : '';
      const brainLine = dedaoBrainLine(memory, theme, pain, clean, true);
      const steps = plan.steps.map(step => String(step).replace(/^第[一二三四五六七八九十]+[，、]/, '').trim());
      const script = [
        openings[variant % openings.length],
        hotLine,
        caseLine,
        brainLine,
        `真正拉开差距的地方，是「${{plan.angle}}」。${{plan.scene}}。`,
        `${{plan.first}}。这不是一个表格动作，而是一种内容生产方式：热点不再只是热点，评论不再只是评论，旧作品也不再只是过去发过的一条视频。它们会变成下一条口播的开头、场景、观点和结尾。`,
        `一个能长期跑起来的内容系统，里面一定有三个东西：${{steps[0]}}，${{steps[1]}}，${{steps[2]}}。少了其中任何一个，文案都会变成临时发挥，看起来很努力，听起来却没有连续性。`,
        `${{plan.proof}}。这就是 AI 内容管理真正有价值的地方：不是让 AI 替你说漂亮话，而是让每一个素材都能找到自己的位置，让每一个观点都能变成可发布的口播。`,
        `你会发现，内容一旦进入工作台，创作就不再是“今天我有没有灵感”。它会变成一条很清楚的链路：用户正在讨论什么，你能补充什么判断，这个判断能不能变成一句好懂的话，发出去以后又能沉淀出什么新问题。`,
        `所以 AI 超级个体不是工具用得多，而是一个人也能拥有一套内容生产系统。系统越清楚，文案越不像套话；复盘越稳定，下一条选题越不需要从零开始。`,
        `这也是 AI 超级个体和普通内容创作者最大的区别：别人是在每天临时找感觉，你是在让每一次采集、每一次生成、每一次发布，都回到同一套系统里继续生长。`,
        `当这套内容系统跑起来，选题会越来越准，文案会越来越像你，封面和标题也会越来越知道该承诺什么。到最后，你不是被热点推着走，而是能把热点、素材和旧作品，都变成你的下一条内容。`,
        `如果你也想把内容从混乱变成系统，评论区告诉我：你现在最卡的是素材、选题、文案，还是复盘？`
      ].filter(Boolean).join('\\n\\n');
      const titles = [
        clean,
        plan.title,
        hotTitle ? `别硬蹭${{hotTitle}}，先放进内容工作台` : `${{themeName}}先搭${{plan.badge}}`,
        `${{pain.slice(0, 18)}}，先做${{plan.angle}}`
      ];
      const cover = [
        safeClip(plan.cover[0], 10),
        safeClip(plan.cover[1], 10),
        safeClip(plan.cover[2], 10)
      ];
      return {{ title: clean, titles: titles.slice(0,4), cover, script, theme, pain, formula, viralCase, hot, memory, aiMode:true, angle:plan.angle, domain:'ai_super_workbench' }};
    }}

    function topicPackage(topicOrIdea, theme, pain) {{
      const idea = typeof topicOrIdea === 'object' ? topicOrIdea : {{ topic:topicOrIdea, theme, pain, variant:0 }};
      const rawTopic = String(idea.topic || '');
      const baseClean = cleanTopic(rawTopic);
      const suffixLabel = rawTopic.includes('｜') ? rawTopic.split('｜').slice(1).join('｜').trim() : '';
      const clean = suffixLabel ? `${{baseClean}}（${{suffixLabel}}）` : baseClean;
      theme = idea.theme || theme || selectedIdeaTheme();
      pain = idea.pain || pain || selectedIdeaPain();
      if (isAISuperContentTheme(theme, pain)) {{
        return aiSuperTopicPackage(idea, rawTopic, baseClean, suffixLabel, theme, pain);
      }}
      const themeName = theme.split('/')[0] || theme;
      const painCore = pain.replace('的人', '').replace('导致', '').replace('却', '，却');
      const formula = hookById($('#ideaHook')?.value || currentHookId());
      const viralCase = currentViralArchive();
      const careerMode = isCareerTheme(theme, pain);
      const hot = idea.hot || selectedIdeaHot();
      const hotTitle = hot?.title || '';
      const hotSummary = hotSummaryLine(hot);
      const hotMeta = hotMetaLine(hot);
      const variant = Number(idea.variant || 0);
      const plan = ideaVariantPlan(`${{clean}} ${{hotTitle}}`, theme, pain, variant);
      const voice = oralVariantProfile(clean, theme, pain, plan, variant, careerMode);
      const memory = idea.memory || state.dedaoBrain?.current || null;
      const brainLine = dedaoBrainLine(memory, theme, pain, clean, careerMode);
      const baseOpening = hookLine(formula, clean, theme, pain);
      const openingLead = /[。！？.!?]$/.test(baseOpening.trim()) ? baseOpening.trim() : `${{baseOpening.trim()}}。`;
      const opening = voice.hook || openingLead;
      const hotMetaText = hotMeta ? `它现在是${{hotMeta}}。` : '';
      const hotSummaryText = hotSummary && !hotSummary.includes('手动输入') ? `可以顺手带一句：${{hotSummary}}。` : '';
      const evidenceLine = careerMode
        ? `这里一定要补一个具体证据：${{plan.proof}}。不要只告诉别人你有方法，要让他看见这个方法放进真实场景以后，能解决哪一个具体卡点。`
        : `这里一定要补一个具体例子：${{plan.proof}}。例子一出来，你就不用猜这句话到底怎么用，也更容易把它放回自己的生活里。`;
      const actionLine = careerMode
        ? `你不用把所有能力一次讲完，先把眼前这个问题讲透。别人能听懂一个具体结果，才会愿意继续相信你后面的内容。`
        : `你不用等状态完全准备好，也不用一次做得很漂亮。今天先完成一个小动作，有了第一次反馈，下一步才会变得更清楚。`;
      const hotLineOptions = careerMode
        ? [
            `拿今天抖音上的「${{hotTitle}}」来说。${{hotMetaText}}它能被讨论起来，说明大家会为一个具体问题停下来；你的${{themeName}}也一样，先让用户听见自己的卡点。`,
            `「${{hotTitle}}」这个热点可以借一个入口。${{hotSummaryText}}不要硬蹭热度，要把它转成用户正在经历的一个真实问题。`,
            `热点「${{hotTitle}}」真正能用的地方，不是标题里的热词，而是它让你看到：用户会为什么事情立刻产生判断。`,
            `今天如果要借「${{hotTitle}}」，我不会先改标题，我会先问：它和${{themeName}}里的哪一个信任问题有关。`
          ]
        : [
            `拿今天抖音上的「${{hotTitle}}」举个例子。${{hotMetaText}}热点本身只是入口，真正能用的是它背后那个具体选择。`,
            `「${{hotTitle}}」能被讨论起来，说明大家对一个现实问题有反应。放到${{themeName}}里看，你要抓的不是热闹，而是它对应的真实卡点。`,
            `今天这个热点「${{hotTitle}}」不要直接照搬。先把它拆成一句话：它让人在哪个瞬间停下来，又让人想解决什么。`,
            `如果把「${{hotTitle}}」放进今天这件事里，重点不是追热度，而是用它把「${{pain}}」讲得更具体。`
          ];
      const hotBridgeOptions = careerMode
        ? [
            `所以这一条要回到「${{clean}}」：让用户先听懂你解决什么，再相信你值得继续看。`,
            `你的表达不能只停在热点表面，要顺着它把用户的疑问、你的判断和下一步动作连起来。`,
            `只要能把热点变成一个具体场景，内容就不会飘，用户也更容易知道为什么要关注你。`,
            `热度只是开门，真正留下人的，是你后面给出的清楚路径。`
          ]
        : [
            `所以今天不是复述热点，而是借这个入口，把「${{clean}}」讲到一个能马上照做的层面。`,
            `你要听完以后知道：这件事跟我有关，而且我现在可以先做一个动作。`,
            `热点负责让人停一下，后面要回到具体场景和具体行动里。`,
            `一旦它和「${{pain}}」连起来，今天这段话就不再是泛泛而谈，而是能落到现实里。`
          ];
      const hotLine = hotTitle ? hotLineOptions[variant % hotLineOptions.length] : '';
      const hotBridge = hotTitle ? hotBridgeOptions[variant % hotBridgeOptions.length] : '';
      const titles = careerMode
        ? [
            clean,
            `${{clean}}：先从${{plan.angle}}讲起`,
            `普通人做${{themeName}}，先把「${{plan.method[0]}}」讲清楚`,
            `${{themeName}}做不起来，可能卡在${{plan.mistake}}`
          ]
        : [
            clean,
            `${{clean}}：先从${{plan.angle}}开始落地`,
            `${{painCore}}，先别急着下结论`,
            `${{themeName}}里最该先做清楚的，是这一步`
          ];
      if (viralCase) {{
        titles.splice(1, 0, `${{clean}}｜照着爆款结构讲透`);
      }}
      const cover = viralCase?.cover?.length
        ? [safeClip(clean, 10), safeClip(viralCase.cover[1] || plan.cover[1], 10), safeClip(plan.angle, 10)]
        : careerMode
        ? [safeClip(plan.cover[0], 10), safeClip(plan.cover[1], 10), safeClip(themeName, 10)]
        : theme.includes('追星')
        ? [safeClip(clean, 10), safeClip(plan.angle, 10), '追自己']
        : theme.includes('边界') || theme.includes('讨好')
          ? [safeClip(clean, 10), safeClip(plan.angle, 10), '边界感']
          : theme.includes('情绪')
            ? [safeClip(clean, 10), safeClip(plan.angle, 10), '稳定感']
            : [safeClip(clean, 10), safeClip(plan.cover[1], 10), safeClip(plan.angle, 10)];
      const viralLine = viralCase
        ? `${{opening}} 真正能借鉴爆款的，不是照搬句子，而是把「${{clean}}」讲到当前用户的真实处境里。`
        : opening;
      const script = careerMode
        ? [
            viralLine,
            hotLine,
            hotBridge,
            brainLine,
            voice.scene,
            voice.conflict,
            voice.turn,
            voice.methodLine,
            evidenceLine,
            voice.proof,
            actionLine,
            hotTitle ? `「${{hotTitle}}」只是让人停下来的入口，真正让人留下来的，是你把「${{clean}}」讲得具体、讲得有用、讲得他能马上用上。` : `入口只是入口，真正让人留下来的，是你讲得具体、讲得有用、讲得他能马上用上。`,
            voice.close
          ].filter(Boolean).join('\\n\\n')
        : [
            viralLine,
            hotLine,
            hotBridge,
            brainLine,
            voice.scene,
            voice.conflict,
            voice.turn,
            voice.methodLine,
            evidenceLine,
            voice.proof,
            actionLine,
            `最后我想问你一句：${{voice.close}}`
          ].filter(Boolean).join('\\n\\n');
      return {{ title: clean, titles: titles.slice(0,4), cover, script, theme, pain, formula, viralCase, hot, memory }};
    }}

    async function renderIdeaPackage(index) {{
      const item = state.currentIdeas?.[index];
      if (!item) return;
      $$('.idea-card').forEach((card, i)=>card.classList.toggle('active', i === index));
      $('#ideaPackage').innerHTML = '<div class="result muted">正在读取得到大脑记忆、成果和知识库，并生成标题 / 文字稿 / 封面...</div>';
      const itemHot = item.hot || selectedIdeaHot();
      item.memory = await recallDedaoBrain(
        '确定选题后的文稿生成',
        `${{cleanTopic(item.topic)}} ${{item.theme}} ${{item.pain}} ${{itemHot?.title || ''}} ${{item.angle || ''}}`,
        8
      );
      const pack = topicPackage(item);
      const packHotMeta = hotMetaLine(pack.hot);
      const packHotSummary = hotSummaryLine(pack.hot);
      const teleprompterText = String(pack.script || '').trim();
      const materialText = [
        '【选题】' + pack.title,
        '',
        pack.hot ? `【抖音新闻热点】${{pack.hot.title}}（${{pack.hot.source || '抖音热搜'}}）` : '',
        pack.hot && packHotMeta ? `热搜数据：${{packHotMeta}}` : '',
        pack.hot && packHotSummary ? `热点信息：${{packHotSummary}}` : '',
        pack.hot ? '' : '',
        '【标题】',
        ...pack.titles.map((t,i)=>`${{i+1}}. ${{t}}`),
        '',
        '【封面三行字】',
        pack.cover.join(' / '),
        '',
        '【文字稿】',
        teleprompterText
      ].join('\\n');
      $('#ideaPackage').dataset.copy = teleprompterText;
      $('#ideaPackage').dataset.script = teleprompterText;
      $('#ideaPackage').dataset.title = pack.title;
      $('#ideaPackage').dataset.materials = materialText;
      $('#ideaPackage').innerHTML = `
        <section class="teleprompter-pack">
          <div class="teleprompter-head">
            <div>
              <div class="teleprompter-label">提词器口播正文</div>
              <div class="teleprompter-title">${{esc(pack.title)}}</div>
              <div class="muted">下面只保留可直接口播的正文，不包含来源、提示、分析或核对信息。</div>
            </div>
            <button class="primary teleprompter-copy" onclick="copyIdeaScript()">复制口播文稿</button>
          </div>
          <div class="teleprompter-box">${{esc(teleprompterText)}}</div>
        </section>
        <section class="reference-pack">
          <div class="reference-head">
            <b>生成依据与核对来源</b>
            <span class="muted">这些内容只用于检查和继续优化，不进入提词器正文。</span>
          </div>
          <div class="reference-grid">
            <div class="result">
              <b>当前选题：</b>${{esc(pack.title)}}<br>
              <span class="chip theme-chip">${{esc(pack.theme)}}</span>
              <span class="chip">${{esc(pack.pain)}}</span>
            </div>
            <div class="result"><b>标题方案：</b><br>${{pack.titles.map((t,i)=>`${{i+1}}. ${{esc(t)}}`).join('<br>')}}</div>
            <div class="cover">${{esc(pack.cover.join(' / '))}}</div>
            <div class="result"><b>自动套用钩子：</b>${{esc(pack.formula.name)}}<br><span class="muted">${{esc(pack.formula.pattern)}}</span></div>
            ${{pack.hot ? `<div class="result"><b>结合抖音热点：</b>${{esc(pack.hot.title)}}<br><span class="muted">${{esc(pack.hot.source || '抖音热搜')}}${{packHotMeta ? ' · ' + esc(packHotMeta) : ''}}</span>${{packHotSummary ? `<div class="muted" style="margin-top:6px">${{esc(packHotSummary)}}</div>` : ''}}</div>` : ''}}
            ${{pack.viralCase ? `<div class="result"><b>套用爆款案例：</b>${{esc(pack.viralCase.title)}}<br><span class="muted">${{esc(pack.viralCase.source)}} · 爆款潜力 ${{pack.viralCase.avg}}</span></div>` : ''}}
            ${{renderDedaoBrainReference('确定选题后的文稿生成', pack.memory, 4)}}
            ${{renderDanaoReference('选题生成器', 3)}}
          </div>
          <div class="actions">
            <button class="secondary" onclick="copyIdeaMaterials()">复制标题封面素材</button>
            <button class="secondary" onclick="sendIdeaToOptimizer()">拿去继续优化</button>
          </div>
        </section>`;
    }}
    window.renderIdeaPackage = renderIdeaPackage;

    window.copyIdeaScript = async function() {{
      await navigator.clipboard.writeText($('#ideaPackage').dataset.script || $('#ideaPackage').dataset.copy || '');
    }}

    window.copyIdeaPackage = window.copyIdeaScript;

    window.copyIdeaMaterials = async function() {{
      await navigator.clipboard.writeText($('#ideaPackage').dataset.materials || '');
    }}

    window.sendIdeaToOptimizer = function() {{
      const box = $('#ideaPackage');
      const title = box.dataset.title || '';
      const script = box.dataset.script || box.dataset.copy || '';
      $('#draftTitle').value = title;
      $('#draftText').value = script;
      const theme = selectedIdeaTheme();
      if ([...$('#draftTheme').options].some(option => option.value === theme || option.textContent === theme)) {{
        $('#draftTheme').value = theme;
      }} else {{
        $('#draftTheme').value = '';
      }}
      switchView('optimizer');
      analyzeDraft();
    }}

    async function generateIdeas() {{
      const theme = selectedIdeaTheme();
      const pain = selectedIdeaPain();
      const count = Number($('#ideaCount').value);
      syncHookSelects($('#ideaHook').value);
      const viralCase = currentViralArchive();
      const aiSuperMode = isAISuperContentTheme(theme, pain);
      const careerMode = !aiSuperMode && isCareerTheme(theme, pain);
      const hot = selectedIdeaHot();
      const memory = await recallDedaoBrain('选题生成器', `${{theme}} ${{pain}} ${{hot?.title || ''}}`, 8);
      const templates = aiSuperMode ? aiSuperTopicTemplates : careerMode ? careerTopicTemplates : topicTemplates;
      const rows = [];
      for (let i=0;i<count;i++) {{
        const brainBase = dedaoTopicBase(theme, pain, memory, i);
        const base = brainBase || templates[i % templates.length].replaceAll('{{pain}}', pain).replaceAll('{{theme}}', theme.split('/')[0]);
        const suffixPool = viralCase
          ? ['｜爆款同构','｜外部案例复刻','｜高互动结构','｜封面反差','｜评论区入口']
          : aiSuperMode
            ? ['｜采集台','｜选题库','｜脚本工厂','｜封面标题','｜复盘表','｜发布日历','｜AI分工','｜旧作品库']
          : careerMode
            ? ['｜个人品牌','｜信任资产','｜内容定位','｜AI超级个体','｜成交路径']
            : ['｜热点切入','｜实操方法','｜案例拆解','｜避坑清单','｜行动方案'];
        const suffix = suffixPool[i % suffixPool.length];
        const topic = `${{i+1}}. ${{base}}${{suffix}}`;
        const plan = aiSuperMode ? aiSuperWorkflowPlan(cleanTopic(topic), theme, pain, i) : ideaVariantPlan(`${{cleanTopic(topic)}} ${{hot?.title || ''}}`, theme, pain, i);
        rows.push({{ topic, theme, pain, hot, memory, variant:i, angle:plan.angle, domain:aiSuperMode ? 'ai_super_workbench' : plan.domain }});
      }}
      state.currentIdeas = rows;
      $('#ideasResult').innerHTML = rows.map((x,i)=>`
        <div class="result idea-card">
          <div><strong>${{esc(x.topic)}}</strong><div class="idea-meta"><span class="chip theme-chip">${{esc(x.theme.split('/')[0])}}</span><span class="chip">${{esc(x.angle || '独立角度')}}</span><span class="chip">${{esc(x.pain.slice(0,12))}}</span></div></div>
          <button class="secondary" onclick="renderIdeaPackage(${{i}})">确定并生成</button>
        </div>`).join('');
      $('#ideasResult').dataset.copy = rows.map(x=>x.topic).join('\\n');
      renderIdeaPackage(0);
    }}
    let generateIdeasTimer = null;
    function scheduleGenerateIdeas() {{
      clearTimeout(generateIdeasTimer);
      generateIdeasTimer = setTimeout(()=>generateIdeas(), 520);
    }}
    window.makeSiblingIdeas = function(idx) {{
      const v = state.videos.find(x=>x.idx===idx);
      $('#ideaTheme').value = v.theme;
      $('#ideaThemeCustom').value = '';
      $('#ideaPainCustom').value = '';
      switchView('ideas');
      generateIdeas();
    }}

    function countBy(list, fn) {{
      return list.reduce((acc, item)=>{{ const key = fn(item) || '未分类'; acc[key] = (acc[key] || 0) + 1; return acc; }}, {{}});
    }}

    function topEntries(obj, limit=3) {{
      return Object.entries(obj).sort((a,b)=>b[1]-a[1]).slice(0,limit);
    }}

    function weakDimension(videos) {{
      const dims = ['hook','structure','emotion','cover'];
      const avg = Object.fromEntries(dims.map(k=>[k, Math.round(videos.reduce((n,v)=>n+(v.scores?.[k]||0),0)/Math.max(1,videos.length))]));
      const label = {{ hook:'开场钩子', structure:'内容结构', emotion:'情绪共鸣', cover:'封面点击' }};
      const key = dims.sort((a,b)=>avg[a]-avg[b])[0];
      return {{ key, label:label[key], avg:avg[key], all:avg }};
    }}

    function titleSeed(theme, pain, mode, best) {{
      const t = (theme || '综合清醒文案').split('/')[0];
      const bestTitle = best?.title || '';
      const pools = {{
        pain: [`你以为你缺的是方法，其实是${{pain}}`, `越想改变，越容易卡在${{pain}}`, `别再用努力掩盖${{pain}}`],
        trust: [`${{t}}真正有效的 3 个动作`, `我把${{t}}拆成了普通人能做的步骤`, `别只听金句，${{t}}要这样落地`],
        story: [`一个真实场景，讲透${{pain}}`, `为什么你明明懂了，还是做不到`, `从${{bestTitle.slice(0,12) || t}}延伸出的一条新内容`],
        series: [`${{t}}系列第 1 条：先改掉这个误区`, `围绕${{pain}}，连续做 3 条更容易涨粉`, `把爆款主题做成栏目，而不是单条`],
      }};
      const list = pools[mode] || pools.pain;
      return list[Math.floor(Math.random()*list.length)];
    }}

    function renderPlanner() {{
      const videos = [...state.videos];
      if (!videos.length) {{
        $('#plannerSummary').innerHTML = '<div class="result">暂无作品数据。先到“抖音数据抓取”同步你的账号作品。</div>';
        $('#calendar').innerHTML = '';
        $('#trustActions').innerHTML = '';
        return;
      }}
      const themes = topEntries(countBy(videos, v=>v.theme), 4);
      const avg = Math.round(videos.reduce((n,v)=>n+(v.scores?.score||0),0)/videos.length);
      const best = [...videos].sort((a,b)=>(b.scores?.score||0)-(a.scores?.score||0))[0];
      const weak = weakDimension(videos);
      const low = videos.filter(v=>(v.scores?.score||0)<68).length;
      const primaryTheme = themes[0]?.[0] || state.pillars[0];
      const secondaryTheme = themes[1]?.[0] || state.pillars[1] || primaryTheme;
      const painPool = state.painPoints || [];
      const primaryPain = painPool.find(p=>primaryTheme.includes('追星') ? p.includes('追星') : p) || painPool[0] || '用户当下最强痛点';

      $('#plannerSummary').innerHTML = [
        `<div class="result"><b>账号主线：</b>${{esc(primaryTheme)}}<br><span class="muted">当前作品最多的方向是「${{esc(themes.map(x=>`${{x[0]}} ${{x[1]}}条`).join(' / '))}}」。未来 7 天要围绕主线做连续记忆点。</span></div>`,
        `<div class="result"><b>优先补短板：</b>${{esc(weak.label)}} ${{weak.avg}}分<br><span class="muted">本周每条内容都要补这个短板：钩子不够就先说结果，结构弱就固定“痛点-误区-真相-动作”。</span></div>`,
        `<div class="result"><b>涨粉机会：</b>平均潜力 ${{avg}}分，待优化 ${{low}}条<br><span class="muted">最强样本「${{esc(best.title.slice(0,28))}}」适合拆成连续栏目，承接关注理由。</span></div>`
      ].join('') + renderDanaoReference('发布规划', 3);

      const plan = [
        {{ day:'周一', type:'强痛点拉新', theme:primaryTheme, mode:'pain', goal:'拉新：用一句扎心判断让陌生人停住。', action:'开头 3 秒直接点名用户处境，不讲背景；结尾问“你中了哪一条？”' }},
        {{ day:'周二', type:'方法论建立信任', theme:primaryTheme, mode:'trust', goal:'信任：把观点拆成 3 个可执行动作。', action:'中段必须出现“第一步/第二步/第三步”，让用户感觉你不是只会讲情绪。' }},
        {{ day:'周三', type:'真实场景共鸣', theme:secondaryTheme, mode:'story', goal:'共鸣：用一个生活场景证明你懂她。', action:'开头先讲场景，再给判断；封面写具体人群，不写抽象概念。' }},
        {{ day:'周四', type:'系列栏目延伸', theme:primaryTheme, mode:'series', goal:'记忆点：把高分主题做成固定栏目。', action:'标题加“第1条/第2条”或固定栏目名，形成追更理由。' }},
        {{ day:'周五', type:'评论区互动', theme:primaryTheme, mode:'pain', goal:'互动：让用户留下自己的问题。', action:'结尾只问一个问题；发出后 30 分钟内高频回复，并挑 1 条评论做次日选题。' }},
        {{ day:'周六', type:'信任资产沉淀', theme:secondaryTheme, mode:'trust', goal:'转粉：把你的方法论和人设说清楚。', action:'做一条“我为什么做这个账号/我能帮你解决什么”的内容，置顶或加入合集。' }},
        {{ day:'周日', type:'复盘与下周预热', theme:primaryTheme, mode:'story', goal:'复看：总结一周主题，预告下周系列。', action:'发布“这周最扎心的 3 个真相”，评论区收集下周想看的问题。' }},
      ].map((x,i)=>{{
        const title = titleSeed(x.theme, primaryPain, x.mode, best);
        const cover = x.mode === 'trust'
          ? ['别只听懂', '照着做才变好', x.theme.split('/')[0]]
          : x.mode === 'series'
            ? ['这个系列', '专治反复内耗', x.theme.split('/')[0]]
            : ['你不是不行', '是卡在这里', primaryPain.slice(0,8)];
        return {{...x, title, cover}};
      }});

      $('#calendar').innerHTML = plan.map(x=>`
        <div class="panel day plan-card">
          <strong>${{esc(x.day)}}</strong>
          <p class="muted">${{esc(x.type)}} · ${{esc(x.theme)}}</p>
          <h3>${{esc(x.title)}}</h3>
          <div class="day-cover">${{esc(x.cover.join(' / '))}}</div>
          <div class="day-goal">${{esc(x.goal)}}</div>
          <ul>
            <li>${{esc(x.action)}}</li>
            <li>文案结构：痛点一句话 -> 误区翻转 -> 具体动作 -> 评论区问题。</li>
            <li>发布后：30 分钟内回复评论，记录高频问题进选题库。</li>
          </ul>
        </div>`).join('');

      const trustCards = [
        {{
          title:'涨粉动作：把单条爆点做成系列',
          items:['从最高分作品里提炼一个固定栏目名，每周至少连续 3 条。','每条结尾统一一句关注理由：关注我，下一条继续拆“怎么做”。','主页置顶 1 条“你是谁、你帮谁、解决什么问题”。']
        }},
        {{
          title:'信任感动作：从金句升级到方法',
          items:['每条至少给一个能当天执行的动作，避免只让用户“被说中”。','每 3 条情绪共鸣内容，搭配 1 条清单/步骤/案例拆解。','把评论区真实问题改成视频标题，用户会感觉你在现场解决问题。']
        }},
        {{
          title:'封面与标题动作：固定识别资产',
          items:['封面三行字固定：痛点人群 + 反常识判断 + 栏目标签。','标题少用空泛词，多用“你/不是/其实/为什么/别再”。','低分作品先改封面和前 3 秒，不急着推翻整条文案。']
        }},
        {{
          title:'运营动作：让粉丝留下来',
          items:['每天固定回复 20 条评论，优先回复“我也是/怎么办/怎么改”。','把高频问题整理成“下周选题池”，周日做一次预告。','建立合集：新粉进主页后能按主题连续看，信任更快形成。']
        }}
      ];
      $('#trustActions').innerHTML = trustCards.map(card=>`
        <div class="panel trust-card">
          <div class="module-label">growth action</div>
          <h2>${{esc(card.title)}}</h2>
          <ul>${{card.items.map(item=>`<li>${{esc(item)}}</li>`).join('')}}</ul>
        </div>`).join('');
    }}

    function switchView(id) {{
      $$('.view').forEach(v=>v.classList.toggle('active', v.id===id));
      $$('nav button').forEach(b=>b.classList.toggle('active', b.dataset.view===id));
      document.body.dataset.view = id;
    }}

    function renderRefreshStatus(data) {{
      const status = $('#refreshStatus');
      const homeStatus = $('#homeRefreshStatus');
      const log = $('#refreshLog');
      if (!data) return;
      const okText = data.ok === true ? '完成' : data.ok === false ? '失败' : data.running ? '进行中' : '待命';
      const sourceLine = data.sourceUrl ? `<br><span class="muted">来源：${{esc(data.sourceUrl)}}</span>` : '';
      const html = `<b>状态：</b>${{esc(okText)}}　<b>步骤：</b>${{esc(data.step || '-')}}<br><span class="muted">${{esc(data.message || '')}}</span>${{sourceLine}}`;
      if (status) status.innerHTML = html;
      if (homeStatus) homeStatus.innerHTML = html;
      if (log && data.logs?.length) {{
        log.classList.remove('hidden');
        log.textContent = data.logs.join('\\n');
        log.scrollTop = log.scrollHeight;
      }}
      if (data.ok === true && state.refreshStarted) {{
        state.refreshStarted = false;
        setTimeout(()=>location.reload(), 1200);
      }}
    }}

    async function pollRefreshStatus() {{
      try {{
        const res = await fetch(apiUrl('/api/refresh-status?t=' + Date.now()), apiOptions({{ cache:'no-store' }}));
        const data = await res.json();
        renderRefreshStatus(data);
        if (data.running) setTimeout(pollRefreshStatus, 2500);
      }} catch (err) {{
        const message = '<b>状态：</b>无法连接本地刷新服务，请确认正在使用 http://127.0.0.1:8787/ 打开工作台。';
        if ($('#refreshStatus')) $('#refreshStatus').innerHTML = message;
        if ($('#homeRefreshStatus')) $('#homeRefreshStatus').innerHTML = message;
      }}
    }}

    function setRefreshButtonsDisabled(disabled) {{
      ['refreshDouyin','homeRefreshDouyin','refreshProfile','homeRefreshProfile'].forEach(id => {{
        const el = $('#' + id);
        if (el) el.disabled = disabled;
      }});
    }}

    async function startDouyinRefresh() {{
      state.refreshStarted = true;
      setRefreshButtonsDisabled(true);
      const starting = '<b>状态：</b>正在启动自动抓取...';
      if ($('#refreshStatus')) $('#refreshStatus').innerHTML = starting;
      if ($('#homeRefreshStatus')) $('#homeRefreshStatus').innerHTML = starting;
      try {{
        const res = await fetch(apiUrl('/api/refresh'), apiOptions({{ method:'POST', cache:'no-store' }}));
        renderRefreshStatus(await res.json());
        pollRefreshStatus();
      }} catch (err) {{
        const failed = '<b>状态：</b>启动失败，请确认通过 http://127.0.0.1:8787/ 打开工作台。';
        if ($('#refreshStatus')) $('#refreshStatus').innerHTML = failed;
        if ($('#homeRefreshStatus')) $('#homeRefreshStatus').innerHTML = failed;
      }} finally {{
        setTimeout(()=>{{
          setRefreshButtonsDisabled(false);
        }}, 3000);
      }}
    }}

    async function startProfileRefresh(source) {{
      const homeInput = $('#homeProfileUrl');
      const pageInput = $('#profileUrl');
      const url = (source || homeInput?.value || pageInput?.value || '').trim();
      if (!url) {{
        const failed = '<b>状态：</b>请先粘贴抖音博主主页分享链接。';
        if ($('#refreshStatus')) $('#refreshStatus').innerHTML = failed;
        if ($('#homeRefreshStatus')) $('#homeRefreshStatus').innerHTML = failed;
        return;
      }}
      if (homeInput) homeInput.value = url;
      if (pageInput) pageInput.value = url;
      state.refreshStarted = true;
      setRefreshButtonsDisabled(true);
      const starting = '<b>状态：</b>正在按主页链接抓取博主作品...';
      if ($('#refreshStatus')) $('#refreshStatus').innerHTML = starting;
      if ($('#homeRefreshStatus')) $('#homeRefreshStatus').innerHTML = starting;
      try {{
        const res = await fetch(apiUrl('/api/refresh-profile'), apiOptions({{
          method:'POST',
          cache:'no-store',
          headers:{{'Content-Type':'application/json'}},
          body:JSON.stringify({{url}})
        }}));
        renderRefreshStatus(await res.json());
        pollRefreshStatus();
      }} catch (err) {{
        const failed = '<b>状态：</b>启动失败，请确认通过 http://127.0.0.1:8787/ 打开工作台。';
        if ($('#refreshStatus')) $('#refreshStatus').innerHTML = failed;
        if ($('#homeRefreshStatus')) $('#homeRefreshStatus').innerHTML = failed;
      }} finally {{
        setTimeout(()=>setRefreshButtonsDisabled(false), 3000);
      }}
    }}

    $$('nav button').forEach(btn=>btn.addEventListener('click',()=>switchView(btn.dataset.view)));
    $('#searchVideo').addEventListener('input', renderVideoList);
    $('#themeFilter').addEventListener('change', renderVideoList);
    $('#viewNeedVideos').addEventListener('click', showNeedVideos);
    $('#filterNeeds').addEventListener('click',()=>{{ state.onlyNeeds = !state.onlyNeeds; renderVideoList(); }});
    $('#sortScore').addEventListener('click', e=>{{ e.currentTarget.dataset.sort = e.currentTarget.dataset.sort === 'on' ? '' : 'on'; renderVideoList(); }});
    $('#analyzeDraft').addEventListener('click', analyzeDraft);
    $('#plainRewrite').addEventListener('click', plainRewriteDraft);
    $('#useBestVideo').addEventListener('click',()=>loadVideoToOptimizer([...state.videos].sort((a,b)=>b.scores.score-a.scores.score)[0].idx));
    $('#analyzeViral').addEventListener('click', analyzeViral);
    $('#generateIdeas').addEventListener('click', generateIdeas);
    $('#copyIdeas').addEventListener('click', async()=>{{ await navigator.clipboard.writeText($('#ideasResult').dataset.copy || ''); }});
    $('#ideaTheme').addEventListener('change', scheduleGenerateIdeas);
    $('#ideaPain').addEventListener('change', scheduleGenerateIdeas);
    $('#ideaThemeCustom').addEventListener('input', scheduleGenerateIdeas);
    $('#ideaPainCustom').addEventListener('input', scheduleGenerateIdeas);
    $('#ideaViralCase').addEventListener('change', scheduleGenerateIdeas);
    $('#ideaHotTopic').addEventListener('change', scheduleGenerateIdeas);
    $('#ideaHotCustom').addEventListener('input', scheduleGenerateIdeas);
    $('#refreshHotTopics').addEventListener('click', loadHotTopics);
    $('#checkDedaoBrain').addEventListener('click', loadDedaoStatus);
    $('#homeRefreshDouyin').addEventListener('click', startDouyinRefresh);
    $('#refreshDouyin').addEventListener('click', startDouyinRefresh);
    $('#homeRefreshProfile').addEventListener('click',()=>startProfileRefresh($('#homeProfileUrl').value));
    $('#refreshProfile').addEventListener('click',()=>startProfileRefresh($('#profileUrl').value));
    $('#homeProfileUrl').addEventListener('input', e=>{{ if ($('#profileUrl')) $('#profileUrl').value = e.target.value; }});
    $('#profileUrl').addEventListener('input', e=>{{ if ($('#homeProfileUrl')) $('#homeProfileUrl').value = e.target.value; }});
    $('#checkRefresh').addEventListener('click', pollRefreshStatus);
    ['draftHook','ideaHook'].forEach(sel => {{
      const el = $('#' + sel);
      if (el) el.addEventListener('change', e=>syncHookSelects(e.target.value));
    }});

    renderSelectors();
    renderHookFormulas();
    renderKpis();
    renderVideoList();
    renderPlanner();
    loadDedaoStatus();
    loadHotTopics();
    generateIdeas();
    pollRefreshStatus();
  </script>
</body>
</html>"""


def main():
    subprocess.run(
        [sys.executable, "scripts/build_danao_knowledge.py"],
        cwd=str(ROOT),
        check=False,
    )
    items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    rows = build_rows(items)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(render(rows), encoding="utf-8")
    print(OUT_FILE)


if __name__ == "__main__":
    main()
