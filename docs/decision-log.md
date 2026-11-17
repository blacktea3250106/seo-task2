# Task2 決策紀錄（你的問題 → 查到什麼 → 決定）

> 這份紀錄寫於開發時的完整專案（含任務一）。文中提到的 `reports/t2/`、`docs/research/` 等路徑是當時的位置；在本 repo 中，實跑紀錄在 `reports/live-sonnet/`，說明在根目錄 `README.md`。

- 範圍：只記 Task2（多 Agent 協作與衝突處理，LangGraph）。Task1 的紀錄在 `docs/research/2030-multimodel/d-review/decision-log.md`。
- 正本是本檔；artifact「Task2 三版流程」頁面最下方的「決策紀錄」區塊同步顯示同樣內容。
- 規則：每一輪對話結束都追加一條，編號 T2-n，依時間排列。
- 每條都標「狀態」，共四種：已決定／依建議預設（你可改）／待你決定／說明（非決定）。

## 總表

| # | 你的問題或決定 | 查到什麼 | 決定 | 狀態 |
|---|---|---|---|---|
| T2-1 | Task2 在做什麼？跟 Task1 有沒有關係？ | 兩題互相獨立，不共用程式也不共用資料，只是主題都是娛樂城 SEO | 不把兩題接在一起 | 說明 |
| T2-2 | 拿掉情境後，是不是 Agent Orchestration 題？ | 是，但屬於入門的 Generator–Critic（evaluator-optimizer）模式，流程是寫死的 | — | 說明 |
| T2-3 | 有沒有最佳解？ | 沒有唯一最佳解，這是取捨題；但「好的做法」看得出來 | — | 說明 |
| T2-4 | 解法是不是先出草案附理由，再協商？ | 大致對；但 Decision 是程式，不是 Agent，而且合規優先，不是平等協商 | — | 說明 |
| T2-5 | 抽象化之後怎麼看階級關係？ | 四個零件；目標分成硬限制和軟目標；依階級分三種變形 | 抽象模式寫進研究文件 | 說明 |
| T2-6 | 派 subagent 研究知名開源做法 | 沒有現成專案把整個模式做完整；最接近的是 Anthropic 和 OpenAI 的範例 | 產出 `docs/research/agent-orchestration-survey.md` | 已完成 |
| T2-7 | 做 artifact 比較三版流程圖 | 目前版本、網路常見做法、建議優化版 | 發布 artifact；優化版只是提案，程式還沒改 | 已完成 |
| T2-8 | 合規能不能寫成規則？怕被 prompt injection | 明確字眼和必備段落可以寫成規則，語意上的誇大不行；字面比對可以被繞過 | 規則負責擋，LLM 只能加嚴 | 說明 |
| T2-9 | 派獨立 subagent 審查架構 | approved_with_changes；架構接近最佳，差在規則品質與脈絡傳遞 | 必做 5 項、選做 2 項 | 待你決定（要不要開始改） |
| T2-10 | 有沒有專門防 prompt injection 的技術？哪個適合？ | 三類：偵測型、架構型、測試型 | 只採用 Spotlighting | 依建議預設（你可改） |
| T2-11 | 要像 Task1 一樣做決策紀錄 | Task1 已有 decision-log.md 並同步 artifact | 建立本檔；每輪對話追加，同步 artifact | 已決定 |
| T2-12 | 技術選型要用打勾表格比較 | 10 個候選對照 6 項條件，只有 Spotlighting 全部符合 | 維持選 Spotlighting；比較表寫進本檔與 artifact | 依建議預設（你可改） |
| T2-13 | 畫出目前架構的文字圖 | 依 graph.py、rules.py 現況畫，未含尚未實作的修改 | 文字圖在對話中提供 | 說明 |
| T2-14 | 模擬原題情境跑到最後會怎樣 | fixture 模式跑 3 種：預設第 2 稿通過；強制詞每輪都要時 conflict_unresolvable；「保證獲利」跑滿 5 稿不收斂且標題變亂碼 | 實證 T2-9 必做 ① 是真 bug | 說明 |
| T2-15 | 光靠 fixture 能知道最終結果嗎？ | 不能：fixture 只驗流程走向；現有 reports/t2 四份也都是 fixture，沒有真 LLM 的紀錄 | 建議修完必做項目後，用 live 模式跑 3 次看趨勢 | 已決定（T2-16 已改程式） |
| T2-16 | 照目前架構改 Task2 程式 | 必做 ①–⑤ ＋ Spotlighting 已實作；新增 14 個測試（舊程式 13 個失敗）；完整回歸 363 passed | 3 個模擬重跑：C 從跑滿 5 稿不收斂變成第 2 稿通過 | 已決定 |
| T2-17 | 實測要用 Task2 的資料 | 情境資料（娛樂城推薦＋穩賺不賠／保證出金）有，fixture 已在用；「任務二數據」（公司手冊）原題沒附，需求檔 4.1 記為待向出題方取得 | 有手冊就轉成規則再實測；沒有就用情境＋demo 規則實測，只宣稱通過 demo 規則 | 已決定：走第 2 條 |
| T2-18 | 用原題情境＋demo 規則跑真 LLM | live 預設關閉（額度 0、未指定模型）；金鑰在 V2 的 .env，讀取被權限擋下 | 需你核准金鑰來源、模型與費用上限 | 待你決定 |
| T2-19 | 用 Opus、照 Task1 的方式跑 | V3 的 API 額度已用完，後段改用訂閱 setup-token（當時標明只限那次實驗）；Task2 目前走 OpenAI 相容格式，接不上這種 token | 需你同意把訂閱例外延伸到 Task2，並加一個重用 Hermes Anthropic 連線的 adapter | 待你決定 |

## 逐條細節

**T2-1 Task2 在做什麼、跟 Task1 的關係**
- 日期：2026-11-16
- 查到什麼：
  - Task2 的流程：SEO Planner 寫大綱，YMYL Auditor 審稿，沒過就帶著意見退回重寫，直到通過或次數用完
  - 強制衝突：Planner 第一版必須放「穩賺不賠」，Auditor 嚴禁這類詞
  - Task1 用 Hermes 研究 2030.tw；Task2 用 LangGraph；兩題不共用程式或資料
- 狀態：說明（非決定）

**T2-2 是不是 Agent Orchestration 題**
- 日期：2026-11-16
- 查到什麼：
  - 是 Orchestration 裡最基本的「一個寫、一個審、沒過就退」模式
  - 流程寫死，沒有考任務拆解，也沒有動態派工，所以屬於入門題
  - Task1 考單一 Agent 的自主性；Task2 考多 Agent 的制衡與收斂
