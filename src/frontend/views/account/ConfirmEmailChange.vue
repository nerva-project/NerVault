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
    const res = await api.post(`/auth/change-email/${token}`)
    message.value = res.message || "Your email address has been updated."
    state.value = "success"
    await auth.fetchMe()
    window.setTimeout(() => router.push({ name: "profile" }), 1600)
  } catch (e) {
    message.value = e instanceof ApiError ? e.message : "Email change failed."
    state.value = "error"
  }
})
</script>

<template>
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[520px] mx-auto flex flex-col justify-center">
    <Card class="text-center">
      <h1 class="text-[1.1rem] font-bold mb-4">Email change</h1>

      <div v-if="state === 'loading'">
        <Spinner label="Confirming your new email…" />
      </div>

      <div v-else-if="state === 'success'">
        <Alert variant="success">{{ message }}</Alert>
        <p class="text-text-dim mt-4">Redirecting…</p>
      </div>

      <div v-else>
        <Alert>{{ message }}</Alert>
        <p class="mt-4"><RouterLink to="/profile">Back to profile</RouterLink></p>
      </div>
    </Card>
  </section>
</template>
