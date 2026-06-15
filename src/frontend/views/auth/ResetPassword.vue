<script setup lang="ts">
import { ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import Alert from "../../components/ui/Alert.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import FormField from "../../components/ui/FormField.vue"
import PasswordInput from "../../components/ui/PasswordInput.vue"
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
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[520px] mx-auto flex flex-col justify-center">
    <Card>
      <h1 class="text-[1.1rem] font-bold mb-4">Set a new password</h1>

      <Alert v-if="error" class="mb-4">{{ error }}</Alert>

      <form @submit.prevent="submit">
        <FormField label="New password" input-id="password">
          <PasswordInput id="password" v-model="password" autocomplete="new-password" required />
        </FormField>
        <FormField label="Confirm password" input-id="confirm">
          <PasswordInput id="confirm" v-model="confirm" autocomplete="new-password" required />
        </FormField>
        <Btn type="submit" variant="primary" block :disabled="loading">
          {{ loading ? "Saving…" : "Change password" }}
        </Btn>
      </form>
    </Card>
  </section>
</template>
