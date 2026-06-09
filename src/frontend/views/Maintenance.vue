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
  <section class="page container page--narrow center">
    <img src="/maintenance.png" alt="" style="max-width: 200px; margin: 2rem auto 1rem; display: block" />
    <h1>Under maintenance</h1>
    <p class="dim">
      NerVault is temporarily down for maintenance. Please check back shortly — this page refreshes
      automatically.
    </p>
  </section>
</template>
