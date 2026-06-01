# Acceptance Criteria

> 最后更新：2026-05-19
>
> 相关文档：`docs/specs/02_mvp_scope.md` · `docs/engineering/evaluation_plan.md`

## PM Acceptance

- MVP 包含教师端完整功能 + 学生端基础功能。
- 产品文档清晰区分已交付 MVP 和未来愿景。
- 所有 AI 输出带教师审核门 (`pending_teacher_review`)。
- 无排名、无打卡、无家长压力。
- 产品叙事体现"我的计算森林"品牌。
- 错因编码使用 E-K01~E-K23 + E-H01~E-H21 体系。

## Teacher Acceptance

- 教师无需读代码即可理解诊断结果。
- 每个结果解释系统选择该错因标签的原因。
- 建议的处理动作适合课堂短时反馈。
- 练习推荐遵循 3-5 分钟约束。

## Engineering Acceptance

- 后端测试 341+ passed (`pytest -s tests/ -q`)。
- 前端构建无错误 (`npx next build --no-lint`)。
- 类型检查通过 (`npx tsc --noEmit`)。
- API 返回结构化响应（~75 个端点）。
- 合成数据验证无缺失字段。
- 运行命令使用 `pyt0` 环境。

## Competition Acceptance

- 材料能展示 AI 辅助开发证据。
- 材料能展示代码、Prompt/工作流设计、测试、合成案例。
- AI 生成内容标注为待教师审核。
- 无真实学生面部或敏感数据。

## 验证命令

```bash
# 后端测试
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/backend
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/ -q \
  --ignore=tests/test_e2e_smoke.py \
  --ignore=tests/test_dify_e2e.py \
  -k "not full_pipeline"

# 前端构建
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/web
npx next build --no-lint

# 类型检查
npx tsc --noEmit
```
