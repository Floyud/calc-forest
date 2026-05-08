# Knowledge Base Setup

## Goal

给“我的计算森林”准备一套 **可导入 Dify Knowledge** 的最小知识库源文档，用于后续正式版工作流中的检索节点。

## Suggested Knowledge Groups

### 1. 错因标签

来源建议：

- `docs/specs/04_error_taxonomy.md`

用途：

- 帮助检索节点理解 `E01-E11`
- 给 LLM 节点提供稳定术语表

### 2. 教材对齐引导

来源建议：

- `docs/specs/09_guidance_system.md`

用途：

- 标准模式下优先使用教材方法
- 探索/挑战模式下给出明确边界

### 3. 森林成长语气

来源建议：

- `docs/specs/08_forest_growth_system.md`

用途：

- 保持“低压力成长、无排名、教师可控”的品牌语气口径
- 不作为当前教师端主流程的核心知识源

### 4. 年级输入与适配

来源建议：

- `docs/specs/10_multimodal_input.md`

用途：

- 让后续 LLM 节点或 retrieval node 适配不同年级表达

## Current Ready-to-Import Files

本目录下已新增：

- `knowledge_sources/01_error_taxonomy_compact.md`
- `knowledge_sources/02_textbook_guidance_compact.md`
- `knowledge_sources/03_forest_growth_tone_compact.md`

这些文件是面向 Dify Knowledge 的轻量化版本，比直接导入整份 specs 更适合作为第一批知识库内容。
其中 `03_forest_growth_tone_compact.md` 应被视为可选语气层材料，而不是当前 MVP 主能力依据。

## Import Advice

### Chunking

- 建议使用较小 chunk
- 不要把整份大文档一次性塞进去
- 目标是让每个 chunk 只回答一个问题：
  - 一个错因解释
  - 一个引导原则
  - 一个森林语气原则

### Retrieval Query

建议正式版工作流使用：

```text
年级={{grade}} 错因={{primary_error_code}} 引导模式={{guidance_mode}}
```

### Metadata

后续如果在 Dify UI 中支持 metadata，可考虑加：

- `category=taxonomy`
- `category=guidance`
- `category=forest-tone`
- `grade=1-2 / 3-4 / 5-6`

## Current Limitation

当前本地环境还没有通过 API 完整创建和绑定知识库，因此这部分已经把 **知识源文档** 准备好，但尚未完成自动接入。

这也是正式版 V3 的主要补项之一。
