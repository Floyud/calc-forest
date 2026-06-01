# 前端界面规划与实现

> 最后更新：2026-05-19 | 基于代码库实际状态
>
> 相关文档：`docs/engineering/architecture.md` · `docs/engineering/api_plan.md` · `AGENTS.md`

## 当前状态

前端已完整实现，Next.js 15.5 App Router，教师端 + 学生端双布局。

```text
calc_forest/web/src/
├── app/
│   ├── (teacher)/          # 教师端路由组 (10 页面)
│   │   ├── login/          # /login — 教师登录
│   │   ├── page.tsx        # / — 班级森林网格 + 错因热力图
│   │   ├── classroom/      # /classroom — 备课→白板→测验→总结
│   │   ├── homework/       # /homework — 生成→布置→AI批阅→审核
│   │   ├── schedule/       # /schedule — 教学进度 + 自动布置
│   │   ├── diagnose/       # /diagnose — 单题诊断演示
│   │   ├── guidance/       # /guidance — Edge-TTS 语音引导
│   │   ├── forest/         # /forest — 学生成长详情
│   │   ├── botanical/      # /botanical — 树种知识卡片
│   │   └── chat/           # /chat — Dify 聊天代理
│   ├── (student)/          # 学生端路由组 (7 页面)
│   │   ├── s/login/        # /s/login — 学生登录
│   │   ├── s/home/         # /s/home — 学生仪表盘
│   │   ├── s/growth/       # /s/growth — 个人成长树
│   │   ├── s/practice/     # /s/practice — 自主练习
│   │   ├── s/scan/[hwId]/  # /s/scan/:hwId — OCR 拍照批改
│   │   ├── s/homework/[id]/# /s/homework/:id — 作业详情
│   │   └── s/quiz/[id]/    # /s/quiz/:id — 课堂测验
│   └── (全局)              # loading.tsx, error.tsx, not-found.tsx
├── components/             # 44 个组件
│   ├── forest/             # 森林可视化 (含 Canvas + 粒子系统)
│   ├── classroom/          # 课堂视图
│   ├── homework/           # 作业表单/分析/批改
│   ├── guidance/           # 引导对话 + 竖式动画
│   ├── diagnose/           # 诊断管道进度
│   ├── ui/                 # shadcn 基础组件
│   └── layout/             # 导航/页脚/工作台
├── lib/
│   ├── api/                # 集中式 API 客户端 + TanStack Query hooks
│   ├── types/              # TypeScript 类型定义 (504 行)
│   ├── config.ts           # 默认配置 (G6C1, S001)
│   ├── labels.ts           # 中文标签映射
│   └── presentation.ts     # 导航/演示/UI 辅助
```

## 技术栈（实际使用）

| 层级 | 选择 | 说明 |
|---|---|---|
| 框架 | Next.js 15.5 (App Router) | React 19 |
| 样式 | Tailwind CSS 4 | 原子化 CSS |
| 组件 | shadcn/ui + @base-ui/react | 原语组件 |
| 图表 | **ECharts 6.x** | 雷达图、趋势线、热力图、柱状图 |
| 动画 | Framer Motion | 页面过渡 + 树生长动画 |
| 状态 | TanStack Query v5 | 服务端状态缓存 |
| 图标 | Lucide React | 图标库 |
| 构建 | TypeScript 5 + ESLint 9 | 类型安全 |

> **注意：** 规划阶段曾考虑 Recharts，实际实现使用 ECharts 6.x，因其对雷达图、热力图支持更好。

## 设计原则（已实现）

1. **自然系配色** — 森林绿、嫩芽绿、暖米白、阳光黄、果实橙
2. **插画感轻** — 卡片 + 柔和图形 + 小树成长组件，不走幼儿园路线
3. **教师端专业，学生端有温度** — 清晰可信 vs 陪伴鼓励
4. **功能信息优先** — 看懂项目功能是第一任务

## 核心组件清单

### 森林可视化 (`components/forest/`)

| 组件 | 功能 |
|---|---|
| `ClassForestGrid.tsx` | 班级森林网格（缩略/展开模式） |
| `StudentTreeCard.tsx` | 学生树木卡片 |
| `StudentDetailDrawer.tsx` | 学生 3-tab 详情抽屉（概览/轨迹/画像） |
| `ForestBackground.tsx` | 森林背景 + Canvas 粒子系统（萤火虫 + 生长脉冲） |
| `ClassErrorHeatmap.tsx` | 班级错因热力图 |
| `ErrorRadarChart.tsx` | E01-E11 错因雷达图 |
| `AccuracyTrendChart.tsx` | 准确率趋势线 |
| `SvgTree.tsx` + `TreeDefs.tsx` | SVG 树木 + 情绪状态（Happy/Thriving/Struggling/Wilting） |
| `CanvasTreeRenderer.ts` | Canvas 树木渲染器 |
| `CanvasParticleSystem.ts` | Canvas 粒子系统 |

### 课堂视图 (`components/classroom/`)

| 组件 | 功能 |
|---|---|
| `ClassPrepView.tsx` | 备课视图 |
| `WhiteboardDisplay.tsx` | 白板展示 |
| `QuizSummaryView.tsx` | 测验统计 |

### 作业 (`components/homework/`)

| 组件 | 功能 |
|---|---|
| `HomeworkForm.tsx` | 作业生成表单 |
| `HomeworkAnalytics.tsx` | 作业分析 |
| `ProblemPreview.tsx` | 题目预览 |
| `GradingResult.tsx` | 批改结果 |
| `StudentAnswerSimulator.tsx` | 学生作答模拟器 |

### 引导 (`components/guidance/`)

| 组件 | 功能 |
|---|---|
| `GuidanceChat.tsx` | 引导对话界面 |
| `VerticalCalcAnimation.tsx` | 竖式计算分步动画（退位减法 + 进位加法） |

## API 层

集中式 fetch 封装（重试 + 45s 超时），暴露 ~35 个 API 函数。

TanStack Query hooks：
- `useClassForest` — 班级森林数据
- `useClassSummary` — 班级摘要
- `useStudentProfile` — 学生画像
- `useCurrentCycle` — 当前周期
- `useTreeSpecies` — 树种配置
- `useSessionDraft` — Dify 会话草稿
- `useUpdateStudentProfile` — 更新画像

## 包依赖

```json
{
  "next": "15.5.15",
  "react": "19.2.5",
  "@tanstack/react-query": "^5.100.8",
  "echarts": "^6.0.0",
  "framer-motion": "^12.38.0",
  "lucide-react": "^0.545.0",
  "shadcn": "^4.6.0",
  "tailwindcss": "^4.2.4"
}
```

## 构建命令

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/web
npm run dev                              # 开发服务器 (port 3000)
npx next build --no-lint                 # 生产构建 (必须 --no-lint)
npx tsc --noEmit                         # 类型检查
```

## 演示适配

1. 表单默认带示例题，打开页面就能演示
2. 诊断结果用"标签 + 证据 + 建议动作"三段式展示
3. 学生引导页每一步只呈现一个重点
4. 树木成长动画 300ms-800ms 过渡
5. 鼓励语像老师和伙伴在说话
6. 显眼位置标注"教师审核后再给学生"
