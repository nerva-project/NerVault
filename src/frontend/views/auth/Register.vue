<script setup lang="ts">
import { ref } from "vue"
import { RouterLink, useRouter } from "vue-router"

import Alert from "../../components/ui/Alert.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import FormField from "../../components/ui/FormField.vue"
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
    error.value = "Please confirm you have read the FAQ, Terms, and Privacy Policy."
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
  <section class="page container page--narrow">
    <Card>
      <h1 class="card__title">Create an account</h1>

      <Alert v-if="error" style="margin-bottom: 1rem">{{ error }}</Alert>

      <form @submit.prevent="submit">
        <FormField label="Username" input-id="username">
          <input id="username" class="input" v-model="username" autocomplete="username" required />
        </FormField>
        <FormField label="Email address" input-id="email">
          <input id="email" class="input" type="email" v-model="email" autocomplete="email" required />
        </FormField>
        <FormField label="Password" input-id="password">
          <input id="password" class="input" type="password" v-model="password"
            autocomplete="new-password" required />
        </FormField>
        <FormField label="Confirm password" input-id="confirm">
          <input id="confirm" class="input" type="password" v-model="confirmPassword"
            autocomplete="new-password" required />
        </FormField>

        <label class="checkbox">
          <input type="checkbox" v-model="reviewed" />
          <span>
            I have read and agree to the
            <RouterLink to="/faq" target="_blank">FAQ</RouterLink>,
            <RouterLink to="/terms" target="_blank">Terms of Service</RouterLink>, and
            <RouterLink to="/privacy" target="_blank">Privacy Policy</RouterLink>.
          </span>
        </label>

        <Btn type="submit" variant="primary" block :disabled="loading">
          {{ loading ? "Creating account…" : "Register" }}
        </Btn>
      </form>

      <p class="dim" style="margin-top: 1rem; font-size: 0.9rem">
        Already have an account? <RouterLink to="/login">Login</RouterLink>
      </p>
    </Card>
  </section>
</template>
