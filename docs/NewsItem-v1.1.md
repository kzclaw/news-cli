---
title: "NewsItem v1.1 Schema"
version: v1.1
type: schema-doc
project: news-cli
created: 2026-06-02
author: 戴大虾🍤
---

# NewsItem v1.1 Schema

> **项目**：newscli
> **版本**：v1.1（v1.0 → v1.1 schema 文档化）
> **状态**：✅ 已文档化

## 版本对比

| 版本 | 变更 |
|------|------|
| v1.0 | 9 字段统一 schema（source/module/title/url/time/summary/heat/author/extra）|
| v1.1 | **文档化字段约定**（heat 字符串 / time 行为）+ **预留 time_iso 字段约定** + heat 验证 |

**v1.1 不改 schema 字段名**（向后兼容），仅文档化字段语义 + 约定。

---

## 字段定义（9 字段 + 1 约定字段）

### source (str)
- **含义**：来源显示名（**大写**或品牌名）
- **示例**：`'GitHub'`, `'Hacker News'`, `'HuggingFace'`, `'ZAKER'`, `'V2EX'`, `'DEV.to'`, `'Lobsters'`, `'Reddit'`, `'Paul Graham Essays'`
- **调用方注意**：如需统一比较，**先 `source.lower()`**

### module (str)
- **含义**：来源内的子模块
- **示例**：`'trending'`, `'topstories'`, `'daily'`, `'hot'`, `'node:python'`

### title (str)
- **含义**：标题
- **示例**：`'Memory engine and app that is extremely fast, scalable'`
- **去重关键字段**：`_deduplicate` 用 `normalize_title()` 标准化后比对
- **normalize_title 算法**：lowercase + 去除标点 + strip()

### url (str)
- **含义**：原文链接
- **示例**：`'https://github.com/supermemoryai/supermemory'`
- **空字符串 `''`**：RSS preset 当前 bug，**不要**视为有效 URL
- **None**：极少数情况下不返回 URL

### time (str | null)
- **含义**：人类可读时间（**不保证机器可解析**）
- **v1.0 实测格式**（per source）：

| Source | time 实测值 | 格式类型 | 备注 |
|--------|-----------|---------|------|
| github:trending | `None` | 永远 None | trending 源本无时间 |
| hackernews:* | `'13m ago'` / `'2h ago'` | 相对时间 | 字符串，无 ISO |
| huggingface:* | `None` | 永远 None | daily/trending 列表无时间 |
| zaker:* | `'2026-06-01 23:22:29'` | 接近 ISO | 缺 T 和 Z 后缀 |
| v2ex:* | `'14h ago'` | 相对时间 | 字符串，无 ISO |
| devto:* | `'2026-06-01T14:31:53Z'` | ✅ 标准 ISO 8601 | |
| lobsters:* | `'2026-06-01T06:57:04Z'` | ✅ 标准 ISO 8601 | |
| rss:* | `null` | RSS preset 当前不解析 | v0.0 残缺 |

### time_iso (str | null)  ← v1.1 约定字段
- **含义**：ISO 8601 UTC 格式
- **v1.1 状态**：**当前几乎所有 source 未实现**，仅 Dev.to / Lobsters 实际有
- **未来约定**：HN/V2EX 应当在 fetcher 解析 published_at 后填到这里
- **调用方建议**：v1.1 调用方应**准备好 None**——`time_iso` 可能是 null
- **示例（v1.1 已有）**：`'2026-06-01T14:31:53Z'`

### summary (str | null)
- **含义**：摘要
- **空值处理**：如果 source API 没返回，**newscli 自动 enrich**（curl 拉原文 og:description / meta description）
- **enrich 行为**：用 `--no-enrich` 关闭

### heat (str | null)  ← v1.1 重点文档化
- **含义**：热度（不限定格式）
- **v1.1 真实类型是 `str` 而非 int**（重要！）

