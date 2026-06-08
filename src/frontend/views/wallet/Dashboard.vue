<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"

import { api, ApiError, API_BASE } from "../../lib/api"
import { fromAtomic, formatTimestamp, shortenAddress } from "../../lib/format"
import { useToast } from "../../composables/useToast"
import { useWalletStore } from "../../stores/wallet"

const router = useRouter()
const wallet = useWalletStore()
const toast = useToast()

const loading = ref(true)
const error = ref("")
const qrSrc = `${API_BASE}/wallet/qr`

const overview = computed(() => wallet.overview)

const txList = computed(() => {
  const sorted = wallet.overview?.sorted_transactions ?? {}
  return Object.entries(sorted)
    .map(([txid, t]) => ({ txid, ...t }))
    .sort((a, b) => b.timestamp - a.timestamp)
})

function preloadImage(src: string): Promise<void> {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve()
    img.onerror = () => resolve()
    img.src = src
  })
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    await wallet.fetchOverview()
    await preloadImage(qrSrc)
  } catch (e) {
    if (e instanceof ApiError) {
      if (e.code === "not_created") {
        router.replace({ name: "wallet-setup" })
        return
      }
      if (e.code === "not_connected" || e.code === "not_ready") {
        router.replace({ name: "wallet-loading" })
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

onMounted(load)

async function copyAddress(): Promise<void> {
  if (!overview.value) return
  try {
    await navigator.clipboard.writeText(overview.value.address)
    toast.success("Address copied.")
  } catch {
    /* ignore */
  }
}

/* ---- Send ---- */
const sendOpen = ref(false)
const sendAddr = ref("")
const sendAmount = ref("")
const sendPid = ref("")
const sending = ref(false)
const sendErr = ref("")

function openSend(): void {
  sendErr.value = ""
  sendOpen.value = true
}

async function send(): Promise<void> {
  sendErr.value = ""
  sending.value = true
  try {
    const res = await api.post("/wallet/transfer", {
      address: sendAddr.value.trim(),
      amount: sendAmount.value.trim(),
      payment_id: sendPid.value.trim() || undefined,
    })
    toast.success(res.message || "Transaction sent.")
    sendOpen.value = false
    sendAddr.value = ""
    sendAmount.value = ""
    sendPid.value = ""
    await load()
  } catch (e) {
    sendErr.value = e instanceof ApiError ? e.message : "Transaction failed."
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
  secretErr.value = ""
}

async function reveal(): Promise<void> {
  secretErr.value = ""
  secretLoading.value = true
  try {
    const res = await api.post<Record<string, string>>("/wallet/secrets", {
      password: secretPass.value,
    })
    secrets.value = res.result ?? null
  } catch (e) {
    secretErr.value = e instanceof ApiError ? e.message : "Could not reveal secrets."
  } finally {
    secretLoading.value = false
  }
}

/* ---- Delete ---- */
const deleteOpen = ref(false)
const deleting = ref(false)

async function remove(): Promise<void> {
  deleting.value = true
  try {
    await api.post("/wallet/delete", { confirm: true })
    toast.success("Wallet data deleted.")
    wallet.reset()
    router.push({ name: "wallet-setup" })
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : "Could not delete wallet.")
  } finally {
    deleting.value = false
    deleteOpen.value = false
  }
}
</script>

<template>
  <section class="page container">
    <div v-if="loading" class="center">
      <div class="spinner"></div>
      <p class="dim">Loading your wallet…</p>
    </div>

    <div v-else-if="error" class="alert alert--error">{{ error }}</div>

    <div v-else-if="overview" class="dash">
      <div class="dash__top">
        <div class="card dash__balance">
          <div>
            <div class="stat__label">Balance</div>
            <div class="balance__value">
              {{ fromAtomic(overview.balance) }} <span class="balance__unit">XNV</span>
            </div>
            <p class="muted" style="font-size: 0.85rem; margin: 0.25rem 0 0">
              {{ fromAtomic(overview.unlocked_balance) }} XNV unlocked
            </p>
          </div>
          <div class="stack" style="gap: 0.5rem">
            <button class="btn btn--primary btn--block" @click="openSend">Send XNV</button>
            <button class="btn btn--ghost btn--block" @click="load">Refresh</button>
          </div>
        </div>

        <div class="card center">
          <img class="qr" :src="qrSrc" alt="Wallet address QR code" />
          <div class="address-box" style="margin-top: 0.75rem">
            <span>{{ shortenAddress(overview.address, 12, 12) }}</span>
          </div>
          <button class="btn btn--ghost btn--block" style="margin-top: 0.6rem" @click="copyAddress">
            Copy address
          </button>
        </div>
      </div>

      <div class="card">
        <div class="card__title">Transactions</div>
        <p v-if="!txList.length" class="muted">No transactions yet.</p>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Date</th>
                <th class="num">Amount</th>
                <th class="num">Balance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tx in txList" :key="tx.txid">
                <td>
                  <span class="badge" :class="tx.type === 'in' ? 'badge--in' : 'badge--out'">
                    {{ tx.type }}
                  </span>
                </td>
                <td class="dim">{{ formatTimestamp(tx.timestamp) }}</td>
                <td class="num">{{ fromAtomic(tx.amount) }}</td>
                <td class="num">{{ fromAtomic(tx.total) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card__title">Wallet tools</div>
        <div class="dash__tools">
          <button class="btn btn--ghost" @click="secretsOpen = true">View secrets</button>
          <button class="btn btn--danger" @click="deleteOpen = true">Delete wallet</button>
        </div>
      </div>
    </div>

    <!-- Send modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="sendOpen" class="modal" role="dialog" aria-modal="true" @click.self="sendOpen = false">
          <div class="modal__panel">
            <button class="modal__close" type="button" aria-label="Close" @click="sendOpen = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
            <h2 class="modal__title">Send XNV</h2>
            <div v-if="sendErr" class="alert alert--error" style="margin-bottom: 1rem">{{ sendErr }}</div>
            <form @submit.prevent="send">
              <div class="field">
                <label for="sa">Destination address</label>
                <input id="sa" class="input" v-model="sendAddr" autocomplete="off" required />
              </div>
              <div class="field">
                <label for="sm">Amount (or "all")</label>
                <input id="sm" class="input" v-model="sendAmount" placeholder='e.g. 12.5 or "all"' required />
              </div>
              <div class="field">
                <label for="sp">Payment ID (optional)</label>
                <input id="sp" class="input" v-model="sendPid" autocomplete="off" />
              </div>
              <button class="btn btn--primary btn--block" :disabled="sending">
                {{ sending ? "Sending…" : "Send transaction" }}
              </button>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Secrets modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="secretsOpen" class="modal" role="dialog" aria-modal="true" @click.self="closeSecrets">
          <div class="modal__panel">
            <button class="modal__close" type="button" aria-label="Close" @click="closeSecrets">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
            <h2 class="modal__title">Wallet secrets</h2>

            <template v-if="!secrets">
              <p class="modal__lead">
                Enter your account password to reveal your seed and keys. Never share these with
                anyone.
              </p>
              <div v-if="secretErr" class="alert alert--error" style="margin-bottom: 1rem">{{ secretErr }}</div>
              <form @submit.prevent="reveal">
                <div class="field">
                  <label for="secp">Account password</label>
                  <input id="secp" class="input" type="password" v-model="secretPass"
                    autocomplete="current-password" required />
                </div>
                <button class="btn btn--primary btn--block" :disabled="secretLoading">
                  {{ secretLoading ? "Verifying…" : "Reveal secrets" }}
                </button>
              </form>
            </template>

            <div v-else>
              <div class="alert alert--warning" style="margin-bottom: 1rem">
                Keep these private. Anyone with your seed can take your funds.
              </div>
              <div v-for="f in secretFields" :key="f.key" class="secret-row">
                <span class="label">{{ f.label }}</span>
                <span class="value">{{ secrets[f.key] }}</span>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Delete modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="deleteOpen" class="modal" role="dialog" aria-modal="true" @click.self="deleteOpen = false">
          <div class="modal__panel">
            <button class="modal__close" type="button" aria-label="Close" @click="deleteOpen = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
            <h2 class="modal__title">Delete wallet</h2>
            <p class="modal__lead">
              This permanently deletes your wallet data from our servers. If you have funds, make
              sure you have saved your seed first — this cannot be undone.
            </p>
            <div class="stack" style="gap: 0.5rem">
              <button class="btn btn--danger btn--block" :disabled="deleting" @click="remove">
                {{ deleting ? "Deleting…" : "Yes, delete my wallet" }}
              </button>
              <button class="btn btn--ghost btn--block" @click="deleteOpen = false">Cancel</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </section>
</template>
