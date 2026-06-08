<script setup lang="ts">
import { ref } from "vue"
import { RouterLink } from "vue-router"

import Alert from "../../components/ui/Alert.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import FormField from "../../components/ui/FormField.vue"
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
    <Card>
      <h1 class="card__title">Reset password</h1>

      <Alert v-if="done" variant="success">
        If that email is registered and confirmed, a reset link has been sent. Please check your
        Junk/Spam folder.
      </Alert>

      <template v-else>
        <Alert v-if="error" style="margin-bottom: 1rem">{{ error }}</Alert>
        <form @submit.prevent="submit">
          <FormField label="Email address" input-id="email">
            <input id="email" class="input" type="email" v-model="email" autocomplete="email" required />
          </FormField>
          <Btn type="submit" variant="primary" block :disabled="loading">
            {{ loading ? "Sending…" : "Send reset link" }}
          </Btn>
        </form>
      </template>

      <p class="dim" style="margin-top: 1rem; font-size: 0.9rem">
        <RouterLink to="/login">Back to login</RouterLink>
      </p>
    </Card>
  </section>
</template>
