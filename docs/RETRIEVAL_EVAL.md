# Golden Query Retrieval Evaluation

这份文档描述一种**面向回归**的检索效果检查方法：

- 选取一组代表性查询（golden queries）
- 为每个查询维护一个“期望答案集合”（expected URLs 或 expected domains）
- 每次代码变更后运行评测并打分，用于发现“检索效果是否下降”

> 说明：真实搜索引擎/网络环境会波动，因此建议把评测分成 **离线可复现** 与 **在线真实检索** 两层。

## 现状

仓库目前主要是：
- 功能/集成 smoke test（例如 `tests/test_comprehensive.py` 会把结果写到 JSON）
- 并发性能对比（例如 `tests/benchmark_concurrent.py`）

这些测试更偏向“功能是否能跑通”，**不包含**“预设答案集 + IR 指标打分”的回归评测门禁。

## 推荐做法：两层评测

### 1) 在线真实检索（更接近用户体验）

用途：监控真实效果，适合 nightly/手动跑。

特点：
- 依赖外网/API Key/代理
- 结果受搜索引擎波动影响
- 不建议作为强门禁（容易误报）

### 2) 离线可复现评测（适合作为 PR/CI 门禁）

用途：保证 merge/dedup/fusion/early-return 等逻辑变更不会导致“指标明显退化”。

做法：
- 将某次在线检索的结果保存为 JSON（或自己构造固定 fixture）
- 之后在 CI 中对这份固定结果打分

它不能覆盖“搜索引擎返回本身变差”，但能覆盖“我们自己的排序/融合策略退化”。

## 工具：`scripts/retrieval_eval.py`

该脚本支持：
- `--mode live`：对每个 case 运行 `SearchManager.search()` 然后评分
- `--mode offline`：从一个 results JSON 读取结果并评分（默认模式）

另外还支持两项“让质量改动可控”的能力：

- **Baseline 对比**：把本次评测报告与一个“基线报告”逐 case/逐指标对比，发现回归就失败退出
- **分桶统计**：按 `theme/language/intent/...` 等字段聚合，快速定位哪个类别变差

### Golden cases 文件格式

见示例：`eval/golden_cases.example.json`，以及可直接改造的模板：`eval/golden_cases.json`。

每个 case 主要字段：
- `id`：唯一标识
- `query`：检索关键词
- `k`：评测 cutoff（例如 10）
- `expected_urls`：期望命中的 URL（推荐）
- `expected_domains`：如果 URL 不稳定，改为域名级别（更稳）
- `thresholds`：最低阈值（可选）
  - `min_hit_at_k`（推荐）：Top-k 内至少命中一个期望 URL/domain（最稳、最适合“官方入口命中”）
  - `min_recall_at_k`
  - `min_mrr`
  - `min_ndcg`

你也可以加入组织/分组字段（运行器会忽略它们，但对维护很有用），例如：
- `theme`（documentation/deployment/security/recency…）
- `language`（zh/en/mixed）
- `difficulty`（easy/medium/hard）
- `intent`（navigational/howto/troubleshooting/informational/recency）
- `freshness`（static/semi-static/high）

#### Baseline 回归容忍度（可选）

当你启用 `--baseline` 时，脚本会比较当前报告与基线报告的差异。

默认策略是**不允许回归**（allowed drop = 0）。如果你希望对某个 case 允许轻微波动，可以在该 case 的 `thresholds` 里加入：

- `max_drop_hit_at_k`
- `max_drop_precision_at_k`
- `max_drop_recall_at_k`
- `max_drop_mrr`
- `max_drop_ndcg`

也支持同义键 `allow_drop_<metric>`。

### Offline results JSON 格式

脚本默认接受：
- `{ "<query>": [ {"title":..., "link":...}, ... ] }`
或
- `{ "<case_id>": [ ... ] }`

例如你可以直接使用 `output/llm_search_results.json` 这种结构（如果它是 query→results）。

## CI 集成建议

- PR/CI：用 offline 模式，固定 results JSON，设置阈值做门禁。
- Nightly：用 live 模式，产出报告（JSON），以“趋势监控”为主，报警阈值可更宽。

### 推荐的“baseline + offline gate”工作流

1) 在一次你认可的 commit 上生成离线报告（作为 baseline），例如放到：`eval/baselines/retrieval_eval_baseline.json`

2) PR/CI 里每次都跑 offline 评测并与 baseline 对比：

- 当 **case thresholds 失败** 或 **baseline 对比出现回归** 时退出码为 1
- 你可以通过 `--allow-drop-...` 或 per-case 的 `max_drop_...` 来放宽

### 分桶统计的用途

脚本会在报告中写入：

- `summary`：总体 case 数、失败数、均值指标
- `buckets`：按 `--bucket-by` 指定字段分桶（默认 `theme,language,intent`）

这能让你快速回答：

- “是不是中文查询整体退化了？”（bucket: language=zh）
- “是不是只有 navigational 没问题，但 informational 掉了？”（bucket: intent）
- “是不是 tritium_fuel_cycle 主题被某个 merge/dedup 改动影响了？”（bucket: theme）

## 常见坑与建议

- **URL 规范化**：脚本使用项目内 `canonicalize_url()` 去除 utm_* 等参数，减少噪声。
- **阈值不要太苛刻**：真实检索波动大；域名匹配通常更稳。
- **query 的代表性**：覆盖你的典型场景（中英文、技术/非技术、短 query/长 query）。
- **答案集维护成本**：建议每个 query 只维护 3~10 个“权威/稳定”的目标站点。
