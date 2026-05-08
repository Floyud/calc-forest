# Tonight Plan: 2026-05-03 Dify Build

今晚目标：把“我的计算森林”从“文档和后端都具备方向”推进到“Dify-first 可开工、可演示、可继续通宵搭建”的状态。

## Tonight Deliverables

### 1. 统一产品精神与文档口径

状态：`DONE`

完成标准：

- 入口文档统一为“我的计算森林”。
- specs 体现“长期坚持、低压力、教材优先、教师主导”。
- 比赛材料不再只像一个泛化的技术系统说明。

### 2. 补齐 Dify-ready 最小工具接口

状态：`DONE`

完成标准：

- `POST /api/diagnose`
- `POST /api/practice/recommend`
- `GET /api/tree-species`
- `GET /api/encouragements`
- 测试通过，运行环境统一 `pyt0`

### 3. 建立产品侧 Dify 工作区

状态：`DONE`

产物：

- `calc_forest/dify/README.md`
- `calc_forest/dify/workflow_checklist.md`
- `calc_forest/dify/demo_input_402_178.json`

### 4. 在 Dify 中跑通首个教师侧工作流

状态：`DONE`

执行顺序：

1. 新建 Dify Workflow 应用“我的计算森林”
2. 配置输入变量
3. 接入 Diagnose 节点
4. 接入 Practice 节点
5. 配置教师摘要和学生引导节点
6. 用 `402-178` 样例跑通

本轮实际结果：

- 本地 Dify 已启动在 `http://127.0.0.1:18080`
- 通过 API 初始化完成首个管理员账号
- 已导入夜间版工作流 DSL
- 已完成一次 draft run，返回 `E03` 相关完整草案

### 5. 产出演示证据

状态：`TODO`

需要留存：

- 工作流总览截图
- 关键 HTTP 节点截图
- 最终输出截图
- 测试结果截图
- 使用 `pyt0` 的命令记录

当前已具备：

- Dify import 结果
- draft run 事件流日志
- 本地测试结果

尚缺：

- UI 截图
- 工作流画布截图
- 最终演示画面截图

### 6. 推进正式版 Dify 编排骨架

状态：`DONE`

本轮实际结果：

- 已新增正式版 V2 设计文档
- 已新增知识库接入说明和轻量知识源文档
- 已导入正式版 V2 DSL
- 已完成正式版 V2 draft run
- 已验证多节点非 LLM 主链路可运行

## Runtime Commands

启动 API：

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

运行测试：

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_diagnosis.py -q
```

## Stop Rules Tonight

- 不为了赶进度接入 OCR。
- 不为了“炫”而扩大到完整学生端。
- 不让 Dify 直接决定数学对错。
- 不引入排名、强制打卡或假期学习压力。

## Next Build Target

在 Dify 跑通首个教师侧工作流后，下一步优先做：

1. 1 到 2 年级口算诊断规则
2. 森林视图 API
3. 教师审核后的成长更新逻辑
4. 为 Dify 配置稳定模型 provider
5. 创建并绑定 Dify Knowledge
6. 正式产品端前端骨架
