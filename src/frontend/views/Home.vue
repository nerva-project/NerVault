<script setup lang="ts">
import { onMounted, ref } from "vue"
import { RouterLink } from "vue-router"

import Stat from "../components/ui/Stat.vue"
import { api } from "../lib/api"
import { useAuthStore } from "../stores/auth"

interface MetaInfo {
  node: Record<string, number | string>
  coin: Record<string, number | string>
}

const auth = useAuthStore()
const info = ref<MetaInfo | null>(null)

function num(value: number | string | undefined): string {
  if (value === undefined || value === null) return "—"
  const n = typeof value === "number" ? value : Number(value)
  return Number.isFinite(n) ? n.toLocaleString() : "—"
}

function usd(value: number | string | undefined): string {
  if (value === undefined || value === null) return "—"
  const n = typeof value === "number" ? value : Number(value)
  return Number.isFinite(n)
    ? n.toLocaleString(undefined, { style: "currency", currency: "USD" })
    : "—"
}

onMounted(async () => {
  try {
    const res = await api.get<MetaInfo>("/meta/info")
    info.value = res.result ?? null
  } catch {
    /* ignore */
  }
})
</script>

<template>
  <section class="page container">
    <div class="hero">
      <h1>Your XNV, in the browser</h1>
      <p>
        NerVault is a custodial web wallet for the Nerva (XNV) cryptocurrency. Create or restore a
        wallet, check your balance, and send XNV — no software to install.
      </p>
      <div class="stack" style="flex-direction: row; justify-content: center; gap: 0.75rem">
        <template v-if="auth.isAuthenticated">
          <RouterLink class="btn btn--primary btn--lg" to="/wallet/dashboard">Open wallet</RouterLink>
        </template>
        <template v-else>
          <RouterLink class="btn btn--primary btn--lg" to="/register">Get started</RouterLink>
          <RouterLink class="btn btn--ghost btn--lg" to="/login">Login</RouterLink>
        </template>
      </div>
    </div>

    <div class="grid grid--stats" style="margin-top: 2rem">
      <Stat label="Block height">{{ num(info?.node.height) }}</Stat>
      <Stat label="Difficulty">{{ num(info?.node.difficulty) }}</Stat>
      <Stat label="Price">{{ usd(info?.coin.current_price) }}</Stat>
      <Stat label="Market cap">{{ usd(info?.coin.market_cap) }}</Stat>
    </div>
  </section>
</template>
