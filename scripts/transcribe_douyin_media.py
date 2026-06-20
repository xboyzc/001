import json
from pathlib import Path

from faster_whisper import WhisperModel


DETAILS = Path("data/douyin_details_merged.json")
OUT = Path("output/transcripts")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    items = json.loads(DETAILS.read_text(encoding="utf-8"))
    model = None
    for item in items:
        media_path = item.get("media_path")
        out_path = OUT / f"{item['index']:02d}_{item['aweme_id']}.txt"
        existing_text = (item.get("transcript") or "").strip()
        if not media_path:
            if existing_text:
                item["transcript_status"] = item.get("transcript_status") or "saved_text"
            else:
                item["transcript"] = ""
                item["transcript_status"] = "no_play_url"
            print(item["index"], item["aweme_id"], "SKIP no media")
            continue
        if existing_text and item.get("transcript_status") == "done":
            text = existing_text
            if not out_path.exists() or not out_path.read_text(encoding="utf-8", errors="ignore").strip():
                out_path.write_text(text, encoding="utf-8")
        elif out_path.exists() and out_path.read_text(encoding="utf-8").strip():
            text = out_path.read_text(encoding="utf-8").strip()
        else:
            if model is None:
                model = WhisperModel("small", device="cpu", compute_type="int8")
            segments, info = model.transcribe(
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
            text = "\n".join(parts).strip()
            out_path.write_text(text, encoding="utf-8")
        item["transcript"] = text
        item["transcript_path"] = str(out_path)
        item["transcript_status"] = "done" if text else "empty"
        try:
            media_file = Path(media_path)
            if media_file.exists():
                media_file.unlink()
                print(item["index"], item["aweme_id"], "REMOVED_MEDIA", media_file)
        except Exception as exc:
            print(item["index"], item["aweme_id"], "KEEP_MEDIA", exc)
        item.pop("media_path", None)
        print(item["index"], item["aweme_id"], item["transcript_status"], len(text))
    DETAILS.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
