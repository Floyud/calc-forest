<div align="center">

<img src="docs/images/cover.png" alt="我的计算森林" width="100%">

<br/>

<h1>🌲 我的计算森林</h1>

**✨ AI 批阅，教师把关 ✨** — 小学数学智能错因诊断与自适应练习系统

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15.5-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 🤔 老师真正需要的，不是"对错"

小学数学批改是一个每天重复的高频场景。传统工具只能回答"对"还是"错"，但同样一道减法题 `402 - 178`，学生写成 `334`，背后的原因可能是：

| 🔍 错因 | 💭 学生怎么想的 | 📚 教学对策 |
|:---|:---|:---|
| 🔢 退位错误 | 个位不够减，忘了从十位借 1 | 用数位表复盘退位过程 |
| ⬆️ 进位错误 | 加法满十后忘了进位 | 显式标注进位 |
| 🧮 基础事实错误 | 口诀背错了 8×7=54 | 短时低负荷口算练习 |
| ✅ 未验算 | 算完没检查，结果明显不合理 | 引入逆运算检查习惯 |

**这些错因的教学对策完全不同。** 把所有错误都归为"粗心"，是对教学时间的浪费。

我的计算森林做的事情很简单——告诉老师**这道题错在哪里、为什么错、下一步该怎么练**。

---

## 🌟 五个核心能力

### 🔬 1. 纳米级错因诊断

自研 **E-K01~E-K23 + E-H01~E-H21** 共 🎯 44 种错因分类体系，覆盖知识缺陷（23 种）和习惯问题（21 种），是国内小学数学领域最精细的诊断分类。

诊断引擎完全基于**规则推理**（regex + AST 分析），不依赖大模型判断对错。结果可解释、可复现、可审计。大模型仅负责生成评语和教学建议——**🤖 人机各司其职**。

### 👩‍🏫 2. 教师审核门控

所有 AI 诊断结果默认标记为 `⏳ pending_teacher_review`，教师确认后才对学生生效。

这不是可选功能，而是系统底层的**默认行为**——AI 是助手，教师是决策者。这天然符合 2025 年教育部《未成年人人工智能使用规范》中"13 岁以下学生不得独立使用生成式 AI"的要求 📜。

### 💡 3. 引导不倒答案

学生端使用**四步引导法**：

> 🤗 安慰（你很接近了）→ 🧠 推理（想想个位够不够减）→ 📝 归纳（所以退位的时候……）→ 🎯 练习（再试一道类似的）

通过 🔊 Edge-TTS 语音合成，一步步引导学生自己想明白，**永远不直接给出答案**。

### 📋 4. 作业全生命周期

```
🎲 程序化出题 → 📤 教师布置 → ✍️ 学生提交 → 🤖 AI批改 → 👩‍🏫 教师审核 → 📄 PDF报告 → 🎯 针对性练习
```

- 🎲 **程序化出题器**（142KB）：按错因代码精准出题，A/B/C 三级难度自适应，无限供应
- ⚙️ **AI 批改管道**（11 个节点）：诊断 → 画像更新 → 成长计算 → 练习推荐，全流程编排
- 📊 **BKT 掌握度追踪**：贝叶斯知识追踪，量化每个知识点的掌握概率

### 🌳 5. 成长型反馈

每个孩子种一棵树 🌱。做对一道题，树就长高一点 🌿。

没有排名榜 🚫，没有打卡提醒 🚫，没有家长端的焦虑推送 🚫。每个学期一棵树，六年十二棵树长成一片森林——**用成长代替焦虑，让每个孩子都看见自己的进步** 🌲🌲🌲。

---

## 🏗️ 技术架构

```
 ┌──────────────────────────────────────────────────────┐
 │  👩‍🏫  教师端 · Next.js                                │
 │     班级森林看板 · 作业工作流 · 诊断演示 · 课表管理     │
 ├──────────────────────────────────────────────────────┤
 │  👧  学生端 · Next.js                                │
 │     成长仪表盘 · 自主练习 · 扫码批改 · 课堂测验        │
 ├──────────────────────────────────────────────────────┤
 │  ⚙️  FastAPI 后端 · ~75 端点                         │
 │     13 路由器 · 30+ 服务 · 批改管道 · BKT 掌握度      │
 ├──────────────────────────────────────────────────────┤
 │  🤖  AI / LLM 集成层                                │
 │     Dify 三级回退 · DeepSeek/GLM · RAG 知识检索       │
 ├──────────────────────────────────────────────────────┤
 │  💾  SQLite · 33 表 + FTS5                          │
 └──────────────────────────────────────────────────────┘
```

### 🛠️ 技术栈概览

