# Codex Session Protocol

## 每次开始前先确认

- 当前目标是 exploration、exploitation 还是 validation。
- 本次 session 是否允许修改文件。
- 要修改的文件范围。
- 是否需要使用 `pyt0` Python 环境：`/home/lyzhang/miniconda3/envs/pyt0`。
- 是否需要同步更新任务板或决策记录。
- 是否需要同步更新根目录 `Agent.md`。

## Exploration Session 规则

Exploration session 用来减少不确定性。

允许：

- 阅读项目文档和本地 `docs/source_materials/`。
- 搜索权威资料、平台文档、GitHub 项目。
- 写研究总结、对比表、风险清单。
- 做独立小实验并记录结果。

避免：

- 直接改核心产品代码。
- 在没有决策记录的情况下引入新框架。
- 把一次性验证脚本当成正式工程。

结束时必须回答：

- 本次解决了哪个未知问题。
- 推荐方案是什么。
- 还剩什么风险。
- 下一步 exploitation 任务是什么。

## Exploitation Session 规则

Exploitation session 用来交付明确产物。

允许：

- 创建或修改正式文档。
- 实现 API、规则引擎、测试、演示数据。
- 优化页面、脚本和比赛材料。
- 运行测试和验证命令。

要求：

- 开工前读根目录 `Agent.md`。
- 开工前读相关设计文档。
- 改动范围尽量小。
- 每个任务都要有验收标准。
- 结束前更新 `task_board.md`，必要时更新 `Agent.md`。

结束时必须回答：

- 改了哪些文件。
- 如何验证。
- 还有什么没有完成。

## Validation Session 规则

Validation session 用来做质量检查。

检查范围：

- 功能是否跑通。
- 诊断结果是否可解释。
- 生成内容是否需要教师审核。
- 数据是否脱敏。
- 文档是否互相矛盾。
- 是否符合《创AI》材料要求。

结束时必须给出：

- 通过项。
- 阻塞项。
- 建议修复任务。

## Session 命名建议

```text
EXPLORE-YYYYMMDD-topic
BUILD-YYYYMMDD-topic
VALIDATE-YYYYMMDD-topic
```

示例：

- `EXPLORE-20260501-dify-http-tool`
- `BUILD-20260501-diagnosis-api`
- `VALIDATE-20260501-competition-docs`
