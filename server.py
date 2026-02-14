from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request, send_from_directory, session, redirect, url_for

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
FAISS_PATH = WORKSPACE / "faiss_metadata.json"
EXPORT_PATH = ROOT / "memos.json"

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")
app.secret_key = os.environ.get("OPENCLAW_MEMO_SECRET", "change-this-secret")

LOGIN_EMAIL = "junichoon@gmail.com"
LOGIN_HASH = "scrypt:32768:8:1$DZYpN0yDDJ9QJ1TF$33df9de05818ac68ed9af4762f41e651815c72e545f6e0c6da1a1f452208d1a35ab758e8d08ce0d02af6285f57f47f306709303ed85a473ee1ff972c17138878"

PUBLIC_PATHS = {
    "/login",
    "/login.html",
    "/login.js",
    "/styles.css",
}


def _load_items() -> List[Dict[str, Any]]:
    return json.loads(FAISS_PATH.read_text(encoding="utf-8"))


def _save_items(items: List[Dict[str, Any]]) -> None:
    FAISS_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _export_memos(items: List[Dict[str, Any]]) -> Dict[str, Any]:
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
    EXPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _sync_and_export() -> Dict[str, Any]:
    items = _load_items()
    return _export_memos(items)


@app.before_request
def require_login():
    if request.path in PUBLIC_PATHS or request.path.startswith("/static"):
        return None
    if request.path.startswith("/api/") or request.path.endswith(".html") or request.path == "/":
        if not session.get("user"):
            return redirect(url_for("login", next=request.path))
    return None


@app.get("/login")
def login():
    return send_from_directory(ROOT, "login.html")


@app.post("/login")
def login_post():
    data = request.form or {}
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    from werkzeug.security import check_password_hash

    if email == LOGIN_EMAIL and check_password_hash(LOGIN_HASH, password):
        session["user"] = email
        next_path = request.args.get("next") or "/"
        return redirect(next_path)

    return redirect(url_for("login") + "?error=1")


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.get("/tags.html")
def tags_page():
    return send_from_directory(ROOT, "tags.html")


@app.get("/tags.js")
def tags_script():
    return send_from_directory(ROOT, "tags.js")


@app.get("/login.js")
def login_script():
    return send_from_directory(ROOT, "login.js")


@app.get("/api/memos")
def list_memos():
    payload = _sync_and_export()
    return jsonify(payload)


@app.post("/api/memos")
def create_memo():
    data = request.get_json(force=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "content is required"}), 400

    items = _load_items()
    next_id = max((x.get("id", -1) for x in items), default=-1) + 1
    now = datetime.now().isoformat(timespec="seconds")
    memo = {
        "id": next_id,
        "content": content,
        "timestamp": now,
        "metadata": data.get("metadata", {}),
    }
    items.append(memo)
    _save_items(items)
    payload = _export_memos(items)
    return jsonify(payload)


@app.put("/api/memos/<int:memo_id>")
def update_memo(memo_id: int):
    data = request.get_json(force=True) or {}
    items = _load_items()
    updated = False
    for memo in items:
        if memo.get("id") == memo_id and not memo.get("deleted"):
            if "content" in data:
                memo["content"] = data["content"].strip()
            if "metadata" in data:
                memo["metadata"] = data["metadata"] or {}
            memo["timestamp"] = datetime.now().isoformat(timespec="seconds")
            updated = True
            break

    if not updated:
        return jsonify({"error": "memo not found"}), 404

    _save_items(items)
    payload = _export_memos(items)
    return jsonify(payload)


@app.delete("/api/memos/<int:memo_id>")
def delete_memo(memo_id: int):
    items = _load_items()
    deleted = False
    for memo in items:
        if memo.get("id") == memo_id and not memo.get("deleted"):
            memo["deleted"] = True
            memo["deleted_at"] = datetime.now().isoformat(timespec="seconds")
            deleted = True
            break

    if not deleted:
        return jsonify({"error": "memo not found"}), 404

    _save_items(items)
    payload = _export_memos(items)
    return jsonify(payload)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=True)
