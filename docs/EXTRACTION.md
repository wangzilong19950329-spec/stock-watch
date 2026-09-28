# 抽离边界与来源

源仓库：`wangzilong19950329-spec/ai-meeting-room-new`
源提交：`eb674b736589fe8ddc716c15af3b400342286f57`

## 文件选择

复制 `Stock*.java` 的 Controller / Service / DAO / Entity 以及 `Stock*.xml`；
补齐认证、ApiResponse、模型注册/路由/通用客户端及其搜索依赖，前端保留 StockWatch/Login/ModelConfig。
不复制会议、投票、奖励评分、工作流、追踪、默认账户初始化器、个人数据文件或上游 Git 历史。

## 必要适配

- 新入口 StockWatchApplication；保留 Java 包名及 Mapper namespace。
- AppConfig 仅保留密码编码器，删除会议线程池和会议引擎配置。
- ConfigController/ModelConfig.vue 仅保留模型注册及邮件测试，移除会议设置和旧模型已验证宣称。
- NotificationService 仅保留邮件能力，移除会议通知和会议 ServerChan 方法。
- 使用显式、失败即终止的 SQL 初始化，只加载 6 张 Stock Watch 表及 ai_user；H2 补齐 FC 卡表。
- 端口 8117/3017/8790/9334 和 ./data、~/.stock-watch 独立；不读取原 .aimeeting-room 的运行数据。
- 新浏览器 Profile 不复制日常 Chrome 的 Cookie/会话，要求手工登录。
- 默认自动任务、自动通知关闭；前端持续显示遗留模拟数据警告。
- 依赖版本保持上游选择；新增测试而非升级业务架构。

## 再现和验收

`tools/extract_stock_watch.py` 是生成器：输入指定版本的只读源码和一个空目录。
静态适配文件位于 `tools/extraction-files/`，便于审阅，不含运行数据。
输出 `docs/extraction-manifest.json` 记录每份保留/修改文件的源 SHA-256、目标 SHA-256 和适配原因。
`tools/verify_extraction.py` 检查内部依赖闭环、业务模块边界、SQL 表范围及文件指纹。
测试只使用虚拟行情和测试账户；这些是测试夹具，不是原用户数据。
后续修改正式代码时，应同步维护指纹或把“初次抽离指纹”校验作为单独审计任务，不能自动覆盖用户改动。

## 历史和许可

这是一次带来源清单的源码快照抽离，不迁移完整 Git 历史，避免混入无关模块及历史数据。
保留上游现有许可证文件（若存在）；本次未自行声明 MIT/Apache 等新许可证。

## 回滚

目标仓库在独立分支生成代码，构建通过后再发布；原仓库无写操作。
只需停用独立进程即可，不会改变原项目。禁止让独立项目连接原业务库。
