<script setup lang="ts">
import { ref } from "vue"
import { RouterLink, useRoute, useRouter } from "vue-router"

import { api, ApiError } from "../../lib/api"
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

    const next = typeof route.query.next === "string" ? route.query.next : null
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
  <section class="page container page--narrow">
    <div class="card">
      <h1 class="card__title">Login</h1>

      <div v-if="error" class="alert alert--error" style="margin-bottom: 1rem">{{ error }}</div>

      <form @submit.prevent="submit">
        <div class="field">
          <label for="username">Username</label>
          <input id="username" class="input" v-model="username" autocomplete="username" required />
        </div>
        <div class="field">
          <label for="password">Password</label>
          <input id="password" class="input" type="password" v-model="password"
            autocomplete="current-password" required />
        </div>
        <button class="btn btn--primary btn--block" :disabled="loading">
          {{ loading ? "Logging in…" : "Login" }}
        </button>
      </form>

      <p class="dim" style="margin-top: 1rem; font-size: 0.9rem">
        <RouterLink to="/reset">Forgot password?</RouterLink>
        &middot; No account? <RouterLink to="/register">Register</RouterLink>
      </p>
    </div>
  </section>
</template>
