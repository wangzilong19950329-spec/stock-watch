package com.aimeeting.room;

import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.datasource.init.ScriptUtils;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;

import static org.junit.jupiter.api.Assertions.assertEquals;

class StockWatchSchemaRestartPersistenceTest {

    @Test
    void rerunningStandaloneSchemaDoesNotResetOperationalState() throws Exception {
        String url = "jdbc:h2:mem:standalone_schema_restart;MODE=MySQL;DB_CLOSE_DELAY=-1";
        try (Connection connection = DriverManager.getConnection(url, "sa", "")) {
            applySchema(connection);
            try (Statement statement = connection.createStatement()) {
                statement.executeUpdate(
                        "UPDATE stock_watch_analysis_migration_state "
                                + "SET generation = 17, status = 'CUTOVER_READY', technical_task_cutoff_id = 41, "
                                + "legacy_analysis_cutoff_id = 42, legacy_analysis_count = 43, plan_hash = 'preserve-me' "
                                + "WHERE migration_key = 'stock-watch-v6'");
                statement.executeUpdate(
                        "UPDATE stock_watch_analysis_scheduler_ownership "
                                + "SET mode = 'V6', generation = 19, row_version = 23, last_error = 'preserve-me' "
                                + "WHERE id = 1");
            }

            applySchema(connection);

            try (Statement statement = connection.createStatement();
                 ResultSet state = statement.executeQuery(
                         "SELECT generation, status, technical_task_cutoff_id, legacy_analysis_cutoff_id, "
                                 + "legacy_analysis_count, plan_hash FROM stock_watch_analysis_migration_state "
                                 + "WHERE migration_key = 'stock-watch-v6'")) {
                state.next();
                assertEquals(17, state.getInt("generation"));
                assertEquals("CUTOVER_READY", state.getString("status"));
                assertEquals(41L, state.getLong("technical_task_cutoff_id"));
                assertEquals(42L, state.getLong("legacy_analysis_cutoff_id"));
                assertEquals(43L, state.getLong("legacy_analysis_count"));
                assertEquals("preserve-me", state.getString("plan_hash"));
            }
            try (Statement statement = connection.createStatement();
                 ResultSet ownership = statement.executeQuery(
                         "SELECT mode, generation, row_version, last_error "
                                 + "FROM stock_watch_analysis_scheduler_ownership WHERE id = 1")) {
                ownership.next();
                assertEquals("V6", ownership.getString("mode"));
                assertEquals(19L, ownership.getLong("generation"));
                assertEquals(23L, ownership.getLong("row_version"));
                assertEquals("preserve-me", ownership.getString("last_error"));
            }
        }
    }

    private void applySchema(Connection connection) {
        ScriptUtils.executeSqlScript(connection, new ClassPathResource("sql/schema-h2.sql"));
    }
}
