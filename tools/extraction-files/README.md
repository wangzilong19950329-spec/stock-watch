# Stock Watch · 股票盯盘独立项目

从 `wangzilong19950329-spec/ai-meeting-room-new` 的固定提交
`eb674b736589fe8ddc716c15af3b400342286f57` 抽出实际源码，而非重新编写盯盘业务。
原仓库不修改。本仓库只承接现有功能；此前讨论的 FactPacket、双视角、严格 INVALID_OUTPUT、资金保护等改造**尚未实现**。

## 包含什么

- Vue 盯盘页：自选股、行情刷新、观察条件、FC 卡、日/周/月技术分析、邮件配置。
- Java：9 个 Stock Watch Controller、8 个行情/盯盘 Service、6 组 Entity/Mapper/XML。
- 必要公共依赖：登录注册、Token、ApiResponse、API 模型注册/路由、邮件发送、网页搜索适配。
- 独立启动入口、H2 / MySQL 建表脚本、独立前端路由、DeepSeek 网页桥。
- 无会议、评分、工作流、项目跟踪业务；没有复制原项目数据库行、账户、密钥、Cookie、模型注册 JSON 或浏览器 Profile。

沿用 `com.aimeeting.room` 包名便于追溯源码，不代表运行时依赖原项目。
文件级来源及变更记录见 `docs/extraction-manifest.json`，已知限制见 `docs/KNOWN_LIMITATIONS.md`。

## 快速启动（默认 H2，不需要 MySQL）

前提：Java 11+、Maven 3.8+、Node.js 22+、npm。

```bash
git clone https://github.com/wangzilong19950329-spec/stock-watch.git
cd stock-watch
cp .env.example .env
bash scripts/start-backend.sh
```

另开终端：

```bash
cd stock-watch
bash scripts/start-frontend.sh
```

打开 `http://127.0.0.1:3017`。后端为 `http://127.0.0.1:8117`。
首次使用在本机注册账号，**没有预置 admin 账号或密码**。
默认 H2 数据文件、规则、模型注册数据写入 `./data`，不读取原项目 `.aimeeting-room`。

默认关闭定时监控、自动技术分析和自动邮件；前端手动刷新仍会请求行情。
旧页面包含源项目的演示指标、示意价格线与硬编码状态，请看页面顶部提示。
从“空白独立库”启动不等于旧页面所有静态示例都变成真实数据。

## DeepSeek 网页分析

```bash
bash scripts/start-bridge.sh
```

独立 Bridge 默认 `127.0.0.1:8790`，Chrome 调试端口 `9334`。
第一次调用可能需要先启动专用 Chrome，并在专用 Profile 中手工登录 DeepSeek：

```bash
# macOS 示例；不能指向你的日常浏览器 Profile。
mkdir -p "$HOME/.stock-watch/deepseek-web-profile"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9334 \
  --remote-debugging-address=127.0.0.1 \
  --user-data-dir="$HOME/.stock-watch/deepseek-web-profile" \
  https://chat.deepseek.com/
```

Windows / Linux 可用 `DEEPSEEK_WEB_CHROME_BIN` 指定 Chrome 可执行文件。
Bridge 继承原仓库的页面自动化逻辑；网页变化、账户权限、登录态和供应商限制都可能影响可用性。
**代码构建通过不代表已经验证真实 DeepSeek 登录和回答。**不拷贝个人 Chrome Cookie，不暴露调试端口到公网。

API 模型配置（界面“API 模型配置”）用于原有 AI 观察规则的 API 调用，和网页分析是两条链路。
没有配置 API Key 时不提供伪造模型回答。环境变量只用于首次初始化模型注册文件；后续在界面更新配置。

## MySQL（可选）

先手工创建**新的**空数据库 `stock_watch` 及专用账号；不要指向 `ai_meeting` 或原库。
在 `.env` 配置：

```dotenv
SPRING_PROFILES_ACTIVE=mysql
STOCK_WATCH_DB_URL='jdbc:mysql://127.0.0.1:3306/stock_watch?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai'
STOCK_WATCH_DB_USERNAME=stock_watch
STOCK_WATCH_DB_PASSWORD=填写你本机专用账号的密码
```

启动时加载 `schema-mysql.sql`，仅创建 6 张盯盘表及 1 张认证表；无数据导入、无 DROP、无 USE 原库。
已有数据库的增量升级未包含在本次抽离中。H2 仅作为本机开发入口；MySQL 验证结果以 CI 日志为准。

## 定时分析及邮件

确认手工功能、模型和数据后再在 `.env` 显式启用：

```dotenv
STOCK_WATCH_MONITOR_ENABLED=true
STOCK_WATCH_TECH_ANALYSIS_ENABLED=true
STOCK_WATCH_DELIVERY_ENABLED=true
```

邮件需另设 SMTP 参数和单股收件策略；全局监控邮件还需要
`STOCK_WATCH_NOTIFY_ENABLED=true`、`NOTIFICATION_EMAIL_ENABLED=true` 及全局收件地址。
不要在未核对收件人时启用自动发信。本项目没有自动下单接口。

## 验证

```bash
mvn -B test
mvn -B -DskipTests package
(cd frontend && npm ci && npm run build)
npm run bridge:check
python tools/verify_extraction.py
```

自动化测试使用虚拟行情、隔离临时文件和本机测试数据库，不使用真实密钥、不发邮件、不登录 DeepSeek。
见 `.github/workflows/verify.yml` 和 Actions 运行记录。CI 不能替代真实浏览器和行情/SMTP 联调。

## 安全和继承限制

本版是**单人本机或可信内网工具**，后端、前端和 Bridge 默认仅监听回环地址。
原认证、共享股票空间、自然语言规则阈值、宽松模型解析、示意指标和定时调度逻辑基本保留；
不是互联网多租户服务，不应暴露公网，不是已证明有效的交易决策系统。
模型注册文件包含你后来填写的密钥，请保护 `data/` 和 `.env`，不要提交它们。
未替原作者添加新的开源许可证；上游许可证如存在会保留，见 `docs/EXTRACTION.md`。
