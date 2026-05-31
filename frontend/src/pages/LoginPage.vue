<template>
  <Card class="w-1/2 mx-auto">
    <template #title>{{ t("login") }}</template>
    <template #subtitle>{{ t("authLoginSubtitle") }}</template>
    <template #content>
      <form class="flex flex-col gap-3" @submit.prevent="submitLogin">
        <InputText placeholder="Email" id="email" v-model="email" type="email" autocomplete="email" required
          class="w-full" />
        <Password :placeholder="t('password')" inputId="password" v-model="password" :feedback="false" toggleMask
          autocomplete="current-password" required :inputStyle="{ width: '100%' }" :style="{ width: '100%' }" />
        <Message v-if="errorMessage" severity="error">{{
          errorMessage
        }}</Message>
        <Button :label="t('login')" icon="pi pi-sign-in" type="submit" :loading="isSubmitting" />
      </form>
    </template>
    <template #footer>
      <RouterLink to="/register">{{ t("createNewAccount") }}</RouterLink>
    </template>
  </Card>
</template>

<script setup>
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Password from "primevue/password";

import { login } from "../services/api";
import { usePreferences } from "../services/preferences";

const router = useRouter();
const email = ref("");
const password = ref("");
const errorMessage = ref("");
const isSubmitting = ref(false);
const { t } = usePreferences();

async function submitLogin() {
  errorMessage.value = "";
  isSubmitting.value = true;

  try {
    await login({ email: email.value, password: password.value });
    await router.push("/");
  } catch {
    errorMessage.value = t("loginFailed");
  } finally {
    isSubmitting.value = false;
  }
}
</script>
