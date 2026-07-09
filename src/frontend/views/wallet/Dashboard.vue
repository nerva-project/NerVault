<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch, type ComponentPublicInstance } from "vue"
import { useRouter } from "vue-router"

import { api, ApiError, API_BASE } from "../../lib/api"
import { fromAtomic, toAtomic, formatTimestamp, shortenAddress } from "../../lib/format"
import Alert from "../../components/ui/Alert.vue"
import Badge from "../../components/ui/Badge.vue"
import BaseModal from "../../components/ui/BaseModal.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import CopyField from "../../components/ui/CopyField.vue"
import FormField from "../../components/ui/FormField.vue"
import PasswordInput from "../../components/ui/PasswordInput.vue"
import TwoFactorField from "../../components/ui/TwoFactorField.vue"
import InfoTip from "../../components/ui/InfoTip.vue"
import Spinner from "../../components/ui/Spinner.vue"
import { useToast } from "../../composables/useToast"
import { useWalletStore } from "../../stores/wallet"
import { useAuthStore } from "../../stores/auth"

const router = useRouter()
const wallet = useWalletStore()
const auth = useAuthStore()
const toast = useToast()

const loading = ref(true)
const error = ref("")
const qrSrc = `${API_BASE}/wallet/qr`
const addrQrLoaded = ref(false)

const overview = computed(() => wallet.overview)

const recvCard = ref<ComponentPublicInstance | null>(null)
const txCard = ref<ComponentPublicInstance | null>(null)

const now = ref(Date.now())

const fiat = computed(() => {
  const o = overview.value
  if (!o || !o.price) return null
  const usd = Number(fromAtomic(o.balance)) * o.price
  return usd.toLocaleString(undefined, { style: "currency", currency: "USD" })
})

const locked = computed(() => {
  const o = overview.value
  if (!o) return 0n
  const diff = BigInt(o.balance) - BigInt(o.unlocked_balance)
  return diff > 0n ? diff : 0n
})

const balanceLine1 = computed(() => {
  const o = overview.value
  if (!o) return ""
  const parts: string[] = []
  if (fiat.value) parts.push(`≈ ${fiat.value}`)
  if (locked.value > 0n) parts.push(`${fromAtomic(o.unlocked_balance)} unlocked`)
  return parts.join(" · ")
})

const lockedLine = computed(() => {
  const o = overview.value
  if (!o || locked.value <= 0n) return ""
  const n = o.blocks_to_unlock
  const suffix =
    n > 0 ? ` · unlocks in ~${n} ${n === 1 ? "block" : "blocks"}` : ""
  return `${fromAtomic(locked.value)} locked${suffix}`
})

const synced = computed(() => {
  const o = overview.value
  if (!o || !o.network_height) return false
  return o.wallet_height >= o.network_height - 1
})

const blocksBehind = computed(() => {
  const o = overview.value
  if (!o) return 0
  return Math.max(0, o.network_height - o.wallet_height)
})

const sessionLeft = computed(() => {
  const o = overview.value
  if (!o?.expires_at) return null
  const ms = new Date(o.expires_at).getTime() - now.value
  if (ms <= 0) return "expired"
  const totalMin = Math.floor(ms / 60000)
  if (totalMin >= 60) return `${Math.floor(totalMin / 60)}h ${totalMin % 60}m`
  if (totalMin >= 1) return `${totalMin}m`
  return `${Math.floor(ms / 1000)}s`
})

let expiring = false
function expireSession(): void {
  if (expiring) return
  expiring = true
  wallet.reset()
  router.replace({ name: "wallet-loading" })
}

watch(sessionLeft, (left) => {
  if (left === "expired") expireSession()
})

// Keep an actively-used tab's container warm instead of letting it expire and
// rebuild: renew shortly before expiry, but only while the user is genuinely
// here (recent interaction, tab visible). A walked-away tab still lapses and
// gets reaped.
const IDLE_LIMIT_MS = 5 * 60 * 1000
const RENEW_MARGIN_MS = 60 * 1000
const ACTIVITY_EVENTS = ["mousemove", "mousedown", "keydown", "scroll", "touchstart"] as const

let lastActivity = Date.now()
function markActive(): void {
  lastActivity = Date.now()
}

