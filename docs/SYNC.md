# 当前同步基线

- 源仓库：`https://github.com/wangzilong19950329-spec/ai-meeting-room-new`
- 源提交：`2f816607b920bd1c71e37a2d72ccf965c332140f`
- 目标仓库：`https://github.com/wangzilong19950329-spec/stock-watch`

## 本次包含

- 当前 Stock Watch Controller、Service、Entity、Mapper、SQL schema 与测试。
- 当前盯盘前端、预测复盘、方向/区间/背离统计及 M30 预测展示。
- V6 分析需求、任务、事实、预测、调度所有权、告警投递和价格失败研究数据结构。
- DeepSeek Bridge 实现、请求身份/账本/账号 broker、健康检查与相关 Node 测试。
- 独立 Docker 镜像与 Compose 部署入口。

## 明确不包含

- 会议、评分、项目追踪和 n8n 业务编排模块。
- 源项目数据库、历史运行数据、`.env`、API Key、Cookie、Chrome Profile 或任何个人登录态。
- 从源数据库导出的研究指标/样本、包含本机绝对路径的研究产物，以及源项目专用的启动包装脚本。
- 源项目前后端进程、容器和数据卷的迁移或替换。

`docs/extraction-manifest.json` 记录的是项目最初从源仓库抽离时的历史文件指纹；当前同步后的验收以
`SOURCE_REVISION`、`tools/verify_extraction.py`、构建测试和真实容器 smoke 为准。
