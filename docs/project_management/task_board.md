# Task Board

状态说明：

- `TODO`：未开始。
- `DOING`：正在做。
- `BLOCKED`：被外部条件阻塞。
- `DONE`：已完成。
- `PARKED`：暂缓，不影响当前 MVP。

## Current Focus

当前阶段目标：保持 `Agent.md`、`docs/`、`development/`、`calc_forest/` 四条主线一致，把当前主叙事聚焦为 **教师工作台 + 纳米级错因图谱 + 课本章节精准定位 + 森林情感成长**，让 E01-E11 错因被雷达图看见、被热力图看见、被 TTS 听见、被粒子动画感受到。

## Exploration Backlog

| ID | 状态 | 任务 | 输出 |
| --- | --- | --- | --- |
| EX-001 | DONE | 梳理《教AI》《用AI》《创AI》赛道差异 | `docs/research/competition_tracks.md` |
| EX-002 | DONE | 梳理小学数学计算错因和教师痛点 | `docs/research/pain_points_primary_math.md` |
| EX-003 | DONE | 比较 Coze / Dify / Coze Studio | `docs/research/coze_dify_agent_platforms.md` |
| EX-004 | DONE | 深挖 Dify HTTP Tool / Workflow 调用方式 | 更新 `docs/engineering/dify_workflow_plan.md` |
| EX-005 | TODO | 调研 PaddleOCR / Pix2Text 对手写算式的可行性 | 更新 `docs/research/tech_landscape.md` |
| EX-006 | DONE | 调研小学一至六年级计算知识点范围 | 更新 `docs/specs/04_error_taxonomy.md` + 新增 `docs/specs/08_forest_growth_system.md` |
| EX-007 | DONE | 选定首版演示题型 | 更新 `docs/specs/02_mvp_scope.md` |
| EX-008 | DONE | 提炼教师《计算小树苗》材料 | `docs/specs/teacher_feedback_digest.md` |
| EX-009 | DONE | 评估第4次修改可行性并调整框架 | 更新 `docs/specs/01_prd.md` + `02_mvp_scope.md` + `Agent.md` |
| EX-010 | DONE | 规划网页端展示界面与前端技术栈 | `docs/engineering/frontend_experience_plan.md` |

## Exploitation Backlog

