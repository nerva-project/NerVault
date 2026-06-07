<script setup lang="ts">
import { ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import { api, ApiError } from "../../lib/api"
import { useToast } from "../../composables/useToast"

const route = useRoute()
const router = useRouter()
const toast = useToast()

const token = String(route.params.token)
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
    await api.post(`/auth/reset/${token}`, {
      password: password.value,
      confirm_password: confirm.value,
    })
    toast.success("Your password has been changed. Please log in.")
    router.push({ name: "login" })
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Reset failed."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page container page--narrow">
    <div class="card">
      <h1 class="card__title">Set a new password</h1>

      <div v-if="error" class="alert alert--error" style="margin-bottom: 1rem">{{ error }}</div>

      <form @submit.prevent="submit">
        <div class="field">
          <label for="password">New password</label>
          <input id="password" class="input" type="password" v-model="password"
            autocomplete="new-password" required />
        </div>
        <div class="field">
          <label for="confirm">Confirm password</label>
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
