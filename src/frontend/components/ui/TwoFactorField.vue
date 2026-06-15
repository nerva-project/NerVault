<script setup lang="ts">
import { computed, ref, useId } from "vue"

import Btn from "./Btn.vue"
import FormField from "./FormField.vue"
import { api, ApiError } from "../../lib/api"
import { useToast } from "../../composables/useToast"
import { useAuthStore } from "../../stores/auth"

const model = defineModel<string>({ required: true })

const auth = useAuthStore()
const toast = useToast()
const id = useId()
const sending = ref(false)

const method = computed(() => auth.user?.two_factor?.method ?? null)

async function sendCode(): Promise<void> {
  if (sending.value) return
  sending.value = true
  try {
    const res = await api.post("/auth/2fa/step-up/send")
    toast.success(res.message || "A code has been sent to your email.")
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : "Could not send a code.")
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <FormField v-if="method" :input-id="id" label="Two-factor code"
    :hint="method === 'totp' ? 'From your authenticator app.' : undefined">
    <div class="flex gap-2">
      <input :id="id" class="input" v-model="model" autocomplete="one-time-code"
        :inputmode="method === 'totp' ? 'numeric' : 'text'"
        :placeholder="method === 'totp' ? '123456' : 'Code from your email'" required />
      <Btn v-if="method === 'email'" type="button" variant="ghost" size="sm" class="shrink-0"
        :disabled="sending" @click="sendCode">
        {{ sending ? "Sending…" : "Send code" }}
      </Btn>
    </div>
  </FormField>
</template>