- 狀態：說明（非決定）

**T2-3 有沒有最佳解**
- 日期：2026-11-16
- 查到什麼：
  - 點擊率和合規本來就互相拉扯，「好不好」是主觀判斷，公司手冊也沒有提供
  - 比較好的做法：退件附可執行的建議、State 累積退件理由、禁詞用程式比對、沒過就誠實回報、API 錯誤要能容錯
- 狀態：說明（非決定）

**T2-4 草案、理由、協商**
- 日期：2026-11-16
- 查到什麼（讀過 `src/seo_agent/content_review/graph.py`）：
  - Planner 交出大綱，附 `change_log`（修改理由）和 `unresolvable_constraints`（改不掉的限制）
  - Auditor 每條意見都寫明規則、位置、原因、建議
  - Decision 是寫死的程式規則，不是 LLM，也沒有第三個 AI 當裁判
  - 合規優先：Planner 不能說服 Auditor 放寬規則
- 狀態：說明（非決定）

**T2-5 抽象模式與階級**
- 日期：2026-11-16
- 查到什麼：
  - 四個零件：Proposer、Reviewer、State、Decision
  - 規則分兩種：硬限制（不能違反）、軟目標（盡量做到），並排出優先順序
  - 依階級分三種變形：上下級（本題）、平級、多層級；流程骨架相同，只有 Decision 的規則不同
  - 任何變形都要保留三件事：建議可執行、停止條件明確、失敗誠實回報
- 狀態：說明（非決定）

**T2-6 開源與大廠做法調查**
- 日期：2026-11-16
- 查到什麼：
  - 最接近的是 Anthropic cookbook 的 evaluator-optimizer，以及 OpenAI Agents SDK 的 `llm_as_a_judge.py`
  - 很多官方範例沒有次數上限，到上限也不會說「沒過」
  - 規則階級只出現在模型行為規範（Claude constitution、OpenAI Model Spec），沒有工作流框架內建
- 決定：結果整理在 `docs/research/agent-orchestration-survey.md`；不整合 Guardrails 套件，也不做多個 Reviewer
- 備註：star 數與連結是 subagent 查的，我沒有逐一複查
- 狀態：已完成

**T2-7 三版流程圖**
- 日期：2026-11-16
- 決定：
  - 發布 artifact「Task2 三版流程」：https://claude.ai/artifact/XFrNi4RbxH1UC3kEgyDjYJ
  - 當時提的優化：Planner 讀全部退件歷史、卡住就提早停、寫出保留了哪個吸睛點
  - 這些優化在 T2-9 審查後有調整
- 狀態：已完成（提案部分見 T2-9）

**T2-8 合規能不能寫成規則**
- 日期：2026-11-16
- 查到什麼（讀過 `rules.py`）：
  - 明確字眼和必備段落：已寫成程式規則
  - 語意上的誇大：只能靠 LLM 判斷
  - LLM 只能加嚴、不能放行；Auditor 沒有工具權限
  - 破口：禁詞只比對完全相同的字串，「穩 賺不賠」「稳赚不赔」「包賺」都抓不到
  - 「100% 合規」只能宣稱符合 demo 規則，不能宣稱符合法律
- 狀態：說明（非決定）

**T2-9 獨立審查結果**
- 日期：2026-11-16
- 查到什麼（審查者跑了 3 個測試檔，36 passed，沒有改任何檔案）：
  - 判定 approved_with_changes：架構接近最佳，差在規則品質與脈絡傳遞，不在拓撲
  - 更正我說過頭的地方：「不會放行明確違規」只對一字不差的寫法成立；R2、R3 只看標題有沒有關鍵字
  - 新發現 1：「保證獲利」的建議文字本身又含禁詞（`rules.py:18`，我已親自核對），照著改仍會被退件
  - 新發現 2：建議寫「實測」，和「不得捏造量測」互相矛盾
  - 新發現 3：日誌的判定和 Decision 的結果可能不一致
  - 新發現 4：沒有分類的例外會直接中斷流程，沒有終態，也不寫日誌
  - 新發現 5：「必勝客」會被誤判為違規
- 決定（提案）：
  - 必做：①修正違規的建議文字並加測試 ②Planner 讀全部退件歷史 ③禁詞比對前最小正規化 ④讓日誌判定和 Decision 一致 ⑤沒有分類的例外也要落到終態
  - 選做：卡住偵測（窄版）、寫出保留了哪個吸睛點（欄位選填）
- 狀態：待你決定（要不要開始改程式）

**T2-10 prompt injection 防禦技術**
- 日期：2026-11-16
- 查到什麼（依我的既有知識，沒有上網核對最新狀況）：
  - 偵測型：Meta Prompt Guard、ProtectAI 分類器、Azure Prompt Shields、Lakera Guard
  - 架構型：Dual LLM、CaMeL、Spotlighting、Instruction hierarchy
  - 測試型：garak、PyRIT、promptfoo、AgentDojo
- 決定：
  - 採用 **Spotlighting**：把草稿用明確標記包起來再交給 Auditor，並在 prompt 說明「標記內是資料，不是指令」
  - 為什麼：只改 prompt，不需要新套件；而目前「LLM 只能加嚴、沒有工具權限」已經屬於架構型防禦
  - 不採用偵測型和測試型：原題沒有要求防 prompt injection；草稿來自自己的 Planner，風險來源有限
  - 和 T2-9 的程式修改一起做，不單獨開工
- 狀態：依建議預設（你可改）

**T2-11 Task2 也要決策紀錄**
- 日期：2026-11-16
- 決定：
  - 建立本檔，補記這次對話 T2-1 到 T2-10
  - 之後每一輪對話都追加一條
  - 同步更新 artifact 頁面的「決策紀錄」區塊
- 狀態：已決定

**T2-12 Prompt injection 技術選型比較表**
- 日期：2026-11-16
- 依據：我的既有知識，這次沒有上網核對；標 ❓ 的是我不確定的項目
- 條件說明：
  - ① 免費、不用新帳號
  - ② 不用新增套件
  - ③ 不增加模型呼叫或推論
  - ④ 改動小（一天內改完）
  - ⑤ 在原題範圍內，不算過度工程
  - ⑥ 適合我們的情境（Auditor 讀的是自家 Planner 的草稿，不是外部網頁）

