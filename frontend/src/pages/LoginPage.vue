<template>
  <section class="auth-page">
    <Card class="auth-card">
      <template #title>{{ t('login') }}</template>
      <template #subtitle>{{ t('authLoginSubtitle') }}</template>
      <template #content>
        <form class="auth-form" @submit.prevent="submitLogin">
          <label class="field-block">
            <span>{{ t('email') }}</span>
            <InputText v-model="email" type="email" autocomplete="email" required />
          </label>
          <label class="field-block">
            <span>{{ t('password') }}</span>
            <Password v-model="password" :feedback="false" toggleMask autocomplete="current-password" required />
          </label>
          <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
          <Button :label="t('login')" icon="pi pi-sign-in" type="submit" :loading="isSubmitting" />
        </form>
      </template>
      <template #footer>
        <RouterLink to="/register">{{ t('createNewAccount') }}</RouterLink>
      </template>
    </Card>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'

import { login } from '../services/api'
import { usePreferences } from '../services/preferences'

const router = useRouter()
const email = ref('')
const password = ref('')
const errorMessage = ref('')
const isSubmitting = ref(false)
const { t } = usePreferences()

async function submitLogin() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    await login({ email: email.value, password: password.value })
    await router.push('/')
  } catch {
    errorMessage.value = t('loginFailed')
  } finally {
    isSubmitting.value = false
  }
}
</script>