| ID | 状态 | 任务 | 输出 |
| --- | --- | --- | --- |
| BI-001 | DONE | 初始化 Python 工程骨架 | `development/app/`, `development/tests/`, `development/data/` |
| BI-002 | DONE | 建立 20-50 条合成作答样例 | `development/data/demo_answer_records.json` |
| BI-003 | DONE | 实现 Pydantic 数据结构 | `development/app/schemas.py` |
| BI-004 | DONE | 实现基础错因诊断规则 | `development/app/services/diagnosis.py` |
| BI-005 | DONE | 实现 FastAPI `/api/diagnose` | `development/app/main.py` |
| BI-006 | DONE | 实现学生画像更新逻辑（含森林数据） | `development/app/services/profiles.py` — `get_student_profile_summary()`, `get_class_profile_summary()` |
| BI-007 | DONE | 实现分层练习推荐草案 | `development/app/services/practice.py` |
| BI-008 | DONE | 实现班级摘要接口 | `development/app/services/summaries.py` — `get_class_error_summary()`, `get_class_period_summary()`, `get_error_code_breakdown()` |
| BI-009 | DONE | 写首批诊断单元测试 | `development/tests/test_diagnosis.py` |
| BI-010 | DONE | 写 README 和本地运行命令 | `README.md` |
| BI-011 | TODO | 增强括号混合运算步骤错误诊断 | `development/app/services/diagnosis.py` |
| BI-012 | TODO | 增强两位数乘法部分积错位合并诊断 | `development/app/services/diagnosis.py` |
| BI-013 | DONE | 将成长里程碑 + 树种 + 引导模式加入 schemas | `development/app/schemas.py` |
| BI-014 | DONE | 创建8种核心树种数据和鼓励语配置 | `development/data/tree_species.json` + `development/data/encouragements.json` |
| BI-015 | DONE | 实现成长里程碑更新逻辑 | `development/app/services/growth_milestone.py` — 9阶段自动递进 |
| BI-016 | TODO | 实现4步引导法（标准模式） | 扩展 `development/app/services/diagnosis.py` 的 student_feedback |
| BI-017 | TODO | 实现1-2年级口算题型诊断规则 | `development/app/services/diagnosis.py` |
| BI-018 | DONE | E01-E11错因雷达图 | `calc_forest/web/src/components/forest/ErrorRadarChart.tsx` |
| BI-019 | DONE | 班级错因热力图 | `calc_forest/web/src/components/forest/ClassErrorHeatmap.tsx` |
| BI-020 | DONE | Edge-TTS语音端点 + Fake IRT掌握度API | `development/app/services/tts_service.py` + `/api/tts/*`, `/api/mastery/*` |
| BI-021 | DONE | Canvas粒子系统增强（萤火虫+生长脉冲） | `calc_forest/web/src/components/forest/ForestBackground.tsx` |
| BI-022 | DONE | 错因→知识点映射表 + 学生档案增强 | `error_code_knowledge_map` 数据表 + `student_service.py` 扩展字段 |
| BI-023 | DONE | 前端展示课本章节级薄弱知识点 | `calc_forest/web/src/components/forest/StudentDetailDrawer.tsx` |
| BI-048 | DONE | 真实感多轮作业模拟（好中差学生 + 写→批→改循环） | `development/scripts/simulate_realistic.py` — 824行, 10学生×3层级×8周, 218作业/506提交/2111答题 |
| BI-024 | TODO | 竖式计算分步动画（Photomath对标） | `calc_forest/web/src/components/` |
| BI-025 | TODO | SSE Agent执行流可视化 | `development/app/` + 前端组件 |
| BI-026 | TODO | 上下文感知引导（历史错因注入Dify prompt） | Dify workflow + `session_draft.py` |
| BI-033 | TODO | 评估森林视图 API 是否仍保留在后续扩展层 | 范围澄清后再决定是否实现 |
| BI-034 | DONE | 建立产品侧 Dify 工作区和首个工作流清单 | `calc_forest/dify/` |
| BI-035 | DONE | 实现 Dify 夜间版组合接口 | `development/app/services/session_draft.py` + `POST /api/dify/session-draft` |
| BI-036 | DONE | 产出正式版 V2 多节点 Dify 工作流 | `calc_forest/dify/my_calc_forest_dify_formal_v2.yml` |
| BI-037 | DONE | 补齐 Dify 设计文档、运行脚本和知识源文档 | `calc_forest/dify/formal_workflow_design.md` + `knowledge_sources/` + `scripts/` |
| BI-038 | DONE | 扩展 DB schema — 6 张新表 + students 扩展字段 | `teaching_units`, `teaching_schedule`, `calendar_weeks`, `student_error_trajectory`, `scanned_submissions`, `homework_pdfs` |
| BI-039 | DONE | 人教版六年级下册种子数据 | `development/scripts/seed_curriculum.py` |
| BI-040 | DONE | 课程 API 端点 — units/schedule/calendar/trajectory | `development/app/services/curriculum_service.py` |
| BI-041 | DONE | 《火山的女儿》视觉风格重构 — 色板/卡片/字体 | `globals.css` parchment/warm/volcano/ink/sage 色系 |
| BI-042 | DONE | 森林网格缩略/展开 Zoom 模式 | `ClassForestGrid.tsx` + `StudentTreeCard.tsx` compact |
| BI-043 | DONE | 学生 3-tab 详情 drawer (数据概览/错因轨迹/学习画像) | `StudentDetailDrawer.tsx` |
| BI-044 | DONE | PDF 作业生成 (weasyprint + jinja2) | `development/app/services/pdf_service.py` + `templates/homework.html` |
| BI-045 | DONE | 前端 bundle 优化 — dynamic import + memo + tree-shaking | 首页 277kB→167kB (-40%) |
| BI-046 | DONE | OCR schema stub + API (returns 501) | `scanned_submissions` table + `/api/ocr/stub`, `/api/ocr/upload` |
| BI-047 | DONE | 前端全量接入真实后端 API (所有页面) | 所有页面已接入 `/api/classes/G6C1/forest` 等真实端点，仅 `/guidance` 为纯静态页 |

