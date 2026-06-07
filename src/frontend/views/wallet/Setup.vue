<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"

import { ApiError } from "../../lib/api"
import { useWalletStore } from "../../stores/wallet"

const router = useRouter()
const wallet = useWalletStore()

const mode = ref<"choose" | "restore">("choose")
const seed = ref("")
const agree = ref(false)
const loading = ref(false)
const error = ref("")

onMounted(async () => {
  try {
    const status = await wallet.fetchStatus()
    if (status?.created) router.replace({ name: "wallet-loading" })
  } catch {
    /* ignore */
  }
})

async function create(): Promise<void> {
  error.value = ""
  loading.value = true
  try {
    await wallet.setup("create")
    router.push({ name: "wallet-loading" })
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Could not create wallet."
  } finally {
    loading.value = false
  }
}

async function restore(): Promise<void> {
  error.value = ""
  if (!agree.value) {
    error.value = "Please confirm you understand the risks."
    return
  }
  loading.value = true
  try {
    await wallet.setup("restore", seed.value.trim())
    router.push({ name: "wallet-loading" })
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Could not restore wallet."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page container page--narrow">
    <div class="card">
      <h1 class="card__title">Set up your wallet</h1>

      <div v-if="error" class="alert alert--error" style="margin-bottom: 1rem">{{ error }}</div>

      <template v-if="mode === 'choose'">
        <p class="dim">Create a brand-new Nerva wallet, or restore an existing one from its seed.</p>
        <div class="stack" style="margin-top: 1.25rem">
          <button class="btn btn--primary btn--block" :disabled="loading" @click="create">
            {{ loading ? "Creating…" : "Create a new wallet" }}
          </button>
          <button class="btn btn--ghost btn--block" :disabled="loading" @click="mode = 'restore'">
            Restore from seed
          </button>
        </div>
      </template>

      <template v-else>
        <div class="field">
          <label for="seed">25-word mnemonic seed</label>
          <textarea id="seed" class="textarea" v-model="seed" placeholder="word1 word2 word3 …"
            autocomplete="off" spellcheck="false"></textarea>
        </div>
        <label class="checkbox">
          <input type="checkbox" v-model="agree" />
          <span>I understand this is a custodial wallet and accept the associated risks.</span>
        </label>
        <div class="stack" style="margin-top: 0.5rem">
          <button class="btn btn--primary btn--block" :disabled="loading" @click="restore">
            {{ loading ? "Restoring…" : "Restore wallet" }}
          </button>
          <button class="btn btn--ghost btn--block" :disabled="loading" @click="mode = 'choose'">
            Back
          </button>
        </div>
      </template>
    </div>
  </section>
</template>
