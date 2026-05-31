<template>
  <section class="mx-auto my-16 max-w-[440px]">
    <Card>
      <template #title>{{ t('createAccount') }}</template>
      <template #subtitle>{{ t('registerSubtitle') }}</template>
      <template #content>
        <form class="grid gap-4" @submit.prevent="submitRegister">
          <FloatLabel>
            <InputText id="name" v-model="name" autocomplete="name" required class="w-full" />
            <label for="name">{{ t('name') }}</label>
          </FloatLabel>
          <FloatLabel>
            <InputText id="email" v-model="email" type="email" autocomplete="email" required class="w-full" />
            <label for="email">{{ t('email') }}</label>
          </FloatLabel>
          <FloatLabel>
            <Password
              inputId="password"
              v-model="password"
              toggleMask
              autocomplete="new-password"
              required
              inputClass="w-full"
              class="w-full"
            />
            <label for="password">{{ t('password') }}</label>
          </FloatLabel>
          <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
          <Button :label="t('createAccount')" icon="pi pi-user-plus" type="submit" :loading="isSubmitting" />
        </form>
      </template>
      <template #footer>
        <RouterLink to="/login">{{ t('alreadyHaveAccount') }}</RouterLink>
      </template>
    </Card>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import FloatLabel from 'primevue/floatlabel'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'

import { registerAccount } from '../services/api'
import { usePreferences } from '../services/preferences'

const router = useRouter()
const name = ref('')
const email = ref('')
const password = ref('')
const errorMessage = ref('')
const isSubmitting = ref(false)
const { t } = usePreferences()

async function submitRegister() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    await registerAccount({ name: name.value, email: email.value, password: password.value })
    await router.push('/')
  } catch {
    errorMessage.value = t('registerFailed')
  } finally {
    isSubmitting.value = false
  }
}
</script>