| 技術 | 類型 | ① | ② | ③ | ④ | ⑤ | ⑥ | 備註 |
|---|---|---|---|---|---|---|---|---|
| **Spotlighting** | 架構型 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 只改 prompt：用標記包住草稿 |
| Dual LLM | 架構型 | ✅ | ✅ | ✅ | — | ✅ | ✅ | 精神已做到：Auditor 沒有工具權限、放不放行由程式決定 |
| Instruction hierarchy | 模型訓練 | — | — | — | — | — | — | 由模型供應商訓練，我們不能選擇 |
| CaMeL | 架構型 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | 針對會呼叫工具的 Agent，要重寫流程 |
| Meta Prompt Guard | 偵測型 | ✅ | ❌ | ❌ | ❌ | ❌ | ⚠️ | 要下載模型並在本機推論；中文效果 ❓ |
| ProtectAI 分類器 | 偵測型 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | 偏英文 ❓ |
| Azure Prompt Shields | 偵測型 | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | 雲端付費服務 |
| Lakera Guard | 偵測型 | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | 雲端服務，要帳號 |
| NeMo Guardrails | 偵測型 | ✅ | ❌ | ❌ | ❌ | ❌ | ⚠️ | self check 會多一次 LLM 呼叫 |
| garak／PyRIT／promptfoo | 測試型 | ✅ | ❌ | ❌ | ❌ | ❌ | — | 用來攻擊測試，不是防禦本身 |

- 決定：選 Spotlighting。Dual LLM 的精神已經做到，不另外處理；其他候選至少有一項不符合
- 狀態：依建議預設（你可改）

**T2-13 目前架構文字圖**
- 日期：2026-11-16
- 內容：依 `graph.py`、`rules.py` 現況畫出 Start → Planning → Audit → Decision 與 6 種終態；標出 State 欄位、規則與 LLM 的合併方式，以及 Planner 目前只拿到上一輪意見
- 尚未實作的修改（T2-9、T2-10）沒有畫進去
- 狀態：說明（非決定）

**T2-14 模擬原題情境**
- 日期：2026-11-16
- 做法：`uv run python -m seo_agent.cli collaborate --out <scratchpad> --run-name ...`，fixture 模式（Planner、Auditor 是寫死規則的替身，不是真 LLM），3 次 exit 0，沒有寫入專案
- 結果：
  - A 預設（強制詞只在第 1 版）：第 2 稿 approved，4 次呼叫；最終標題「勝率與風險實話、出金速度實測的 3A娛樂城排行」
  - B 強制詞每輪都要：第 2 稿 conflict_unresolvable，Planner 宣告改不掉
  - C 強制詞改成「保證獲利」：跑滿 5 稿 max_iterations_reached；第 2 稿標題變成「沒有沒有沒有沒有保證獲利的真相的真相…」
- 發現：
  - C 實證 T2-9 必做 ①：建議文字本身含禁詞，加上替身逐條替換，同一字被重複替換，永遠不收斂
  - A 的「出金速度實測」「出金流程實測」是沒有做過的量測，對應 T2-9 的「建議誘導捏造」
- 狀態：說明（非決定）

**T2-15 fixture 能不能看出最終結果**
- 日期：2026-11-16
- 查到什麼：
  - fixture 的 Planner、Auditor 是照固定規則改稿的替身，只能驗證流程：會不會退回、何時停止、失敗會不會誠實回報
  - 驗證不了內容：真 LLM 會怎麼改、折衷版本好不好、每次結果會不會不同、語意誇大抓不抓得到
  - `reports/t2/` 現有 4 份結果（P1、P2）標題與 fixture 完全相同，可以判定都是 fixture，沒有真 LLM 的執行紀錄
- 建議：先修必做項目，再用 `--mode live` 以較省額度的模型跑 3 次，看得出趨勢就停
- 狀態：待你決定

**T2-16 依決定修改 Task2 程式**
- 日期：2026-11-16
- 你的決定：「按照目前決策出最好的架構去改」→ 做 T2-9 必做 ①–⑤ 與 T2-10 Spotlighting；選做項目不做
- 改了什麼（`src/seo_agent/content_review/`）：
  - ① `rules.py`、`agents.py`：建議文字與替換詞不含禁詞、不寫「實測」，也不含「風險」，避免普通段落被當成風險揭露段
  - ② `graph.py`：Planner 多收到 `rejection_history`（每一輪退件），prompt 要求不要把舊問題改回去
  - ③ `rules.py`：比對前先 NFKC 正規化、去空白標點，並加入簡體寫法；「穩 賺不賠」「稳赚不赔」「１００％」都抓得到
  - ④ `graph.py`：日誌的 verdict 只看 blocking，和 Decision 一致，另記 `blocking_count`
  - ⑤ `graph.py`：模型呼叫的未分類例外變成 `*_failed`；節點外例外變成新終態 `internal_error`，照樣寫 state_log
  - Spotlighting：Auditor 的草稿包在 `<<<DRAFT_DATA>>>` 標記內，JSON 裡的「<」轉義，草稿無法偽造結束標記
  - 版本：規則 `demo-ymyl-2026.11-v2`、prompt `t2-roles-v3`
- 驗證：
  - 新測試 `tests/test_t2_review_fixes.py` 14 個，舊程式上 13 個失敗（剩下 1 個是「乾淨文字不誤判」，新舊都應通過）
  - `uv run pytest -q`：363 passed、4 skipped，exit 0
  - 模擬重跑：A 第 2 稿通過；B conflict_unresolvable；C 第 2 稿通過，標題「獲利機率真相的 3A娛樂城排行」
- 限制：
  - 仍是 fixture，不是真 LLM；「必勝客」誤判沒修（選做）；R2、R3 仍只看標題關鍵字
  - `reports/t2`、`reports/gates/P1.json` 是舊版程式的證據，hash 不對應新程式；沒有 commit
- 狀態：已決定


**T2-17 實測要用 Task2 的資料**
- 日期：2026-11-16
- 你的意見：實測應該拿 Task2 裡面的資料
- 查到什麼：
  - 原題給的 Task2 資料有兩部分：情境（主題「娛樂城推薦」、強制詞「穩賺不賠」「保證出金」）與 Auditor 依據的「公司內部手冊（參考任務二數據）」
  - 情境部分：現有 fixture 與預設 CLI 參數已經用它
  - 手冊部分：`references/` 兩份需求檔都沒有附上，`project-requirements.md` 4.1 記為待向出題方取得；目前 Auditor 用的是標明 demo 的規則集
- 建議：有手冊就先轉成規則再實測；沒有就用原題情境＋demo 規則跑 live，只宣稱「符合 demo 規則」
- 狀態：待你決定