let renewing = false
async function maybeRenew(): Promise<void> {
  const o = overview.value
  if (!o?.expires_at || renewing || document.hidden) return
  if (now.value - lastActivity > IDLE_LIMIT_MS) return
  const ms = new Date(o.expires_at).getTime() - now.value
  if (ms <= 0 || ms > RENEW_MARGIN_MS) return
  renewing = true
  try {
    await wallet.keepAlive()
  } catch (e) {
    if (e instanceof ApiError && (e.code === "not_connected" || e.status === 401)) {
      expireSession()
    }
  } finally {
    renewing = false
  }
}

// Silently re-fetch the overview so balances and transactions stay current
// without a manual reload. Skips hidden tabs; a failed attempt waits out the
// full interval before retrying.
const REFRESH_INTERVAL_MS = 30 * 1000

let lastRefresh = Date.now()
let refreshing = false
async function maybeRefresh(): Promise<void> {
  if (loading.value || refreshing || document.hidden) return
  if (now.value - lastRefresh < REFRESH_INTERVAL_MS) return
  refreshing = true
  try {
    await wallet.fetchOverview()
  } catch (e) {
    if (e instanceof ApiError && (e.code === "not_connected" || e.code === "not_ready" || e.status === 401)) {
      expireSession()
    }
  } finally {
    lastRefresh = Date.now()
    refreshing = false
  }
}

async function keepAlive(): Promise<void> {
  try {
    await wallet.keepAlive()
    toast.success("Session extended.")
  } catch (e) {
    if (e instanceof ApiError && (e.code === "not_connected" || e.status === 401)) {
      expireSession()
      return
    }
    toast.error(e instanceof ApiError ? e.message : "Could not extend session.")
  }
}

function txBadge(type: string): { variant: "in" | "out" | "pending"; label: string } {
  if (type === "in" || type === "out") return { variant: type, label: type }
  if (type === "failed") return { variant: "out", label: "failed" }
  return { variant: "pending", label: "pending" }
}

const txList = computed(() => {
  const sorted = wallet.overview?.sorted_transactions ?? {}
  return Object.entries(sorted)
    .map(([key, t]) => ({ key, ...t }))
    .sort((a, b) => b.timestamp - a.timestamp)
})

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    await wallet.fetchOverview()
  } catch (e) {
    if (e instanceof ApiError) {
      if (e.code === "not_created") {
        router.replace({ name: "wallet-setup" })
        return
      }
      if (e.code === "not_connected" || e.code === "not_ready" || e.status === 401) {
        expireSession()
        return
      }
      error.value = e.message
    } else {
      error.value = "Could not load your wallet."
    }
  } finally {
    loading.value = false
  }
}

function syncCardHeights(): void {
  const recv = recvCard.value?.$el as HTMLElement | undefined
  const tx = txCard.value?.$el as HTMLElement | undefined
  if (!recv || !tx) return
  // Side-by-side: match the transactions card to the (dynamic) receive card.
  // Stacked on mobile, so let it size naturally.
  tx.style.height = window.innerWidth <= 640 ? "" : `${recv.offsetHeight}px`
}

let timer: ReturnType<typeof setInterval> | undefined
let cardRO: ResizeObserver | undefined
onMounted(() => {
  void load()
  timer = setInterval(() => {
    now.value = Date.now()
    void maybeRenew()
    void maybeRefresh()
  }, 1000)
  ACTIVITY_EVENTS.forEach((ev) => window.addEventListener(ev, markActive, { passive: true }))
  cardRO = new ResizeObserver(() => syncCardHeights())
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  ACTIVITY_EVENTS.forEach((ev) => window.removeEventListener(ev, markActive))
  cardRO?.disconnect()
})

watch(
  loading,
  async (l) => {
    if (l) return
    await nextTick()
    const recv = recvCard.value?.$el as HTMLElement | undefined
    if (recv && cardRO) {
      cardRO.disconnect()
      cardRO.observe(recv)
    }
    syncCardHeights()
  },
  { immediate: true },
)

/* ---- Receive ---- */
const receiveMode = ref<"address" | "integrated">("address")
const intAddr = ref("")
const intQr = ref("")
const intPid = ref("")
const intErr = ref("")
const intLoading = ref(false)
const intCustomLoad = ref(false)

