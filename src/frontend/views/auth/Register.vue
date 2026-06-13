<script setup lang="ts">
import { ref } from "vue"
import { RouterLink, useRouter } from "vue-router"

import Alert from "../../components/ui/Alert.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import FormField from "../../components/ui/FormField.vue"
import PasswordInput from "../../components/ui/PasswordInput.vue"
import { api, ApiError } from "../../lib/api"
import { useAuthStore, type User } from "../../stores/auth"

const router = useRouter()
const auth = useAuthStore()

const username = ref("")
const email = ref("")
const password = ref("")
const confirmPassword = ref("")
const reviewed = ref(false)
const loading = ref(false)
const error = ref("")

async function submit(): Promise<void> {
  error.value = ""

  if (password.value !== confirmPassword.value) {
    error.value = "Passwords do not match."
    return
  }
  if (!reviewed.value) {
    error.value = "Please confirm you have read the Terms of Service and Privacy Policy."
    return
  }

  loading.value = true
  try {
    const res = await api.post<User>("/auth/register", {
      username: username.value,
      email: email.value,
      password: password.value,
      confirm_password: confirmPassword.value,
    })
    auth.setUser(res.result ?? null)
    router.push({ name: "unconfirmed" })
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Registration failed."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[520px] mx-auto flex flex-col justify-center">
    <Card>
      <h1 class="text-[1.1rem] font-bold mb-4">Create an account</h1>

      <Alert v-if="error" class="mb-4">{{ error }}</Alert>

      <form @submit.prevent="submit">
        <FormField label="Username" input-id="username">
          <input id="username" class="input" v-model="username" autocomplete="username" required />
        </FormField>
        <FormField label="Email address" input-id="email">
          <input id="email" class="input" type="email" v-model="email" autocomplete="email" required />
        </FormField>
        <FormField label="Password" input-id="password">
          <PasswordInput id="password" v-model="password" autocomplete="new-password" required />
        </FormField>
        <FormField label="Confirm password" input-id="confirm">
          <PasswordInput id="confirm" v-model="confirmPassword" autocomplete="new-password" required />
        </FormField>

        <label class="flex items-start gap-[0.55rem] text-[0.9rem] text-text-dim mb-3">
          <input type="checkbox" v-model="reviewed" class="mt-[0.2rem] accent-accent" />
          <span>
            I have read and agree to the
            <RouterLink to="/terms" target="_blank">Terms of Service</RouterLink> and
            <RouterLink to="/privacy" target="_blank">Privacy Policy</RouterLink>.
          </span>
        </label>

        <Btn type="submit" variant="primary" block :disabled="loading">
          {{ loading ? "Creating account…" : "Register" }}
        </Btn>
      </form>

      <p class="text-text-dim mt-4 text-[0.9rem]">
        Already have an account? <RouterLink to="/login">Login</RouterLink>
      </p>
    </Card>
  </section>
</template>
