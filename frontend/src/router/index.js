import { createRouter, createWebHistory } from 'vue-router'

import HomePage from '../pages/HomePage.vue'
import LoginPage from '../pages/LoginPage.vue'
import RegisterPage from '../pages/RegisterPage.vue'
import ScanPage from '../pages/ScanPage.vue'
import { isAuthenticated } from '../services/api'

const routes = [
  { path: '/', name: 'home', component: HomePage, meta: { requiresAuth: true } },
  { path: '/login', name: 'login', component: LoginPage, meta: { guestOnly: true } },
  { path: '/register', name: 'register', component: RegisterPage, meta: { guestOnly: true } },
  { path: '/scans/:caseId', name: 'scan', component: ScanPage, props: true, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const authenticated = isAuthenticated()
  if (to.meta.requiresAuth && !authenticated) {
    return { name: 'login' }
  }

  if (to.meta.guestOnly && authenticated) {
    return { name: 'home' }
  }

  return true
})

export default router
