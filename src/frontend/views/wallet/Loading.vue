<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue"
import { useRouter } from "vue-router"

import Card from "../../components/ui/Card.vue"
import { useWalletStore } from "../../stores/wallet"

const router = useRouter()
const wallet = useWalletStore()

const statusText = ref("Preparing your wallet…")
let timer: number | undefined
let connecting = false
let stopped = false

function stop(): void {
  stopped = true
  if (timer) clearInterval(timer)
}

async function poll(): Promise<void> {
  try {
    const s = await wallet.fetchStatus()
    if (!s || stopped) return

    if (!s.created) {
      stop()
      router.replace({ name: "wallet-setup" })
      return
    }

    if (s.connected && s.ready) {
      stop()
      // The container is up, but the session timer may have lapsed (e.g. the
      // reaper was down during an outage). Refresh it before handing off so the
      // dashboard doesn't immediately treat the session as expired and bounce
      // straight back here in a loop.
      try {
        await wallet.keepAlive()
      } catch {
        /* non-fatal — the dashboard handles a still-expired session */
      }
      router.replace({ name: "wallet-dashboard" })
      return
    }

    if (s.initializing) {
      statusText.value = "Initializing your wallet…"
      return
    }

    if (s.created && !s.connected && !connecting) {
      connecting = true
      statusText.value = "Connecting to your wallet…"
      try {
        await wallet.connect()
      } catch {
        /* retry on the next poll */
      }
      connecting = false
      return
    }

    if (s.connected && !s.ready) {
      statusText.value = "Syncing with the network…"
    }
  } catch {
    /* transient; retry on the next poll */
  }
}

onMounted(() => {
  poll()
  timer = window.setInterval(() => {
    if (!stopped) poll()
  }, 2500)
})

onUnmounted(stop)
</script>

<template>
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[520px] mx-auto flex flex-col justify-center text-center">
    <Card>
      <div class="size-[42px] rounded-full border-[3px] border-border border-t-accent animate-spin mx-auto my-6"></div>
      <h1 class="text-[1.1rem] font-bold mb-4">Loading your wallet</h1>
      <p class="text-text-dim">{{ statusText }}</p>
      <p class="text-muted text-[0.85rem]">
        This can take a moment while the wallet container starts and syncs with the network.
      </p>
    </Card>
  </section>
</template>
