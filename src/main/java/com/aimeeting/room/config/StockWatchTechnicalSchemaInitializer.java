package com.aimeeting.room.config;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;

/**
 * Standalone schema gate. The dedicated H2/MySQL schema scripts own DDL; this
 * bean keeps the upstream startup dependency explicit and fails fast if SQL
 * initialization did not create the v6 tables.
 */
@Component
@RequiredArgsConstructor
public class StockWatchTechnicalSchemaInitializer {

    private final JdbcTemplate jdbcTemplate;

    @PostConstruct
    public void ensureSchema() {
        jdbcTemplate.queryForObject("SELECT COUNT(*) FROM stock_watch_item", Integer.class);
        jdbcTemplate.queryForObject("SELECT COUNT(*) FROM stock_watch_prediction", Integer.class);
        jdbcTemplate.queryForObject("SELECT COUNT(*) FROM stock_watch_analysis_migration_state", Integer.class);
    }
}