| Source | heat 实测值 | 解析方法 |
|--------|-----------|---------|
| github:trending | `'10,748 stars'` | 正则 `(\d+(?:,\d+)*)` + 去逗号 |
| hackernews:* | `'455 points'` | 正则 + 去 "points" |
| huggingface:daily | `'4 upvotes'` | 正则 + 去 "upvotes" |
| v2ex:* | (HN 风格数字) | 复用 HN 解析 |
| zaker:* | `'1.5w 阅读'` | 复杂（中英文混） |
| devto:* | `'11 reactions'` | 正则 |
| lobsters:* | 数字 | 复用 HN 解析 |
| rss:* | `null` | RSS preset 不解析 |

**重要：v1.1 引入 heat 验证**（详见后文 `validate.py` 章节）
- 数字藏在 `extra` 字段（`extra.stars`, `extra.descendants`, `extra.upvotes`）——优先用这些 int
- 当 `heat` 字符串解析失败时，**用 extra 兜底**
- 都失败时记 `schema_validation` 警告

### author (str | null)
- **含义**：作者
- **v1.1 真实是字符串，可能含尾随空格**（`'nesquena '`）
- **v1.1 约定**：调用方记得 `.strip()`

### extra (dict)
- **含义**：source-specific 扩展字段
- **v1.1 关键数字通常在这里**：
  - `extra.stars` (int) — GitHub stars
  - `extra.descendants` (int) — HN 评论数
  - `extra.upvotes` (int) — HF upvotes / Reddit score / Lobsters 投票
  - `extra.hn_id` / `extra.v2ex_id` — 平台内 ID
  - `extra.language` — 编程语言（GitHub）

**v1.1 调用方建议**：要排序/打分，**优先用 `extra` 里的 int**，不用 `heat` 字符串

---

## v1.1 验证规则

`validate.py` 模块在 v1.1 引入，**默认 warn + continue**，可选 `--strict` 硬失败。

| 验证项 | 规则 | 默认行为 | --strict |
|-------|------|---------|----------|
| heat 是字符串 | 不可 cast 到 int | warn, continue | hard fail |
| heat 可解析 | 用正则 `\d+(?:,\d+)*` 能提取数字 | 提取值 + continue | 失败时 hard fail |
| extra 兜底 | 找 `extra.stars/descendants/upvotes` | 找到就替代 heat 解析值 | - |
| time 不为 None（如果 source 应该有）| 跨源 cross-check | warn | hard fail |
| url 非空字符串 | url 必须是有效 URL 或 None | warn | hard fail |

**输出字段**（`validate.py` 加在 result）：
```json
{
  "ok": true,
  "schema": "NewsItem v1.1",
  "schema_validation": [
    "github:trending item 0: heat parse failed, used extra.stars=10748"
  ],
  ...
}
```

---

## v1.1 与 v1.0 兼容性

- ✅ **完全向后兼容**——字段名、类型都没变
- ✅ v1.0 调用方代码无需改动
- ✅ v1.1 新增的 `time_iso` 字段缺失时为 None，不影响 v1.0 解析
- ✅ v1.1 新增的 `schema_validation` 字段缺失时 v1.0 解析为 None

---

## 调用方最佳实践

```python
item = news_item_dict

# 1. 时间：优先用 ISO，没有就用人读的
when = item.get("time_iso") or item.get("time") or "时间未知"

# 2. 热度：优先用 extra 里的 int
if "extra" in item and "stars" in item["extra"]:
    heat_int = item["extra"]["stars"]
elif "extra" in item and "upvotes" in item["extra"]:
    heat_int = item["extra"]["upvotes"]
else:
    heat_int = parse_heat_string(item.get("heat") or "0")

# 3. URL：检查非空字符串
url = item.get("url") or None
if url == "":
    url = None  # RSS preset 残缺兼容

# 4. 校验结果
if result.get("schema_validation"):
    for warning in result["schema_validation"]:
        log_warning(warning)
```

---

## v1.1 变更日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-06-01 | v1.0 | 9 字段统一 schema |
| 2026-06-02 | v1.1 | 文档化字段约定 + heat 验证 + time_iso 预留 |

---

*Schema doc 创建于 2026-06-02 by 戴大虾🍤，依据 newscli v1.1 ORK 附录 C 实测输出*
