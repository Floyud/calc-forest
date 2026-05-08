# Error Taxonomy

This is the PM-facing source of truth for first-version error codes.

| Code | Label | Typical Signal | Teacher Action |
| --- | --- | --- | --- |
| `E01` | 基础事实错误 | 口诀、口算、基础加减乘除事实错误 | 短时低负荷练习，要求说出计算依据 |
| `E02` | 进位错误 | 加法或乘法中满十进位遗漏或未加 | 显式标注进位，再做同结构少量练习 |
| `E03` | 退位错误 | 减法本位不够减时退位处理错误 | 用数位表复盘退位过程 |
| `E04` | 数位对齐错误 | 竖式错位、小数位或部分积位置错误 | 用方格纸/数位表重写 |
| `E05` | 运算顺序错误 | 混合运算未按括号或先乘除后加减 | 先圈出第一步再计算 |
| `E06` | 小数点/分数单位错误 | 小数点位置、分子分母或分数单位错误 | 先估算范围或统一分数单位 |
| `E07` | 抄题/转写错误 | 数字、符号、条件从题目到步骤变化 | 圈画原题数字和符号后再列式 |
| `E08` | 步骤遗漏 | 漏部分积、漏商位、跳过关键中间步骤 | 要求补齐每步 |
| `E09` | 算理理解不足 | 方法选择错误或迁移失败 | 用图示、操作、反例讲清算理 |
| `E10` | 审题与单位理解错误 | 问题对象或单位理解错误 | 复述问题，标注单位 |
| `E11` | 习惯性未验算 | 结果明显不合理但未发现 | 引入估算、逆运算、代入检查 |
| `E99` | 暂未识别错因 | 规则无法稳定判断 | 提示教师补充步骤或人工判断 |

## MVP Required Coverage

Must cover:

- `E01`
- `E02`
- `E03`
- `E04`
- `E05`
- `E07`
- `E08`
- `E11`

Optional/partial in MVP:

- `E06`
- `E09`
- `E10`

## Diagnosis Output Rule

Every diagnosis must include:

- Code.
- Label.
- Confidence.
- Evidence.
- Teacher action.
- Student-facing hint.
- Review status.