**T2-18 跑真 LLM 前的條件**
- 日期：2026-11-16
- 你的決定：沒有任務二數據，用原題情境＋demo 規則跑真 LLM（T2-17 第 2 條）
- 查到什麼：
  - `config/run_policy.json`：`external_calls_enabled=false`、`external_budget_usd=0`、`product_model_id=null`，所以 live 會回 blocked
  - 要開啟需要：`config/local.json`（已 gitignore）設定模型與額度，以及環境變數 `SEO_MODEL_BASE_URL`、`SEO_MODEL_API_KEY`、`SEO_MODEL_WORST_USD_PER_CALL`
  - 金鑰在 V2 的 `.env`；我嘗試讀取被權限分類器擋下，沒有讀到任何內容
  - 規則禁止我自行提高額度，所以先問你
- 狀態：待你決定

**T2-19 照 Task1 的方式跑 Task2**
- 日期：2026-11-16
- 你的意見：用 Opus；Task1 怎麼跑，Task2 就怎麼跑
- 查到什麼（V3 的 README、build-log、scripts，沒有讀任何金鑰檔）：
  - V3 前段用 V2 `.env` 的 API key 走 Anthropic Messages API；後段 API 額度用完
  - 後段經你同意，改用 Claude 訂閱的 `claude setup-token`，放在 `.env.subscription`，由 Hermes 的 Anthropic adapter 帶上 OAuth 需要的標頭；當時寫明「只限這次實驗」
  - Task2 的 live 走 OpenAI 相容 `/chat/completions` 格式，用不了訂閱 token
- 要做才能跑：①你同意把訂閱例外延伸到 Task2 ②加一個 Task2 adapter，重用已鎖定版本的 Hermes Anthropic 連線 ③執行時從 V3 的 `.env.subscription` 載入，不印出、不寫入紀錄
- 狀態：已決定（你同意延伸訂閱例外，見 T2-20）

**T2-20 Task2 用 Opus 實跑（原題情境＋demo 規則）**
- 日期：2026-11-16
- 你的決定：同意把訂閱例外延伸到 Task2（T2-19 改為已決定）
- 做了什麼：
  - 新增 `src/seo_agent/content_review/anthropic_model.py`，重用 vendor Hermes 的 Anthropic 連線；CLI 加 `--mode anthropic`（預設 `claude-opus-5-5`，逾時 180 秒，每次最多 12 次呼叫）
  - token 執行時從 V3 `.env.subscription` 載入，輸出裡掃描過沒有 token
  - 測試：`tests/test_t2_anthropic_adapter.py` 用假 client 離線測試（6 項）；完整回歸 368 passed、4 skipped
- 第一輪踩到的坑（已修）：
  - 輸出上限 4096 token 不夠，Opus 的大綱被截斷變成無效 JSON → 改成 16000，並在截斷時明確報錯
  - 10 秒連線逾時被當成「可能已送出」而停跑 → 連線沒建立就改為可安全重試
  - 失敗的兩次保留在 `reports/private/live-t2-opus/failed-v1-r2`、`failed-v1-r3`
- 結果（`reports/private/live-t2-opus/opus-r1..r3`，gitignore）：
  - 3 次都在第 2 稿 approved，每次 4 次呼叫，約 1.5–2.5 分鐘
  - 第 1 稿照規定放進強制詞，Auditor 退回 15–23 條（R1 為主；r1 另抓到 1 條規則表沒有的「無依據事實宣稱」）
  - 第 2 稿三次都沒有違規詞、沒有「實測」，都有年齡限制、法律風險、查證方法、風險揭露、FAQ；不排名、不捏造數據
  - 和 fixture 比：通過稿數一樣（第 2 稿），但 Opus 是整份重寫，fixture 只是換字
- 限制：只代表「符合 demo 規則」，不是真實法律合規；Planner、Auditor 同一個模型，只靠 prompt 分角色；用訂閱 token 違反「開發與產品憑證分開」，是你同意的例外
- 狀態：已完成

**T2-21 對原題逐條核對**
- 日期：2026-11-16
- 你的意見：拆解原題，逐條核對；把原文、拆解、核對結果條列放進 artifact
- 結果：9 項符合、3 項部分符合，沒有完全不符合
  - 部分符合：Auditor 依據（公司手冊沒拿到，用 demo 規則）、Mermaid 退回線沒標條件、推理品質（建議囉嗦、最終標題 38–55 字偏長，偏向合規）
- 建議補強：標題長度提醒 → Mermaid 邊標條件 → 合併重複建議 → 實跑結果放進正式交付物 → 拿公司手冊
- 狀態：核對已完成；補強待你決定

**T2-22 外部缺的資料不算我方缺陷**
- 日期：2026-11-16
- 你的意見：公司沒提供的資料不是你的問題；規則都做到就打勾，缺的部分另外框起來說明
- 改動：Agent B 那條改為 ✅ 符合，另框「外部條件：出題方未提供公司手冊，不是實作缺陷」；總結改為 10 項符合、2 項部分符合
- 沒改的：Mermaid 退回線沒標條件、建議囉嗦與標題偏長，這兩項是程式自己能補的，仍標部分符合
- 狀態：已完成

**T2-23 補 Mermaid 條件文字與推理品質**
- 日期：2026-11-16
- 你的意見：拓撲圖和推理品質這兩條應該能補完整
- 改動：
  - `graph.py`：條件邊改用有意義的名稱，Mermaid 直接顯示「草稿完成送審」「Planner 失敗或超出預算」「fail 帶修訂建議退回」「pass 或其他終態」
  - `rules.py`（規則版本 v3）：同一禁詞多處合併成一條；新增 `S1-title-length`，標題超過 32 字退回，標明是 SEO 底線、不是合規規則
  - `graph.py`：程式已在同位置抓到的同規則問題，略過模型重複的那條；模型多抓到的保留
  - `prompts.py`（t2-roles-v4）：Planner 標題 32 字內、保留誠實吸睛點；Auditor 同一問題只報一次
  - 測試新增 4 項；完整回歸 372 passed、4 skipped
- Opus 重跑 3 次（`reports/private/live-t2-opus-v2/`）：
  - 3 次 approved（2、3、2 稿），第 1 稿被退 2–3 條（原本 15–23 條）
  - 終稿標題 20–21 字（原本 38–55 字），例如「娛樂城推薦可信嗎？出金前先看這份查核清單」
  - r2 多一稿：第 2 稿寫了否定句「沒有必勝法」，規則連否定句也禁，第 3 稿改掉
  - 終稿都沒有違規詞；輸出掃描沒有 token
- 核對結果：12 項全部符合（手冊為外部條件，另框說明）
- 狀態：已完成

