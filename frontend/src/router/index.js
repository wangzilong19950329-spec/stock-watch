import { createRouter, createWebHistory } from 'vue-router'
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
    { path: '/', component: () => import('@/views/StockWatchLayout.vue'), children: [
      { path: '', redirect: '/stock-watch' },
      { path: 'stock-watch', component: () => import('@/views/StockWatch.vue') },
      { path: 'config', component: () => import('@/views/ModelConfig.vue') },
    ] },
    { path: '/:pathMatch(.*)*', redirect: '/stock-watch' },
  ],
})
router.beforeEach(to => {
  if (!to.meta.public && !localStorage.getItem('token')) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
})
export default router
