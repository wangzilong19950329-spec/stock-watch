#!/usr/bin/env python3
"""Real local HTTP smoke test; no requests to quote, AI or SMTP providers."""
import json,os,time,uuid,urllib.request,urllib.error
base='http://127.0.0.1:'+os.environ.get('SMOKE_PORT','18117')
def request(path, data=None, token=None):
    headers={'Content-Type':'application/json'}
    if token:headers['X-Token']=token
    req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
    with urllib.request.urlopen(req,timeout=5) as r:return json.load(r)
ready=False
for _ in range(90):
    try:request('/api/stock-watch/watchlist')
    except urllib.error.HTTPError as e:
        if e.code==401:ready=True;break
    except (OSError,TimeoutError):pass
    time.sleep(1)
assert ready,'Standalone application did not start or auth was not enforced'
account={'username':'smoke_'+uuid.uuid4().hex[:12], 'password':uuid.uuid4().hex}
assert request('/api/auth/register',account)['code']==200
token=request('/api/auth/login',account)['data']['token']
assert request('/api/stock-watch/watchlist',token=token)['code']==200
assert request('/api/stock-watch/monitor/status',token=token)['data']['enabled'] is False
assert request('/api/stock-watch/technical-analysis/status',token=token)['data']['enabled'] is False
assert request('/api/config/registry',token=token)['code']==200
print('PASS: real HTTP startup, registration/login, authenticated watchlist/status/model-registry; no external provider called')