async function fetchIntegrated(paymentId: string): Promise<void> {
  intErr.value = ""
  // A non-empty payment ID came from the user (typed/pasted): keep it visible
  // and just disable the input while regenerating, rather than shimmering it.
  intCustomLoad.value = paymentId !== ""
  intLoading.value = true
  try {
    const res = await api.post<{
      integrated_address: string
      payment_id: string
      qr: string
    }>("/wallet/integrated-address", { payment_id: paymentId })
    const r = res.result
    if (r) {
      intAddr.value = r.integrated_address
      intQr.value = r.qr
      intPid.value = r.payment_id
    }
  } catch (e) {
    intErr.value =
      e instanceof ApiError ? e.message : "Could not generate an integrated address."
  } finally {
    intLoading.value = false
  }
}

function showIntegrated(): void {
  receiveMode.value = "integrated"
  if (!intAddr.value) void fetchIntegrated("")
}

function regenerateIntegrated(): void {
  void fetchIntegrated("")
}

let pidDebounce: ReturnType<typeof setTimeout> | undefined
function onPidInput(): void {
  // Apply a typed/pasted payment ID automatically (no Enter needed), debounced
  // so we don't refetch on every keystroke.
  if (pidDebounce) clearTimeout(pidDebounce)
  pidDebounce = setTimeout(() => {
    const pid = intPid.value.trim().toLowerCase()
    if (!pid) {
      intErr.value = ""
      return
    }
    if (/^[0-9a-f]{16}$/.test(pid)) {
      intErr.value = ""
      void fetchIntegrated(pid)
      return
    }
    // Only complain once the entry is clearly wrong, not while still typing.
    intErr.value =
      pid.length >= 16 || /[^0-9a-f]/.test(pid)
        ? "Payment ID must be 16 hexadecimal characters."
        : ""
  }, 500)
}

/* ---- Send ---- */
const sendOpen = ref(false)
const sendAddr = ref("")
const sendAmount = ref("")
const sendSweep = ref(false)
const sendPid = ref("")
const reviewing = ref(false)
const sending = ref(false)
const sendErr = ref("")
const confirmOpen = ref(false)
const confirmErr = ref("")
const sendCode = ref("")
const sendPass = ref("")
const hasTwoFactor = computed(() => !!auth.user?.two_factor?.method)
const prepared = ref<{
  prepare_id: string
  amount: string
  fee: string
  address: string
} | null>(null)
const sweepToggleDisabled = computed(() => !sendAddr.value.trim())

const unlockedBalance = computed(() => wallet.overview?.unlocked_balance ?? "0")

const amountExceeds = computed(() => {
  if (sendSweep.value) return false
  const a = sendAmount.value.trim()
  if (!a || a === ".") return false
  try {
    return toAtomic(a) > BigInt(unlockedBalance.value)
  } catch {
    return false
  }
})

const pidValid = computed(() => {
  const p = sendPid.value.trim().toLowerCase()
  return p === "" || /^[0-9a-f]{16}$/.test(p)
})

const canReview = computed(() => {
  if (reviewing.value || !sendAddr.value.trim()) return false
  if (!pidValid.value) return false
  if (sendSweep.value) return true
  const a = sendAmount.value.trim()
  return !!a && a !== "." && !amountExceeds.value
})

function openSend(): void {
  sendErr.value = ""
  sendSweep.value = false
  prepared.value = null
  confirmErr.value = ""
  sendOpen.value = true
}

// Sweep needs a destination; drop the toggle if the address is cleared.
watch(sendAddr, () => {
  if (!sendAddr.value.trim()) sendSweep.value = false
})

function toggleSweep(): void {
  if (sweepToggleDisabled.value) return
  sendSweep.value = !sendSweep.value
  if (sendSweep.value) sendAmount.value = ""
}

async function review(): Promise<void> {
  if (!canReview.value) return
  sendErr.value = ""
  reviewing.value = true
  try {
    const res = await api.post<{
      prepare_id: string
      amount: string
      fee: string
    }>("/wallet/transfer/prepare", {
      address: sendAddr.value.trim(),
      sweep: sendSweep.value,
      amount: sendSweep.value ? undefined : sendAmount.value.trim(),
      payment_id: sendPid.value.trim() || undefined,
    })
    prepared.value = res.result
      ? { ...res.result, address: sendAddr.value.trim() }
      : null
    if (!prepared.value) {
      sendErr.value = "Could not prepare the transaction."
      return
    }
    confirmErr.value = ""
    sendCode.value = ""
    sendPass.value = ""
    sendOpen.value = false
    confirmOpen.value = true
  } catch (e) {
    sendErr.value =
      e instanceof ApiError ? e.message : "Could not prepare the transaction."
  } finally {
    reviewing.value = false
  }
}

