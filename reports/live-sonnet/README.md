# Task2 Sonnet 實跑（Planner prompt v5）

## 執行條件
- 日期：2026-11-17
- 模型：`claude-sonnet-5-5`，Planner 與 Auditor 同模型
- 憑證：Claude 訂閱 setup-token（使用者同意的例外）
- 版本：規則 `demo-ymyl-2026.11-v3`、Prompt `t2-roles-v5`
- 上限：每次最多 4 份草稿、12 次模型呼叫
- 命令：
  ```bash
  set -a; . ../claude-code-one-shot-kit-v3/.env.subscription; set +a
  uv run --extra anthropic python -m seo_agent.cli collaborate --mode anthropic --model claude-sonnet-5-5 --out reports/t2/live-sonnet --run-name rN
  ```
  三次都是 exit 0

## 結果
| run | 結果 | 草稿數 | 每輪被退條數 | 終稿標題 |
|---|---|---|---|---|
| r1 | approved | 3 | 4 → 1 → 0 | 娛樂城推薦怎麼選？出金流程與評比依據一次看 |
| r2 | approved | 2 | 7 → 0 | 娛樂城推薦怎麼選?5 個必查項目與出金流程檢查 |
| r3 | approved | 2 | 7 → 0 | 娛樂城推薦｜評估方法、出金流程與風險一次看 |

- 三份終稿都沒有提到台灣（v4 的 Opus 版三份都有台灣法律段）
- 第 1 稿被退條數比 v4 多（4–7 條，v4 是 2–3 條）：風險段、年齡、評比方法改由 Auditor 退件，不再寫進 Planner 規則

## attempt1（保留當證據）
- 第一版 v5 沒定義 `unresolvable_constraints` 只能放什麼
- Sonnet 把已移除的強制詞、待收集證據都放進去，加上第 2 稿又引用「零風險」，r1 被判 `conflict_unresolvable`；r2、r3 通過
- 修正：寫明「只放 always 政策下保留的強制詞，否則為 []」，證據清單寫在 sections 內
