package com.aimeeting.room.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.List;
import java.util.Properties;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 股票盯盘邮件通知服务。
 * Server酱和邮件通道均为可选配置，未配置时自动跳过。
 */
@Slf4j
@Service
public class NotificationService {


    @Value("${notification.email.enabled:false}")
    private boolean emailEnabled;

    @Value("${notification.email.from:}")
    private String emailFrom;

    @Value("${notification.email.to:}")
    private String emailTo;

    @Value("${spring.mail.host:}")
    private String mailHost;

    @Value("${spring.mail.username:}")
    private String mailUsername;

    private final ObjectProvider<JavaMailSender> mailSenderProvider;


    public NotificationService(ObjectProvider<JavaMailSender> mailSenderProvider) {
        this.mailSenderProvider = mailSenderProvider;
    }

/**
     * 给后续 stock-watch / 插件式 dispatcher 复用的通用邮件入口。
     */
    public boolean sendStockWatchAlert(String alertTitle, String alertContent) {
        return sendEmail(alertTitle, alertContent);
    }

    /**
     * 股票盯盘单股配置使用的发送入口。这里不读取 notification.email.to，
     * 收件人必须由调用方显式传入，避免全局邮箱污染单股策略。
     */
    public EmailSendResult sendStockWatchAlertToRecipients(String alertTitle,
                                                           String alertContent,
                                                           List<String> recipients,
                                                           EmailSenderConfig senderConfig) {
        List<String> normalizedRecipients = recipients == null
                ? List.of()
                : recipients.stream()
                .map(item -> item == null ? "" : item.trim())
                .filter(item -> !item.isEmpty())
                .distinct()
                .collect(Collectors.toList());
        if (normalizedRecipients.isEmpty()) {
            return EmailSendResult.fail("收件邮箱为空");
        }

        JavaMailSender mailSender = resolveMailSender(senderConfig);
        if (mailSender == null) {
            return EmailSendResult.fail("SMTP 未配置或 JavaMailSender 未初始化");
        }

        SimpleMailMessage message = new SimpleMailMessage();
        message.setTo(normalizedRecipients.toArray(new String[0]));
        String from = senderConfig != null && !isBlank(senderConfig.getFrom())
                ? senderConfig.getFrom()
                : firstNonBlank(emailFrom, mailUsername);
        if (!isBlank(from)) {
            message.setFrom(from);
        }
        message.setSubject(firstNonBlank(alertTitle, "Stock Watch 通知"));
        message.setText(firstNonBlank(alertContent, "Stock Watch 有新的分析结论。"));

        try {
            mailSender.send(message);
            String messageId = "stock-watch-" + UUID.randomUUID();
            log.info("股票盯盘邮件发送成功: subject={}, recipients={}", message.getSubject(), normalizedRecipients);
            return EmailSendResult.ok(messageId);
        } catch (Exception e) {
            log.warn("股票盯盘邮件发送失败: {}", e.getMessage());
            return EmailSendResult.fail(e.getMessage());
        }
    }

    /**
     * 发送通用邮件通知。
     *
     * @return true 表示已提交给 SMTP 客户端；false 表示未启用或配置不完整。
     */
    public boolean sendEmail(String subject, String content) {
        if (!emailEnabled) {
            log.debug("邮件通知未启用，跳过");
            return false;
        }
        if (isBlank(mailHost)) {
            log.warn("邮件通知已启用，但 SMTP_HOST 未配置");
            return false;
        }

        List<String> recipients = parseRecipients(emailTo);
        if (recipients.isEmpty()) {
            log.warn("邮件通知已启用，但 NOTIFICATION_EMAIL_TO 未配置");
            return false;
        }

        JavaMailSender mailSender = mailSenderProvider.getIfAvailable();
        if (mailSender == null) {
            log.warn("邮件通知已启用，但 JavaMailSender 未初始化，请检查 spring.mail 配置");
            return false;
        }

        SimpleMailMessage message = new SimpleMailMessage();
        message.setTo(recipients.toArray(new String[0]));
        String from = firstNonBlank(emailFrom, mailUsername);
        if (!isBlank(from)) {
            message.setFrom(from);
        }
        message.setSubject(firstNonBlank(subject, "Stock Watch通知"));
        message.setText(firstNonBlank(content, "有新的通知事件。"));

        try {
            mailSender.send(message);
            log.info("邮件通知发送成功: subject={}, recipients={}", message.getSubject(), recipients);
            return true;
        } catch (Exception e) {
            log.warn("邮件通知发送失败: {}", e.getMessage());
            return false;
        }
    }

    private JavaMailSender resolveMailSender(EmailSenderConfig senderConfig) {
        if (senderConfig != null && senderConfig.isCustom()) {
            if (isBlank(senderConfig.getHost())) {
                return null;
            }
            JavaMailSenderImpl sender = new JavaMailSenderImpl();
            sender.setHost(senderConfig.getHost().trim());
            sender.setPort(senderConfig.getPort() == null ? 465 : senderConfig.getPort());
            if (!isBlank(senderConfig.getUsername())) {
                sender.setUsername(senderConfig.getUsername().trim());
            }
            if (!isBlank(senderConfig.getPassword())) {
                sender.setPassword(senderConfig.getPassword());
            }
            sender.setProtocol("smtp");
            Properties properties = sender.getJavaMailProperties();
            properties.put("mail.smtp.auth", String.valueOf(!isBlank(senderConfig.getUsername())));
            properties.put("mail.smtp.ssl.enable", String.valueOf(senderConfig.isSsl()));
            properties.put("mail.smtp.starttls.enable", String.valueOf(senderConfig.isStarttls()));
            properties.put("mail.smtp.connectiontimeout", "10000");
            properties.put("mail.smtp.timeout", "15000");
            properties.put("mail.smtp.writetimeout", "15000");
            return sender;
        }
        if (isBlank(mailHost)) {
            log.warn("系统 SMTP_HOST 未配置，无法发送股票盯盘邮件");
            return null;
        }
        return mailSenderProvider.getIfAvailable();
    }



    private List<String> parseRecipients(String raw) {
        if (isBlank(raw)) {
            return List.of();
        }
        return Arrays.stream(raw.split("[,;\\n]"))
                .map(String::trim)
                .filter(item -> !item.isEmpty())
                .distinct()
                .collect(Collectors.toList());
    }

    private String firstNonBlank(String... values) {
        if (values == null) {
            return "";
        }
        for (String value : values) {
            if (!isBlank(value)) {
                return value.trim();
            }
        }
        return "";
    }

    private String safeText(String value) {
        return value == null ? "" : value;
    }

    private boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }

    @lombok.Data
    public static class EmailSenderConfig {
        private boolean custom;
        private String host;
        private Integer port;
        private String username;
        private String password;
        private String from;
        private boolean ssl = true;
        private boolean starttls = false;
    }

    @lombok.Data
    public static class EmailSendResult {
        private boolean success;
        private String messageId;
        private String errorMessage;

        public static EmailSendResult ok(String messageId) {
            EmailSendResult result = new EmailSendResult();
            result.success = true;
            result.messageId = messageId;
            return result;
        }

        public static EmailSendResult fail(String errorMessage) {
            EmailSendResult result = new EmailSendResult();
            result.success = false;
            result.errorMessage = errorMessage == null ? "unknown" : errorMessage;
            return result;
        }
    }
}
