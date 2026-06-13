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
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[520px] mx-auto flex flex-col justify-center">
    <Card>
      <h1 class="text-[1.1rem] font-bold mb-4">Reset password</h1>

      <Alert v-if="done" variant="success">
        If that email is registered and confirmed, a reset link has been sent. Please check your
        Junk/Spam folder.
      </Alert>

      <template v-else>
        <Alert v-if="error" class="mb-4">{{ error }}</Alert>
        <form @submit.prevent="submit">
          <FormField label="Email address" input-id="email">
            <input id="email" class="input" type="email" v-model="email" autocomplete="email" required />
          </FormField>
          <Btn type="submit" variant="primary" block :disabled="loading">
            {{ loading ? "Sending…" : "Send reset link" }}
          </Btn>
        </form>
      </template>

      <p class="text-text-dim mt-4 text-[0.9rem]">
        <RouterLink to="/login">Back to login</RouterLink>
      </p>
    </Card>
  </section>
</template>
