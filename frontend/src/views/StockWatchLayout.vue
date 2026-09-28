<template>
  <div class="standalone-layout">
    <header>
      <strong>Stock Watch · 股票盯盘</strong>
      <nav><router-link to="/stock-watch">盯盘</router-link><router-link to="/config">API 模型配置</router-link>
        <button @click="logout">退出登录</button></nav>
    </header>
    <el-alert type="warning" :closable="false" show-icon
      title="源码抽离版：保留原有分析逻辑，原页面含演示指标及示意价格线，不是可信的真实 K 线或资金保护系统。定时分析、自动通知默认关闭。" />
    <main><router-view /></main>
  </div>
</template>
<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'
const router = useRouter()
const user = useUserStore()
async function logout() {
  try { await authApi.logout() } finally { user.logout(); await router.replace('/login') }
}
</script>
<style scoped>
header { display:flex; justify-content:space-between; align-items:center; padding:16px 24px; background:#172235; color:white; gap:16px; flex-wrap:wrap; }
nav { display:flex; align-items:center; gap:20px; }
nav a { color:#c5d7f0; text-decoration:none; }
nav .router-link-active { color:white; text-decoration:underline; }
button { padding:6px 12px; cursor:pointer; }
main { padding:16px; }
</style>
