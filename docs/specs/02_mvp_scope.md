# MVP Scope

> 最后更新：2026-05-19 | 基于代码库实际状态
>
> 相关文档：`docs/engineering/architecture.md` · `docs/specs/01_prd.md` · `docs/specs/04_error_taxonomy.md`

## In Scope（已实现）

### 后端核心

- FastAPI 后端，13 个路由器，~75 个 API 端点 (`calc_forest/backend/app/`)
- SQLite 数据库，33 张表 + 1 个 FTS5 虚拟表
- 纯规则诊断引擎（regex + ast/operator），覆盖 E-K01~E-K23 + E-H01~E-H21
- 程序化题目生成器（142KB），A/B/C 三级难度，无限供应
- 批改管道（pipeline/），11 个节点模块
- 数据访问层（repositories/），3 个仓库模块

### 作业全生命周期

- 生成 → 布置 → 提交 → 批改 → PDF → 分析
- AI 批改（LLM 增强）+ 逐题评语
- 班级批量流水线
- 作业生命周期管理（全流程/单步）

### 学生端基础功能

- 学生登录 + 仪表盘
- 自主练习会话（start → next → answer → end）
- 作业查看 + 提交
- 课堂测验
- 扫码批改（OCR，端点已定义，部分实现）

### 教师端完整功能

- 班级森林可视化（含 Canvas 渲染器 + 粒子系统）
- 错因热力图 + 雷达图 + 趋势线
- 诊断演示 + Dify 聊天代理
- 引导对话（Edge-TTS 语音）
- 课表管理 + 自动布置作业
- 学生画像 + 掌握度（BKT）+ 轨迹
- 知识库搜索 + 知识图谱
- PDF 生成（xelatex + weasyprint）
- 学生报告 + 班级报告

### AI 集成

- Dify 三级回退：本地 → 云端 → DeepSeek 直连
- 3 个 Dify App（教师诊断、学生引导、AI批改画像）
- LLM 三级回退（DeepSeek/GLM）
- 本地模型服务（Embedding + Reranker）

### 认证

- 教师登录（手机号 + 密码）
- 学生登录（学号 + 密码）

### OCR

- PaddleOCR 本地识别
- 百度智能作业纠错 API

### 知识库

- 135+ 个中文 Markdown 文件
- 44 个错因类型（knowledge 23 + habitual 21）
- 1~6 年级知识点
- 题库（六年级上册 5 单元 × 3 难度）
- FTS5 全文搜索

## Out of Scope（未来）

- 完整 OCR 拍照批改（当前为基础实现）
- 家长端 App
- 完整知识图谱（当前为基础版）
- 语音输入（ASR 集成）
- 完整游戏化系统（无排名、无打卡、无家长压力）
- 多教材版本支持（当前仅人教版）
- 六年级以上内容
- 真实学生数据

## 当前证据

- **测试**: 341 passed / 9 pre-existing failures (pytest) + 73 (Vitest) + 6 (Playwright) + 3 (Dify E2E)
- **数据库**: 33 张表，覆盖完整作业闭环、诊断错因、课堂测验、学生成长、教学体系
- **API**: ~75 个端点，13 个路由器
- **前端**: 17 个页面（教师端 10 + 学生端 7），44 个组件
- **知识库**: 135+ 个文件，44 个错因类型，1~6 年级覆盖
- **Dify**: 3 个 App 已导入本地 Dify
- **模拟数据**: 真实感 8 周模拟（3 档学生、自适应难度、E01-E11 错因模拟器）

## Known Gaps

- 混合运算括号诊断和两位数乘法部分积对齐未覆盖 (BI-011, BI-012)
- 成长里程碑更新逻辑未实现 (BI-015)
- 4 步标准引导反馈未完成 (BI-016)
- 一二年级口算诊断规则未实现 (BI-017)
- Cloud Dify 3 个 API 返回 401（需从 DSL 重新导入）
- Local Dify Embedding 供应商连接验证失败
- OCR 扫码批改端点返回 501（未实现）
