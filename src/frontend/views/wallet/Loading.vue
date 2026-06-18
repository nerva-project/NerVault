<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue"
import { useRouter } from "vue-router"

import Card from "../../components/ui/Card.vue"
import { useWalletStore } from "../../stores/wallet"

const router = useRouter()
const wallet = useWalletStore()

const steps = ["Set up", "Connect", "Sync"]
const currentStep = ref(0)
const progress = ref<{ current: number; total: number } | null>(null)

const pct = computed(() => {
  if (!progress.value || progress.value.total <= 0) return 0
  return Math.min(
    100,
    Math.floor((progress.value.current / progress.value.total) * 100),
  )
})

const hints = [
  "Preparing your wallet…",
  "Connecting to the Nerva node…",
  "Syncing recent blocks…",
]
const hint = computed(() => hints[currentStep.value] ?? "")

function stepState(i: number): "done" | "active" | "pending" {
  if (i < currentStep.value) return "done"
  if (i === currentStep.value) return "active"
  return "pending"
}

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

    progress.value = s.progress ?? null

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
      currentStep.value = 0
      return
    }

    if (s.created && !s.connected && !connecting) {
      connecting = true
      currentStep.value = 1
      try {
        await wallet.connect()
      } catch {
        /* retry on the next poll */
      }
      connecting = false
      return
    }

    if (s.connected && !s.ready) {
      currentStep.value = 2
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
      <h1 class="text-[1.1rem] font-bold mt-2 mb-5">Loading your wallet</h1>
      <div class="flex items-center justify-center gap-2 sm:gap-3">
        <template v-for="(label, i) in steps" :key="label">
          <div class="flex items-center gap-2">
            <span
              class="grid place-items-center size-7 rounded-full border text-[0.72rem] font-bold transition-colors"
              :class="{
                'bg-accent/[0.14] text-accent border-accent/40': stepState(i) === 'done',
                'bg-accent text-accent-contrast border-accent ring-4 ring-accent/20': stepState(i) === 'active',
                'bg-surface text-muted border-border': stepState(i) === 'pending',
              }"
            >
              <span
                v-if="stepState(i) === 'active'"
                class="size-[13px] rounded-full border-2 border-current/30 border-t-current animate-spin"
              ></span>
              <svg
                v-else-if="stepState(i) === 'done'"
                class="size-[13px]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M20 6 9 17l-5-5" />
              </svg>
              <span v-else>{{ i + 1 }}</span>
            </span>
            <span
              class="text-[0.82rem] font-semibold transition-colors"
              :class="{
                'text-accent': stepState(i) === 'done',
                'text-text': stepState(i) === 'active',
                'text-muted': stepState(i) === 'pending',
              }"
              >{{ label }}</span
            >
          </div>
          <span
            v-if="i < steps.length - 1"
            class="h-0.5 w-6 sm:w-10 rounded-full transition-colors"
            :class="i < currentStep ? 'bg-accent' : 'bg-border'"
          ></span>
        </template>
      </div>
      <template v-if="currentStep === 0 && progress">
        <p class="text-muted text-[0.85rem] mt-5">
          Restoring from your seed — scanning the blockchain. This can take a while
          (often a few hours). You can safely leave this page and come back.
        </p>
        <div class="mt-4 h-3 w-full rounded-full bg-surface overflow-hidden">
          <div
            class="h-full rounded-full bg-accent progress-stripes transition-[width] duration-500"
            :style="{ width: pct + '%' }"
          ></div>
        </div>
        <p class="text-muted text-[0.8rem] mt-2 tabular-nums">
          {{ progress.current.toLocaleString() }} / {{ progress.total.toLocaleString() }} blocks ({{ pct }}%)
        </p>
      </template>
      <p v-else class="text-muted text-[0.85rem] mt-5">{{ hint }}</p>
    </Card>
  </section>
</template>
