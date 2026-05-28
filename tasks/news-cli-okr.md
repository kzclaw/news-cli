# Task #2026-0528 — News CLI 构建

**状态**：✅ 完成 | **创建时间**：2026-05-28 19:02
**最后更新**：2026-05-28 20:08

---

## Objective（O）

**为 News Agent 构建模块化、可复用、可扩展的标准新闻源工具链**

> 画板 entry：`memory/multi-topic.md` — 🔥待决策/[News Agent 工具链构建]

---

## Key Results（KR）

> **判断标准**：KR 全部 checked = O 达成 → 🔍review → Kwokzit 确认 → ✅

- [x] **KR1**: [框架] sources/base.py 定义完整标准接口，所有 source 实现统一返回格式 `NewsItem` ✅ 2026-05-28
- [x] **KR2**: [GitHub] 接入 gitrends-api.vercel.app/trending，支持 language 过滤 ✅ 2026-05-28
- [x] **KR3**: [Hacker News] 接入 Firebase API（topstories + newest + ask + show + jobs 5个模块） ✅ 2026-05-28
- [x] **KR4**: [HuggingFace] 接入 huggingface.co/api/daily_papers + trending papers ✅ 2026-05-28
- [x] **KR5**: [ZAKER] 接入 skills.myzaker.com（hot + category + search 3个模块，3个 API） ✅ 2026-05-28
- [x] **KR6**: [V2EX] 接入 v2ex.com/api/topics/hot.json + latest + node 分流 ✅ 2026-05-28
- [x] **KR7**: [RSS] 通用 RSS fetcher，12个 presets（Ben's Bites / PG / Latent Space 等） ✅ 2026-05-28
- [x] **KR8**: [Reddit] Reddit JSON API（popular + hot + r/<subreddit>） ✅ 2026-05-28
- [x] **KR9**: [DEV.to] DEV.to public API（trending + latest + tag 过滤） ✅ 2026-05-28
- [x] **KR10**: [Lobsters] Lobsters JSON API（hottest + newest） ✅ 2026-05-28
- [x] **KR11**: [架构] aggregator.py 统一调度 + CLI 入口（--source/--params/--json/--modules） ✅ 2026-05-28
- [x] **KR12**: [安全] 所有 source 无 Playwright、无 SSL verify=False、无裸 except、所有请求带 timeout ✅ 2026-05-28
- [x] **KR13**: [schema] 所有 source 所有 module 输出统一 NewsItem v1.0 schema（9字段，None 保留在 JSON 中） ✅ 2026-05-28

---

## 参考项目（OKR 决策参考，非直接使用）

| 项目 | Stars | 核心参考 |
|------|------|---------|
| **TRENDRADAR** (SANSAN0) | 54k | 架构思路、source 标准接口设计 |
| **news-aggregator-skill** (cclank) | 1k | 28源 API 接入方式（已做安全审查） |

**审查结论**：两个参考项目扒 API 逻辑即可，不直接克隆使用；本项目重写实现。

---

## 学习仓库 OKR 追踪

| 仓库 | URL | 状态 | 关键收获 |
|------|-----|------|---------|
| **TRENDRADAR** | github.com/SANSAN0/TRENDRADAR | ✅ 分析完成 | source fetcher 模块化；fetch() 统一返回格式；RSS 支持方案 |
| **news-aggregator-skill** | github.com/cclank/news-aggregator-skill | ✅ 已审查 | 28源 API 接入逻辑；安全教训（SSL off/ReDoS/裸 except） |

---

## 完成摘要

### 已接入 9 个 source，25+ modules

| Source | Modules | API |
|--------|---------|-----|
| **Hacker News** | topstories / newest / ask / show / jobs | Firebase API |
| **GitHub** | trending（+ language 过滤） | gitrends-api |
| **HuggingFace** | daily / trending | HF API |
| **ZAKER** | hot / category / search | 3 个独立 API |
| **V2EX** | hot / latest / node:\<name\> | V2EX JSON API |
| **Reddit** | popular / hot / r/\<subreddit\> | Reddit JSON API |
| **DEV.to** | trending / latest（+ tag 过滤） | DEV.to API |
| **Lobsters** | hottest / newest | Lobsters JSON API |
| **RSS** | 12 presets + custom | html.parser |

### NewsItem v1.0 Schema（9字段统一输出）

```
source / module / title / url / time / summary / heat / author / extra
全部字段始终存在，null 值在 JSON 中保留，text 输出不显示 null
```

---

## 归档区块

| 归档时间 | 归档方式 | 画板同步 |
|---------|---------|---------|
| 2026-05-28 20:08 | ✅ 完成 | ✅ 已同步到多话题画板 |

**归档操作**：
1. ✅ 更新状态为 ✅ 完成
2. ✅ 填写归档区块
3. ✅ 多话题画板 entry 已打 ✅ 标记
---

## 待定事项

### 去重机制（KR14 — P2）
- **触发条件**：跨 source 聚合时（`--source all` 或多 source 并行）
- **去重标准**：标题相似度 ≥ 70%（字符串相似度算法，不依赖精确匹配）
- **实现位置**：`aggregator.py`，在 fetch 完成后、limit 全局截断前处理
- **去重粒度**：按 (normalized_title, domain) 组合判断
  - normalized_title = 小写 + 去除标点 + strip()
  - domain = urlparse(netloc)
- **原因**：当前 9 source 测试 0 重复，但 RSS preset（同一文章多平台）和 future 扩展需要预防
- **状态**：🔄 待开发

---

## 已完成追加（2026-05-28 21:10）

### --enrich 功能（方案 A：curl 并发，summary=null 时触发）
- **实现**：enrich.py + `--enrich` CLI flag，aggregator.fetch() 透传 enrich 参数
- **触发条件**：summary=null 的 item（null 时才拉，非 null 不覆盖）
- **并发数**：max_workers=8，8s timeout/subprocess
- **来源**：curl（绕过 Python requests TLS 超时问题）+ og:description / meta description 双提取 + HTML entity 清洗
- **验证**：
  - lenz.io → ✅ 拉取成功（Python requests 超时，curl 成功）
  - YouTube blog → ✅ 拉取成功（Python requests 超时，curl 成功）
  - 3 条 HN null → 3 条全部 enriched，真实摘要填充
  - GitHub 有 summary → enrich 不触发，不覆盖
- **commit**: bba4618

---

## Parser.py — 自然语言 DSL（已完成 2026-05-28 22:17）

- **模块**：`parser.py`，~130 行核心逻辑，纯字符串分词，无 AI
- **覆盖**：全部 9 sources、25+ modules、34/34 test cases 通过
- **功能**：get/list + multi-clause(&) + json/noenrich/keyword/language 等修饰词
- **commit**: f44613f

## Enrich.py — curl 并发摘要填充（已完成 2026-05-28 22:17）

- **模块**：`enrich.py`，concurrent ThreadPoolExecutor，8s timeout
- **触发条件**：summary=null 的 item（已有 summary 不覆盖）
- **数据源**：curl → og:description / meta description 双提取
- **验证**：lenz.io / YouTube blog / HN items 全成功
- **commit**: bba4618
