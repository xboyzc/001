import json
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "data/browser_profile",
    "data/media",
    "data/tmp_media",
    "data/douyin_capture",
    "data/douyin_profile_capture",
    "data/douyin_details",
}

EXCLUDE_SUFFIXES = {
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".webm",
    ".pyc",
    ".DS_Store",
}


def excluded(path):
    rel = path.relative_to(ROOT).as_posix()
    parts = rel.split("/")
    for i in range(1, len(parts) + 1):
        if "/".join(parts[:i]) in EXCLUDE_DIRS:
            return True
    if path.name in EXCLUDE_SUFFIXES or path.suffix in EXCLUDE_SUFFIXES:
        return True
    if rel.startswith("dist/"):
        return True
    return False


def manifest(files):
    return {
        "name": "douyin-content-agent",
        "packaged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_count": len(files),
        "notes": [
            "原始视频、虚拟环境、Git 历史、浏览器登录缓存不包含在轻量包中。",
            "新电脑首次启动会根据 requirements.txt 自动安装依赖。",
            "长期保存内容包括文案、转写稿、分析结果和工作台页面。",
        ],
    }


def main():
    DIST.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    zip_path = DIST / f"douyin-content-agent-{stamp}.zip"
    files = [p for p in ROOT.rglob("*") if p.is_file() and not excluded(p)]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, path.relative_to(ROOT).as_posix())
        zf.writestr("PACKAGE_MANIFEST.json", json.dumps(manifest(files), ensure_ascii=False, indent=2))

    size = zip_path.stat().st_size / 1024 / 1024
    print(f"created {zip_path}")
    print(f"files {len(files)}")
    print(f"size {size:.1f} MB")


if __name__ == "__main__":
    main()
