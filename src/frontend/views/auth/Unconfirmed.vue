<script setup lang="ts">
import { ref } from "vue"

import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
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
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[520px] mx-auto flex flex-col justify-center">
    <Card class="text-center">
      <h1 class="text-[1.1rem] font-bold mb-4">Confirm your email</h1>
      <p class="text-text-dim">
        We've sent a confirmation link to <b>{{ auth.user?.email }}</b>. Please click it to activate
        your account. Check your Junk/Spam folder if you don't see it.
      </p>
      <Btn variant="ghost" :disabled="loading" @click="resend">
        {{ loading ? "Sending…" : "Resend email" }}
      </Btn>
    </Card>
  </section>
</template>
