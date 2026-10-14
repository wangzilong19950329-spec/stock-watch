#!/usr/bin/env python3
"""Offline checks for the current standalone sync and its isolation boundary."""

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPOSITORY = "https://github.com/wangzilong19950329-spec/ai-meeting-room-new"
SOURCE_COMMIT = "2f816607b920bd1c71e37a2d72ccf965c332140f"
EXPECTED_TABLES = {
    "ai_user",
    "stock_watch_item",
    "stock_watch_technical_session",
    "stock_watch_technical_analysis",
    "stock_watch_prediction",
    "stock_watch_fact_head",
    "stock_watch_fact_observation",
    "stock_watch_intent_test",
    "stock_watch_intent_test_result",
    "stock_watch_analysis_task",
    "stock_watch_analysis_observation_identity",
    "stock_watch_analysis_identity_candidate",
    "stock_watch_analysis_migration_state",
    "stock_watch_delivery_config",
    "stock_watch_delivery_log",
    "stock_watch_analysis_demand",
    "stock_watch_analysis_scheduler_ownership",
    "stock_watch_alert_delivery_obligation",
    "stock_watch_price_failure_state",
    "stock_watch_price_failure_assessment",
    "stock_watch_price_failure_ledger",
    "stock_watch_fc_card",
}
REQUIRED_PATHS = {
    "Dockerfile",
    "compose.yaml",
    "docs/SYNC.md",
    "docs/extraction-manifest.json",
    "frontend/src/modules/stock-watch/components/M30ForecastLine.vue",
    "frontend/src/modules/stock-watch/runtime/intradayForecast.mjs",
    "frontend/src/modules/stock-watch/runtime/predictionHistory.mjs",
    "scripts/deepseek-request-ledger.js",
    "scripts/deepseek-account-broker.js",
    "src/main/java/com/aimeeting/room/service/StockWatchPredictionService.java",
    "src/main/java/com/aimeeting/room/service/StockWatchAnalysisTaskService.java",
}


def tracked_and_pending_files():
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    )
    return {line.strip() for line in output.splitlines() if line.strip()}


revision = dict(
    line.split("=", 1)
    for line in (ROOT / "SOURCE_REVISION").read_text("utf-8").splitlines()
    if "=" in line
)
assert revision == {"repository": SOURCE_REPOSITORY, "commit": SOURCE_COMMIT}, revision

files = tracked_and_pending_files()
missing = sorted(REQUIRED_PATHS - files)
assert not missing, f"Missing synced paths: {missing}"
assert ".env" not in files
assert not any(path.startswith("data/") for path in files), "Runtime data must stay untracked"
assert not any(path.startswith("docs/research/") for path in files), (
    "Database-derived research artifacts must not be copied into the standalone repository"
)

classes = {}
for path in (ROOT / "src/main/java").rglob("*.java"):
    text = path.read_text("utf-8")
    package_match = re.search(r"^package\s+([\w.]+);", text, re.M)
    assert package_match, f"Missing package declaration: {path}"
    classes[package_match.group(1) + "." + path.stem] = path

for path in classes.values():
    text = path.read_text("utf-8")
    for imported in re.findall(r"^import (com\.aimeeting\.[\w.]+);", text, re.M):
        assert any(imported == name or imported.startswith(name + ".") for name in classes), (
            path,
            imported,
        )
    assert not path.stem.startswith(("AiMeeting", "AiWorkflow", "Meeting", "Workflow", "Tracking")), path

for schema_name in ("schema-h2.sql", "schema-mysql.sql"):
    schema = (ROOT / "src/main/resources/sql" / schema_name).read_text("utf-8")
    tables = set(re.findall(r"CREATE TABLE IF NOT EXISTS\s+`?(\w+)", schema, re.I))
    assert tables == EXPECTED_TABLES, (schema_name, sorted(tables ^ EXPECTED_TABLES))
    assert not re.search(r"\b(DROP TABLE|USE ai_meeting)\b", schema, re.I), schema_name
    insert_targets = set(re.findall(r"INSERT INTO\s+`?(\w+)", schema, re.I))
    assert insert_targets <= {
        "stock_watch_analysis_migration_state",
        "stock_watch_analysis_scheduler_ownership",
    }, (schema_name, insert_targets)

standalone_runtime_paths = (
    "scripts/deepseek-web-client.js",
    "scripts/deepseek-web-bridge.js",
    "scripts/deepseek-account-broker.js",
    "scripts/start-bridge.sh",
    "scripts/run-stock-watch-v6-migration.sh",
)
for relative in standalone_runtime_paths:
    text = (ROOT / relative).read_text("utf-8")
    assert ".aimeeting-room" not in text, relative

package_json = (ROOT / "package.json").read_text("utf-8")
assert '"bridge": "bash scripts/start-bridge.sh"' in package_json

compose = (ROOT / "compose.yaml").read_text("utf-8")
for expected in (
    "name: stock-watch-standalone-v2",
    "container_name: stock-watch-standalone-v2",
    "stock-watch-standalone-v2-data",
    "127.0.0.1:3017:8117",
    "127.0.0.1:8117:8117",
):
    assert expected in compose, expected
for flag in (
    "AI_SCHEDULING_ENABLED",
    "STOCK_WATCH_MONITOR_ENABLED",
    "STOCK_WATCH_NOTIFY_ENABLED",
    "STOCK_WATCH_TECH_ANALYSIS_ENABLED",
    "STOCK_WATCH_PREDICTION_EVALUATION_ENABLED",
    "STOCK_WATCH_DELIVERY_ENABLED",
    "STOCK_WATCH_PRICE_FAILURE_RESEARCH_ENABLED",
    "STOCK_WATCH_M30_ENABLED",
):
    assert re.search(rf"{flag}:\s*[\"']false[\"']", compose), flag

secret_pattern = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{25,}|sk-[A-Za-z0-9]{32,}"
)
for relative in sorted(files):
    path = ROOT / relative
    if not path.is_file() or path.stat().st_size > 2_000_000:
        continue
    try:
        text = path.read_text("utf-8")
    except UnicodeDecodeError:
        continue
    assert not secret_pattern.search(text), relative

print(
    f"PASS: source {SOURCE_COMMIT[:8]}; {len(classes)} Java classes; "
    f"{len(EXPECTED_TABLES)} isolated tables; {len(files)} tracked/pending files"
)
