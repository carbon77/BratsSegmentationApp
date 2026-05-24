<template>
  <div class="app-shell">
    <Toolbar class="app-toolbar">
      <template #start>
        <RouterLink to="/" class="brand-link">{{ t('appName') }}</RouterLink>
      </template>
      <template #end>
        <div class="toolbar-actions">
          <Dropdown
            :modelValue="language"
            :options="languageOptions"
            optionLabel="label"
            optionValue="value"
            class="toolbar-dropdown"
            :placeholder="t('language')"
            @update:modelValue="setLanguage"
          />
          <Dropdown
            :modelValue="theme"
            :options="themeOptions"
            optionLabel="label"
            optionValue="value"
            class="toolbar-dropdown"
            :placeholder="t('theme')"
            @update:modelValue="setTheme"
          />
          <Tag v-if="user" :value="user.name" severity="success" rounded />
          <RouterLink v-if="!user" to="/login">
            <Button :label="t('login')" icon="pi pi-sign-in" text />
          </RouterLink>
          <RouterLink v-if="!user" to="/register">
            <Button :label="t('register')" icon="pi pi-user-plus" outlined />
          </RouterLink>
          <Button v-if="user" :label="t('logout')" icon="pi pi-sign-out" text @click="handleLogout" />
        </div>
      </template>
    </Toolbar>

    <main class="page-content">
      <RouterView />
    </main>

    <Dialog
      v-model:visible="showLogoutDialog"
      modal
      :header="t('logoutConfirmTitle')"
      :style="{ width: '28rem' }"
    >
      <p>{{ t('logoutConfirmText') }}</p>
      <div class="dialog-actions">
        <Button :label="t('cancel')" text @click="cancelLogout" />
        <Button :label="t('logout')" icon="pi pi-sign-out" severity="danger" @click="confirmLogout" />
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import Toolbar from 'primevue/toolbar'

import { getStoredUser, logout } from './services/api'
import { usePreferences } from './services/preferences'

const router = useRouter()
const user = ref(getStoredUser())
const showLogoutDialog = ref(false)
const { language, theme, setLanguage, setTheme, t } = usePreferences()

const languageOptions = computed(() => [
  { label: t('english'), value: 'en' },
  { label: t('russian'), value: 'ru' }
])

const themeOptions = computed(() => [
  { label: t('themeLight'), value: 'light' },
  { label: t('themeDark'), value: 'dark' },
  { label: t('themeSystem'), value: 'system' }
])

function syncUser() {
  user.value = getStoredUser()
}

function handleLogout() {
  showLogoutDialog.value = true
}

async function confirmLogout() {
  logout()
  user.value = null
  showLogoutDialog.value = false
  await router.push('/login')
}

function cancelLogout() {
  showLogoutDialog.value = false
}

onMounted(() => {
  window.addEventListener('auth-changed', syncUser)
})

onUnmounted(() => {
  window.removeEventListener('auth-changed', syncUser)
})
</script>