**T2-24 subagent 獨立審查**
- 日期：2026-11-16
- 你的意見：派 subagent 審查，不過度工程化、維持需求，直到沒問題
- 審查結果：approved，沒有 blocking；原題各點都對得上；憑證沒有外洩路徑
- minor 處理：
  - 已修：`--mode anthropic` 外層逾時 180 → 400 秒，明顯大於 SDK 各階段逾時，避免外層先逾時、重送已送出的請求
  - 已修：補「模型 finding 只有部分位置被程式涵蓋時要保留」的測試
  - 不修：模型重複判斷只比規則與位置（最多多花一輪，不會錯誤通過）；StubPlanner 不處理變體寫法（只在 fixture，真模型不受影響）
- 完整回歸：373 passed、4 skipped
- 狀態：已完成

**T2-25 Opus 實跑放進正式交付物**
- 日期：2026-11-16
- 你的決定：把 Opus 實跑結果換進正式交付物
- 做法：
  - 新增 `reports/t2/live-opus/`，內容：
    - r1–r3 的 state_log、result、final
    - `graph.mmd`
    - README，記錄來源、版本、命令、結果與限制
  - 原本的 fixture 版 `P1-*`、`P2-*` 不覆蓋，因為 `reports/gates/P1.json`、`P5.json` 以 hash 引用
  - 輸出檔掃描過，沒有憑證
- 限制：gate 報告與 traceability 還沒指向新資料夾；程式還沒 commit
- 狀態：已完成

**T2-26 交付紀錄接上並 commit**
- 日期：2026-11-16
- 你的決定：把追蹤表、gate 紀錄和 commit 一起做完
- 做法：
  - 需求追蹤表的 C22 維持 blocked，因為契約沒有設定產品模型，測試規定這種情況 live 不能標 passed
  - C22 附上契約外的實跑證據和 hash
  - 現況覆疊 `requirements-current.json` 記錄 Opus 結果
  - 歷史 gate P5.json 不重寫，沿用 Codex 的做法
  - 文件稽核抓到 `docs/t2-graph.mmd` 過期，已同步
  - README 補上 `--mode anthropic` 的命令
- 驗證：完整回歸 373 passed／4 skipped；文件稽核 41/41
- commit：`c1bcad8`
- 不 commit：另一個 Session 的 `docs/research/2030-*`
- 狀態：已完成

**T2-27 Task2 README：先放格式化題目**
- 日期：2026-11-16
- 你的意見：Task2 做完了，要一份 README；先把題目格式化填上去
- 改動：新增 `reports/t2/README.md`，題目四段（背景、要求 A／B／C、交付物、評核標準）照原文排版，角色、交付物、評核改成表格；文字未改寫
- 下一步：補實作說明、交付物對照、執行方式與限制
- 狀態：已完成（T2-28 補交付物）

**T2-28 README 填入四項交付物（用真實資料）**
- 日期：2026-11-16
- 你的意見：README 要放四大交付物，範例都用真實的
- 改動：`reports/t2/README.md` 新增「交付物」：
  - 資料全取自 Opus 實跑 `reports/t2/live-opus/`，r1–r3 結果表；示範用 r2（協商 3 輪最多）
  - 拓撲圖：原樣貼 `graph.mmd`，附節點／邊邏輯表
  - 狀態日誌：r2 三輪 Planner／Auditor／Decision 條列，引文取自 result.json，附 jsonl 原文兩行
  - 原始碼：`ReviewState` 原文、三層迭代限制（草稿上限、recursion_limit、模型呼叫上限）與程式片段
  - 最終產出：r2 final.md 大綱原文，加衝突點折衷表
- 驗證：相關測試 61 passed
- 狀態：已完成

**T2-29 README 交付物精簡**
- 日期：2026-11-16
- 你的意見：太亂、太複雜，精簡就好
- 改動：交付物段從約 230 行縮到約 80 行
  - 拓撲圖只留節點與條件邊（拿掉樣式設定）
  - 狀態日誌改成一張 3 輪表格
  - State Schema 只列關鍵欄位，迭代上限只留兩段程式
  - 最終產出只放標題、章節順序、3 條協商重點，完整內容改用連結
- 狀態：已完成

**T2-30 Planner prompt 先定義 SEO 目標、不預設台灣**
- 日期：2026-11-16
- 你的意見：內容不是在台灣推薦，台灣法律段無關；應在 prompt 一開始定義以 SEO 為目標
- 查到什麼：
  - `prompts.py` 沒提台灣，是 Opus 看到繁中自行假設
  - Planner 開頭是「兼顧點擊與證據、風險」，不是原題的「最大化點擊率」，所以第一稿就自我審查、偏合規
- 建議：Planner 首要目標改成最大化點擊率、合規交給 Auditor；不預設地區；版本升 t2-roles-v5；補測試後 Opus 重跑 3 次
- 限制：沒有真實平台資料，仍不能列具體推薦名單（會是捏造，也違反 R3）
- 狀態：待決定

**T2-31 Planner prompt v5 草稿**
- 日期：2026-11-16
- 你的問題：一開始會怎麼寫 SEO Planner 的 prompt
- 草稿重點（英文原文與繁中翻譯在對話中提供，尚未改程式）：
  - 第一句定義目標：最大化搜尋點擊率，符合搜尋意圖
  - 合規交給 Auditor，Planner 不先自我審查；被退時換成同樣吸引人的誠實說法，不直接刪
  - 不預設國家或地區，不引用特定國家法律
  - change_log 要寫保留了哪個吸睛點
  - 拿掉 v4 的「兼顧風險」與「先放風險段、年齡、評比方法」，交給 Auditor 規則退件
- 風險：第一稿被退條數與輪數可能增加，可能碰到 4 稿上限；需 Opus 重跑驗證
- 狀態：待決定

**T2-32 Planner prompt 依官方建議精簡（v5 精簡版草稿）**
- 日期：2026-11-17
- 你的意見：不要過度 prompt，越精簡越好，照 Anthropic／OpenAI 官方建議
- 依據的官方建議：角色與目標放第一句並說明原因；用正面說法寫要做什麼；不用全大寫或 NEVER 強調；資料與指示分開；輸出格式寫清楚；刪掉互相重複或交給別處處理的規則
- 草稿重點（英文原文與繁中翻譯在對話中提供，尚未改程式）：
  - 約 v4 一半長度，13 條規則併成 5 條
  - 刪掉：風險段、年齡限制、評比方法段（交給 Auditor R2／R3 退件）、標題「不能無聊」等重複說明、全大寫強調
  - 保留：JSON 格式、第一稿放強制詞、依 rule_id 修、不重犯舊問題、always 政策回報衝突、32 字、不捏造、防 injection
  - 新增：首要目標是點擊率；合規交給 Auditor；不預設國家
- 查到：測試沒有綁 Planner 字句，改 prompt 不必改既有測試
- 風險：第一稿會被退更多條，輪數可能增加；需 Opus 重跑 3 次確認仍在上限內通過
- 狀態：待決定（取代 T2-31 草稿）

