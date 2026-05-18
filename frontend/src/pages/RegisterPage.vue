<template>
  <section class="auth-page">
    <Card class="auth-card">
      <template #title>Create account</template>
      <template #subtitle>Register to keep scans private and tied to your profile.</template>
      <template #content>
        <form class="auth-form" @submit.prevent="submitRegister">
          <label class="field-block">
            <span>Name</span>
            <InputText v-model="name" autocomplete="name" required />
          </label>
          <label class="field-block">
            <span>Email</span>
            <InputText v-model="email" type="email" autocomplete="email" required />
          </label>
          <label class="field-block">
            <span>Password</span>
            <Password v-model="password" toggleMask autocomplete="new-password" required />
          </label>
          <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
          <Button label="Create account" icon="pi pi-user-plus" type="submit" :loading="isSubmitting" />
        </form>
      </template>
      <template #footer>
        <RouterLink to="/login">Already have an account? Login</RouterLink>
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

import { registerAccount } from '../services/api'

const router = useRouter()
const name = ref('')
const email = ref('')
const password = ref('')
const errorMessage = ref('')
const isSubmitting = ref(false)

async function submitRegister() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    await registerAccount({ name: name.value, email: email.value, password: password.value })
    await router.push('/')
  } catch {
    errorMessage.value = 'Could not create account. The email may already be registered.'
  } finally {
    isSubmitting.value = false
  }
}
</script>
