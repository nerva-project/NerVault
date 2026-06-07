<script setup lang="ts">
import { ref } from "vue"
import { RouterLink } from "vue-router"

import { api, ApiError } from "../../lib/api"
import { useToast } from "../../composables/useToast"

const toast = useToast()
const email = ref("")
const loading = ref(false)
const done = ref(false)
const error = ref("")

async function submit(): Promise<void> {
  error.value = ""
  loading.value = true
  try {
    const res = await api.post("/auth/reset", { email: email.value })
    done.value = true
    toast.success(res.message || "If that email is registered, a reset link has been sent.")
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Request failed."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page container page--narrow">
    <div class="card">
      <h1 class="card__title">Reset password</h1>

      <div v-if="done" class="alert alert--success">
        If that email is registered and confirmed, a reset link has been sent. Please check your
        Junk/Spam folder.
      </div>

      <template v-else>
        <div v-if="error" class="alert alert--error" style="margin-bottom: 1rem">{{ error }}</div>
        <form @submit.prevent="submit">
          <div class="field">
            <label for="email">Email address</label>
            <input id="email" class="input" type="email" v-model="email" autocomplete="email" required />
          </div>
          <button class="btn btn--primary btn--block" :disabled="loading">
            {{ loading ? "Sending…" : "Send reset link" }}
          </button>
        </form>
      </template>

      <p class="dim" style="margin-top: 1rem; font-size: 0.9rem">
        <RouterLink to="/login">Back to login</RouterLink>
      </p>
    </div>
  </section>
</template>
