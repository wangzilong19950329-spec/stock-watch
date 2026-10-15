# Stock Watch · 股票盯盘独立项目

这是从 `wangzilong19950329-spec/ai-meeting-room-new` 同步出来的独立 Stock Watch 应用。
当前代码基线固定为源提交 `2f816607b920bd1c71e37a2d72ccf965c332140f`；同步边界见
[`docs/SYNC.md`](docs/SYNC.md)。

## 当前能力

- 自选股、实时行情、分钟 Bar、观察条件、FC 卡和邮件配置。
- 日/周/月与 M30 技术分析、预测历史、方向/区间/宽松方向/背离复盘。
- V6 分析需求、任务、事实、预测、调度所有权、告警投递和价格失败研究链路。
- 独立 DeepSeek Bridge 代码与 Bridge-first 调用协议。
- H2/MySQL schema、独立前端、后端和单容器部署。

项目不包含会议、评分、项目追踪和 n8n 业务模块，也不复制源项目数据库、账号、密钥、Cookie
或浏览器 Profile。沿用 `com.aimeeting.room` 包名只为保持源码兼容和可追溯性。

## Docker 启动（推荐）

```bash
git clone https://github.com/wangzilong19950329-spec/stock-watch.git
cd stock-watch
docker compose up -d --build
```

打开 `http://127.0.0.1:3017`，后端也可通过 `http://127.0.0.1:8117` 访问。首次使用请注册本机账号。

Compose 使用独立的：

- project：`stock-watch-standalone-v2`
- container：`stock-watch-standalone-v2`
- volume：`stock-watch-standalone-v2-data`
- ports：`3017` / `8117`

这些名字和端口不会替换源项目现有容器。默认关闭监控、通知、技术分析、预测验真、价格失败研究、
投递和 M30 自动任务，避免新实例刚启动就产生外部调用。

## 本机开发

前提：Java 11+、Maven 3.8+、Node.js 22+、npm。

```bash
cp .env.example .env
bash scripts/start-backend.sh
```

另开终端：

```bash
bash scripts/start-frontend.sh
```

默认使用独立 H2 数据目录 `./data`，不读取源项目的 `.aimeeting-room` 数据。

## DeepSeek Bridge

本机独立 Bridge 可这样启动：

```bash
bash scripts/start-bridge.sh
```

它默认监听 `127.0.0.1:8790`，使用 `~/.stock-watch/` 下的专用 Profile 和会话文件。首次使用需在专用
Chrome Profile 中手工登录 DeepSeek。不要指向日常浏览器 Profile，也不要把调试端口暴露到公网。

仓库内的 Compose 默认连接本项目宿主机 Bridge `http://host.docker.internal:8790/search`，不复用源项目的
8791 Bridge、Cookie 或浏览器 Profile。供 Docker 容器访问时，Bridge 必须绑定宿主机并启用认证：

```bash
DEEPSEEK_WEB_BRIDGE_HOST=0.0.0.0 \
DEEPSEEK_OPENAI_FACADE_API_KEY='...' \
bash scripts/start-bridge.sh
```

启动 Compose 时传入同一个 Key：

```bash
DEEPSEEK_OPENAI_FACADE_API_KEY='...' docker compose up -d
```

也可用 `STOCK_WATCH_TECH_BRIDGE_URL` 和 `STOCK_WATCH_AI_RULES_BRIDGE_URL` 指向另一个独立 Bridge。
Bridge 进程在线不代表 DeepSeek 登录态、账号容量或真实回答已经可用。

## MySQL（可选）

请创建新的空数据库和专用账号，禁止指向源项目业务库：

```dotenv
SPRING_PROFILES_ACTIVE=mysql
STOCK_WATCH_DB_URL='jdbc:mysql://127.0.0.1:3306/stock_watch?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai'
STOCK_WATCH_DB_USERNAME=stock_watch
STOCK_WATCH_DB_PASSWORD=填写专用密码
```

H2/MySQL schema 都包含 1 张认证表和 21 张 Stock Watch 表。已有数据库升级应先备份并走迁移流程，
不要把新的 schema 直接当成历史库迁移工具。

## 验证

```bash
mvn -B test
(cd frontend && npm ci && npm run build)
node --test scripts/deepseek-*.test.js scripts/run-stock-watch-v6-migration.test.js scripts/stock-watch-ai-rule-expert-smoke.test.js
python3 tools/verify_extraction.py
docker compose config
```

自动化测试不登录 DeepSeek、不发送邮件、不使用真实密钥。完整边界见
[`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md)。本项目不是自动下单系统，也不构成投资建议。
