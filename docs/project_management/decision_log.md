# Decision Log

## 2026-05-05: 《创AI》口径收口为“教育智能体 + Dify 主入口 + 教师工作台主叙事”

决策：以《创AI》指南为唯一上游标准，当前项目对外统一按 **教育智能体** 申报；Dify 保留为主交付入口与主演示链路；当前 MVP 主叙事收口为 **教师工作台 + 错因诊断闭环 + 教师审核边界**；森林相关内容降级为品牌表达与成长语气层。

原因：

- 《创AI》指南明确允许基于国产智能体平台（含 Dify）开发教育智能体。
- 当前仓库已经具备 Dify 工作流、本地导入、draft run 和文档证据，继续保留 Dify 反而更符合“AI赋能开发”和“可复现”要求。
- 若继续把“多树森林累计”和长期成长系统写成当前主交付，会偏离已实现能力，也会削弱真实教学问题、实用性和教师审核边界。

影响：

- 新增 `docs/competition/创AI_申报总纲.md` 作为比赛材料主入口。
- `docs/competition/`、`docs/specs/`、`docs/engineering/`、`Agent.md` 和项目管理文档都需要按新口径统一修订。
- 森林相关设计继续保留，但默认不再作为当前 MVP 的中心卖点。

## 2026-05-03: 正式版 Dify 工作流先落 V2，再升级 V3

决策：不直接把正式版 Dify 工作流建立在未配置完成的模型 provider 和知识库之上，而是先落一个 **正式版 V2**：使用多 HTTP 节点、Code 节点、If-Else 分支和配置接口组成可运行编排，再把 LLM 和 Knowledge Retrieval 作为 V3 升级层。

原因：

- 夜间版已经证明“组合接口 + Dify”能跑，但还不够像正式编排。
- 直接上 V3 会被本地模型 provider 和知识库绑定阻塞，影响今晚交付。
- V2 可以把节点职责拆开、把编排逻辑沉淀下来，同时保持本地可运行和可验证。

影响：

- 新增正式版资产：`calc_forest/dify/my_calc_forest_dify_formal_v2.yml`
- 新增设计文档：`calc_forest/dify/formal_workflow_design.md`
- 新增知识库接入文档和轻量知识源：`calc_forest/dify/knowledge_base_setup.md` + `knowledge_sources/`
- 本地已完成正式版 V2 的 import 和 draft run 验证。

## 2026-05-03: 夜间版 Dify 工作流改为组合接口优先

决策：为确保今晚能够真正跑通 Dify 工作流，新增 `POST /api/dify/session-draft` 作为夜间版组合接口，让 Dify 在未额外配置模型和插件的情况下，也能返回完整诊断草案。

原因：

- 细粒度工作流在当前环境中会受到模型配置和 builtin plugin 可用性的影响。
- 组合接口可以先把诊断、练习、教师摘要、学生引导、树种和鼓励语统一返回，保证演示闭环先成立。
- 后续仍可在此基础上拆回更细粒度的多节点 Dify 工作流。

影响：

- 新增 `development/app/services/session_draft.py`
- 新增 `POST /api/dify/session-draft`
- 新增夜间版 Dify DSL：`calc_forest/dify/my_calc_forest_dify_night_build.yml`

## 2026-05-03: 本地 Dify 已成功启动并完成 import + draft run

决策：在本机通过 Docker 启动 Dify，自助完成初始化、DSL 导入和首个 draft run 验证。

原因：

- 仅有文档和接口还不够，需要至少一次真实 Dify 运行来验证“今晚版本”不是纸面方案。
- 实际运行暴露了两个关键问题：Dify JSON body 数字/字符串类型差异，以及 builtin `json_parse` plugin 不可用。
- 两个问题都已通过后端入参放宽和 Code 节点替代 plugin 的方式修复。

影响：

- 本地 Dify 地址：`http://127.0.0.1:18080`
- Dify 夜间版已导入并成功运行
- 运行记录写入 `calc_forest/dify/local_build_status.md`

## 2026-05-03: Dify-first 夜间构建主线

决策：正式以 `Dify-first` 作为“我的计算森林”的当前构建主线。仓库内先完成三件事：统一产品精神文档、补齐 Dify-ready 工具接口、在 `calc_forest/dify/` 建立产品侧工作区和工作流清单。

