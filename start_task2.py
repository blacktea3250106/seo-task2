"""Task2 one-command launcher (macOS / Linux / Windows).

Builds a clean, lockfile-pinned environment and runs one Planner/Auditor negotiation:

    1. fetch the pinned Hermes source (sha256 verified)
    2. `uv sync --frozen` into .venv (uv downloads Python 3.12 if missing)
    3. optionally run the Task2 test suite
    4. ask for an Anthropic API key (hidden, never written to disk; Enter = offline demo)
    5. run the LangGraph workflow and print the final outline

Usually started through ./start_task2.sh (macOS/Linux) or .\\start_task2.ps1 (Windows),
which install uv when it is missing and then run:

    uv run --no-project --python 3.12 python start_task2.py [--offline] [--test]

Standard library only, so it runs before any dependency is installed.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "t2-output"
DEFAULT_MODEL = "claude-sonnet-5-5"
IS_WINDOWS = os.name == "nt"
VENV_PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


# Windows 在輸出被導向（CI、Tee-Object）時預設 cp1252，中文會讓 print 直接丟例外
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

UTF8_ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def step(n: int, total: int, title: str) -> None:
    print(f"\n==> [{n}/{total}] {title}", flush=True)


def run(cmd: list[str], env: dict[str, str] | None = None, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, env=env, **kwargs)


def must(cmd: list[str], what: str, env: dict[str, str] | None = None) -> None:
    if run(cmd, env=env).returncode != 0:
        sys.exit(f"\n[失敗] {what}。上方是原始錯誤訊息；修正後重跑即可（已完成的步驟會略過）。")


def find_uv() -> str:
    uv = os.environ.get("UV") or shutil.which("uv")
    if not uv:
        sys.exit("找不到 uv。請改用 ./start_task2.sh（macOS/Linux）或 .\\start_task2.ps1（Windows），"
                 "它們會先安裝 uv；或參考 https://docs.astral.sh/uv/getting-started/installation/")
    return uv


def ask_api_key(offline: bool) -> str:
    if offline:
        return ""
    key = os.environ.get("SEO_MODEL_API_KEY", "").strip()
    if key:
        print("使用環境變數 SEO_MODEL_API_KEY。")
        return key
    if not sys.stdin.isatty():
        print("非互動環境：改用離線示範。")
        return ""
    print("要用真實模型跑嗎？貼上 Anthropic API key（輸入不會顯示，也不會存檔；最多 12 次模型呼叫）。")
    print("取得 API key：https://console.anthropic.com/settings/keys")
    try:
        return getpass.getpass("直接按 Enter = 離線示範：").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Task2 one-command launcher")
    parser.add_argument("--offline", action="store_true", help="不問 API key，用 fixture 模型離線跑")
    parser.add_argument("--test", action="store_true", help="建好環境後先跑 Task2 測試")
    args = parser.parse_args()

    if sys.version_info < (3, 11, 4):
        sys.exit("需要 Python 3.11.4 以上；建議用 start_task2.sh／start_task2.ps1 啟動，uv 會自動準備 Python 3.12。")
    uv = find_uv()
    total = 5 if args.test else 4
    n = 0

    n += 1
    step(n, total, "下載鎖定版 Hermes（驗 sha256；已存在就略過）")
    must([sys.executable, "tools/fetch_hermes.py"], "下載 Hermes", env=UTF8_ENV)

    n += 1
    step(n, total, "依 uv.lock 建立 .venv（Python 3.12）")
    must([uv, "sync", "--python", "3.12", "--extra", "dev", "--extra", "anthropic", "--frozen"], "建立環境",
         env=UTF8_ENV)

    env = dict(UTF8_ENV)
    if args.test:
        n += 1
        step(n, total, "Task2 測試")
        must([str(VENV_PYTHON), "-m", "pytest", "-q", "tests"], "Task2 測試", env=env)

    n += 1
    step(n, total, "選擇模型")
    key = ask_api_key(args.offline)
    model = os.environ.get("SEO_MODEL_ID") or DEFAULT_MODEL
    if key:
        env["SEO_MODEL_API_KEY"] = key
        cmd_mode = ["--mode", "anthropic", "--model", model]
        print(f"模式：真實模型 {model}（約 1–2 分鐘）")
    else:
        env.pop("SEO_MODEL_API_KEY", None)
        cmd_mode = ["--mode", "fixture"]
        print("模式：離線示範（fixture 模型，不連網、不花額度）")

    n += 1
    step(n, total, "執行 LangGraph 協商：Start → Planning → Audit → Decision")
    OUT.mkdir(exist_ok=True)
    cli = [str(VENV_PYTHON), "-m", "seo_agent.cli"]
    graph = run(cli + ["graph"], env=env, capture_output=True, text=True, encoding="utf-8")
    if graph.returncode == 0:
        (OUT / "graph.mmd").write_text(graph.stdout, encoding="utf-8")
    result = run(cli + ["collaborate", *cmd_mode, "--out", str(OUT), "--run-name", "latest"],
                 env=env, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(result.stdout + result.stderr, file=sys.stderr)

    final = OUT / "latest" / "final.md"
    if final.is_file():
        print("\n" + "-" * 24 + " 最終大綱 " + "-" * 24)
        print(final.read_text(encoding="utf-8"))
        print("-" * 58)
    summary = OUT / "latest" / "result.json"
    if summary.is_file():
        data = json.loads(summary.read_text(encoding="utf-8"))
        rounds = " → ".join(str(len(f)) for f in data.get("findings_history", []))
        print(f"\n結果：{data.get('status')}｜草稿 {len(data.get('drafts', []))} 份" + (f"｜每輪退件 {rounds}" if rounds else ""))
        if data.get("status") in {"planner_failed", "auditor_failed"}:
            print("模型呼叫失敗：請確認 API key 是否正確、額度是否足夠（詳細原因見上方訊息與 result.json 的 usage.errors）。")
    rel = OUT.relative_to(ROOT)
    print(f"""
輸出在 {rel}/：
  graph.mmd               工作流拓撲圖（Mermaid）
  latest/state_log.jsonl  每一步的狀態日誌（Agent 協商過程）
  latest/result.json      完整 State（每一稿、每輪退件原因、用量）
  latest/final.md         最終大綱與協商摘要""")
    if not key:
        print("\n這次是離線示範。要用真實模型：重跑並貼上 API key，或先設定環境變數 SEO_MODEL_API_KEY。")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
