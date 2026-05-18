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
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import Toolbar from 'primevue/toolbar'

import { getStoredUser, logout } from './services/api'
import { usePreferences } from './services/preferences'

const router = useRouter()
const user = ref(getStoredUser())
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
