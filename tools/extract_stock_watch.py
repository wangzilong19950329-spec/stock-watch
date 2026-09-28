#!/usr/bin/env python3
"""Extract a pinned stock-watch snapshot; never modify the upstream checkout.
Run: python tools/extract_stock_watch.py SOURCE_DIR EMPTY_OUTPUT_DIR
No credentials, git history, database rows or runtime JSON files are copied.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

SOURCE_SHA = 'eb674b736589fe8ddc716c15af3b400342286f57'
BASE = 'src/main/java/com/aimeeting/room/'
manifest = []

def require_replace(text, old, new, count=1):
    if text.count(old) != count:
        raise ValueError('Upstream content changed; expected %s occurrences: %r' % (count, old[:100]))
    return text.replace(old, new)

def remove_method(text, signature):
    """Remove one Java method, respecting braces inside quoted strings/comments."""
    start = text.index(signature)
    opening = text.index('{', start)
    level, state, i = 1, 'code', opening + 1
    while level:
        ch = text[i]
        nxt = text[i:i+2]
        if state == 'line':
            if ch == '\n': state = 'code'
        elif state == 'comment':
            if nxt == '*/': state = 'code'; i += 1
        elif state in ('"', "'"):
            if ch == '\\': i += 1
            elif ch == state: state = 'code'
        elif nxt == '//': state = 'line'; i += 1
        elif nxt == '/*': state = 'comment'; i += 1
        elif ch in ('"', "'"): state = ch
        elif ch == '{': level += 1
        elif ch == '}': level -= 1
        i += 1
    return text[:start] + text[i:]

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def run(src, out):
    src, out = src.resolve(), out.resolve()
    if src == out or src in out.parents or out in src.parents:
        raise ValueError('Source and output must be separate directories')
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output must be empty (no deletion or overwrite of existing project)')
    out.mkdir(parents=True, exist_ok=True)

    def write(path, text, origin=None, reason='New standalone support file'):
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        manifest.append(dict(path=path, source=origin,
            source_sha256=sha((src/origin).read_text('utf-8')) if origin else None,
            result_sha256=sha(text), change=reason))

    def copy(path, transform=None, reason='Copied without business-logic changes'):
        text = (src/path).read_text('utf-8')
        if transform: text = transform(text)
        write(path, text, path, reason)

    # Exact dependency boundary, not an entire repository copy.
    for sub in ('controller', 'service', 'dao', 'entity'):
        for path in sorted((src/BASE/sub).glob('Stock*.java')):
            relative = str(path.relative_to(src))
            copy(relative, lambda s: s.replace('.aimeeting-room', '.stock-watch'),
                 'Preserved stock-watch behavior; isolated fallback runtime directory')
    for path in sorted((src/'src/main/resources/mapper').glob('Stock*.xml')):
        copy(str(path.relative_to(src)))
    shared = [
        'common/ApiResponse.java', 'controller/AuthController.java',
        'config/AuthInterceptor.java', 'config/TokenStore.java',
        'config/WebMvcConfig.java', 'config/ModelEntry.java',
        'config/ModelRegistryStore.java', 'dao/AiUserMapper.java',
        'entity/AiUser.java', 'dto/LoginRequest.java', 'dto/ChatResult.java',
        'service/ai/AiModelRouter.java', 'service/ai/AiModelClient.java',
        'service/ai/GenericAiClient.java', 'service/ai/WebSearchService.java'
    ]
    for name in shared:
        copy(BASE+name, lambda s: s.replace('.aimeeting-room', '.stock-watch'),
             'Shared auth/API-model dependency retained; runtime directory isolated')

    # No meeting executor, meeting configuration, fake model clients or seed users.
    props = (src/BASE/'config/AiModelProperties.java').read_text('utf-8')
    props = require_replace(props, '    private MeetingConfig meeting = new MeetingConfig();\n', '')
    props = props[:props.index('    @Data\n    public static class MeetingConfig')] + '}\n'
    write(BASE+'config/AiModelProperties.java', props, BASE+'config/AiModelProperties.java',
          'Removed meeting-only configuration; model properties unchanged')
    app = (src/BASE/'AiMeetingApplication.java').read_text('utf-8').replace('AiMeetingApplication', 'StockWatchApplication')
    write(BASE+'StockWatchApplication.java', app, BASE+'AiMeetingApplication.java', 'Renamed application entry point')
    write(BASE+'config/AppConfig.java', '''package com.aimeeting.room.config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
@Configuration
public class AppConfig {
    @Bean public BCryptPasswordEncoder passwordEncoder() { return new BCryptPasswordEncoder(); }
}
''', BASE+'config/AppConfig.java', 'Retained password encoder; removed meetingExecutor')

    notification = (src/BASE/'service/NotificationService.java').read_text('utf-8')
    notification = remove_method(notification, '    public void sendMeetingConclusion(')
    notification = remove_method(notification, '    private void sendServerChan(')
    notification = re.sub(r'    @Value\("\$\{notification.serverchan-key:\}"\)\n    private String serverChanKey;\n', '', notification)
    notification = re.sub(r'    private final OkHttpClient http = new OkHttpClient.Builder\(\).*?\.build\(\);\n', '', notification, flags=re.S)
    notification = notification.replace('import okhttp3.*;\n', '').replace('import java.util.concurrent.TimeUnit;\n', '')
    notification = notification.replace('AI 会议室', 'Stock Watch').replace('会议结论通知服务。', '股票盯盘邮件通知服务。')
    notification = re.sub(r'    /\*\*\n     \* 发送会议结论通知。.*?\*/\s*', '', notification, flags=re.S)
    write(BASE+'service/NotificationService.java', notification, BASE+'service/NotificationService.java',
          'Retained email methods; removed meeting/ServerChan-only methods')

    config = (src/BASE/'controller/ConfigController.java').read_text('utf-8')
    config = config.replace('import com.aimeeting.room.config.AiModelProperties;\n', '').replace('import com.aimeeting.room.dto.ModelConfigRequest;\n', '')
    config = config.replace('    private final AiModelProperties aiModelProperties;\n', '')
    a = config.index('    // ============================================================\n    // 会议引擎参数')
    b = config.index('    @PostMapping("/notification/test-email")', a)
    config = config[:a] + config[b:]
    a = config.index('    private Map<String, Object> buildVerificationMeta(')
    config = remove_method(config, '    private Map<String, Object> buildVerificationMeta(')
    helper = '''    private Map<String, Object> buildVerificationMeta(String modelKey) {
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("verificationStatus", "unverified");
        meta.put("verificationLabel", "未验证");
        meta.put("verificationNote", "独立仓库未运行真实模型验证；注册配置不代表模型可用。");
        meta.put("recommended", false);
        return meta;
    }
'''
    config = config[:a] + helper + config[a:]
    config = config.replace('供创建会议时使用', '供股票观察规则选择模型使用').replace('AI 会议室', 'Stock Watch')
    write(BASE+'controller/ConfigController.java', config, BASE+'controller/ConfigController.java',
          'Retained model registry and mail-test APIs; removed meeting settings and stale verification claims')

    # Keep original SQL columns/indexes, but only the six Stock Watch tables + auth.
    init = (src/'src/main/resources/sql/init.sql').read_text('utf-8')
    tables = re.findall(r'CREATE TABLE IF NOT EXISTS `(stock_watch_[^`]+)`\s*\(.*?\) ENGINE=[^;]+;', init, re.S)
    blocks = re.findall(r'CREATE TABLE IF NOT EXISTS `stock_watch_[^`]+`\s*\(.*?\) ENGINE=[^;]+;', init, re.S)
    if len(blocks) != 6: raise ValueError('Expected six stock-watch DDL tables')
    user_h2 = (src/'src/main/resources/sql/schema-local.sql').read_text('utf-8').split('CREATE TABLE IF NOT EXISTS ai_meeting_room')[0]
    user_mysql = '''CREATE TABLE IF NOT EXISTS ai_user (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    password VARCHAR(255) NOT NULL,
    nickname VARCHAR(128),
    gmt_create DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    gmt_modify DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ai_user_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
    write('src/main/resources/sql/schema-mysql.sql', '-- New dedicated database only. No rows or credentials are seeded.\n'+user_mysql+'\n\n'.join(blocks)+'\n',
          'src/main/resources/sql/init.sql', 'Extracted six stock-watch tables and auth schema; no CREATE DATABASE/USE/DROP/data imports')
    h2_blocks = []
    for name, block in zip(tables, blocks):
        block = re.sub(r"\s+COMMENT\s+'[^']*'", '', block)
        block = re.sub(r'\) ENGINE=[^;]+;', ');', block)
        block = block.replace('`','').replace('MEDIUMTEXT','CLOB').replace('TEXT','CLOB').replace('DATETIME','TIMESTAMP')
        block = block.replace(' ON UPDATE CURRENT_TIMESTAMP', '')
        indices = []
        lines = []
        for line in block.splitlines():
            m = re.match(r'\s*(UNIQUE )?KEY\s+(\w+)\s*(\([^;]+?\)),?\s*$',line)
            if m:
                indices.append('CREATE '+('UNIQUE ' if m.group(1) else '')+'INDEX IF NOT EXISTS '+m.group(2)+' ON '+name+m.group(3)+';')
            else: lines.append(line)
        block = '\n'.join(lines)
        block = re.sub(r',\s*\);', '\n);', block)
        h2_blocks.append(block+'\n'+'\n'.join(indices))
    write('src/main/resources/sql/schema-h2.sql', user_h2+'\n\n'.join(h2_blocks)+'\n',
          'src/main/resources/sql/schema-local.sql', 'Standalone H2 equivalent, including FC card missing from upstream local schema')

    pom = (src/'pom.xml').read_text('utf-8')
    pom = pom.replace('<artifactId>ai-meeting-room</artifactId>', '<artifactId>stock-watch</artifactId>').replace('<name>ai-meeting-room</name>', '<name>stock-watch</name>')
    pom = re.sub(r'<description>.*?</description>', '<description>Standalone stock-watch extracted from ai-meeting-room-new</description>', pom)
    write('pom.xml', pom, 'pom.xml', 'Changed application coordinates only; preserved dependency versions and Java 11')

    for path in ('frontend/package.json','frontend/package-lock.json','frontend/vite.config.js','frontend/index.html',
                 'frontend/src/main.js','frontend/src/App.vue','frontend/src/api/http.js','frontend/src/api/auth.js',
                 'frontend/src/api/config.js','frontend/src/stores/user.js','frontend/src/views/Login.vue',
                 'frontend/src/views/ModelConfig.vue','frontend/src/views/StockWatch.vue'):
        text = (src/path).read_text('utf-8')
        if path.endswith('package.json') or path.endswith('package-lock.json'):
            text = text.replace('ai-meeting-room-frontend', 'stock-watch-frontend')
        if path.endswith('vite.config.js'):
            text = text.replace('127.0.0.1:8115','127.0.0.1:8117').replace('port: 3000,','host: \'127.0.0.1\',\n    port: 3017,\n    strictPort: true,')
        if path.endswith('index.html'):
            text = re.sub('<title>.*?</title>', '<title>Stock Watch · 股票盯盘</title>', text)
            text = text.replace('  <link rel="icon" href="/favicon.ico" />\n','')
        if path.endswith('/api/http.js') or path.endswith('Login.vue'):
            text = text.replace("'/meetings'", "'/stock-watch'")
        if path.endswith('Login.vue'):
            text = text.replace('AI 会议室', 'Stock Watch').replace('多智能体协作决策平台','股票盯盘独立工作台')
            text = text.replace('默认账号：admin / admin123','无默认账号。首次使用请在本机注册；数据空间为单人/可信内网共享。')
        if path.endswith('/api/config.js'):
            text = text[:text.index('  // 会议引擎参数')]+'}\n'
        if path.endswith('ModelConfig.vue'):
            a = text.index('    <!-- 会议')
            b = text.index('    <!-- 添加/编辑对话框 -->', a)
            text = text[:a]+text[b:]
            text = text.replace('const savingMeeting = ref(false)\n','')
            text = re.sub(r'const meetingForm = reactive\(\{.*?\}\)\n', '', text, flags=re.S)
            text = re.sub(r'async function loadMeetingConfig\(\) \{.*?\n\}\n', '', text, flags=re.S)
            text = re.sub(r'async function saveMeeting\(\) \{.*?\n\}\n', '', text, flags=re.S)
            text = text.replace('loadRegistry(); loadMeetingConfig()', 'loadRegistry()').replace('~/.aimeeting-room/model-registry.json', '独立数据目录（默认 ./data/model-registry.json）')
        if path.endswith('StockWatch.vue'):
            for key in ('custom-watchlist.v1','custom-observations.v1','deleted-events.v1'):
                text = text.replace('stock-watch.'+key, 'stock-watch.standalone.'+key)
        write(path, text, path, 'Standalone shell/routes/data namespaces; stock-watch view and API behavior preserved')

    for path in ('scripts/deepseek-web-bridge.js','scripts/deepseek-web-client.js','scripts/deepseek-web-search.js'):
        text = (src/path).read_text('utf-8').replace('.aimeeting-room', '.stock-watch')
        if path.endswith('bridge.js'): text = text.replace('BRIDGE_PORT || 8789', 'BRIDGE_PORT || 8790')
        if path.endswith('client.js'):
            text = text.replace("const CHROME_BIN = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';", "const CHROME_BIN = process.env.DEEPSEEK_WEB_CHROME_BIN || (process.platform === 'darwin' ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : process.platform === 'win32' ? 'C:/Program Files/Google/Chrome/Application/chrome.exe' : 'google-chrome');")
            text = text.replace('DEBUG_PORT || 9333','DEBUG_PORT || 9334').replace("path.join(os.tmpdir(), 'deepseek-web-profile')", "path.join(os.homedir(), '.stock-watch', 'deepseek-web-profile')")
            text = re.sub(r"const SOURCE_CHROME_DIR = .*?;\n", '', text)
            a = text.index('function ensureAutomationProfile()')
            b = text.index('function cleanupProfileLocks()', a)
            text = text[:a]+'''function ensureAutomationProfile() {
  // A fresh dedicated profile. Never copy personal Chrome cookies/login data.
  fs.mkdirSync(PROFILE_ROOT, { recursive: true });
  cleanupProfileLocks();
}

'''+text[b:]
            text = text.replace("  const chromeLogFd = fs.openSync(CHROME_LOG_PATH, 'a');", "  fs.mkdirSync(path.dirname(CHROME_LOG_PATH), { recursive: true });\n  const chromeLogFd = fs.openSync(CHROME_LOG_PATH, 'a');")
        write(path, text, path, 'Isolated ports/profile/session storage; optional Chrome path; no personal-profile copying')

    for path, text in TEMPLATES.items(): write(path, text)
    write('SOURCE_REVISION', 'repository=https://github.com/wangzilong19950329-spec/ai-meeting-room-new\ncommit='+SOURCE_SHA+'\n')
    for name in ('LICENSE','LICENSE.md','LICENSE.txt','NOTICE','NOTICE.md'):
        if (src/name).is_file(): copy(name)
    check_closure(out)
    (out/'docs').mkdir(exist_ok=True)
    (out/'docs/extraction-manifest.json').write_text(json.dumps(dict(source_commit=SOURCE_SHA, files=manifest), ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    print('Extracted %s files from %s; dependency closure OK' % (len(manifest)+1,SOURCE_SHA))

def check_closure(out):
    classes = {}
    for p in (out/'src/main/java').rglob('*.java'):
        t=p.read_text('utf-8');pkg=re.search(r'^package\s+([\w.]+);',t,re.M)
        classes[pkg.group(1)+'.'+p.stem]=p
    missing=[]
    for p in classes.values():
        for imp in re.findall(r'^import (com\.aimeeting\.[\w.]+);',p.read_text('utf-8'),re.M):
            if not any(imp==c or imp.startswith(c+'.') for c in classes):missing.append((str(p),imp))
    if missing: raise ValueError('Missing internal imports: '+str(missing))
    forbidden = ('AiMeetingApplication.java','MeetingController.java','MeetingOrchestratorService.java','WorkflowSchemaInitializer.java','DataInitializer.java','MockResponseGenerator.java')
    if any(p.name in forbidden for p in classes.values()): raise ValueError('Unrelated business class leaked')

TEMPLATE_ROOT = Path(__file__).with_name('extraction-files')
TEMPLATES = {str(p.relative_to(TEMPLATE_ROOT)): p.read_text('utf-8')
             for p in sorted(TEMPLATE_ROOT.rglob('*')) if p.is_file()}

if __name__ == '__main__':
    if len(sys.argv) != 3: raise SystemExit(__doc__)
    run(Path(sys.argv[1]), Path(sys.argv[2]))
