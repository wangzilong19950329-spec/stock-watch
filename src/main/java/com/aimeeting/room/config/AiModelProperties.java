package com.aimeeting.room.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

@Component
@ConfigurationProperties(prefix = "ai")
@Data
public class AiModelProperties {

    private String defaultModel = "gpt-4";
    private Map<String, ModelConfig> models = new HashMap<>();

    @Data
    public static class ModelConfig {
        private String apiUrl;
        private String apiKey;
        private String secretKey;
        private String apiVersion;
        private boolean enabled = false;
    }

}