**T2-33 補跑 C25 乾淨環境重現**
- 日期：2026-11-17
- 你的決定：把還沒做的部分做完，先不發布
- 第一次跑：失敗，368 passed、302 errors
  - 原因：同時間另一個 V3 Session 在家目錄建立了 `~/.hermes`，觸發測試的保護檢查
  - 用隔離的 HOME 在同一份 clone 重跑，368 passed，也沒有建立 `.hermes`，證實不是本專案程式造成的
- 正式重跑：用隔離的 HOME 跑 `clean_repro.sh`，結果 passed
  - 測試 368 passed／5 skipped
  - source hash 與主線相同
  - fixture completed、live blocked（B-LLM）
- 保留：第一次失敗的紀錄
- 不做：
  - 不清理 `~/.hermes`，因為它是使用者檔案
  - 不發布
- 狀態：已完成

**T2-34 Planner prompt 改成條列、每條明確定義**
- 日期：2026-11-17
- 你的意見：還不夠精簡；要條列式，而且精簡要明確定義
- 改法：整份改成「角色／目標／輸入／規則／輸出」五欄，每條規則一行、只寫一件事、有明確條件或數字；拿掉段落說明
- 狀態：待決定（取代 T2-32 草稿）

**T2-35 套用 v5 prompt，改用 Sonnet 實跑 3 次**
- 日期：2026-11-17
- 你的決定：照 T2-34 條列版改；實跑改用 Sonnet，不用 Opus
- 改動：`prompts.py` Planner 換成條列版，版本 `t2-roles-v5`；Task2 相關測試 66 passed
- 第一次（attempt1）：r1 被判 conflict_unresolvable。原因是 v5 沒定義 `unresolvable_constraints` 只能放什麼，Sonnet 把已移除的強制詞與待收集證據放進去；r2、r3 通過
- 修正：寫明 `unresolvable_constraints` 只放 always 政策下保留的強制詞，否則為 []；證據清單寫在 sections 內
- 重跑 3 次：全部 approved，草稿 3／2／2 份，第 1 稿被退 4–7 條；三份終稿都沒提台灣
- 輸出：`reports/t2/live-sonnet/`（attempt1 保留）
- 狀態：已完成；README 交付物仍引用 Opus v4 結果，是否改用 Sonnet v5 結果待決定

**T2-36 README 交付物改用 Sonnet v5 結果**
- 日期：2026-11-17
- 你的決定：好，README 改用 Sonnet 結果
- 改動：`reports/t2/README.md` 四項交付物改引用 `live-sonnet/r1`（協商 3 輪）；拓撲圖複製一份到 `live-sonnet/graph.mmd`（圖與模型無關）
- `live-opus/` 保留當對照
- 狀態：已完成

**T2-37 用評審 Agent 的角度檢查 Task2 並修正**
- 日期：2026-11-17
- 你的要求：用 Task1 同一套標準（clone 能不能跑、README 和程式一致、程式底子、工程習慣）看 Task2，並修好
- 發現並修正：
  - 乾淨 clone 第一步下載 Hermes 被 GitHub 回 429 → `tools/fetch_hermes.py` 加換來源與退避重試，失敗時提示 `--from-file`
  - 預設安裝沒裝 anthropic SDK，5 個連線測試被 skip → 安裝命令改加 `--extra anthropic`
  - Task2 README 沒寫怎麼跑、沒說明容錯 → 加「30 秒驗證」「容錯設計」「怎麼跑」
  - 程式註解滿是內部代號（T2-9、G1 F5、C23、R13）→ 改成白話說明
  - 函式內 import（graph.mermaid、httpx）→ 移到檔頭；Hermes 與 anthropic 保留延後 import（前者要先設 HERMES_HOME，後者是選裝）
  - 沒有 CI → 加 `.github/workflows/ci.yml`（下載 Hermes、裝環境、跑測試、Task2 冒煙）
- 沒動：測試檔名（gate 證據有引用）、根目錄 README（屬規格包、被 MANIFEST 凍結）
- 驗證：乾淨目錄重裝後 Task2 測試 66 passed、0 skipped；fixture 跑出 approved 與 conflict_unresolvable；主目錄完整回歸 373 passed、4 skipped；凍結契約 0 錯誤
- 狀態：已完成；Task2 交付物仍未 commit，評審 clone 看不到

**T2-38 在本機模擬 CI**
- 日期：2026-11-17
- 你的意見：CI 可以在這裡模擬跑
- 做法：本機沒有 Docker，改用乾淨副本（含 git、不含 vendor 與 .venv），從 `ci.yml` 讀出每步命令照順序執行
- 第一次 16 failed：模擬缺 `.git` 與已追蹤的 `reports/runs/`，屬模擬環境問題，不是 CI 檔問題；補齊後重跑
- 結果：4 步全過；測試 373 passed、4 skipped（都是需要付費憑證的 live 測試或已無未來階段）；冒煙 approved、conflict_unresolvable
- 限制：跑在 macOS 不是 Ubuntu；Hermes 真實下載在第一次模擬已驗證（130 秒），第二次沿用；GitHub 上的實際執行要 push 後才知道
- 狀態：已完成；仍待 commit

**T2-39 推送前檢查與修正（不推送）**
- 日期：2026-11-17
- 你的要求：先檢查檔案是否乾淨、必要、看得出工程底子，問題都修掉；中途改成先不推、不必重跑 CI
- 修正：
  - Sonnet 日誌的本機絕對路徑改相對路徑（Opus 重現日誌有 sha256 釘住，不動）
  - `graph.py` 5 處 except 內重拋改加 `from error`，保留錯誤來源；import 排序
  - Task2 測試註解拿掉內部代號；import 排序
  - `pyproject.toml` 加 ruff 設定（忽略 E501：中文訊息字串）；CI 加一步只檢查 Task2 程式與測試的 lint
- 驗證：ruff 0 錯誤；Task2 測試 66 passed；凍結契約 0 錯誤；lockfile 不變
- commit 時只放 Task2 相關檔案；`.claude/`、`docs/research/2030-*`、`agent-orchestration-survey.md` 不放
- 狀態：已完成；未 commit、未推送

