# User Flows

> 最后更新：2026-05-19
>
> 相关文档：`docs/engineering/api_plan.md` · `docs/specs/02_mvp_scope.md`

## 教师端流程（已实现）

### 诊断流程

```text
教师录入题目、标准答案、学生作答
  → POST /api/diagnose（规则引擎诊断）
  → 系统返回：错因编码 + 证据 + 教师建议 + 学生提示
  → 教师审核后用于讲评、订正或短时巩固
```

### 作业流程

```text
教师生成作业（POST /api/homework/generate）
  → 布置作业（POST /api/homework/assign）
  → 学生提交（POST /api/homework/submit）
  → AI 批改（POST /api/homework/ai-grade）
  → 教师审核
  → PDF 生成（POST /api/homework/{id}/generate-pdf）
  → 分析报告（GET /api/homework/{id}/analytics）
```

### 课堂测验流程

```text
教师生成测验（POST /api/quiz/generate）
  → 学生实时答题（POST /api/quiz/{id}/student-answer）
  → 教师查看实时统计（GET /api/quiz/{id}/live-stats）
  → 测验总结（GET /api/quiz/{id}/summary）
```

### 森林视图流程

```text
教师查看班级森林（GET /api/classes/{id}/forest）
  → 查看学生详情（GET /api/students/{id}/profile）
  → 查看错因轨迹（GET /api/students/{id}/trajectory）
  → 查看掌握度（GET /api/students/{id}/mastery）
```

## 学生端流程（已实现）

### 自主练习流程

```text
学生登录（POST /api/student-auth/login）
  → 查看仪表盘（GET /api/students/{id}/dashboard）
  → 开始练习（POST /api/students/{id}/practice/start）
  → 逐题作答（GET /api/students/{id}/practice/{session_id}/next → POST .../answer）
  → 结束练习（POST /api/students/{id}/practice/{session_id}/end）
```

### 作业查看流程

```text
学生查看待做作业（GET /api/students/{id}/pending-homework）
  → 查看作业详情（GET /api/students/{id}/homework/{hw_id}/problems）
  → 提交答案（POST /api/homework/submit）
  → 查看 PDF（GET /api/students/{id}/homework/{hw_id}/pdf）
```

### 扫码批改流程（部分实现）

```text
学生拍照上传（POST /api/ocr/recognize-work）
  → OCR 识别
  → 自动诊断
  → 返回结果
```

## 未来流程

### 假期模式

```text
假期开始 → 树进入休眠状态
  → 无推送、无排名、无强制打卡
  → 学生可自愿复习已学内容
  → 内容不超前于当前进度
```

### 森林成长（品牌表达层）

```text
学生选择树种 → 每学期一棵树
  → 练习积累可见成长阶段
  → 森林记录长期成长
  → 无比较排行榜
```

## MVP 边界

教师端完整实现（诊断、作业、测验、森林视图、课表、认证）。学生端基础实现（仪表盘、练习、作业查看、测验）。扫码批改端点已定义，部分实现。
