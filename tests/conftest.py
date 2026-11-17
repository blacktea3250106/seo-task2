"""測試共用設定。在任何 Hermes import 之前把 HERMES_HOME 指到暫存目錄。"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TEST_HOME = Path(tempfile.mkdtemp(prefix="seo-agent-tests-hermes-"))
os.environ["HERMES_HOME"] = str(_TEST_HOME)

import pytest  # noqa: E402

GLOBAL_HERMES_HOME = Path.home() / ".hermes"
_GLOBAL_EXISTED = GLOBAL_HERMES_HOME.exists()


@pytest.fixture(autouse=True)
def _global_hermes_home_untouched():
    """每個測試結束時確認沒有建立使用者的 ~/.hermes（原本不存在時）。"""
    yield
    if not _GLOBAL_EXISTED:
        assert not GLOBAL_HERMES_HOME.exists(), "測試在使用者家目錄建立了 ~/.hermes"