function backToReview(): void {
  if (sending.value) return
  confirmOpen.value = false
  confirmErr.value = ""
  sendOpen.value = true
}

function onSendAmountInput(e: Event): void {
  const el = e.target as HTMLInputElement
  let v = el.value.replace(/[^0-9.]/g, "")
  const dot = v.indexOf(".")
  if (dot !== -1) {
    v = v.slice(0, dot + 1) + v.slice(dot + 1).replace(/\./g, "")
  }
  sendAmount.value = v
  if (el.value !== v) el.value = v
}

function generatePaymentId(): void {
  const bytes = new Uint8Array(8)
  crypto.getRandomValues(bytes)
  sendPid.value = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")
}

async function confirmSend(): Promise<void> {
  if (sending.value) return
  confirmErr.value = ""
  sending.value = true
  try {
    const res = await api.post("/wallet/transfer", {
      prepare_id: prepared.value?.prepare_id,
      code: sendCode.value,
      password: sendPass.value,
    })
    toast.success(res.message || "Transaction sent.")
    confirmOpen.value = false
    prepared.value = null
    sendCode.value = ""
    sendPass.value = ""
    sendAddr.value = ""
    sendAmount.value = ""
    sendSweep.value = false
    sendPid.value = ""
    await load()
  } catch (e) {
    const err = e instanceof ApiError ? e : null
    // A stale/expired preview can't be relayed — send them back to re-review.
    if (err && err.code === "expired") {
      confirmOpen.value = false
      prepared.value = null
      sendOpen.value = true
      sendErr.value = err.message
    } else {
      confirmErr.value = err ? err.message : "Transaction failed."
    }
  } finally {
    sending.value = false
  }
}

/* ---- Secrets ---- */
const secretsOpen = ref(false)
const secretPass = ref("")
const secrets = ref<Record<string, string> | null>(null)
const secretLoading = ref(false)
const secretErr = ref("")
const secretCode = ref("")

const secretFields: { key: string; label: string }[] = [
  { key: "mnemonic_seed", label: "Mnemonic seed" },
  { key: "public_spend_key", label: "Public spend key" },
  { key: "secret_spend_key", label: "Secret spend key" },
  { key: "public_view_key", label: "Public view key" },
  { key: "secret_view_key", label: "Secret view key" },
]

function closeSecrets(): void {
  secretsOpen.value = false
  secrets.value = null
  secretPass.value = ""
  secretCode.value = ""
  secretErr.value = ""
}

async function reveal(): Promise<void> {
  if (secretLoading.value) return
  secretErr.value = ""
  secretLoading.value = true
  try {
    const res = await api.post<Record<string, string>>("/wallet/secrets", {
      password: secretPass.value,
      code: secretCode.value,
    })
    secrets.value = res.result ?? null
  } catch (e) {
    secretErr.value = e instanceof ApiError ? e.message : "Could not reveal secrets."
  } finally {
    secretLoading.value = false
    secretPass.value = ""
    secretCode.value = ""
  }
}

/* ---- Delete ---- */
const deleteOpen = ref(false)
const deleting = ref(false)
const deleteCode = ref("")
const deletePass = ref("")
const deleteErr = ref("")

function openDelete(): void {
  deleteCode.value = ""
  deletePass.value = ""
  deleteErr.value = ""
  deleteOpen.value = true
}

function closeDelete(): void {
  if (deleting.value) return
  deleteOpen.value = false
  deleteCode.value = ""
  deletePass.value = ""
  deleteErr.value = ""
}

