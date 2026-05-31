<template>
  <div>
    <Toolbar :style="{ minHeight: '3rem', paddingBlock: '0.25rem' }">
      <template #start>
        <RouterLink to="/">{{ t('appName') }}</RouterLink>
      </template>
      <template #end>
        <Button
          icon="pi pi-language"
          text
          rounded
          size="small"
          :aria-label="t('language')"
          aria-haspopup="true"
          aria-controls="language_menu"
          @click="toggleLanguageMenu"
        />
        <Menu id="language_menu" ref="languageMenu" :model="languageMenuItems" popup />

        <Button
          icon="pi pi-palette"
          text
          rounded
          size="small"
          :aria-label="t('theme')"
          aria-haspopup="true"
          aria-controls="theme_menu"
          @click="toggleThemeMenu"
        />
        <Menu id="theme_menu" ref="themeMenu" :model="themeMenuItems" popup />

        <Badge v-if="user" :value="user.name" severity="success" />
        <RouterLink v-if="!user" to="/login">
          <Button :label="t('login')" icon="pi pi-sign-in" text size="small" />
        </RouterLink>
        <RouterLink v-if="!user" to="/register">
          <Button :label="t('register')" icon="pi pi-user-plus" outlined size="small" />
        </RouterLink>
        <Button v-if="user" :label="t('logout')" icon="pi pi-sign-out" text size="small" @click="handleLogout" />
      </template>
    </Toolbar>

    <main :style="{ maxWidth: '1200px', margin: '0 auto', padding: '1rem' }">
      <RouterView />
    </main>

    <Dialog
      v-model:visible="showLogoutDialog"
      modal
      :header="t('logoutConfirmTitle')"
      :style="{ width: '28rem' }"
    >
      <p>{{ t('logoutConfirmText') }}</p>
      <template #footer>
        <Button :label="t('cancel')" text @click="cancelLogout" />
        <Button :label="t('logout')" icon="pi pi-sign-out" severity="danger" @click="confirmLogout" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import Badge from 'primevue/badge'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Menu from 'primevue/menu'
import Toolbar from 'primevue/toolbar'

import { getStoredUser, logout } from './services/api'
import { usePreferences } from './services/preferences'

const router = useRouter()
const user = ref(getStoredUser())
const showLogoutDialog = ref(false)
const languageMenu = ref(null)
const themeMenu = ref(null)
const { language, theme, setLanguage, setTheme, t } = usePreferences()

const languageOptions = computed(() => [
  { label: t('english'), value: 'en' },
  { label: t('russian'), value: 'ru' }
])

const themeOptions = computed(() => [
  { label: t('themeLight'), value: 'light', icon: 'pi pi-sun' },
  { label: t('themeDark'), value: 'dark', icon: 'pi pi-moon' },
  { label: t('themeSystem'), value: 'system', icon: 'pi pi-desktop' }
])

const languageMenuItems = computed(() => languageOptions.value.map((option) => ({
  label: option.label,
  icon: language.value === option.value ? 'pi pi-check' : 'pi pi-circle',
  command: () => setLanguage(option.value)
})))

const themeMenuItems = computed(() => themeOptions.value.map((option) => ({
  label: option.label,
  icon: theme.value === option.value ? 'pi pi-check' : option.icon,
  command: () => setTheme(option.value)
})))

function toggleLanguageMenu(event) {
  languageMenu.value.toggle(event)
}

function toggleThemeMenu(event) {
  themeMenu.value.toggle(event)
}

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
