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
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[1080px] mx-auto">
    <div class="text-center pt-12 pb-4">
      <h1 class="text-[clamp(2rem,5vw,3rem)] tracking-[-0.03em] bg-[image:var(--grad)] bg-clip-text text-transparent">Your XNV, in the browser</h1>
      <p class="text-text-dim max-w-[560px] mx-auto mb-6 text-[1.1rem]">
        NerVault is a custodial web wallet for the Nerva (XNV) cryptocurrency. Create or restore a
        wallet, check your balance, and send XNV — no software to install.
      </p>
      <div class="flex flex-row justify-center gap-3">
        <template v-if="auth.isAuthenticated">
          <RouterLink
            class="inline-flex items-center justify-center gap-2 border border-transparent font-semibold cursor-pointer transition px-8 py-4 text-[1.05rem] rounded-card bg-accent text-accent-contrast hover:bg-accent-strong hover:no-underline"
            to="/wallet/dashboard"
            >Open wallet</RouterLink
          >
        </template>
        <template v-else>
          <RouterLink
            class="inline-flex items-center justify-center gap-2 border border-transparent font-semibold cursor-pointer transition px-8 py-4 text-[1.05rem] rounded-card bg-accent text-accent-contrast hover:bg-accent-strong hover:no-underline"
            to="/register"
            >Get started</RouterLink
          >
          <RouterLink
            class="inline-flex items-center justify-center gap-2 border border-border font-semibold cursor-pointer transition px-8 py-4 text-[1.05rem] rounded-card bg-surface text-text hover:border-accent hover:no-underline"
            to="/login"
            >Login</RouterLink
          >
        </template>
      </div>
    </div>

    <div class="grid gap-4 grid-cols-[repeat(auto-fit,minmax(180px,1fr))] mt-8">
      <Stat label="Block height">{{ num(info?.node.height) }}</Stat>
      <Stat label="Difficulty">{{ num(info?.node.difficulty) }}</Stat>
      <Stat label="Price">{{ usd(info?.coin.current_price) }}</Stat>
      <Stat label="Market cap">{{ usd(info?.coin.market_cap) }}</Stat>
    </div>
  </section>
</template>
