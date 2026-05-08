# Dify Workflow Checklist

## Goal

用一晚上先把“我的计算森林”的教师侧 Dify 工作流跑通，重点证明：

- 教师输入短题目后能得到结构化错因
- 系统会给出教材对齐的温和引导
- 系统会给出 3 到 5 分钟短练习
- 输出默认保留教师审核边界

## App Type

- 推荐：`Workflow`
- 产品名：`我的计算森林`
- 副标题：`教师主导的错因诊断与引导工作台`

## Input Variables

- `student_id`：可选
- `problem_text`：必填
- `correct_answer_text`：必填
- `student_answer_text`：必填
- `grade`：必填
- `guidance_mode`：可选，默认 `standard`

注意：当前 workflow 的 Start 输入使用 `text-input`，通过 API 调试运行时，像 `grade` 这样的字段也应先按字符串传入，例如 `"4"`。

## Host Access Note

- 当前这台 Linux Docker 环境下，Dify 容器访问宿主机 FastAPI 使用 `http://172.17.0.1:8000`
- `host.docker.internal` 在当前环境中不可直接解析
- 因此夜间版 DSL 已默认写入 `http://172.17.0.1:8000/api/dify/session-draft`

## HTTP Nodes

### 1. Diagnose

- Method: `POST`
- Path: `/api/diagnose`
- Body mapping:

```json
{
  "student_id": "{{student_id}}",
  "grade": {{grade}},
  "problem": "{{problem_text}}",
  "correct_answer": "{{correct_answer_text}}",
  "student_answer": "{{student_answer_text}}",
  "student_steps": []
}
```

### 2. Practice Recommend

- Method: `POST`
- Path: `/api/practice/recommend`
- Body mapping:

```json
{
  "error_code": "{{diagnose.primary_error.code}}",
  "grade": {{grade}},
  "guidance_mode": "{{guidance_mode}}"
}
```

### 3. Tree Species

- Method: `GET`
- Path: `/api/tree-species`
- 用途：可选成长语气配置，不作为教师主流程必需节点

### 4. Encouragements

- Method: `GET`
- Path: `/api/encouragements`
- 用途：保持低压力、教师可控的反馈语气

## LLM Nodes

### Teacher Summary

- 输入：诊断结果 + 练习结果
- 输出：教师可读摘要
- 原则：不改写 `primary_error.code`

### Student Guidance

- 输入：诊断结果 + 教材策略
- 输出：1 到 3 个引导问题 + 简短小结
- 原则：不直接给最终答案，不使用羞辱性表达

## Knowledge Base

优先导入：

- `docs/specs/04_error_taxonomy.md`
- `docs/specs/09_guidance_system.md`
- `docs/specs/10_multimodal_input.md`
- `docs/engineering/prompt_registry.md`
- `docs/specs/08_forest_growth_system.md`（仅作为品牌语气与后续扩展参考）

## First Demo Case

使用 `demo_input_402_178.json`。

预期：

- 主错因：`E03`
- 引导方式：`standard`
- 输出包含错因证据、教师摘要、短时练习
- 语气温和，不直接给答案

## Evidence To Save

- 工作流总览截图
- Diagnose 节点输入输出截图
- Practice 节点输入输出截图
- 最终回复截图
- 测试命令与结果截图

## Night-Build Shortcut

如果今晚优先追求“先跑通一套完整闭环”，可直接导入：

- `my_calc_forest_dify_night_build.yml`

这版工作流优先调用：

- `POST /api/dify/session-draft`

优点：

- 不依赖先配置大模型
- 能直接输出诊断、练习、教师摘要、学生引导，以及可选成长语气信息
- 适合今晚快速形成可演示版本

## Formal V2 Shortcut

如果要继续沿着“正式编排版”推进，可直接导入：

- `my_calc_forest_dify_formal_v2.yml`

这版已经验证通过：

- 多 HTTP 节点
- Code 节点组装请求与结果
- If-Else 分支
- 练习与可选成长语气配置的多源聚合

运行时建议直接使用：

- `scripts/run_draft_workflow.sh`

并传入：

- `APP_ID=5435fba0-0196-4cea-84ac-2405ff372818`