**T2-40 Task2 README 重排**
- 日期：2026-11-17
- 你的要求：README 要有專案介紹、怎麼啟動，以及是否符合題目標準的視覺化呈現
- 改法（`reports/t2/README.md`）：
  - 開頭改成白話介紹：兩個 Agent 各做什麼、Decision 怎麼判斷，用「編輯與法務來回改稿」比喻
  - 「快速開始」移到前面：安裝、離線跑、拓撲圖、測試、真實模型 5 步
  - 新增「符合題目要求一覽」：交付物 4 項、評核標準 6 項，都附 ✅、做法、證據連結；加上實跑 3 次的結果表
  - 新增 r1 協商過程的 Mermaid 時序圖
  - 公司手冊缺口框起來，標明是外部條件、非實作缺陷
  - 題目原文收進可展開區塊，放在最後
- 驗證：README 內的相對連結都存在
- 狀態：已完成；未 commit、未推送

**T2-41 一鍵啟動腳本**
- 日期：2026-11-17
- 你的要求：一個指令就把環境全部建好，會問 API key，然後直接跑
- 改法：
  - 新增根目錄 `start_task2.sh`：檢查 uv（缺就詢問安裝）→ 下載 Hermes → 依 lockfile 建環境 → 詢問 API key（不顯示、不存檔；Enter = 離線）→ 跑協商並印出大綱
  - 參數：`--offline`、`--test`；非互動環境自動離線
  - 輸出到 `t2-output/`，已加入 `.gitignore`
  - `reports/t2/README.md` 快速開始改成一個指令，手動步驟收進展開區塊；CI 加一步 `./start_task2.sh --offline`
- 驗證：macOS bash 3.2 下離線 exit 0；非互動自動離線；假 key 停在 `planner_failed` 且日誌不含 key；凍結契約 0 錯誤
- 狀態：已完成；未 commit、未推送

**T2-42 一鍵啟動改成跨作業系統、乾淨環境可跑**
- 日期：2026-11-17
- 你的要求：想像對方的環境是乾淨的，用最不會出問題、任何作業系統都能跑的方式安裝，看起來要專業
- 選擇：只依賴 uv（官方安裝腳本，三個系統都有；會自己下載 Python 3.12、依 `uv.lock` 裝固定版本）。Docker 本機沒有、無法驗證，所以不採用
- 改法：
  - 主程式 `start_task2.py`：只用標準函式庫，三系統共用；處理 Windows 的 `.venv\Scripts`、UTF-8 輸出；API key 用 getpass 不顯示、不存檔；失敗時給白話提示
  - 薄殼：`start_task2.sh`（macOS／Linux）、`start_task2.ps1`（Windows），缺 uv 就安裝，再交給主程式
  - CI 新增 Ubuntu、macOS、Windows 三系統的乾淨 runner，不預裝 uv 與 Python，直接跑 `--offline --test`
  - README 快速開始改成按作業系統一個指令
- 驗證（本機 macOS）：全新資料夾、隔離 HOME、空的 uv 快取，從零跑 `./start_task2.sh --offline --test`：自動下載 Python 3.12 與 Hermes、裝 89 個套件、Task2 測試 66 passed、協商 approved，exit 0，約 6 分鐘；HOME 沒有被寫入
- 未驗證：Linux、Windows 要推上 GitHub 後由 CI 跑才知道
- 狀態：已完成；未 commit、未推送

**T2-43 README 整理**
- 日期：2026-11-17
- 你的問題：一鍵啟動有寫進 README 嗎？README 整理乾淨了嗎
- 檢查結果：Task2 README 已寫一鍵啟動；有 3 處不乾淨，已修
  - 協商過程同時有時序圖和表格，內容重複：只留時序圖，放在「交付物細節 2」
  - 「CI 三系統都跑」寫得像已驗證：改成「已在 macOS 從零驗證；CI 設定三系統」
  - 手動步驟只適用 macOS／Linux：標明 Windows 路徑差異
- `docs/README.md` 的 T2 部分過時（只寫 macOS／Linux、沒提一鍵啟動）：安裝段開頭加一鍵啟動與 T2 README 連結，實跑命令改帶 `--model claude-sonnet-5-5`
- 沒動：根目錄 `README.md`（規格包說明、MANIFEST 凍結、Task1 共用）；`docs/README.md` 第 8 行的狀態摘要（Task1／Task2 共用、寫於 11-16，已過時）
- 狀態：已完成；未 commit、未推送

**T2-44 README 結構重整與啟動體驗**
- 日期：2026-11-17
- 你的問題：README 要怎麼拆或結構化，讓整份說明是最好的狀態
- 決定：不拆檔，單一 README 加目錄；評審不用到處點。順序改成「怎麼跑 → 怎麼運作 → 符合題目 → 交付物 → 容錯 → 常見問題 → 題目原文」
- README 改法：
  - 快速開始只留指令、會問什麼、跑完會看到什麼；腳本細節、其他參數、手動安裝收進折疊區
  - 新增：系統設計重點（禁詞由程式判定、退件歷史全部帶回、不會無限循環、草稿不當指令）、程式在哪一覽表、Planner 收到退件的實際紀錄（r1 第 1 稿退件 → 第 2 稿逐條回應）、實跑模型呼叫次數、常見問題 6 題
  - 刪除：換模型範例、與評核表重複的協商段落
- 程式配合改：
  - `fetch_hermes.py` 下載時顯示進度（知道大小就印百分比，不知道就每 20 MB 印一次）
  - `start_task2.sh`／`.ps1` 安裝 uv 前先詢問（CI 等非互動環境直接安裝），並且不修改 shell 設定檔與 PATH 設定
  - 輸入 key 時附上 API key 取得網址與「最多 12 次呼叫」
- 驗證：ruff 通過；Task2 測試 66 passed；凍結契約 0 錯誤；README 內部連結全部有效；乾淨環境（隔離 HOME、空的 uv 快取）從零跑 `./start_task2.sh --offline --test`：approved、退件 5 → 0、exit 0，約 5 分 25 秒；HOME 只多 uv 本體，shell 設定檔沒被修改
- 狀態：已完成；未 commit、未推送

**T2-45 獨立審查與互動測試**
- 日期：2026-11-17
- 你的問題：這個有獨立測試過、跑過都沒有問題了嗎？（同意補測；真實 key 改用 Mock 方式）
- 獨立審查（唯讀子代理）：第一輪 changes_requested（1 blocker、4 major、9 minor），全部修正後複查 approved，剩下的 4 個 minor 也已修
  - blocker：Windows 輸出被導向時中文會讓程式當掉 → 強制 UTF-8
  - major：README 沒揭露實跑用 setup-token 與 attempt1 為 2/3；API key 路徑沒證據 → 補離線測試並如實標明；容錯表把實跑逾時寫成 400 秒重試 → 改成 170 秒、可能已送達不重送；把 `responding_to` 寫成 Planner 行為 → 改成程式填入
  - minor：測試數 66 混入任務一測試 → 篩選改為 `(t2 or collab) and not c06`，共 61 個；終態 7 種；JSON 摘錄改回原文；手動指令改用 uv；sh 補 curl 與安裝失敗提示；範例輸出換成真實輸出
