import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEDIA_DIRS = [
    ROOT / "data" / "media",
    ROOT / "data" / "tmp_media",
]
DETAILS = ROOT / "data" / "douyin_details_merged.json"


def remove_media_dirs():
    removed = []
    for directory in MEDIA_DIRS:
        if not directory.exists():
            continue
        size = sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())
        count = sum(1 for p in directory.rglob("*") if p.is_file())
        shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)
        removed.append((directory, count, size))
    return removed


def clean_details():
    if not DETAILS.exists():
        return 0
    try:
        items = json.loads(DETAILS.read_text(encoding="utf-8"))
    except Exception:
        return 0
    changed = 0
    for item in items:
        if isinstance(item, dict) and "media_path" in item:
            item.pop("media_path", None)
            changed += 1
    DETAILS.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed


def human(size):
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024:
            return f"{value:.1f}{unit}"
        value /= 1024
    return f"{value:.1f}PB"


def main():
    removed = remove_media_dirs()
    changed = clean_details()
    total = sum(size for _, _, size in removed)
    for directory, count, size in removed:
        print(f"removed {count} files from {directory}: {human(size)}")
    print(f"removed media_path from {changed} detail rows")
    print(f"total saved: {human(total)}")


if __name__ == "__main__":
    main()
