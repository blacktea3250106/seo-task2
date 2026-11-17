#!/usr/bin/env python3
"""取得鎖定版 Hermes 原始碼到 vendor/hermes-agent。

Hermes 的 build backend 拒絕打包 wheel／sdist，只支援 editable 安裝，所以不能用 URL 依賴。
本腳本下載固定 commit 的 GitHub tarball、驗證 sha256、解壓到 vendor/hermes-agent，並寫入
vendor/hermes-agent/.seo_agent_pin.json。已存在且 pin 相符時不重抓。只用標準函式庫。

用法：uv run --no-project --python 3.12 python tools/fetch_hermes.py [--from-file 已下載的.tar.gz]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "f97608f178d1ffeca59860195ab7da295f7c8e5f"
TAG = "v2026.9.24"
URL = f"https://github.com/NousResearch/hermes-agent/archive/{COMMIT}.tar.gz"
# GitHub archive 實際轉址到 codeload；內容相同，sha256 一樣驗證
MIRRORS = (URL, f"https://codeload.github.com/NousResearch/hermes-agent/tar.gz/{COMMIT}")
SHA256 = "babbdb9706ad1c96708d75914afb45d809cd4b73dec1ceae233a6814f5ed97e3"
DEST = ROOT / "vendor" / "hermes-agent"
PIN = {"repo": "NousResearch/hermes-agent", "tag": TAG, "commit": COMMIT, "url": URL, "sha256": SHA256}


def copy_with_progress(response, out, total: int) -> None:
    """壓縮檔約 60MB；每 10%（不知道總大小時每 20MB）印一次進度，免得看起來像當掉。"""
    done, next_mark = 0, 0.1 if total else 20 << 20
    while chunk := response.read(1 << 20):
        out.write(chunk)
        done += len(chunk)
        if total and done / total >= next_mark:
            print(f"  下載 Hermes：{done * 100 // total}%（{done >> 20} MB）", file=sys.stderr, flush=True)
            next_mark += 0.1
        elif not total and done >= next_mark:
            print(f"  下載 Hermes：{done >> 20} MB", file=sys.stderr, flush=True)
            next_mark += 20 << 20


def download(archive: Path, attempts: int = 4) -> None:
    """GitHub 偶爾回 429／5xx：換來源並退避重試；最後仍失敗才報錯。"""
    last: Exception | None = None
    for attempt in range(attempts):
        url = MIRRORS[attempt % len(MIRRORS)]
        try:
            with urllib.request.urlopen(url, timeout=600) as response, archive.open("wb") as out:
                copy_with_progress(response, out, int(response.headers.get("Content-Length") or 0))
            return
        except urllib.error.HTTPError as error:
            if error.code != 429 and error.code < 500:
                raise
            last, wait = error, min(int(error.headers.get("Retry-After") or 0) or 5 * 2 ** attempt, 60)
        except urllib.error.URLError as error:
            last, wait = error, 5 * 2 ** attempt
        if attempt + 1 < attempts:
            print(f"下載失敗（{last}），{wait} 秒後重試", file=sys.stderr)
            time.sleep(wait)
    raise SystemExit(f"無法下載 Hermes：{last}。可手動下載 {URL} 後執行 uv run --no-project --python 3.12 python tools/fetch_hermes.py --from-file <檔案>")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-file", type=Path)
    args = parser.parse_args()
    pin_file = DEST / ".seo_agent_pin.json"
    if pin_file.is_file() and json.loads(pin_file.read_text()) == PIN:
        print(json.dumps({"status": "already_present", **PIN}))
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "hermes.tar.gz"
        if args.from_file:
            shutil.copyfile(args.from_file, archive)
        else:
            download(archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != SHA256:
            print(json.dumps({"status": "sha256_mismatch", "expected": SHA256, "actual": digest}), file=sys.stderr)
            return 1
        extract = Path(tmp) / "x"
        with tarfile.open(archive) as tar:
            tar.extractall(extract, filter="data")  # data filter：拒絕絕對路徑、..、裝置檔
        top = extract / f"hermes-agent-{COMMIT}"
        if not top.is_dir():
            print("tarball 結構不符", file=sys.stderr)
            return 1
        if DEST.exists():
            shutil.rmtree(DEST)
        DEST.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(top), DEST)
    pin_file.write_text(json.dumps(PIN, indent=2) + "\n")
    print(json.dumps({"status": "fetched", **PIN}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
