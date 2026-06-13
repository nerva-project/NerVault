<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"

import Alert from "../../components/ui/Alert.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import FormField from "../../components/ui/FormField.vue"
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
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[520px] mx-auto flex flex-col justify-center">
    <Card>
      <h1 class="text-[1.1rem] font-bold mb-4">Set up your wallet</h1>

      <Alert v-if="error" class="mb-4">{{ error }}</Alert>

      <template v-if="mode === 'choose'">
        <p class="text-text-dim">Create a brand-new Nerva wallet, or restore an existing one from its seed.</p>
        <div class="flex flex-col gap-4 mt-5">
          <Btn variant="primary" block :disabled="loading" @click="create">
            {{ loading ? "Creating…" : "Create a new wallet" }}
          </Btn>
          <Btn variant="ghost" block :disabled="loading" @click="mode = 'restore'">
            Restore from seed
          </Btn>
        </div>
      </template>

      <template v-else>
        <FormField label="25-word mnemonic seed" input-id="seed">
          <textarea id="seed"
            class="w-full px-[0.85rem] py-[0.7rem] bg-bg-soft border border-border rounded-field text-text resize-y min-h-[90px] font-mono text-[0.9rem] focus:border-accent focus:outline-none"
            v-model="seed" placeholder="word1 word2 word3 …"
            autocomplete="off" spellcheck="false"></textarea>
        </FormField>
        <label class="flex items-start gap-[0.55rem] text-[0.9rem] text-text-dim mb-3">
          <input type="checkbox" v-model="agree" class="mt-[0.2rem] accent-accent" />
          <span>I understand this is a custodial wallet and accept the associated risks.</span>
        </label>
        <div class="flex flex-col gap-4 mt-2">
          <Btn variant="primary" block :disabled="loading" @click="restore">
            {{ loading ? "Restoring…" : "Restore wallet" }}
          </Btn>
          <Btn variant="ghost" block :disabled="loading" @click="mode = 'choose'">
            Back
          </Btn>
        </div>
      </template>
    </Card>
  </section>
</template>
