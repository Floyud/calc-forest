# Formal Workflow Design

## Goal

把夜间版的单接口闭环，升级成 **更接近正式产品编排方式** 的 Dify 工作流，同时保证：

- 今晚仍然能跑通
- 节点责任清楚
- 以后可以继续拆成 LLM + Knowledge Retrieval 版本
- 后续接手的人能快速理解这版是怎么搭出来的

## Why V2 Exists

夜间版 `my_calc_forest_dify_night_build.yml` 已经证明：

- Dify 本地可启动
- DSL 可导入
- Workflow draft run 可跑通
- FastAPI 工具链可被 Dify 调用

但夜间版有一个明显限制：

- 它把诊断、练习、教师摘要、学生引导、树种和鼓励语都压进了 `POST /api/dify/session-draft`

这适合“先跑通”，但不适合后续正式产品迭代。因此需要第二版：

- 把诊断、练习、分支逻辑、结果组装拆成多个节点
- 保留可运行性
- 为后续引入 LLM 与 Knowledge Retrieval 留清晰插槽

## V2 Scope

V2 仍然优先保证 **可运行**，所以采用：

- `HTTP Request` 节点
- `Code` 节点
- `If-Else` 节点
- `End` 节点

V2 暂不强依赖：

- Dify 内部模型 provider
- Dify builtin `json_parse` plugin
- 已创建的数据集 ID

原因：这些依赖在本地环境里都可能成为阻塞点，而我们今晚的目标是“先把正式编排骨架跑起来”。

## V2 Graph

```text
Start
  -> Build Diagnose Request (Code)
  -> Diagnose HTTP (/api/diagnose)
  -> Parse Diagnosis (Code)
  -> If confidence route

If high_confidence:
  -> Build Practice Request (Code)
  -> Practice HTTP (/api/practice/recommend)
  -> Optional Tone Config
  -> Assemble High Confidence Result (Code)
  -> End High

Else:
  -> Assemble Clarify Result (Code)
  -> End Low
```

## Node Responsibilities

### 1. Start

收集输入：

- `student_id`
- `grade`
- `problem_text`
- `correct_answer_text`
- `student_answer_text`
- `student_steps_text`
- `guidance_mode`
- `tree_species_id`

### 2. Build Diagnose Request

作用：

- 把 Start 输入规范化成稳定 JSON
- 避免 Dify HTTP JSON body 在字符串/数字混合时出现奇怪修复行为

### 3. Diagnose HTTP

调用：

- `POST /api/diagnose`

作用：

- 取得结构化主错因、次错因、证据和教师摘要

### 4. Parse Diagnosis

作用：

- 把 HTTP body JSON 转回工作流可用变量
- 提取 `primary_error_code`
- 提取 `confidence`
- 生成路由字段 `route`

当前路由规则：

- `confidence >= 0.65` -> `high_confidence`
- 其他 -> `low_confidence`

### 5. If Confidence Route

作用：

- 在“已有较稳定诊断”与“更适合先追问/保守输出”之间分支

### 6. Build Practice Request

作用：

- 根据 `primary_error_code`、`grade`、`guidance_mode` 构造短练习请求

### 7. Practice HTTP

调用：

- `POST /api/practice/recommend`

作用：

- 返回 3 到 5 分钟短练习建议

### 8. Optional Tone Config

调用：

- 可选读取 `GET /api/tree-species`
- 可选读取 `GET /api/encouragements`

作用：

- 仅为品牌化表达保留轻量语气配置
- 不再把树种和鼓励语当作教师端主流程的关键节点

### 9. Assemble High Confidence Result

作用：

- 合并诊断、练习，以及可选的成长语气配置
- 输出一个教师侧可读、学生侧温和的结构

### 10. Assemble Clarify Result

作用：

- 当置信度不足时，不急着给练习主线
- 返回一个更保守的“先追问/先补步骤”草案

## Why Code Nodes Are Used So Much

这不是因为 Dify 不够强，而是因为当前环境要先保证：

1. 不依赖未配置的模型 provider
2. 不依赖额外 plugin
3. 不被 JSON body 和插件可用性卡住

所以 V2 采用的策略是：

- 让 `HTTP Request` 负责调用真实业务能力
- 让 `Code` 节点承担“格式整理、变量转换、分支路由、最终组装”

这是一种 **工程上更稳的正式编排过渡版**。

## Planned V3 Upgrade

等本地 Dify provider 和 Knowledge Base 都就位后，V3 会继续拆成：

```text
Start
  -> Diagnose HTTP
  -> Parse Diagnosis
  -> If confidence
  -> Knowledge Retrieval
  -> LLM Teacher Summary
  -> LLM Student Guidance
  -> Practice HTTP
  -> Optional Tone Config
  -> End
```

V3 新增价值：

- 知识库检索教材方法
- LLM 用年级化语言润色教师摘要
- LLM 用教材优先原则生成学生引导
- 条件分支更细，比如 `standard/exploration/challenge`

## Current Constraints

1. 当前本地 Dify 尚未配置稳定可用的模型 provider。
2. 当前本地 Dify 的 builtin `json_parse` plugin 不可直接依赖。
3. 当前还没有通过 API 自动创建 Knowledge Base 并绑定到工作流。

因此：

- V2 先保证正式编排骨架可运行
- V3 再把 LLM 和 Knowledge Retrieval 接上

## Runtime Note

当前 Linux Docker 环境中，Dify 容器访问宿主机 FastAPI 使用：

- `http://172.17.0.1:8000`

不要直接使用：

- `host.docker.internal`

因为当前环境里它不能解析。
