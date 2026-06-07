<script setup lang="ts">
import { onMounted, ref } from "vue"
import { RouterLink, useRoute, useRouter } from "vue-router"

import { api, ApiError } from "../../lib/api"
import { useAuthStore } from "../../stores/auth"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const state = ref<"loading" | "success" | "error">("loading")
const message = ref("")

onMounted(async () => {
  const token = String(route.params.token)
  try {
    const res = await api.get(`/auth/confirm/${token}`)
    message.value = res.message || "Your account has been confirmed."
    state.value = "success"
    await auth.fetchMe()
    window.setTimeout(() => {
      router.push(auth.isAuthenticated ? { name: "wallet-setup" } : { name: "login" })
    }, 1600)
  } catch (e) {
    message.value = e instanceof ApiError ? e.message : "Confirmation failed."
    state.value = "error"
  }
})
</script>

<template>
  <section class="page container page--narrow">
    <div class="card center">
      <h1 class="card__title">Account confirmation</h1>

      <div v-if="state === 'loading'">
        <div class="spinner"></div>
        <p class="dim">Confirming your account…</p>
      </div>

      <div v-else-if="state === 'success'">
        <div class="alert alert--success">{{ message }}</div>
        <p class="dim" style="margin-top: 1rem">Redirecting…</p>
      </div>

      <div v-else>
        <div class="alert alert--error">{{ message }}</div>
        <p style="margin-top: 1rem"><RouterLink to="/login">Back to login</RouterLink></p>
      </div>
    </div>
  </section>
</template>
