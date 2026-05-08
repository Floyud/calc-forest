# Calc Forest

产品侧工作区，对应 **我的计算森林** 的后续正式产品实现。

这个目录与 `development/` 区分：

- `development/` 用于当前 MVP 后端、规则验证、测试和演示数据。
- `calc_forest/` 用于后续真正的产品工程、界面实现和独立 git 管理准备。

## Naming

`calc_forest` 取自“计算 + 森林”，保持 ASCII 路径，便于后续单独初始化 git、接入前端工程、部署脚本或产品资源目录。

## Current Role

- 作为产品实现主目录预留。
- 默认不承载当前 `development/` 中的 MVP 诊断服务。
- 后续如果开始做正式产品端，优先从这里起步。
- 当前优先方向是 `dify/`，用于沉淀 Dify 工作流、演示输入和产品侧配置资产。

## Suggested Next Step

如果你后面准备把这里单独作为产品仓管理，可以直接在本目录内初始化 git，并逐步放入：

- 前端应用
- 产品配置
- UI 资源
- 部署脚本
- 与 `development/` 对接的 API client

## Current Workspace

- `dify/`：Dify 工作流构建清单、演示输入和产品侧运行资产
