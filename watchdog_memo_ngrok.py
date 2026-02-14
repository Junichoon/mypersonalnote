from __future__ import annotations

import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCAL_HEALTH_URL = "http://127.0.0.1:8081/login"
PUBLIC_URL = "https://unsponsored-vinnie-colourlessly.ngrok-free.dev/"
CHECK_INTERVAL_SECONDS = 30


def is_public_endpoint_healthy(status: int, headers: dict[str, str], body: str) -> bool:
    ngrok_err = headers.get("Ngrok-Error-Code", "")
    if "ERR_NGROK_3200" in ngrok_err:
        return False
    if "ERR_NGROK_3200" in body:
        return False
    return status in {200, 301, 302}


def request_url(url: str) -> tuple[int, dict[str, str], str]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=8) as resp:
        body = resp.read(2000).decode("utf-8", errors="ignore")
        return resp.status, dict(resp.headers), body


def is_local_healthy() -> bool:
    try:
        status, _, _ = request_url(LOCAL_HEALTH_URL)
        return status == 200
    except Exception:
        return False


def is_public_healthy() -> bool:
    try:
        status, headers, body = request_url(PUBLIC_URL)
        return is_public_endpoint_healthy(status, headers, body)
    except urllib.error.HTTPError as e:
        body = e.read(2000).decode("utf-8", errors="ignore") if e.fp else ""
        return is_public_endpoint_healthy(e.code, dict(e.headers), body)
    except Exception:
        return False


def start_memo_server() -> None:
    print("[watchdog] starting memo-web server")
    subprocess.Popen(
        ["python", "server.py"],
        cwd=str(ROOT),
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def restart_ngrok() -> None:
    print("[watchdog] restarting ngrok tunnel")
    subprocess.run(
        ["taskkill", "/IM", "ngrok.exe", "/F"],
        capture_output=True,
        text=True,
    )
    subprocess.Popen(
        ["ngrok", "http", "--url=unsponsored-vinnie-colourlessly.ngrok-free.dev", "8081"],
        cwd=str(ROOT.parent),
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_watchdog() -> None:
    print("[watchdog] started")
    while True:
        if not is_local_healthy():
            start_memo_server()
            time.sleep(3)

        if not is_public_healthy():
            restart_ngrok()
            time.sleep(3)

        print("[watchdog] check complete")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_watchdog()
