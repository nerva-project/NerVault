<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"

import { api, ApiError } from "../../lib/api"
import { useToast } from "../../composables/useToast"

const router = useRouter()
const toast = useToast()

const current = ref("")
const password = ref("")
const confirm = ref("")
const loading = ref(false)
const error = ref("")

async function submit(): Promise<void> {
  error.value = ""

  if (password.value !== confirm.value) {
    error.value = "Passwords do not match."
    return
  }

  loading.value = true
  try {
    await api.post("/auth/change-password", {
      current_password: current.value,
      password: password.value,
      confirm_password: confirm.value,
    })
    toast.success("Your password has been changed.")
    router.push({ name: "wallet-dashboard" })
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Could not change password."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page container page--narrow">
    <div class="card">
      <h1 class="card__title">Change password</h1>

      <div v-if="error" class="alert alert--error" style="margin-bottom: 1rem">{{ error }}</div>

      <form @submit.prevent="submit">
        <div class="field">
          <label for="current">Current password</label>
          <input id="current" class="input" type="password" v-model="current"
            autocomplete="current-password" required />
        </div>
        <div class="field">
          <label for="password">New password</label>
          <input id="password" class="input" type="password" v-model="password"
            autocomplete="new-password" required />
        </div>
        <div class="field">
          <label for="confirm">Confirm new password</label>
          <input id="confirm" class="input" type="password" v-model="confirm"
            autocomplete="new-password" required />
        </div>
        <button class="btn btn--primary btn--block" :disabled="loading">
          {{ loading ? "Saving…" : "Change password" }}
        </button>
      </form>
    </div>
  </section>
</template>