原因：

- 当前项目最需要的是把“教育智能体”真正落到可运行的编排层，而不是继续停留在平台比较阶段。
- Dify 适合作为教师侧工作流壳，配合本地 FastAPI 工具接口，可以在一晚上内搭出首个可演示闭环。
- 先打通 Dify 编排、诊断接口和练习接口，比先做重前端或 OCR 更符合当前节奏。

影响：

- 更新 `docs/engineering/dify_workflow_plan.md`，明确 `correct_answer`、练习接口、树种接口和鼓励语接口的调用方式。
- 新增 `POST /api/practice/recommend`、`GET /api/tree-species`、`GET /api/encouragements` 到当前实现口径。
- 新增 `calc_forest/dify/` 工作区，用于沉淀工作流清单、演示输入和后续 Dify 资产。

## 2026-05-03: 第4次修改精神统一压入主文档和比赛材料

决策：不再只在 `specs/08/09/10` 中保留教师第4次修改精神，而是将其统一传播到入口文档、比赛材料和项目管理文档。

原因：

- 现有 specs 层已经较好吸收教师意图，但根入口和比赛材料仍过于“系统说明”化，弱化了“我的计算森林”的教育温度。
- 如果对外材料继续只讲错因诊断和技术架构，会损失“长期坚持、低压力成长、教材优先、包容起点”的核心价值。

影响：

- 更新 `README.md`、`Agent.md`、`docs/specs/00_project_brief.md`、`03_user_flows.md` 等入口文档。
- 更新 `docs/competition/demo_video_script.md`、`创AI_案例信息表_素材.md`、`创AI_开发与应用报告_草稿.md`。
- 新增 `docs/project_management/tonight_2026-05-03_dify_build.md` 作为当晚构建计划。

## 2026-05-02: 新增 calc_forest 产品工作区

决策：在仓库根目录新增 `calc_forest/`，作为“我的计算森林”后续正式产品实现目录，与 `development/` 的 MVP 后端验证空间分离。

原因：

- `development/` 更偏研发验证和后端 MVP，不适合作为后续产品仓的长期命名。
- 品牌侧实现需要一个更贴近产品语义、也便于未来单独做 git 管理的目录。
- 使用 ASCII 路径 `calc_forest/`，兼顾品牌识别和工程兼容性。

影响：

- 根目录新增 `calc_forest/README.md`。
- `README.md`、`Agent.md`、`docs/README.md` 同步更新入口说明。
- 后续正式产品端优先在 `calc_forest/` 开工，`development/` 继续承担 MVP 诊断服务和验证职责。

## 2026-05-02: 顶层目录重组为 docs + development

决策：将仓库顶层收口为两个主体工作区：`docs/` 和 `development/`。保留根目录 `README.md` 与 `Agent.md` 作为统一入口，其余文档目录全部并入 `docs/`，原 `dev/` 重命名为 `development/`。

原因：

- 当前顶层目录过多，文档和代码入口分散，阅读成本高。
- 教育 Agent 项目同时需要稳定的文档链路和清晰的开发链路，两块式结构更利于后续协作。
- 将文档统一纳入 `docs/` 后，产品、工程、研究、比赛和项目管理之间的边界更清楚。

影响：

- 新增 `docs/README.md` 作为文档侧总索引。
- 根目录主体变为 `docs/` + `development/`。
- 全量更新文档中的目录引用、运行命令和入口说明。

## 2026-05-02: 第4次修改评估与框架调整

决策：接受教师第4次修改的核心创意，品牌升级为「我的计算森林」，在 specs 层面融入森林成长体系、分层引导系统和多模态输入设计。MVP 工程范围不做大幅扩展，但在数据模型上预留接口。

分析：
- 第4次修改共提出10点补充和完整的11部分设计方案
- 核心变化：单树苗→六年森林、品牌升级、30+树种、多模态输入、三种引导模式、寒暑假模式、情感鼓励系统
- 可直接落地：品牌文案、成长里程碑数据模型、树种数据、鼓励语模板、年级扩展1-6
- 需工作量但可做：三种引导模式、假期模式、教材对齐、森林视图 API
- 远超 MVP：语音输入、拍照OCR、30+知识卡、六年用户系统、跨学科教学