| 层 | 技术 | 要点 |
|:---|:---|:---|
| 🐍 后端框架 | FastAPI 0.115 | 13 路由器，异步，自动 OpenAPI 文档 |
| 💾 数据库 | SQLite + FTS5 | 33 张业务表 + 全文检索虚拟表 |
| 🧠 规则引擎 | 自研（regex + AST） | 零 LLM 依赖，44 种错因可解释诊断 |
| ⚛️ 前端框架 | Next.js 15.5 App Router | 教师端/学生端双布局隔离，17 个页面路由 |
| 📊 可视化 | ECharts 6.x + Canvas | 雷达图、热力图、趋势线、森林粒子渲染 |
| 🤖 AI 平台 | Dify + DeepSeek/GLM | 三级回退（本地→云端→直连），RAG 知识检索 |
| 🔍 本地模型 | BAAI/bge-m3 + jina-reranker | Embedding + Reranker，离线可用 |
| 🔊 语音 | Edge-TTS | 引导步骤语音合成 |
| 📷 OCR | 百度智能作业 + PaddleOCR | 拍照识别，自动批改 |
| 📄 PDF | xelatex + weasyprint | 作业单、学生报告、班级报告 |
| ✅ 测试 | pytest | 341 个测试，覆盖诊断/批改/管道/端点 |

### 📁 项目结构

```
calc_forest/
├── 🐍 backend/                # FastAPI 后端
│   ├── app/
│   │   ├── 🛣️ routers/        # 13 个路由器
│   │   ├── ⚙️ services/       # 30+ 服务模块
│   │   ├── 🔀 pipeline/       # 批改管道（11 节点）
│   │   └── 📦 repositories/   # 数据访问层
│   ├── ✅ tests/              # 341 个测试
│   └── 📜 scripts/            # 种子数据、模拟器
├── ⚛️ web/                    # Next.js 前端
│   └── src/
│       ├── 👩‍🏫 app/(teacher)/  # 教师端页面
│       ├── 👧 app/(student)/  # 学生端页面
│       └── 🧩 components/     # 44 个组件
└── 🤖 dify/                   # Dify 工作流 DSL

📚 docs/                       # 产品文档、工程文档、竞赛材料
📖 knowledge_base/             # 147 个知识库文件（1~6 年级）
```

---

## 🚀 快速开始

### 📋 环境要求

- 🐍 Python 3.11+
- 💚 Node.js 18+
- 💾 SQLite 3（Python 内置）

### 🐍 后端

```bash
cd calc_forest/backend
pip install -r requirements.txt

# 运行测试（341 个用例）
pytest -s tests/ -q \
  --ignore=tests/test_e2e_smoke.py \
  --ignore=tests/test_dify_e2e.py \
  -k "not full_pipeline"

# 启动 API 服务
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### ⚛️ 前端

```bash
cd calc_forest/web
npm install

npm run dev                # 🌀 开发服务器 (port 3002)
npx next build --no-lint   # 📦 生产构建
```

### 🎲 模拟数据

```bash
cd calc_forest/backend
python scripts/simulate_realistic.py   # 📊 8 周真实感模拟数据
```

### 🔑 环境变量

```bash
cp .env.example .env   # 填入实际 API 密钥
```

需要配置：DeepSeek API Key、智谱 GLM API Key。Dify 为可选项。

---

## 🎯 核心设计原则

| 🛡️ 原则 | 📖 含义 |
|:---|:---|
| 🧠 对错判断只靠规则 | 大模型可以总结和解释，但**绝不**用来判断答案对错 |
| 👩‍🏫 教师始终是决策者 | 所有 AI 输出必须经教师确认，不可绕过 |
| 💡 引导不倒答案 | 四步引导法帮学生自己想明白，永远不直接给答案 |
| 🔒 合成数据 | 不使用真实学生数据，所有演示数据为模拟生成 |
| 🌳 无排名、无打卡 | 成长型反馈，不制造竞争焦虑 |

## 📚 文档

| 📄 文档 | 📖 说明 |
|:---|:---|
| [🔍 错因分类体系](docs/specs/04_error_taxonomy.md) | 44 种错因定义（E-K/E-H 全表） |
| [🏗️ 系统架构](docs/engineering/architecture.md) | 端点清单、数据流、模块关系 |
| [📋 MVP 范围](docs/specs/02_mvp_scope.md) | 已实现功能 + 未来扩展边界 |
| [🎬 竞赛演示脚本](docs/competition/demo_video_script_v2.md) | 5 幕演示流程 |

---

## 🙏 致谢

本项目为《创AI》全国中小学人工智能教育案例征集参赛作品。

<div align="center">

**用成长代替焦虑，让每个孩子都看见自己的进步** 🌲🌱🌿

</div>

## 📜 License

[MIT](LICENSE)
