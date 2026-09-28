#!/usr/bin/env python3
"""Offline dependency/boundary checks. --sanitize removes personal email examples before first publication."""
from pathlib import Path
import hashlib,json,re,sys
root=Path(__file__).resolve().parents[1]
mp=root/'docs/extraction-manifest.json'
m=json.loads(mp.read_text('utf-8'))
if '--sanitize' in sys.argv:
    # Only UI placeholders in the upstream static view; never read runtime state.
    p=root/'frontend/src/views/StockWatch.vue'
    text=p.read_text('utf-8')
    changed=re.sub(r'[A-Za-z0-9._%+-]+@(?!example\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,}', 'contact@example.com', text)
    if changed != text:
        p.write_text(changed,'utf-8')
        for entry in m['files']:
            if entry['path']==str(p.relative_to(root)):
                entry['result_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
                entry['change']+='; redacted personal email UI placeholder'
        mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf-8')
for entry in m['files']:
    p=root/entry['path']
    assert p.is_file(), f"Missing file: {p}"
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest==entry['result_sha256'], f"Unrecorded change: {p}; update manifest explicitly when editing later"
classes={}
for p in (root/'src/main/java').rglob('*.java'):
    text=p.read_text('utf-8')
    package=re.search(r'^package\s+([\w.]+);',text,re.M).group(1)
    classes[package+'.'+p.stem]=p
for p in classes.values():
    for imp in re.findall(r'^import (com\.aimeeting\.[\w.]+);',p.read_text('utf-8'),re.M):
        assert any(imp==key or imp.startswith(key+'.') for key in classes), (p,imp)
    assert not p.stem.startswith(('AiMeeting','AiWorkflow','Meeting','Workflow','Tracking')), p
schema=(root/'src/main/resources/sql/schema-mysql.sql').read_text('utf-8')
tables=set(re.findall(r'CREATE TABLE IF NOT EXISTS `?(\w+)',schema))
assert tables=={'ai_user','stock_watch_item','stock_watch_technical_session','stock_watch_technical_analysis','stock_watch_delivery_config','stock_watch_delivery_log','stock_watch_fc_card'}, tables
assert not re.search(r'\b(INSERT INTO|DROP TABLE|USE ai_meeting)\b', schema,re.I)
for entry in m['files']:
    assert entry['path'] not in ('.env','data/model-registry.json','data/ai-rules.json')
    text=(root/entry['path']).read_text('utf-8')
    assert not re.search(r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{25,}|sk-[A-Za-z0-9]{32,}',text), entry['path']
print(f"PASS: {len(m['files'])} recorded files; {len(classes)} Java classes; {len(tables)} isolated tables")
