# 知识库 Chunk 格式规范 v2.0

> 本文件定义知识库所有 chunk 文件的统一格式。所有 chunk 必须遵循此规范。

## 设计原则

1. **一个 chunk = 一个原子知识点**：每个文件只讲一个完整、独立的知识单元
2. **机器优先**：YAML frontmatter 提供结构化元数据，正文使用固定层级标题便于正则解析
3. **可检索性**：每个 chunk 必须包含 grade、topic、tags 字段，供向量检索和过滤
4. **自包含**：chunk 内引用错因代码时简写为 E01-E11，详细定义见 00_shared/error_codes.md

## 文件命名规范

```
G{grade}_{semester}_{topic}_{subtopic}.md
```

- grade: 1-6
- semester: 上/下
- topic: 2位数字序号 + 主题名（如 01_整数加减法）
- subtopic: 具体知识点（如 进位加法）

示例：`G3_上_01_万以内加减法_进位加法.md`

## YAML Frontmatter 字段

```yaml
---
id: "G3-UP-01-01"          # 唯一ID: G{grade}-{semester}-{topic_seq}-{chunk_seq}
grade: 3                    # 年级 1-6
semester: "上"              # 上/下
topic: "万以内加减法"       # 主题
subtopic: "进位加法"        # 子主题
question_types:             # 涉及的题型
  - "整数加法"
  - "竖式计算"
difficulty: "A"             # A(基础)/B(提升)/C(挑战)
error_codes: ["E02"]       # 关联的错因代码
tags: ["加法", "进位", "竖式", "三位数"]  # 检索标签
textbook_ref: "人教版三年级上册 第二单元"  # 教材出处
---
```

## 正文结构（固定层级）

```markdown
# {topic} — {subtopic}

## 计算法则
（规则、公式、步骤，用编号列表）

## 典型例题
（每道例题格式：题目 → 解题过程 → 答案）

## 常见错误
（每条格式：错误类型代码 | 错误描述 | 错误示例 | 正确做法）

## 检测规则
（机器可用的判定逻辑，伪代码或自然语言规则）

## 教学提示
（简短的教学建议，1-3条）
```

## 质量要求

- 每个 chunk 正文 200-500 字（不含 frontmatter）
- 例题至少 2 道，覆盖该知识点的主要变式
- 常见错误至少 1 条，必须关联 error_codes 中的代码
- 检测规则必须可被程序解析（不能是模糊描述）
