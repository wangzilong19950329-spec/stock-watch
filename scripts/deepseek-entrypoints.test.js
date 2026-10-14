'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

test('DeepSeek service entrypoints pass the Node syntax gate', () => {
  for (const file of ['deepseek-web-bridge.js', 'deepseek-bridge-proxy.js']) {
    execFileSync(process.execPath, ['--check', path.join(__dirname, file)], {
      stdio: 'pipe'
    });
  }
});

test('standalone Bridge entrypoints share isolated ports and state directories', () => {
  const root = path.join(__dirname, '..');
  const packageJson = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  const client = fs.readFileSync(path.join(__dirname, 'deepseek-web-client.js'), 'utf8');
  const bridge = fs.readFileSync(path.join(__dirname, 'deepseek-web-bridge.js'), 'utf8');
  const launcher = fs.readFileSync(path.join(__dirname, 'start-bridge.sh'), 'utf8');

  assert.equal(packageJson.scripts.bridge, 'bash scripts/start-bridge.sh');
  assert.match(client, /DEEPSEEK_WEB_DEBUG_PORT \|\| 9334/);
  assert.match(client, /\.stock-watch', 'deepseek-web-profile/);
  assert.match(client, /\.stock-watch', 'deepseek-web-chrome\.log/);
  assert.match(bridge, /DEEPSEEK_WEB_BRIDGE_PORT \|\| 8790/);
  assert.match(launcher, /DEEPSEEK_WEB_PROFILE_BOOTSTRAP:-empty/);
  assert.doesNotMatch(`${client}\n${bridge}\n${launcher}`, /\.aimeeting-room/);
});