- 互動測試（expect 模擬終端機、隔離 HOME、空的 uv 快取）：
  - 安裝 uv 時回答 n：乾淨取消，exit 1，HOME 沒寫入
  - 回答 Y、加 --test、送假 API key：從零建好環境、測試通過、401 → planner_failed 並顯示白話提示，exit 1；畫面與輸出檔都沒有 key
- 驗證：ruff 通過；Task2 測試 61 passed；凍結契約 0 錯誤；README 連結有效
- 未驗證：真實 API key 實跑（目前實跑證據是 setup-token）；Windows、Linux 要推上 GitHub 後由 CI 跑
- Task1 一鍵啟動：框架可沿用，但要先確認另一個 Session 沒在改、至少離線從零跑一次；待你確認
- 狀態：已完成；未 commit、未推送

**T2-46 Task2 簡報＋兩次冷讀**
- 日期：2026-11-17
- 你的問題：參考另一個 Session 的 Task1 簡報做 Task2 簡報，兩題獨立、風格一致；再派一個沒有記憶、不能上網、只看截圖的 subagent，列出它所有的疑問來改進
- 做法：沿用 Task1 簡報引擎與配色，18 頁、5 章（題目、架構、打臉、實跑、交付）；數字全部取自真實紀錄（r1 退件 4 → 1 → 0、呼叫 6／4／4、耗時 71–90 秒）
- 第一次冷讀：找到事實錯誤「穩賺不賠 ×2」（實際各 1 條）；題目要交的時序圖、Final Output 不明顯 → 補時序圖頁與 Final Output 頁、State Schema 移進正文
- 第二次冷讀（乾淨眼睛）的主要疑問與改法：
  - 「兩個 AI」其實是同一模型、由程式放行 → 封面與第 3 頁就講明「程式說了算，合規優先」
  - 3/3 像改到通過為止 → 標題改成「修 prompt 後 3/3，第一批 2/3」，說明只改欄位定義、失敗紀錄保留
  - 行銷保留多少沒評估 → 列進「未證明」
  - 名詞與代號太多 → 第一次出現加白話說明（fixture、prompt 注入、uv、429、401、setup-token、Hermes）
  - 終態名稱、5 稿與 4 稿、4 稿與 12 次呼叫不一致 → 統一全名，寫明每稿 2 次 × 4 稿＋重試
  - 時序圖箭頭沒頭 → 隱藏頁同名 marker 造成，改用獨立 id
  - 其他：交付物改並列、模擬 A 不再用綠色、budget_exhausted 與逾時歸屬寫清楚、備用頁補到 6 項
- 不改：頁尾來源路徑保留（給被追問時翻查）
- 簡報：https://claude.ai/artifact/Gfr6BnFsBwx3zofowER8Jb（暫存檔，未放進 repo）
- 狀態：已完成；未 commit、未推送

**T2-47 簡報補上「軟規則」思考鏈與技術選型方法**
- 日期：2026-11-17
- 你的問題：記得做過開源技術比較表、分析哪個最適合；確認是 T2-8（合規能不能寫成規則）、T2-10（防禦技術）、T2-12（選型打勾表），認為這段基礎思路與選技術的過程很重要
- 改法（簡報第 7、8 頁）：
  - 第 7 頁標明「硬規則（看字面）交給程式，軟規則（看意思）交給 AI」，並接一句「語意交給 AI 就可能被草稿說服 → 下一頁怎麼防」，把兩頁串起來
  - 第 8 頁加上選擇方法：① 先分 3 類 ② 先定 6 個條件再看候選 ③ 逐格打勾 ④ 只選全過的、其他寫下為什麼不選；表格每列標出類型（架構、偵測、測試、訓練）
- 說明：Spotlighting 是 prompt 寫法，不是開源套件；比較表依模型既有知識整理，沒有上網核對
- 簡報：https://claude.ai/artifact/Gfr6BnFsBwx3zofowER8Jb（v2）
- 狀態：已完成；未 commit、未推送

**T2-48 Task2 需求與交付物總檢查**
- 日期：2026-11-17
- 你的問題：Task2 是不是都達到需求？該附的東西都有了嗎？
- 對照：原題第 2–4 節與 `project-requirements.md` 第三章，逐條對到 `reports/t2/README.md`
- 驗證（實際執行）：
  - Task2 測試（隔離 HOME）：61 passed，exit 0
  - `cli graph` 輸出和 `live-sonnet/graph.mmd` 完全一致
  - r1／r2／r3 的 result.json：都是 approved，退件 4→1→0、7→0、7→0，呼叫 6／4／4，和 README 一致
  - README 相對連結全部存在
- 發現並修正：簡報第 2 頁把交付物寫成「時序圖、State Schema、Maximum Iterations、Final Output」，和原題不符 → 改成原題的 Graph Visualization、State Logs、Source Code（State Schema＋Maximum Iterations）、Final Output
- 還沒做：Task2 的程式修改與交付檔（README、live-sonnet、啟動腳本、CI 設定、實跑日誌）都還沒進 git；依你的指示未 commit、未推送
- 狀態：已完成檢查

**T2-49 推上 GitHub 並加評估專用授權**
- 日期：2026-11-17
- 你的問題：評審 clone 後可能拿去商用卻不錄取，怎麼避免？但評審也可能需要 clone 下來測試
- 結論：技術上擋不了下載，也不該擋（原題要交 Source Code）；改用授權條款保護＋私人 repo＋限時唯讀開放
- 動作：
  - 建私人 repo `blacktea3250106/seo-harness-agent`，推送 `codex/complete-task1-task2`（Task2 commit `eb6024c`）
  - 新增 `LICENSE`：中英對照專有授權，只准評估目的（含 clone、執行、測試），禁止商用、整合、衍生、散布、拿去訓練 AI；90 天或評估結束自動終止並刪除複本；中華民國法律、臺北地院管轄；第三方套件依原授權
  - Task2 README 開頭加授權提示
- 限制：不是律師審過的文件；要更有保障，建議請律師過目，並在寄連結的 email 裡請對方回覆同意
- 狀態：已 commit、已推送
- 追記：推上後 CI 的離線測試有 1 個 Task1 測試失敗（`test_runs_do_not_share_hermes_state`）。原因：Linux runner 沒設 TMPDIR，Hermes 會把暫存改到 HERMES_HOME 底下。CI 補上 `TMPDIR` 後，4 個 job 全部通過（含 Windows 一鍵啟動）
