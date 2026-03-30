import { createRouter, createWebHistory } from 'vue-router'

import HomePage from '../pages/HomePage.vue'
import ScanPage from '../pages/ScanPage.vue'

const routes = [
  { path: '/', name: 'home', component: HomePage },
  { path: '/scans/:caseId', name: 'scan', component: ScanPage, props: true }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
