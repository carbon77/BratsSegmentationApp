<template>
  <div class="app-shell">
    <Toolbar class="app-toolbar">
      <template #start>
        <RouterLink to="/" class="brand-link">Brats Segmentation App</RouterLink>
      </template>
      <template #end>
        <div class="toolbar-actions">
          <Tag v-if="user" :value="user.name" severity="success" rounded />
          <RouterLink v-if="!user" to="/login">
            <Button label="Login" icon="pi pi-sign-in" text />
          </RouterLink>
          <RouterLink v-if="!user" to="/register">
            <Button label="Register" icon="pi pi-user-plus" outlined />
          </RouterLink>
          <Button v-if="user" label="Logout" icon="pi pi-sign-out" text @click="handleLogout" />
        </div>
      </template>
    </Toolbar>

    <main class="page-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Toolbar from 'primevue/toolbar'

import { getStoredUser, logout } from './services/api'

const router = useRouter()
const user = ref(getStoredUser())

function syncUser() {
  user.value = getStoredUser()
}

async function handleLogout() {
  logout()
  user.value = null
  await router.push('/login')
}

onMounted(() => {
  window.addEventListener('auth-changed', syncUser)
})

onUnmounted(() => {
  window.removeEventListener('auth-changed', syncUser)
})
</script>
