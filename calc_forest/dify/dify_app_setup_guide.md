# Dify 应用配置指南

本指南按步骤说明如何在 Dify Cloud 中创建"我的计算森林"的 3 个 Dify 应用、配置知识库、获取 API Key 并接入 FastAPI 后端。

---

## 前置条件

- Dify Education 会员已激活（lyzhang204@gmail.com）
- DeepSeek 模型供应商已配置（Settings → Model Provider → DeepSeek）
- Embedding 模型已配置（推荐 text-embedding-3-small 或 DeepSeek embedding）
- FastAPI 后端运行在 `http://127.0.0.1:8000`

---

## 第一步：创建知识库

### 1.1 创建知识库

1. 进入 Dify Cloud → 知识（Knowledge）
2. 点击"创建知识库"
3. 名称：**我的计算森林知识库**
4. 索引方式：**高质量**（使用 embedding 向量）
5. Embedding 模型：选择已配置的 embedding 模型
6. 检索设置：
   - 搜索方式：**混合检索**（semantic + keyword）
   - TopK：**5**
   - Score 阈值：**不启用**

### 1.2 上传知识库文件

**方法 A：使用同步脚本（推荐）**

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/knowledge_base

# 安装依赖
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pip install requests

# 获取知识库 API Key：
# Dify Cloud → 知识 → 我的知识库 → 设置 → API 密钥 → 创建密钥

# 全量同步
/home/lyzhang/miniconda3/envs/pyt0/bin/python sync_to_dify.py \
  --api-key "dataset-YOUR_KEY_HERE" \
  --dataset-id "YOUR_DATASET_ID" \
  --full-sync
```

**方法 B：手动上传**

在 Dify 知识库界面上传以下 10 个 markdown 文件（拖拽上传）：

| 文件 | domain | 用途 |
|---|---|---|
| `01_error_taxonomy/error_taxonomy_detailed.md` | 错因分类 | E01-E11 定义、典型表现、教学策略 |
| `02_textbook_content/grade6_semester1_units.md` | 课本内容 | 六年级上册各单元法则、例题、错因映射 |
| `02_textbook_content/calculation_rules_summary.md` | 法则速查 | 所有计算法则的快速参考 |
| `03_teaching_strategies/guidance_system_full.md` | 教学策略 | 三种引导模式、四步引导法、按错因策略 |
| `04_classroom_management/class_error_analysis.md` | 班级管理 | 分层策略、作业流程、滚动复习 |
| `05_growth_system/forest_growth_system.md` | 成长体系 | 树种、阶段、情绪、鼓励语 |
| `06_grading_and_profile/ai_grading_philosophy.md` | 批改理念 | 评语模板、E01-E11 各错因评语 |
| `06_grading_and_profile/student_profiling_system.md` | 学生画像 | 四种原型、标签词库、成长叙事 |
| `07_curriculum_planning/20_week_plan.md` | 教学进度 | 20 周教学进度与计算训练对应 |
| `07_curriculum_planning/practice_generation_rules.md` | 出题规则 | A/B/C 难度标准、滚动复习机制 |

上传时选择分块设置：
- 分段标识符：`\n---\n` 或 `\n\n`
- 最大分块长度：800-1000 tokens
- 分块重叠：100-150 tokens

---

## 第二步：创建 3 个 Dify 应用

### 应用 1：学生引导助手（Chatflow）

**类型**：Chatflow（对话流）

**用途**：学生做错题后，AI 引导学生理解错误，不直接给答案

**创建步骤**：

1. 创建应用 → Chatflow → 名称：**学生引导助手**
2. 配置节点：

```
开始节点
  ↓
知识检索节点
  - 关联知识库：我的计算森林知识库
  - 查询变量：{{sys.query}}
  - TopK：5
  ↓
LLM 节点（DeepSeek chat）
  - System Prompt：

