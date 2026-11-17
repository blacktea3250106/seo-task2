#!/usr/bin/env sh
# Task2 one-command start for macOS / Linux.
#   ./start_task2.sh            build a clean env, ask for an API key (Enter = offline demo), run
#   ./start_task2.sh --offline  skip the key prompt; offline fixture run
#   ./start_task2.sh --test     run the Task2 test suite before the negotiation
# Only prerequisite: network + curl. uv provides Python 3.12 itself.
set -eu
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
  echo "找不到 uv（Python 版本與套件管理工具，https://docs.astral.sh/uv/）。"
  echo "將用官方腳本安裝到 ~/.local/bin，不修改你的 shell 設定檔。"
  if [ -t 0 ]; then
    printf "要繼續嗎？[Y/n] "
    read -r ans
    case "$ans" in [Nn]*) echo "已取消。手動安裝 uv 後重跑即可。"; exit 1 ;; esac
  fi
  if ! command -v curl >/dev/null 2>&1; then
    echo "[失敗] 找不到 curl，無法下載 uv。請先安裝 curl，或手動安裝 uv：https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
  fi
  installer=$(curl -LsSf https://astral.sh/uv/install.sh) || {
    echo "[失敗] 下載 uv 安裝腳本失敗，請檢查網路後重跑。" >&2; exit 1; }
  printf '%s\n' "$installer" | env UV_NO_MODIFY_PATH=1 UV_INSTALL_DIR="$HOME/.local/bin" sh || {
    echo "[失敗] uv 安裝腳本執行失敗，請看上方訊息或手動安裝：https://docs.astral.sh/uv/getting-started/installation/" >&2; exit 1; }
  PATH="$HOME/.local/bin:$PATH"
  export PATH
  if ! command -v uv >/dev/null 2>&1; then
    echo "[失敗] uv 安裝後仍找不到，請手動安裝：https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
  fi
fi

exec uv run --no-project --python 3.12 python start_task2.py "$@"
