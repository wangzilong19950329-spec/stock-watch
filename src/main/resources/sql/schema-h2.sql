CREATE TABLE IF NOT EXISTS ai_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    password VARCHAR(255) NOT NULL,
    nickname VARCHAR(128),
    gmt_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    gmt_modify TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_ai_user_username ON ai_user(username);

CREATE TABLE IF NOT EXISTS stock_watch_item (
    id         BIGINT      NOT NULL AUTO_INCREMENT,
    symbol     VARCHAR(16) NOT NULL,
    market     VARCHAR(8)  NOT NULL,
    stock_name VARCHAR(128),
    image_url  CLOB,
    enabled    TINYINT     NOT NULL DEFAULT 1,
    source     VARCHAR(32) NOT NULL DEFAULT 'manual',
    gmt_create TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    gmt_modify TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_sw_item_symbol ON stock_watch_item(symbol, market);
CREATE INDEX IF NOT EXISTS idx_sw_item_enabled ON stock_watch_item(enabled, symbol, market);

CREATE TABLE IF NOT EXISTS stock_watch_technical_session (
    id                  BIGINT       NOT NULL AUTO_INCREMENT,
    symbol              VARCHAR(16)  NOT NULL,
    market              VARCHAR(8)   NOT NULL,
    stock_name          VARCHAR(128),
    period_type         VARCHAR(16)  NOT NULL DEFAULT 'DAY',
    session_key         VARCHAR(128) NOT NULL,
    bridge_target_id    VARCHAR(128),
    conversation_url    VARCHAR(1024),
    status              VARCHAR(32)  NOT NULL DEFAULT 'ACTIVE',
    generation          INT          NOT NULL DEFAULT 1,
    context_chars       INT          NOT NULL DEFAULT 0,
    context_limit_chars INT          NOT NULL DEFAULT 80000,
    last_run_at         TIMESTAMP,
    last_run_status     VARCHAR(64),
    last_error          CLOB,
    gmt_create          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    gmt_modify          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_sw_tech_session_symbol ON stock_watch_technical_session(symbol, market, period_type, status);
CREATE INDEX IF NOT EXISTS idx_sw_tech_session_key ON stock_watch_technical_session(session_key);

CREATE TABLE IF NOT EXISTS stock_watch_technical_analysis (
    id                  BIGINT       NOT NULL AUTO_INCREMENT,
    session_id          BIGINT,
    symbol              VARCHAR(16)  NOT NULL,
    market              VARCHAR(8)   NOT NULL,
    stock_name          VARCHAR(128),
    analysis_date       DATE         NOT NULL,
    run_slot            VARCHAR(16)  NOT NULL,
    period_type         VARCHAR(16)  NOT NULL DEFAULT 'DAY',
    period_key          VARCHAR(32),
    source_record_ids   CLOB,
    status              VARCHAR(32)  NOT NULL,
    stance              VARCHAR(64),
    tone                VARCHAR(32),
    confidence          DECIMAL(5,4),
    title               VARCHAR(256),
    conclusion          CLOB,
    evidence_json       CLOB,
    raw_response        CLOB,
    prompt_hash         VARCHAR(128),
    provider            VARCHAR(64),
    bridge_target_id    VARCHAR(128),
    conversation_url    VARCHAR(1024),
    context_chars_delta INT          DEFAULT 0,
    error_message       CLOB,
    gmt_create          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_sw_tech_analysis_symbol_date ON stock_watch_technical_analysis(symbol, market, period_type, analysis_date);
CREATE INDEX IF NOT EXISTS idx_sw_tech_analysis_session ON stock_watch_technical_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_sw_tech_analysis_slot ON stock_watch_technical_analysis(symbol, market, period_type, period_key, analysis_date, run_slot);
CREATE INDEX IF NOT EXISTS idx_sw_tech_analysis_period ON stock_watch_technical_analysis(symbol, market, period_type, period_key);

CREATE TABLE IF NOT EXISTS stock_watch_delivery_config (
    id                    BIGINT       NOT NULL AUTO_INCREMENT,
    symbol                VARCHAR(16)  NOT NULL,
    market                VARCHAR(8)   NOT NULL,
    stock_name            VARCHAR(128),
    enabled               TINYINT      NOT NULL DEFAULT 0,
    recipients_json       CLOB         NOT NULL,
    sender_mode           VARCHAR(32)  NOT NULL DEFAULT 'SYSTEM',
    frequency_type        VARCHAR(32)  NOT NULL DEFAULT 'MANUAL',
    interval_minutes      INT          NOT NULL DEFAULT 120,
    trigger_policy_json   CLOB,
    active_from           TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_dispatch_status  VARCHAR(32),
    last_dispatch_message CLOB,
    last_dispatch_at      TIMESTAMP,
    gmt_create            TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    gmt_modify            TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_sw_delivery_config_symbol ON stock_watch_delivery_config(symbol, market);
CREATE INDEX IF NOT EXISTS idx_sw_delivery_config_enabled ON stock_watch_delivery_config(enabled, frequency_type);

CREATE TABLE IF NOT EXISTS stock_watch_delivery_log (
    id               BIGINT       NOT NULL AUTO_INCREMENT,
    config_id        BIGINT       NOT NULL,
    analysis_id      BIGINT       NOT NULL,
    symbol           VARCHAR(16)  NOT NULL,
    market           VARCHAR(8)   NOT NULL,
    recipient_hash   VARCHAR(64)  NOT NULL,
    recipient_masked VARCHAR(255) NOT NULL,
    status           VARCHAR(32)  NOT NULL,
    message_id       VARCHAR(255),
    error_message    CLOB,
    sent_at          TIMESTAMP,
    gmt_create       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    gmt_modify       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_sw_delivery_once ON stock_watch_delivery_log(analysis_id, recipient_hash);
CREATE INDEX IF NOT EXISTS idx_sw_delivery_config_status ON stock_watch_delivery_log(config_id, status);
CREATE INDEX IF NOT EXISTS idx_sw_delivery_symbol_time ON stock_watch_delivery_log(symbol, market, gmt_create);

CREATE TABLE IF NOT EXISTS stock_watch_fc_card (
    id                  BIGINT       NOT NULL AUTO_INCREMENT,
    symbol              VARCHAR(16)  NOT NULL,
    market              VARCHAR(8)   NOT NULL,
    stock_name          VARCHAR(128),
    card_key            VARCHAR(128) NOT NULL,
    card_title          VARCHAR(256) NOT NULL,
    card_type           VARCHAR(64),
    thesis              CLOB,
    trigger_logic       CLOB,
    data_source_tier    VARCHAR(32),
    data_sources        CLOB,
    collection_method   VARCHAR(32),
    frequency           VARCHAR(128),
    parser_spec         CLOB,
    baseline_reading    CLOB,
    failure_monitor     CLOB,
    auto_proxy          CLOB,
    activation_status   VARCHAR(32)  NOT NULL DEFAULT 'DRAFT',
    activation_blockers CLOB,
    enabled             TINYINT      NOT NULL DEFAULT 0,
    notify_enabled      TINYINT      NOT NULL DEFAULT 1,
    last_collect_status VARCHAR(64),
    last_collect_note   CLOB,
    last_collected_at   TIMESTAMP,
    raw_markdown        CLOB,
    gmt_create          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    gmt_modify          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_sw_fc_card_key ON stock_watch_fc_card(symbol, market, card_key);
CREATE INDEX IF NOT EXISTS idx_sw_fc_card_symbol_status ON stock_watch_fc_card(symbol, market, activation_status);
CREATE INDEX IF NOT EXISTS idx_sw_fc_card_enabled ON stock_watch_fc_card(enabled, symbol, market);
