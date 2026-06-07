<script setup lang="ts">
import { ref } from "vue"

import { api, ApiError } from "../../lib/api"
import { useToast } from "../../composables/useToast"
import { useAuthStore } from "../../stores/auth"

const toast = useToast()
const auth = useAuthStore()
const loading = ref(false)

async function resend(): Promise<void> {
  loading.value = true
  try {
    const res = await api.post("/auth/resend-confirmation")
    toast.success(res.message || "A new confirmation email has been sent.")
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : "Could not resend the email.")
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page container page--narrow">
    <div class="card center">
      <h1 class="card__title">Confirm your email</h1>
      <p class="dim">
        We've sent a confirmation link to <b>{{ auth.user?.email }}</b>. Please click it to activate
        your account. Check your Junk/Spam folder if you don't see it.
      </p>
      <button class="btn btn--ghost" :disabled="loading" @click="resend">
        {{ loading ? "Sending…" : "Resend email" }}
      </button>
    </div>
  </section>
</template>