你是"我的计算森林"的学生引导助手。你的目标是帮助学生理解计算错误的原因，而不是直接告诉答案。

核心规则：
1. 先肯定学生已经做出的正确部分
2. 用问题引导学生思考，不直接给答案
3. 每次只纠正一个关键错误
4. 语言温暖、简短，适合小学生理解
5. 结尾给出一个同类练习题让学生尝试

引导四步法：
第一步：接纳与安抚 - "没关系，我们一起看看"
第二步：算理引导 - 指出关键步骤，用问题引导
第三步：总结方法 - 帮学生用自己的话总结
第四步：巩固练习 - 给一道同类题

根据检索到的知识库内容，选择适合的引导策略。如果检索到错因 E01-E11 的定义，使用对应的教学策略。

  - User Prompt：

学生信息：{{student_info}}
诊断结果：{{diagnosis}}
知识库参考：{{#context#}}

请给学生一段引导式反馈：

  ↓
回答节点
  - 输出 LLM 的回复
```

3. 发布应用（右上角"发布"按钮）
4. 获取 API Key：应用 → API 访问 → 创建密钥
5. 记录 API Key → 写入 `calc_forest/backend/.env` 的 `DIFY_WORKFLOW_GUIDANCE_KEY`

---

### 应用 2：教师诊断助手（Workflow）

**类型**：Workflow（工作流）

**用途**：教师提交学生答案后，AI 生成诊断摘要和教学建议

**创建步骤**：

1. 创建应用 → Workflow → 名称：**教师诊断助手**
2. 配置节点：

```
开始节点
  输入变量：
  - diagnosis: string（规则引擎的诊断结果 JSON）
  - student_info: string（学生基本信息）
  - session_history: string（会话历史，可选）
  ↓
知识检索节点
  - 关联知识库：我的计算森林知识库
  - 查询：从 diagnosis 中提取错因代码作为查询
  - TopK：3
  ↓
LLM 节点（DeepSeek chat）
  - System Prompt：

你是一位教学分析助手，帮助教师快速了解学生错误模式。

核心规则：
1. 用客观语言描述证据
2. 区分本次错误和长期能力判断，不要过度推断
3. 给出下一步教学建议
4. 引用知识库中的教学策略

输出 JSON：
{
  "teacher_summary": "教师可读的诊断摘要",
  "observed_evidence": ["观察到的证据1", "证据2"],
  "recommended_intervention": "推荐的教学干预",
  "risk_note": "风险提示（可选）"
}

  - User Prompt：

诊断数据：{{diagnosis}}
学生信息：{{student_info}}
会话历史：{{session_history}}
知识库参考：{{#context#}}

请生成教师诊断摘要。

  ↓
结束节点
  输出变量：LLM 的 JSON 输出
```

3. 发布应用
4. 获取 API Key → 写入 `calc_forest/backend/.env` 的 `DIFY_WORKFLOW_SUMMARY_KEY`

---

### 应用 3：AI 批改+画像助手（Workflow）

**类型**：Workflow（工作流）

**用途**：批改作业后，AI 分析错误模式并生成学习画像

**创建步骤**：

1. 创建应用 → Workflow → 名称：**AI 批改画像助手**
2. 配置节点：

```
开始节点
  输入变量：
  - grading_results: string（批改结果 JSON）
  - student_info: string（学生信息）
  - error_stats: string（错因统计）
  - accuracy_trend: string（正确率趋势）
  - mode: string（grading / profiling）
  ↓
条件判断节点
  条件：mode == "grading" → 走批改路径
         mode == "profiling" → 走画像路径
  ↓
[批改路径]
知识检索 → LLM（批改分析）→ 输出

[画像路径]
知识检索 → LLM（画像生成）→ 输出
```

3. 批改 LLM 节点 Prompt：

```
你是一位小学数学批改助手。
根据规则引擎的批改结果，补充分析学生的错误模式和原因。

核心规则：
1. 归纳本份作业中反复出现的错误模式
2. 判断是概念性错误还是计算习惯问题
3. 给出针对性建议
4. 使用知识库中的评语模板和教学策略

输出 JSON：
{
  "pattern_summary": "错误模式归纳",
  "error_type": "conceptual|habitual|mixed",
  "suggestion": "针对性建议",
  "priority": "high|medium|low",
  "comments": [
    {"problem": "题目", "comment": "评语"}
  ]
}
```

4. 画像 LLM 节点 Prompt：

```
你是一位学习分析助手，根据学生的历史做题数据生成学习画像。

核心规则：
1. 客观分析，不贴负面标签
2. 关注可改进行动
3. 使用正面标签词库（如"稳步进步中""勇于尝试"）
4. 生成成长叙事（正确率变化 + 关键改变 + 下一步目标）

输出 JSON：
{
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["需关注1"],
  "focus_areas": ["重点1"],
  "suggested_actions": ["建议1", "建议2"],
  "personality_tags": ["标签1", "标签2"],
  "growth_narrative": "成长叙事（2-3句）",
  "recommended_level": "A|B|C"
}
```

5. 发布应用
6. 获取 API Key → 写入 `calc_forest/backend/.env` 的 `DIFY_WORKFLOW_GRADING_KEY`

---

## 第三步：配置 FastAPI 后端

### 3.1 更新 .env

在 `calc_forest/backend/.env` 中添加：

```env
# Dify 配置
DIFY_ENABLED=true
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_API_KEY=app-YOUR_DEFAULT_KEY

# 各 workflow 的 API Key
DIFY_WORKFLOW_GUIDANCE_KEY=app-YOUR_GUIDANCE_KEY
DIFY_WORKFLOW_SUMMARY_KEY=app-YOUR_SUMMARY_KEY
DIFY_WORKFLOW_GRADING_KEY=app-YOUR_GRADING_KEY
DIFY_WORKFLOW_PROFILE_KEY=app-YOUR_PROFILE_KEY
```

### 3.2 验证连接

```bash
# 启动后端
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/backend
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 检查 Dify 状态
curl http://127.0.0.1:8000/api/config/dify-status
```

预期输出：
```json
{
  "enabled": true,
  "base_url": "https://api.dify.ai/v1",
  "api_key_set": true,
  "workflows_configured": ["student_guidance", "teacher_summary", "ai_grading", "ai_profile", "problem_generation"]
}
```

### 3.3 测试端到端流程

```bash
# 测试完整作业生命周期（生成→模拟→批改→画像）
curl -X POST http://127.0.0.1:8000/api/homework/lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": "G6C1",
    "error_codes": ["E01", "E06"],
    "difficulty": "B",
    "count": 5
  }'
```

---

## 第四步：知识库更新流程

知识库内容有更新时：

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/knowledge_base

# 增量同步（只上传新文件）
/home/lyzhang/miniconda3/envs/pyt0/bin/python sync_to_dify.py \
  --api-key "dataset-YOUR_KEY" \
  --dataset-id "YOUR_ID"

# 全量同步（删除旧版，重新上传所有文件）
/home/lyzhang/miniconda3/envs/pyt0/bin/python sync_to_dify.py \
  --api-key "dataset-YOUR_KEY" \
  --dataset-id "YOUR_ID" \
  --full-sync
```

---

## 注意事项

1. **Workflow 必须发布**：Dify 的 API 只能调用已发布的 workflow，草稿状态不可用
2. **超时处理**：Dify Cloud 有 100s Cloudflare 超时，长任务考虑用 streaming 模式
3. **回退机制**：`dify_client.py` 内置了 DeepSeek 直连回退，Dify 不可用时自动切换
4. **教师审核**：所有 AI 输出都标记 `pending_teacher_review`，教师确认后才生效
5. **版本兼容**：DSL 导入时确保 Dify 版本一致，大版本差异可能导致兼容问题
