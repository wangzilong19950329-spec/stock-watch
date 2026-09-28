package com.aimeeting.room;

import com.aimeeting.room.service.StockQuoteService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.ApplicationContext;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class StockWatchExtractionTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;
    @Autowired JdbcTemplate jdbc;
    @Autowired ApplicationContext context;
    @MockBean StockQuoteService quoteService;
    private static final Path DATA = tempDir();
    private static Path tempDir() {
        try { return Files.createTempDirectory("stock-watch-tests-"); }
        catch (Exception e) { throw new IllegalStateException(e); }
    }
    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry r) {
        r.add("ai.registry.store-file", () -> DATA.resolve("models.json").toString());
        r.add("stock-watch.ai-rules.store-file", () -> DATA.resolve("rules.json").toString());
        r.add("stock-watch.monitor.state-file", () -> DATA.resolve("monitor.json").toString());
        r.add("stock-watch.monitor.enabled", () -> "false");
        r.add("stock-watch.technical-analysis.enabled", () -> "false");
        r.add("stock-watch.delivery.enabled", () -> "false");
        r.add("notification.email.enabled", () -> "false");
    }
    private String token() throws Exception {
        String user="test_"+UUID.randomUUID().toString().replace("-", "").substring(0,12);
        String body=json.writeValueAsString(Map.of("username",user,"password","test-only-not-a-real-secret"));
        mvc.perform(post("/api/auth/register").contentType("application/json").content(body))
            .andExpect(status().isOk()).andExpect(jsonPath("$.code").value(200));
        String response=mvc.perform(post("/api/auth/login").contentType("application/json").content(body))
            .andExpect(status().isOk()).andExpect(jsonPath("$.code").value(200))
            .andReturn().getResponse().getContentAsString();
        return json.readTree(response).path("data").path("token").asText();
    }
    @Test void authenticationIsNotRemoved() throws Exception {
        mvc.perform(get("/api/stock-watch/watchlist")).andExpect(status().isUnauthorized());
        String token=token();
        mvc.perform(get("/api/auth/me").header("X-Token",token)).andExpect(jsonPath("$.code").value(200));
        mvc.perform(post("/api/auth/logout").header("X-Token",token)).andExpect(jsonPath("$.code").value(200));
        mvc.perform(get("/api/auth/me").header("X-Token",token)).andExpect(status().isUnauthorized());
    }
    @Test void watchlistCreateReadAndDisable() throws Exception {
        String token=token();
        mvc.perform(post("/api/stock-watch/watchlist").header("X-Token",token).contentType("application/json")
            .content("{\"symbol\":\"000001\",\"market\":\"sz\",\"stockName\":\"Test fixture\",\"enabled\":true}"))
            .andExpect(jsonPath("$.code").value(200));
        mvc.perform(get("/api/stock-watch/watchlist").header("X-Token",token))
            .andExpect(jsonPath("$.data[?(@.symbol == '000001')]").isNotEmpty());
        mvc.perform(post("/api/stock-watch/watchlist").header("X-Token",token).contentType("application/json")
            .content("{\"symbol\":\"000001\",\"market\":\"sz\",\"stockName\":\"Test fixture\",\"enabled\":false}"))
            .andExpect(jsonPath("$.code").value(200));
        assertEquals(0,jdbc.queryForObject("SELECT COUNT(*) FROM stock_watch_item WHERE symbol='000001' AND enabled=1",Integer.class));
    }
    @Test void quoteEndpointUsesInjectedFixtureNotLiveProvider() throws Exception {
        Map<String,Object> q=new LinkedHashMap<>();
        q.put("symbol","000001");q.put("market","sz");q.put("ok",true);q.put("price",10.0);
        when(quoteService.fetchQuotes(anyString())).thenReturn(List.of(q));
        mvc.perform(get("/api/stock-watch/quotes").param("symbols","000001.sz").header("X-Token",token()))
            .andExpect(jsonPath("$.code").value(200)).andExpect(jsonPath("$.data[0].price").value(10.0));
    }
    @Test void technicalAnalysisAndDeliveryReadWithoutBridgeOrSmtp() throws Exception {
        String token=token();
        mvc.perform(get("/api/stock-watch/technical-analysis").param("symbol","000001").param("market","sz").header("X-Token",token))
            .andExpect(jsonPath("$.code").value(200));
        mvc.perform(get("/api/stock-watch/technical-analysis/status").header("X-Token",token))
            .andExpect(jsonPath("$.data.enabled").value(false));
        mvc.perform(get("/api/stock-watch/monitor/status").header("X-Token",token))
            .andExpect(jsonPath("$.data.enabled").value(false));
        mvc.perform(get("/api/stock-watch/delivery-config").param("symbol","000001").param("market","sz").header("X-Token",token))
            .andExpect(jsonPath("$.code").value(200));
        mvc.perform(get("/api/stock-watch/delivery-config/preview").param("symbol","000001").param("market","sz").header("X-Token",token))
            .andExpect(jsonPath("$.code").value(200));
    }
    @Test void fcCardAndAiRuleEndpointsHaveTheirDependencies() throws Exception {
        String token=token();
        mvc.perform(get("/api/stock-watch/fc-cards").param("symbol","000001").param("market","sz").header("X-Token",token))
            .andExpect(jsonPath("$.code").value(200));
        String body=json.writeValueAsString(Map.of("symbol","000001","market","sz","name","fixture","conditionText","price > 10","enabled",false));
        String result=mvc.perform(post("/api/stock-watch/ai-rules").contentType("application/json").content(body).header("X-Token",token))
            .andExpect(jsonPath("$.code").value(200)).andReturn().getResponse().getContentAsString();
        String id=json.readTree(result).path("data").path("id").asText();
        assertFalse(id.isEmpty());
        mvc.perform(get("/api/stock-watch/ai-rules").header("X-Token",token)).andExpect(jsonPath("$.code").value(200));
        mvc.perform(delete("/api/stock-watch/ai-rules/"+id).header("X-Token",token)).andExpect(jsonPath("$.code").value(200));
    }
    @Test void modelRegistryAvailableWithoutMeetingEngine() throws Exception {
        mvc.perform(get("/api/config/registry").header("X-Token",token())).andExpect(jsonPath("$.code").value(200));
        assertFalse(context.containsBean("meetingExecutor"));
        assertFalse(context.containsBean("meetingRoomService"));
        assertFalse(context.containsBean("meetingWorkflowService"));
        assertFalse(context.containsBean("dataInitializer"));
    }
    @Test void allSevenStandaloneTablesAreUsable() {
        for(String table:List.of("ai_user","stock_watch_item","stock_watch_technical_session","stock_watch_technical_analysis","stock_watch_delivery_config","stock_watch_delivery_log","stock_watch_fc_card")) {
            assertNotNull(jdbc.queryForObject("SELECT COUNT(*) FROM "+table,Integer.class));
        }
    }
}