## Competition Material Backlog

| ID | 状态 | 任务 | 输出 |
| --- | --- | --- | --- |
| CM-001 | DONE | 创AI开发与应用报告草稿 | `docs/competition/创AI_开发与应用报告_草稿.md` |
| CM-002 | DONE | 创AI案例信息表素材 | `docs/competition/创AI_案例信息表_素材.md` |
| CM-003 | DONE | 演示视频脚本初稿 | `docs/competition/demo_video_script.md` |
| CM-004 | DONE | 形成 300 字案例简介最终版（融入森林概念） | 更新案例信息表素材 |
| CM-005 | TODO | 形成 8 分钟演示视频分镜（Dify 主链路 + 教师审核 + 应用效果） | 更新演示视频脚本 |
| CM-006 | TODO | 准备应用截图清单 | 更新证据清单 |
| CM-007 | TODO | 准备 2-3 个完整诊断案例 | 更新 `docs/competition/evidence_checklist.md` |
| CM-008 | DONE | 更新开发报告融入"我的计算森林"品牌和五大亮点 | 更新 `docs/competition/创AI_开发与应用报告_草稿.md` |

## Validation Backlog

| ID | 状态 | 任务 | 输出 |
| --- | --- | --- | --- |
| VA-001 | DONE | 检查 23 个早期文档是否互相一致 | 一致性检查记录 |
| VA-002 | TODO | 检查隐私合规表述 | 更新 `docs/research/policy_and_compliance.md` |
| VA-003 | DONE | 检查 API 文档和数据模型是否一致 | 更新 `docs/engineering/api_plan.md` / `docs/engineering/data_model.md` |
| VA-004 | DONE | 跑首版测试并记录结果 | 测试输出 |
| VA-005 | DONE | 建立 `Agent.md` 新 session 交接文件 | `Agent.md` |
| VA-006 | DONE | 路径/API/范围变化后同步 `Agent.md`（第4次修改后） | `Agent.md` |
| VA-007 | DONE | 验证新 specs（08/09/10）与现有代码不冲突 | 检查记录 |
| VA-008 | DONE | 重组项目目录为 `docs/` + `development/` 双主线 | `README.md` + `Agent.md` + `docs/README.md` |
| VA-009 | DONE | 新增 `calc_forest/` 作为产品侧工作区 | `calc_forest/README.md` + 入口文档更新 |
| VA-010 | DONE | 将第4次修改精神统一压入主文档和比赛材料 | `docs/specs/` + `docs/competition/` |
| VA-011 | DONE | 本地启动 Dify 并完成夜间版 workflow import + run | `calc_forest/dify/local_build_status.md` |
| VA-012 | DONE | 本地导入并跑通正式版 V2 多节点 workflow | `calc_forest/dify/local_build_status.md` |
| VA-013 | DONE | 为 Dify 版本补齐可追溯设计与运行文档 | `calc_forest/dify/README.md` + `formal_workflow_design.md` |
| VA-014 | TODO | 依据《创AI》指南统一 competition/specs/engineering 总口径 | 新增总纲 + 更新关键文档 |
| VA-015 | DONE | 建立文档对齐总入口与同步触发器地图 | `docs/DOC_ALIGNMENT_MAP.md` + 入口文档更新 |

## Parking Lot

| ID | 状态 | 任务 | 暂缓原因 |
| --- | --- | --- | --- |
| PK-001 | PARKED | 全自动拍照批改 / OCR | 首版先用手工录入和人工校正 |
| PK-002 | PARKED | 家长端 | 不是《创AI》首版核心 |
| PK-003 | PARKED | 小程序端 | 先证明诊断闭环 |
| PK-004 | PARKED | 长期学习预测模型 | 需要真实长期数据 |
| PK-005 | PARKED | 语音输入（ASR） | 工程量大，MVP 不阻塞 |
| PK-006 | PARKED | 30+树种完整知识卡 | 先做8种核心，后续扩展 |
| PK-007 | PARKED | 六年积累 / 毕业纪念册 | 需要持久化用户系统 |
| PK-008 | PARKED | 多教材版本适配 | 先做人教版 |
| PK-009 | PARKED | 森林累计主叙事 | 当前已降级为品牌表达与成长语气层 |
