# 技术栈与竞品格局

> 最后更新：2026-05-19 | 基于代码库实际状态
>
> 相关文档：`docs/engineering/architecture.md` · `docs/research/coze_dify_agent_platforms.md`

## 项目定位

"小学数学错因诊断教育 Agent"，基于题目、学生作答过程和最终答案，识别错误类型、生成个性化引导与巩固练习。

**实际技术路线：** FastAPI 核心服务 + Dify AI 编排 + Next.js 双端前端。Dify 负责 LLM 交互层（对话引导、批改评语、画像分析），FastAPI 负责所有核心业务逻辑。

## 实际技术栈

| 层级 | 实际选择 | 说明 |
|---|---|---|
| 后端框架 | FastAPI + Pydantic v2 | 13 个路由器，~75 个端点 |
| 数据库 | SQLite (aiosqlite) | 33 张表 + FTS5 全文搜索 |
| Python 环境 | conda `pyt0` | 所有 Python 命令使用该环境 |
| 前端框架 | **Next.js 15.5 (App Router) + React 19** | 教师端 + 学生端双布局 |
| 状态管理 | TanStack Query v5 | 服务端状态缓存 |
| 图表 | **ECharts 6.x** | 雷达图、热力图、趋势线 |
| UI 组件 | shadcn/ui + Tailwind CSS 4 | 原子化样式 |
| 动画 | Framer Motion | 页面过渡 + 树生长动画 |
| Agent 编排 | Dify Workflow (本地 + 云端) | 3 个 App，三级回退 |
| LLM | DeepSeek / GLM | 三级回退（官方→代理→智谱） |
| TTS | Edge-TTS | 语音引导 |
| OCR | PaddleOCR (本地) + 百度智能纠错 (API) | 作业拍照识别 |
| PDF | xelatex + weasyprint + Jinja2 | 作业 PDF + 学生报告 |
| 测试 | pytest / Vitest / Playwright | 341 / 73 / 6 |

## Dify 集成架构

三级回退：`Local Dify → Cloud Dify → DeepSeek 直连`

3 个 Dify App：
- 教师诊断助手
- 学生引导助手
- AI 批改画像助手

Dify 负责 LLM 交互（对话、评语、分析），FastAPI 负责规则诊断和数据管理。LLM 不判断算术对错。

## 核心能力地图

| 能力 | 实现方式 | 产物 |
|---|---|---|
| 题目解析 | 程序化生成 (problem_generator.py, 142KB) | 题干、答案、知识点、难度 |
| 错因诊断 | **纯规则引擎** (diagnosis.py, 34KB) | 错因编码、证据、置信度 |
| AI 增强 | LLM 评语 + 摘要 (dify_client.py) | 教师摘要、学生引导、逐题评语 |
| 巩固练习 | 按错因+难度生成 (problem_generator.py) | A/B/C 三级变式题 |
| 掌握度 | BKT 贝叶斯知识追踪 (mastery_service.py) | 每知识点掌握概率 |
| 画像分析 | LLM + 统计 (ai_profile_service) | 学生画像、班级画像 |

## 竞品与参考方向

| 类型 | 代表能力 | 可借鉴点 | 本项目差异 |
|---|---|---|---|
| 拍照搜题类产品 | 快速识别题目并给答案 | OCR、解题步骤展示 | 强调错因诊断和引导，不以秒出答案为目标 |
| AI 家教产品 | 多轮问答、个性化讲解 | 对话体验、学习计划 | 聚焦小学数学错因标签体系，范围更窄、更可评测 |
| 教师作业批改工具 | 批量批改、统计错题 | 班级维度分析 | 先做单题深度诊断，已扩展到班级报告 |
| 通用 Agent 平台 | 工具调用、知识库和工作流 | 快速搭建 | 沉淀教育专用 prompt、数据模型和评测集 |

## 技术风险

1. **错因误判**：规则引擎已覆盖 E-K01~E-K08，但更复杂的错因（如综合应用）仍需 LLM 辅助。结构化证据字段 + 教师审核门。
2. **年级适配**：已支持 1~6 年级，但低年级口算诊断规则未实现 (BI-017)。
3. **平台依赖**：Dify 本地部署为主，Cloud Dify 401 未修复。LLM 三级回退降低风险。
4. **OCR 准确率**：PaddleOCR + 百度智能纠错为基础实现，完整扫码批改流程未完成。

## 已完成里程碑

1. ✅ Demo 版：文本输入 + 规则诊断 + 引导 + 练习
2. ✅ 增强版：Dify Knowledge + 三级回退 LLM
3. ✅ 评测版：341 个 pytest 测试 + 真实感模拟
4. ✅ 展示版：5 幕演示脚本 + 竞赛材料
5. ✅ 学生端：仪表盘 + 练习 + 作业 + 测验
6. 🔄 完整 OCR：基础实现，完整流程待完成
