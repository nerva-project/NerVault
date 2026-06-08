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
  <section class="page container page--narrow center">
    <Card>
      <div class="spinner"></div>
      <h1 class="card__title">Loading your wallet</h1>
      <p class="dim">{{ statusText }}</p>
      <p class="muted" style="font-size: 0.85rem">
        This can take a moment while the wallet container starts and syncs with the network.
      </p>
    </Card>
  </section>
</template>
