<template>
  <section class="auth-page">
    <Card class="auth-card">
      <template #title>Login</template>
      <template #subtitle>Enter your email and password to open your scans.</template>
      <template #content>
        <form class="auth-form" @submit.prevent="submitLogin">
          <label class="field-block">
            <span>Email</span>
            <InputText v-model="email" type="email" autocomplete="email" required />
          </label>
          <label class="field-block">
            <span>Password</span>
            <Password v-model="password" :feedback="false" toggleMask autocomplete="current-password" required />
          </label>
          <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
          <Button label="Login" icon="pi pi-sign-in" type="submit" :loading="isSubmitting" />
        </form>
      </template>
      <template #footer>
        <RouterLink to="/register">Create a new account</RouterLink>
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

const router = useRouter()
const email = ref('')
const password = ref('')
const errorMessage = ref('')
const isSubmitting = ref(false)

async function submitLogin() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    await login({ email: email.value, password: password.value })
    await router.push('/')
  } catch {
    errorMessage.value = 'Could not login. Check your email and password.'
  } finally {
    isSubmitting.value = false
  }
}
</script>
