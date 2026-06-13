<script setup lang="ts">
import { onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"

import { api } from "../lib/api"
import { clearMaintenanceCache } from "../router"

const router = useRouter()
let timer: number | undefined

async function check(): Promise<void> {
  try {
    const res = await api.get<{ maintenance: boolean }>("/meta/maintenance")
    if (!res.result?.maintenance) {
      clearMaintenanceCache()
      router.replace({ name: "home" })
    }
  } catch {
    /* ignore */
  }
}

onMounted(() => {
  check()
  timer = window.setInterval(check, 15000)
})

onUnmounted(() => clearInterval(timer))
</script>

<template>
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[520px] mx-auto flex flex-col justify-center text-center">
    <img src="/maintenance.png" alt="" class="max-w-[200px] mx-auto mt-8 mb-4 block" />
    <h1>Under maintenance</h1>
    <p class="text-text-dim">
      NerVault is temporarily down for maintenance. Please check back shortly — this page refreshes
      automatically.
    </p>
  </section>
</template>
