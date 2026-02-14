import json
import pathlib
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "faiss_metadata.json"
OUT = pathlib.Path(__file__).resolve().parent / "memos.json"

items = json.loads(SRC.read_text(encoding="utf-8"))
active = [x for x in items if not x.get("deleted")]

payload = {
    "generatedAt": datetime.now().isoformat(timespec="seconds"),
    "count": len(active),
    "memos": [
        {
            "id": x.get("id"),
            "content": x.get("content"),
            "timestamp": x.get("timestamp"),
            "metadata": x.get("metadata", {}),
        }
        for x in active
    ],
}

OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {OUT} ({payload['count']} memos)")
