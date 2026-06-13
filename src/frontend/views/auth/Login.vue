<script setup lang="ts">
import { ref } from "vue"
import { RouterLink, useRoute, useRouter } from "vue-router"

import Alert from "../../components/ui/Alert.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import FormField from "../../components/ui/FormField.vue"
import { api, ApiError } from "../../lib/api"
import { safeRedirect } from "../../router"
import { useAuthStore, type User } from "../../stores/auth"

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const username = ref("")
const password = ref("")
const loading = ref(false)
const error = ref("")

async function submit(): Promise<void> {
  error.value = ""
  loading.value = true
  try {
    const res = await api.post<User>("/auth/login", {
      username: username.value,
      password: password.value,
    })
    auth.setUser(res.result ?? null)

    const next = safeRedirect(route.query.next)
    if (next) {
      router.push(next)
    } else if (auth.isConfirmed) {
      router.push({ name: "wallet-dashboard" })
    } else {
      router.push({ name: "unconfirmed" })
    }
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Login failed."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[520px] mx-auto flex flex-col justify-center">
    <Card>
      <h1 class="text-[1.1rem] font-bold mb-4">Login</h1>

      <Alert v-if="error" class="mb-4">{{ error }}</Alert>

      <form @submit.prevent="submit">
        <FormField label="Username" input-id="username">
          <input id="username" class="input" v-model="username" autocomplete="username" required />
        </FormField>
        <FormField label="Password" input-id="password">
          <input id="password" class="input" type="password" v-model="password"
            autocomplete="current-password" required />
        </FormField>
        <Btn type="submit" variant="primary" block :disabled="loading">
          {{ loading ? "Logging in…" : "Login" }}
        </Btn>
      </form>

      <p class="text-text-dim mt-4 text-[0.9rem]">
        <RouterLink to="/reset">Forgot password?</RouterLink>
        &middot; No account? <RouterLink to="/register">Register</RouterLink>
      </p>
    </Card>
  </section>
</template>
