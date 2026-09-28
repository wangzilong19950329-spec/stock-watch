package com.aimeeting.room.controller;

import com.aimeeting.room.common.ApiResponse;
import com.aimeeting.room.config.ModelEntry;
import com.aimeeting.room.config.ModelRegistryStore;
import com.aimeeting.room.service.NotificationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/api/config")
@RequiredArgsConstructor
public class ConfigController {

    private final ModelRegistryStore registry;
    private final NotificationService notificationService;

    // ============================================================
    // 模型注册表 CRUD
    // ============================================================

    /** 获取所有已配置模型（API Key 脱敏） */
    @GetMapping("/registry")
    public ApiResponse<List<Map<String, Object>>> listRegistry() {
        List<Map<String, Object>> result = registry.getAll().stream().map(e -> {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id",          e.getId());
            m.put("displayName", e.getDisplayName());
            m.put("modelId",     e.getModelId());
            m.put("apiUrl",      e.getApiUrl());
            m.put("apiKey",      ModelRegistryStore.maskKey(e.getApiKey()));
            m.put("apiFormat",   e.getApiFormat());
            m.put("enabled",     e.isEnabled());
            return m;
        }).collect(Collectors.toList());
        return ApiResponse.ok(result);
    }

    /** 新增模型 */
    @PostMapping("/registry")
    public ApiResponse<ModelEntry> addModel(@RequestBody ModelEntry entry) {
        if (entry.getDisplayName() == null || entry.getDisplayName().isBlank())
            return ApiResponse.fail("displayName 不能为空");
        if (entry.getModelId() == null || entry.getModelId().isBlank())
            return ApiResponse.fail("modelId 不能为空");
        if (entry.getApiUrl() == null || entry.getApiUrl().isBlank())
            return ApiResponse.fail("apiUrl 不能为空");
        if (entry.getApiFormat() == null) entry.setApiFormat("openai");

        ModelEntry saved = registry.add(entry);
        log.info("Model added: {} ({})", saved.getDisplayName(), saved.getModelId());
        return ApiResponse.ok(saved);
    }

    /** 更新模型（apiKey 含 *** 则不修改） */
    @PutMapping("/registry/{id}")
    public ApiResponse<Void> updateModel(@PathVariable String id, @RequestBody ModelEntry entry) {
        ModelEntry existing = registry.getById(id);
        if (existing == null) return ApiResponse.fail(404, "模型不存在");

        // 未传入真实 key 时保留原 key
        if (entry.getApiKey() == null || entry.getApiKey().contains("***")) {
            entry.setApiKey(existing.getApiKey());
        }
        registry.update(id, entry);
        log.info("Model updated: {}", id);
        return ApiResponse.ok(null);
    }

    /** 删除模型 */
    @DeleteMapping("/registry/{id}")
    public ApiResponse<Void> deleteModel(@PathVariable String id) {
        if (!registry.delete(id)) return ApiResponse.fail(404, "模型不存在");
        log.info("Model deleted: {}", id);
        return ApiResponse.ok(null);
    }

    /** 供股票观察规则选择模型使用：返回所有已启用的模型列表 */
    @GetMapping("/available-models")
    public ApiResponse<List<Map<String, Object>>> availableModels() {
        List<Map<String, Object>> list = registry.getEnabled().stream().map(e -> {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("modelKey",    e.getId());
            m.put("modelId",     e.getModelId());
            m.put("displayName", e.getDisplayName());
            m.putAll(buildVerificationMeta(e.getId()));
            return m;
        }).collect(Collectors.toList());
        return ApiResponse.ok(list);
    }

    private Map<String, Object> buildVerificationMeta(String modelKey) {
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("verificationStatus", "unverified");
        meta.put("verificationLabel", "未验证");
        meta.put("verificationNote", "独立仓库未运行真实模型验证；注册配置不代表模型可用。");
        meta.put("recommended", false);
        return meta;
    }


    @PostMapping("/notification/test-email")
    public ApiResponse<Map<String, Object>> sendTestEmail(@RequestBody(required = false) Map<String, String> body) {
        String subject = body != null ? body.get("subject") : null;
        String content = body != null ? body.get("content") : null;
        boolean sent = notificationService.sendEmail(
                firstNonBlank(subject, "Stock Watch · 邮件通知测试"),
                firstNonBlank(content, "如果你收到这封邮件，说明 SMTP 邮件通知已经配置成功。")
        );
        if (!sent) {
            return ApiResponse.fail("邮件未发送：请确认 NOTIFICATION_EMAIL_ENABLED=true、SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD、NOTIFICATION_EMAIL_TO 已配置，并查看后端日志");
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("sent", true);
        return ApiResponse.ok(result);
    }

    private String firstNonBlank(String value, String fallback) {
        return value == null || value.trim().isEmpty() ? fallback : value.trim();
    }
}