async function remove(): Promise<void> {
  if (deleting.value) return
  deleteErr.value = ""
  deleting.value = true
  try {
    await api.post("/wallet/delete", {
      confirm: true,
      code: deleteCode.value,
      password: deletePass.value,
    })
    toast.success("Wallet data deleted.")
    deleteOpen.value = false
    wallet.reset()
    router.push({ name: "wallet-setup" })
  } catch (e) {
    deleteErr.value = e instanceof ApiError ? e.message : "Could not delete wallet."
  } finally {
    deleting.value = false
    deleteCode.value = ""
    deletePass.value = ""
  }
}
</script>

<template>
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[1080px] mx-auto">
    <Spinner v-if="loading" label="Loading your wallet…" />

    <Alert v-else-if="error">{{ error }}</Alert>

    <div v-else-if="overview" class="flex flex-col gap-5">
      <Card class="flex flex-col gap-4">
        <div
          class="grid grid-cols-4 gap-7 items-stretch [&>*+*]:border-l [&>*+*]:border-border [&>*+*]:pl-7 max-[860px]:grid-cols-1 max-[860px]:gap-5 max-[860px]:[&>*+*]:border-l-0 max-[860px]:[&>*+*]:pl-0"
        >
          <div>
            <div class="text-muted text-[0.8rem] uppercase tracking-[0.05em]">Balance</div>
            <div class="min-h-[2.4rem] mt-[0.35rem] flex items-end">
              <div class="text-[2rem] font-extrabold font-mono break-all">
                {{ fromAtomic(overview.balance) }} <span class="text-muted text-base">XNV</span>
              </div>
            </div>
            <p v-if="balanceLine1" class="text-muted mt-[0.45rem] text-[0.85rem]">{{ balanceLine1 }}</p>
            <p v-if="lockedLine" class="text-muted mt-[0.15rem] text-[0.85rem]">{{ lockedLine }}</p>
          </div>
          <div>
            <div class="text-muted text-[0.8rem] uppercase tracking-[0.05em]">Network</div>
            <div class="min-h-[2.4rem] mt-[0.35rem] flex items-end">
              <Badge :variant="synced ? 'in' : 'out'">
                {{ synced ? "Synced" : `Syncing · ${blocksBehind.toLocaleString()} behind` }}
              </Badge>
            </div>
            <p class="text-muted mt-[0.45rem] text-[0.85rem]">Block {{ overview.network_height.toLocaleString() }}</p>
          </div>
          <div>
            <div class="text-muted text-[0.8rem] uppercase tracking-[0.05em]">Session</div>
            <div class="min-h-[2.4rem] mt-[0.35rem] flex items-end">
              <span class="text-[1.1rem] font-semibold">{{ sessionLeft ?? "—" }}</span>
            </div>
            <Btn variant="ghost" size="sm" class="mt-[0.45rem]" @click="keepAlive">
              Keep alive
            </Btn>
          </div>
          <div class="flex flex-col justify-center gap-2 min-w-[150px] max-[860px]:flex-row">
            <Btn variant="primary" class="max-[860px]:flex-1" @click="openSend">Send XNV</Btn>
            <Btn variant="ghost" class="max-[860px]:flex-1" @click="load">Refresh</Btn>
          </div>
        </div>
      </Card>

      <div class="grid grid-cols-[300px_1fr] gap-5 items-start max-[640px]:grid-cols-1">
        <Card ref="recvCard" class="text-center">
          <div class="inline-flex gap-[2px] mb-4 p-[3px] bg-bg-soft border border-border rounded-field">
            <button type="button"
              class="border-0 text-[0.85rem] font-semibold px-[0.9rem] py-[0.3rem] rounded-[8px] cursor-pointer"
              :class="receiveMode === 'address' ? 'bg-surface text-text' : 'bg-transparent text-muted'"
              @click="receiveMode = 'address'">Address</button>
            <button type="button"
              class="border-0 text-[0.85rem] font-semibold px-[0.9rem] py-[0.3rem] rounded-[8px] cursor-pointer"
              :class="receiveMode === 'integrated' ? 'bg-surface text-text' : 'bg-transparent text-muted'"
              @click="showIntegrated">Integrated</button>
          </div>

          <template v-if="receiveMode === 'address'">
            <div class="w-full max-w-[240px] aspect-square mx-auto flex items-center justify-center rounded-field p-2"
              :class="addrQrLoaded ? 'bg-white' : 'bg-transparent border border-border'">
              <img v-show="addrQrLoaded" class="w-full h-full object-contain block" :src="qrSrc"
                @load="addrQrLoaded = true" alt="Wallet address QR code" />
              <div v-if="!addrQrLoaded" class="size-[42px] rounded-full border-[3px] border-border border-t-accent animate-spin"></div>
            </div>
            <CopyField
              class="mt-3"
              :value="overview.address"
              :display="shortenAddress(overview.address, 10, 8)"
            />
          </template>

          <template v-else>
            <div class="w-full max-w-[240px] aspect-square mx-auto flex items-center justify-center rounded-field p-2"
              :class="intLoading || !intQr ? 'bg-transparent border border-border' : 'bg-white'">
              <img v-if="intQr && !intLoading" class="w-full h-full object-contain block" :src="intQr" alt="Integrated address QR code" />
              <div v-else-if="intLoading" class="size-[42px] rounded-full border-[3px] border-border border-t-accent animate-spin"></div>
            </div>
            <CopyField
              class="mt-3"
              :value="intAddr"
              :display="intAddr ? shortenAddress(intAddr, 10, 8) : ''"
              :loading="intLoading || !intAddr"
            />
            <div class="flex flex-col gap-[0.4rem] w-full mt-[0.6rem] text-left">
              <div class="flex items-center gap-[0.4rem]">
                <label for="intpid">Payment ID</label>
                <InfoTip
                  centered
                  text="A tag embedded in the integrated address to identify incoming payments. A random 16-character hex value is filled in for you — type or paste your own to use a specific one (it applies automatically), or use the refresh button for a new random one."
                />
              </div>
              <div class="flex gap-2">
                <div v-if="intLoading && !intCustomLoad"
                  class="flex-1 w-full px-[0.85rem] py-[0.625rem] bg-bg-soft border border-border rounded-field" aria-hidden="true">
                  <span class="inline-block align-middle w-full h-[0.95rem] rounded-[4px] skel"></span>
                </div>
                <input v-else id="intpid"
                  class="flex-1 w-full px-[0.85rem] py-[0.625rem] bg-bg-soft border border-border rounded-field text-text font-mono text-[0.82rem] focus:border-accent focus:outline-none disabled:opacity-60 disabled:cursor-default"
                  v-model="intPid" @input="onPidInput"
                  :disabled="intLoading" placeholder="16-character hex" autocomplete="off"
                  spellcheck="false" />
                <button type="button" :disabled="intLoading"
                  class="inline-flex items-center justify-center w-[38px] h-auto rounded-field border border-border bg-surface text-text-dim cursor-pointer hover:text-text hover:border-accent [&_svg]:size-[18px]"
                  title="Generate a random payment ID"
                  aria-label="Generate a random payment ID" @click="regenerateIntegrated">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                    stroke-linecap="round" stroke-linejoin="round">
                    <path d="M23 4v6h-6M1 20v-6h6" />
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                  </svg>
                </button>
              </div>
              <p v-if="intErr" class="m-0 mt-[0.1rem] text-[0.82rem] text-danger">{{ intErr }}</p>
            </div>
          </template>
        </Card>

        <Card ref="txCard" class="flex flex-col" title="Transactions">
          <p v-if="!txList.length" class="text-muted">No transactions yet.</p>
          <div v-else class="border border-border rounded-card flex-1 min-h-0 overflow-auto">
            <table
              class="w-full border-collapse text-[0.9rem] [&_th]:px-4 [&_th]:py-3 [&_th]:text-left [&_th]:whitespace-nowrap [&_td]:px-4 [&_td]:py-3 [&_td]:whitespace-nowrap [&_thead_th]:text-muted [&_thead_th]:font-semibold [&_thead_th]:text-[0.78rem] [&_thead_th]:uppercase [&_thead_th]:tracking-[0.04em] [&_thead_th]:border-b [&_thead_th]:border-border [&_tbody_tr+tr_td]:border-t [&_tbody_tr+tr_td]:border-border-soft [&_.num]:text-right [&_td.num]:font-mono">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Date</th>
                  <th>Tx</th>
                  <th class="num">Amount</th>
                  <th class="num">Balance</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="tx in txList" :key="tx.key">
                  <td>
                    <Badge :variant="txBadge(tx.type).variant">{{ txBadge(tx.type).label }}</Badge>
                  </td>
                  <td class="text-text-dim">{{ formatTimestamp(tx.timestamp) }}</td>
                  <td>
                    <a class="font-mono text-[0.85rem]" :href="`https://explorer.nerva.one/detail/${tx.txid}`"
                      target="_blank" rel="noopener">{{ shortenAddress(tx.txid, 8, 6) }}</a>
                  </td>
                  <td class="num">{{ fromAtomic(tx.amount) }}</td>
                  <td class="num">{{ fromAtomic(tx.total) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <Card title="Wallet tools">
        <div class="flex flex-wrap gap-2">
          <Btn variant="ghost" class="flex-1 min-w-[180px]" @click="secretsOpen = true">View secrets</Btn>
          <Btn variant="danger" class="flex-1 min-w-[180px]" @click="openDelete">Delete wallet</Btn>
        </div>
      </Card>
    </div>

    <BaseModal :open="sendOpen" title="Send XNV" @close="sendOpen = false">
      <Alert v-if="sendErr" class="mb-4">{{ sendErr }}</Alert>
      <form @submit.prevent="review">
        <FormField label="Destination address" input-id="sa">
          <input id="sa" class="input" v-model="sendAddr" autocomplete="off" required />
        </FormField>
        <FormField
          label="Amount"
          input-id="sm"
          hint='Amount of XNV to send, e.g. 12.5 (up to 12 decimal places). Tick "Send all" to send your entire unlocked balance, minus the network fee — the amount is calculated for you.'
          :error="amountExceeds ? 'Amount exceeds your unlocked balance.' : ''"
        >
          <div class="flex flex-wrap items-stretch gap-2">
            <input
              id="sm"
              class="input flex-1 min-w-[160px]"
              type="text"
              inputmode="decimal"
              :value="sendAmount"
              @input="onSendAmountInput"
              :disabled="sendSweep"
              :placeholder="sendSweep ? 'Entire balance' : 'e.g. 12.5'"
              :required="!sendSweep"
            />
            <div class="group relative inline-flex">
              <button
                type="button"
                role="checkbox"
                :aria-checked="sendSweep"
                :aria-disabled="sweepToggleDisabled"
                @click="toggleSweep"
                class="inline-flex items-center gap-[0.45rem] h-full px-[0.85rem] rounded-field border text-[0.9rem] font-medium select-none transition-colors"
                :class="sweepToggleDisabled
                  ? 'border-border text-muted opacity-60 cursor-not-allowed'
                  : sendSweep
                    ? 'border-accent text-accent bg-accent/[0.1] cursor-pointer'
                    : 'border-border text-text-dim hover:border-accent cursor-pointer'"
              >
                <input type="checkbox" :checked="sendSweep" tabindex="-1" aria-hidden="true" class="accent-accent pointer-events-none" />
                Send all
              </button>
              <span
                v-if="sweepToggleDisabled"
                class="absolute right-0 bottom-[calc(100%_+_8px)] w-max max-w-[220px] px-[0.7rem] py-[0.55rem] bg-bg-soft border border-border rounded-field shadow-card text-text-dim text-[0.8rem] font-normal leading-[1.4] opacity-0 invisible transition-opacity duration-[120ms] z-20 pointer-events-none group-hover:opacity-100 group-hover:visible"
                >Enter a destination address first.</span
              >
            </div>
          </div>
          <p class="mt-2 text-[0.8rem] text-muted">
            Available: {{ fromAtomic(unlockedBalance) }} XNV<template v-if="lockedLine"> · {{ lockedLine }}</template>
          </p>
        </FormField>
        <FormField
          label="Payment ID (optional)"
          input-id="sp"
          hint="An optional 16-character hex tag some exchanges or services require to credit your deposit. Leave it empty unless the recipient asks for one."
        >
          <div class="flex gap-2">
            <input id="sp" class="input flex-1" v-model="sendPid" autocomplete="off" />
            <Btn variant="ghost" @click="generatePaymentId">Generate</Btn>
          </div>
          <p v-if="!pidValid" class="mt-2 text-[0.8rem] text-danger">
            Payment ID must be 16 hexadecimal characters.
          </p>
        </FormField>
        <Btn type="submit" variant="primary" block :disabled="!canReview">
          {{ reviewing ? "Reviewing…" : "Review transaction" }}
        </Btn>
      </form>
    </BaseModal>

    <BaseModal :open="confirmOpen" title="Confirm transaction" @close="backToReview">
      <Alert v-if="confirmErr" class="mb-4">{{ confirmErr }}</Alert>
      <div class="flex flex-col gap-3 mb-5">
        <div>
          <div class="text-text-dim text-[0.8rem] mb-1">To</div>
          <CopyField :value="prepared?.address ?? ''" wrap />
        </div>
        <div class="flex justify-between gap-4 border-t border-border-soft pt-3 text-[0.95rem]">
          <span class="text-text-dim">{{ sendSweep ? "Amount (send all)" : "Amount" }}</span>
          <span class="font-semibold">{{ prepared ? fromAtomic(prepared.amount) : "—" }} XNV</span>
        </div>
        <div class="flex justify-between gap-4 text-[0.95rem]">
          <span class="text-text-dim">Network fee</span>
          <span>{{ prepared ? fromAtomic(prepared.fee) : "—" }} XNV</span>
        </div>
        <div class="flex justify-between gap-4 border-t border-border-soft pt-3 font-semibold">
          <span>Total</span>
          <span>{{ prepared ? fromAtomic(BigInt(prepared.amount) + BigInt(prepared.fee)) : "—" }} XNV</span>
        </div>
      </div>
      <TwoFactorField v-model="sendCode" />
      <FormField v-if="!hasTwoFactor" label="Account password" input-id="send-pw">
        <PasswordInput id="send-pw" v-model="sendPass" autocomplete="current-password" />
      </FormField>
      <div class="flex gap-2">
        <Btn variant="ghost" class="flex-1" :disabled="sending" @click="backToReview">Back</Btn>
        <Btn variant="primary" class="flex-1" :disabled="sending" @click="confirmSend">
          {{ sending ? "Sending…" : "Confirm & send" }}
        </Btn>
      </div>
    </BaseModal>

    <BaseModal :open="secretsOpen" title="Wallet secrets" @close="closeSecrets">
      <template v-if="!secrets">
        <p class="text-text-dim text-[0.95rem] m-0 mb-5">
          Enter your account password to reveal your seed and keys. Never share these with anyone.
        </p>
        <Alert v-if="secretErr" class="mb-4">{{ secretErr }}</Alert>
        <form @submit.prevent="reveal">
          <FormField label="Account password" input-id="secp">
            <PasswordInput id="secp" v-model="secretPass" autocomplete="current-password" required />
          </FormField>
          <TwoFactorField v-model="secretCode" />
          <Btn type="submit" variant="primary" block :disabled="secretLoading">
            {{ secretLoading ? "Verifying…" : "Reveal secrets" }}
          </Btn>
        </form>
      </template>

      <div v-else>
        <Alert variant="warning" class="mb-4">
          Keep these private. Anyone with your seed can take your funds.
        </Alert>
        <div v-for="f in secretFields" :key="f.key"
          class="flex flex-col gap-1 py-[0.6rem] border-t border-border-soft first:border-t-0">
          <span class="text-muted text-[0.78rem] uppercase tracking-[0.04em]">{{ f.label }}</span>
          <CopyField :value="secrets[f.key]" wrap />
        </div>
      </div>
    </BaseModal>

    <BaseModal :open="deleteOpen" title="Delete wallet" @close="closeDelete">
      <p class="text-text-dim text-[0.95rem] m-0 mb-5">
        This permanently deletes your wallet data from our servers. If you have funds, make sure you
        have saved your seed first — this cannot be undone.
      </p>
      <Alert v-if="deleteErr" class="mb-4">{{ deleteErr }}</Alert>
      <TwoFactorField v-model="deleteCode" />
      <FormField v-if="!hasTwoFactor" label="Account password" input-id="delete-pw">
        <PasswordInput id="delete-pw" v-model="deletePass" autocomplete="current-password" />
      </FormField>
      <div class="flex flex-col gap-2">
        <Btn variant="danger" block :disabled="deleting" @click="remove">
          {{ deleting ? "Deleting…" : "Yes, delete my wallet" }}
        </Btn>
        <Btn variant="ghost" block :disabled="deleting" @click="closeDelete">Cancel</Btn>
      </div>
    </BaseModal>
  </section>
</template>
