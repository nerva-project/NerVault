<script setup lang="ts">
import { onMounted, ref } from "vue"
import { RouterLink, useRoute, useRouter } from "vue-router"

import Alert from "../../components/ui/Alert.vue"
import Card from "../../components/ui/Card.vue"
import Spinner from "../../components/ui/Spinner.vue"
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
    <Card class="center">
      <h1 class="card__title">Account confirmation</h1>

      <div v-if="state === 'loading'">
        <Spinner label="Confirming your account…" />
      </div>

      <div v-else-if="state === 'success'">
        <Alert variant="success">{{ message }}</Alert>
        <p class="dim" style="margin-top: 1rem">Redirecting…</p>
      </div>

      <div v-else>
        <Alert>{{ message }}</Alert>
        <p style="margin-top: 1rem"><RouterLink to="/login">Back to login</RouterLink></p>
      </div>
    </Card>
  </section>
</template>
