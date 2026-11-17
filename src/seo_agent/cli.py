"""CLI：collaborate（Planner／Auditor 協商）、graph（輸出 Mermaid 拓撲圖）。

anthropic 模式會 import Hermes 的連線 adapter；import 前先把 HERMES_HOME 指到專案內，
避免讀到或建立使用者家目錄的 ~/.hermes。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from .config import ROOT

os.environ.setdefault("HERMES_HOME", str(ROOT / ".hermes-runs" / "_cli"))


def _collaborate(args) -> int:
    from .content_review.agents import StubAuditor, StubPlanner
    from .content_review.graph import ReviewConfig, run_review
    from .content_review.render import render_review

    allowance, cfg = None, None
    if args.mode == "anthropic":  # 重用 Hermes 的 Anthropic adapter
        from .content_review.anthropic_model import anthropic_models
        from .harness.model_endpoint import EndpointPolicyError
        try:
            planner, auditor, allowance = anthropic_models(model=args.model)
        except (EndpointPolicyError, ValueError, ImportError) as error:
            print(json.dumps({"status": "blocked", "reason": str(error)}, ensure_ascii=False))
            return 3
        # 外層逾時要明顯大於 SDK 各階段逾時加總（連線 10＋寫入／讀取各 170），避免外層先逾時又重送已送出的請求
        cfg = ReviewConfig(timeout_s=400.0, max_attempts=2, max_model_calls=12, backoff_s=2.0)
    elif args.mode == "live":
        from .config import load_policy
        from .content_review.live_model import api_models
        from .harness.model_endpoint import EndpointPolicyError
        try:
            planner, auditor, allowance = api_models(load_policy())
        except (EndpointPolicyError, ValueError) as error:
            print(json.dumps({"status": "blocked", "reason": str(error)}, ensure_ascii=False))
            return 3
    else:
        planner, auditor = StubPlanner(), StubAuditor()
    out = Path(args.out).resolve() / args.run_name
    result = asyncio.run(run_review(args.topic, args.forced, planner, auditor, args.max_iterations,
                                    force_policy=args.force_policy, cfg=cfg, log_path=out / "state_log.jsonl"))
    result["model_provenance"] = {"mode": args.mode, "planner": planner.name, "auditor": auditor.name}
    if allowance:
        result["model_allowance"] = allowance.snapshot()
    (out / "final.md").write_text(render_review(result), encoding="utf-8")
    (out / "result.json").write_text(json.dumps({k: v for k, v in result.items() if k != "state_log"},
                                                ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "iteration": result["iteration"], "stop_reason": result.get("stop_reason"),
                      "usage": result["usage"], "out": str(out)}, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"approved", "conflict_unresolvable", "max_iterations_reached"} else 1


def _graph(args) -> int:
    from .content_review.graph import mermaid
    print(mermaid())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seo-agent")
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("collaborate", help="Planner／Auditor 協商工作流")
    c.add_argument("--topic", default="娛樂城推薦")
    c.add_argument("--forced", action="append", default=None)
    c.add_argument("--force-policy", choices=["first_draft", "always"], default="first_draft")
    c.add_argument("--max-iterations", type=int, default=None)
    c.add_argument("--mode", choices=["fixture", "live", "anthropic"], default="fixture")
    c.add_argument("--model", default=None, help="--mode anthropic 的模型（預設 claude-opus-5-5）")
    c.add_argument("--out", default=str(ROOT / "reports" / "t2"))
    c.add_argument("--run-name", default="latest")
    c.set_defaults(func=_collaborate)
    g = sub.add_parser("graph", help="輸出 LangGraph 的 Mermaid 拓撲圖")
    g.set_defaults(func=_graph)
    args = parser.parse_args(argv)
    if args.command == "collaborate":
        from .config import load_policy
        args.forced = args.forced or ["穩賺不賠", "保證出金"]
        args.max_iterations = args.max_iterations or load_policy()["runtime"]["t2_max_drafts"]
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
