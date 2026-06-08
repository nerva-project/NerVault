<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue"
import { useRouter } from "vue-router"

import { api, ApiError, API_BASE } from "../../lib/api"
import { fromAtomic, formatTimestamp, shortenAddress } from "../../lib/format"
import Alert from "../../components/ui/Alert.vue"
import Badge from "../../components/ui/Badge.vue"
import BaseModal from "../../components/ui/BaseModal.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import CopyField from "../../components/ui/CopyField.vue"
import Spinner from "../../components/ui/Spinner.vue"
import { useToast } from "../../composables/useToast"
import { useWalletStore } from "../../stores/wallet"

const router = useRouter()
const wallet = useWalletStore()
const toast = useToast()

const loading = ref(true)
const error = ref("")
const qrSrc = `${API_BASE}/wallet/qr`

const overview = computed(() => wallet.overview)

const now = ref(Date.now())

const fiat = computed(() => {
  const o = overview.value
  if (!o || !o.price) return null
  const usd = Number(fromAtomic(o.balance)) * o.price
  return usd.toLocaleString(undefined, { style: "currency", currency: "USD" })
})

const synced = computed(() => {
  const o = overview.value
  if (!o || !o.network_height) return true
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

async function keepAlive(): Promise<void> {
  try {
    await wallet.keepAlive()
    toast.success("Session extended.")
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : "Could not extend session.")
  }
}

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

let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  void load()
  timer = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})

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
    <Spinner v-if="loading" label="Loading your wallet…" />

    <Alert v-else-if="error">{{ error }}</Alert>

    <div v-else-if="overview" class="dash">
      <Card class="dash__balance">
        <div class="dash__stats">
          <div>
            <div class="stat__label">Balance</div>
            <div class="balance__value">
              {{ fromAtomic(overview.balance) }} <span class="balance__unit">XNV</span>
            </div>
            <p class="muted" style="font-size: 0.85rem; margin: 0.3rem 0 0">
              <template v-if="fiat">≈ {{ fiat }} · </template>{{ fromAtomic(overview.unlocked_balance) }} unlocked
            </p>
          </div>
          <div>
            <div class="stat__label">Network</div>
            <div style="margin-top: 0.5rem">
              <Badge :variant="synced ? 'in' : 'out'">
                {{ synced ? "Synced" : `Syncing · ${blocksBehind.toLocaleString()} behind` }}
              </Badge>
            </div>
            <p class="muted" style="font-size: 0.85rem; margin: 0.5rem 0 0">
              Block {{ overview.network_height.toLocaleString() }}
            </p>
          </div>
          <div>
            <div class="stat__label">Session</div>
            <div class="dash__session-val">{{ sessionLeft ?? "—" }}</div>
            <Btn variant="ghost" size="sm" style="margin-top: 0.5rem" @click="keepAlive">
              Keep alive
            </Btn>
          </div>
          <div class="dash__actions">
            <Btn variant="primary" @click="openSend">Send XNV</Btn>
            <Btn variant="ghost" @click="load">Refresh</Btn>
          </div>
        </div>
      </Card>

      <div class="dash__mid">
        <Card class="center">
          <img class="qr" :src="qrSrc" alt="Wallet address QR code" />
          <CopyField
            style="margin-top: 0.75rem"
            :value="overview.address"
            :display="shortenAddress(overview.address, 10, 8)"
          />
        </Card>

        <Card class="dash__tx" title="Transactions">
          <p v-if="!txList.length" class="muted">No transactions yet.</p>
          <div v-else class="table-wrap">
            <table>
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
                <tr v-for="tx in txList" :key="tx.txid">
                  <td>
                    <Badge :variant="tx.type === 'in' ? 'in' : 'out'">{{ tx.type }}</Badge>
                  </td>
                  <td class="dim">{{ formatTimestamp(tx.timestamp) }}</td>
                  <td>
                    <a class="tx-link" :href="`https://explorer.nerva.one/detail/${tx.txid}`"
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
        <div class="dash__tools">
          <Btn variant="ghost" @click="secretsOpen = true">View secrets</Btn>
          <Btn variant="danger" @click="deleteOpen = true">Delete wallet</Btn>
        </div>
      </Card>
    </div>

    <BaseModal :open="sendOpen" title="Send XNV" @close="sendOpen = false">
      <Alert v-if="sendErr" style="margin-bottom: 1rem">{{ sendErr }}</Alert>
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
        <Btn type="submit" variant="primary" block :disabled="sending">
          {{ sending ? "Sending…" : "Send transaction" }}
        </Btn>
      </form>
    </BaseModal>

    <BaseModal :open="secretsOpen" title="Wallet secrets" @close="closeSecrets">
      <template v-if="!secrets">
        <p class="modal__lead">
          Enter your account password to reveal your seed and keys. Never share these with anyone.
        </p>
        <Alert v-if="secretErr" style="margin-bottom: 1rem">{{ secretErr }}</Alert>
        <form @submit.prevent="reveal">
          <div class="field">
            <label for="secp">Account password</label>
            <input id="secp" class="input" type="password" v-model="secretPass"
              autocomplete="current-password" required />
          </div>
          <Btn type="submit" variant="primary" block :disabled="secretLoading">
            {{ secretLoading ? "Verifying…" : "Reveal secrets" }}
          </Btn>
        </form>
      </template>

      <div v-else>
        <Alert variant="warning" style="margin-bottom: 1rem">
          Keep these private. Anyone with your seed can take your funds.
        </Alert>
        <div v-for="f in secretFields" :key="f.key" class="secret-row">
          <span class="label">{{ f.label }}</span>
          <CopyField :value="secrets[f.key]" wrap />
        </div>
      </div>
    </BaseModal>

    <BaseModal :open="deleteOpen" title="Delete wallet" @close="deleteOpen = false">
      <p class="modal__lead">
        This permanently deletes your wallet data from our servers. If you have funds, make sure you
        have saved your seed first — this cannot be undone.
      </p>
      <div class="stack" style="gap: 0.5rem">
        <Btn variant="danger" block :disabled="deleting" @click="remove">
          {{ deleting ? "Deleting…" : "Yes, delete my wallet" }}
        </Btn>
        <Btn variant="ghost" block @click="deleteOpen = false">Cancel</Btn>
      </div>
    </BaseModal>
  </section>
</template>