影响：
- 新增 specs: `08_forest_growth_system.md`, `09_guidance_system.md`, `10_multimodal_input.md`
- 更新 `docs/specs/01_prd.md` 增加森林理念和引导用户故事
- 更新 `docs/specs/02_mvp_scope.md` 扩展年级和新增数据模型
- 更新 `Agent.md` 品牌和范围
- 新增任务 BI-013 到 BI-018, CM-008, VA-007, PK-005 到 PK-008

## 2026-05-02: 外部《第4次修改（5月2号）》文档纳入资料链路

决策：将教师在微信文件中提供的 `第4次修改（5月2号）.docx` 视为正式参考输入，纳入 `docs/source_materials/` 的资料索引和 `docs/specs/teacher_feedback_digest.md` 的摘要来源。

原因：

- 该文档系统化表达了第4次修改的完整版本，信息密度高于聊天摘录。
- 它与现有 `08/09/10` 三份 specs 高度一致，可作为这些设计文档的上游来源补证。
- 将其纳入资料链路后，新 session 更容易理解哪些内容来自教师原始意图，哪些属于 PM/MVP 收敛。

影响：

- 更新 `docs/source_materials/teacher_feedback/README.md` 标注外部文档来源
- 更新 `docs/specs/teacher_feedback_digest.md`，补入六年森林、树种选择、教材优先引导、多模态输入等关键信号
- 更新根目录 `README.md`，统一当前品牌与产品愿景口径

## 2026-05-01: 项目管理目录

决策：新增 `docs/project_management/`，作为跨 Codex session 的推进中枢。

原因：

- 项目会持续多 session 推进，需要稳定的任务板。
- exploration 和 exploitation 要分开，避免探索时误改核心实现。
- 每次新 session 都应能快速恢复上下文。

影响：

- 后续 session 开始前先读 `docs/project_management/session_protocol.md` 和 `docs/project_management/task_board.md`。
- 做完任务后更新任务板。

## 2026-05-01: Session 分类

决策：将任务分为 exploration、exploitation、validation 三类。

原因：

- exploration 用来调查未知和形成决策。
- exploitation 用来实现明确任务。
- validation 用来检查质量和比赛可用性。

影响：

- 每个任务应标注类型。
- 每个 session 应只做与类型匹配的主要工作。

## 2026-05-01: 首版 MVP 题型

决策：首版演示题型收敛为三位数加减法、含 0 连续退位减法、一位数乘两位数、简单四则混合运算。

原因：

- 这些题型足以展示小学计算错因诊断的价值。
- 规则诊断可解释，适合短期做出稳定 Demo。
- 小数、分数、应用题和 OCR 暂不阻塞 MVP。

影响：

- 合成数据和首版测试优先覆盖 `E01/E02/E03/E04/E05/E07/E08/E11`。
- `E06/E10` 保留在 taxonomy 中，但不作为首版必测。

## 2026-05-01: MVP API 路径

决策：首版工程先实现 `GET /health` 和 `POST /api/diagnose`。

原因：

- 今天目标是跑通最小诊断闭环。
- Dify/Coze 后续可以通过 HTTP 工具调用该接口。
- 文档中较完整的多接口 API 设想保留为后续标准化方向，但当前实现以 `/api/diagnose` 为准。

影响：

- 下一轮需要统一 `docs/engineering/api_plan.md` 和 `docs/engineering/dify_workflow_plan.md` 中的接口口径。

## 2026-05-01: 项目结构收口

决策：将项目分为 `development/`、`docs/specs/`、`docs/source_materials/`、`docs/competition/`、`docs/research/`、`docs/engineering/`、`docs/project_management/`。

原因：

- 代码、PM 规划、原始资料和比赛叙事需要解耦。
- 新 Codex session 需要稳定入口快速理解项目。
- 避免把妈妈材料和比赛愿景误当成已实现工程承诺。

影响：

- 纯开发内容只放 `development/`。
- PM 审核入口为 `docs/specs/`。
- 原始资料放 `docs/source_materials/`，视为只读输入。
- 根目录 `Agent.md` 是新 session 第一入口，路径/API/测试命令变更时必须更新。
