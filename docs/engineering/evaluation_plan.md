# 评测方案

> 最后更新：2026-05-19 | 基于代码库实际状态
>
> 相关文档：`docs/engineering/architecture.md` · `AGENTS.md`（测试命令）

## 测试层级

| 层级 | 框架 | 数量 | 命令 |
|---|---|---|---|
| 后端单元测试 | pytest | 341 passed / 9 pre-existing | `pytest -s tests/ -q` |
| 前端单元测试 | Vitest | 73 | `npm run test` |
| E2E 测试 | Playwright | 6 | `npx playwright test` |
| Dify E2E | pytest | 3 | `pytest tests/test_dify_e2e.py` |

## 后端测试命令

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/backend

# 全部测试（排除 E2E 和全管道）
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/ -q \
  --ignore=tests/test_e2e_smoke.py \
  --ignore=tests/test_dify_e2e.py \
  -k "not full_pipeline"

# 仅诊断测试
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_diagnosis.py -q

# E2E 测试
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_e2e_smoke.py -q

# Dify E2E
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_dify_e2e.py -q
```

## 前端测试命令

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/web
npm run test
```

## 测试覆盖范围

### 诊断引擎 (`test_diagnosis.py`)

- 正确答案 → OK
- 进位错误 → E02
- 退位错误 → E03
- 运算顺序错误 → E05
- 基础事实错误 → E01
- 数位对齐错误 → E04
- 抄题/转写错误 → E07
- 步骤遗漏 → E08
- 未验算 → E11
- 括号混合运算
- 两位数乘法部分积

### API 端点

- `/health` 响应格式
- `/api/diagnose` 请求/响应 + `pending_teacher_review`
- `/api/practice/recommend` 练习推荐
- `/api/tree-species` 树种配置
- `/api/encouragements` 鼓励语配置
- `/api/dify/session-draft` 会话草稿

### 前端组件

- 组件渲染测试
- API 客户端 mock 测试
- 类型检查

## 模拟数据

```text
calc_forest/backend/data/demo_answer_records.json
```

- 24 条合成记录
- 5 个匿名学生: S001-S005
- 年级覆盖: 3-6
- 主诊断匹配: 22/24

### 真实感模拟

```bash
/home/lyzhang/miniconda3/envs/pyt0/bin/python scripts/simulate_realistic.py
```

- 10 个学生 × 3 层级 × 8 周
- 218 作业 / 506 提交 / 2111 答题
- 自适应难度 + E01-E11 错因模拟

## 已知问题

1. 9 个 pre-existing failures（非回归）
2. 混合运算括号诊断需增强 (BI-011)
3. 两位数乘法部分积对齐需增强 (BI-012)
4. 一二年级口算诊断规则未实现 (BI-017)

## 验收标准

- 后端测试 341+ passed
- 前端构建无错误 (`npx next build --no-lint`)
- 类型检查通过 (`npx tsc --noEmit`)
- 所有 AI 输出带 `pending_teacher_review`
- 算术对错只用规则引擎，不用 LLM
