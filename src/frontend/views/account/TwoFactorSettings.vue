<script setup lang="ts">
import { computed, reactive, ref } from "vue"

import Alert from "../../components/ui/Alert.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import BaseModal from "../../components/ui/BaseModal.vue"
import CopyField from "../../components/ui/CopyField.vue"
import FormField from "../../components/ui/FormField.vue"
import PasswordInput from "../../components/ui/PasswordInput.vue"
import { api, ApiError } from "../../lib/api"
import { useToast } from "../../composables/useToast"
import { useAuthStore, type User } from "../../stores/auth"

type Modal =
  | ""
  | "emailEnable"
  | "emailDisable"
  | "totpSetup"
  | "totpDisable"
  | "backup"

const auth = useAuthStore()
const toast = useToast()

const tf = computed(
  () => auth.user?.two_factor ?? { email: false, totp: false, method: null },
)

const modal = ref<Modal>("")
const loading = ref(false)
const error = ref("")
const form = reactive({ password: "", code: "" })

const setup = reactive({
  step: "password" as "password" | "verify" | "codes",
  secret: "",
  qr: "",
})
const backupStep = ref<"form" | "codes">("form")
const codes = ref<string[]>([])

function resetState(): void {
  form.password = ""
  form.code = ""
  error.value = ""
  loading.value = false
  setup.step = "password"
  setup.secret = ""
  setup.qr = ""
  backupStep.value = "form"
  codes.value = []
}

function open(m: Modal): void {
  resetState()
  modal.value = m
}

function close(): void {
  modal.value = ""
  resetState()
}

function fail(e: unknown, fallback: string): void {
  error.value = e instanceof ApiError ? e.message : fallback
}

async function copyCodes(): Promise<void> {
  try {
    await navigator.clipboard.writeText(codes.value.join("\n"))
    toast.success("Backup codes copied.")
  } catch {
    /* ignore */
  }
}

async function emailEnable(): Promise<void> {
  error.value = ""
  loading.value = true
  try {
    const res = await api.post<User>("/auth/2fa/email/enable", {
      password: form.password,
    })
    auth.setUser(res.result ?? null)
    toast.success("Email two-factor authentication enabled.")
    close()
  } catch (e) {
    fail(e, "Could not enable email codes.")
  } finally {
    loading.value = false
  }
}

async function emailDisable(): Promise<void> {
  error.value = ""
  loading.value = true
  try {
    const res = await api.post<User>("/auth/2fa/email/disable", {
      password: form.password,
    })
    auth.setUser(res.result ?? null)
    toast.success("Email two-factor authentication disabled.")
    close()
  } catch (e) {
    fail(e, "Could not disable email codes.")
  } finally {
    loading.value = false
  }
}

async function totpStart(): Promise<void> {
  error.value = ""
  loading.value = true
  try {
    const res = await api.post<{ secret: string; otpauth_uri: string; qr: string }>(
      "/auth/2fa/totp/setup",
      { password: form.password },
    )
    setup.secret = res.result?.secret ?? ""
    setup.qr = res.result?.qr ?? ""
    setup.step = "verify"
  } catch (e) {
    fail(e, "Could not start authenticator setup.")
  } finally {
    loading.value = false
  }
}

async function totpVerify(): Promise<void> {
  error.value = ""
  loading.value = true
  try {
    const res = await api.post<{ backup_codes: string[]; user: User }>(
      "/auth/2fa/totp/verify",
      { code: form.code },
    )
    auth.setUser(res.result?.user ?? null)
    codes.value = res.result?.backup_codes ?? []
    setup.step = "codes"
  } catch (e) {
    fail(e, "Could not verify that code.")
  } finally {
    loading.value = false
  }
}

async function totpDisable(): Promise<void> {
  error.value = ""
  loading.value = true
  try {
    const res = await api.post<User>("/auth/2fa/totp/disable", {
      password: form.password,
      code: form.code,
    })
    auth.setUser(res.result ?? null)
    toast.success("Authenticator app disabled.")
    close()
  } catch (e) {
    fail(e, "Could not disable the authenticator app.")
  } finally {
    loading.value = false
  }
}

async function backupRegenerate(): Promise<void> {
  error.value = ""
  loading.value = true
  try {
    const res = await api.post<{ backup_codes: string[] }>(
      "/auth/2fa/backup/regenerate",
      { password: form.password, code: form.code },
    )
    codes.value = res.result?.backup_codes ?? []
    backupStep.value = "codes"
  } catch (e) {
    fail(e, "Could not regenerate backup codes.")
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <Card title="Two-factor authentication">
    <div class="mb-3">
      <span
        class="inline-flex items-center gap-2 px-[0.55rem] py-[0.2rem] rounded-full text-[0.78rem] font-semibold"
        :class="tf.method ? 'text-accent bg-accent/[0.14]' : 'text-muted bg-surface border border-border'"
      >
        <span class="size-[7px] rounded-full" :class="tf.method ? 'bg-accent' : 'bg-muted'"></span>
        {{ tf.method === "totp" ? "Authenticator app" : tf.method === "email" ? "Email codes" : "Off" }}
      </span>
    </div>

    <p class="text-text-dim text-[0.9rem] mb-4">
      <template v-if="tf.method === 'totp'">
        You'll enter a code from your authenticator app each time you log in.
      </template>
      <template v-else-if="tf.method === 'email'">
        We'll email you a one-time code each time you log in.
      </template>
      <template v-else>
        Add a second step at login to keep your account secure even if your
        password is compromised.
      </template>
    </p>

    <div class="flex flex-wrap gap-2">
      <template v-if="tf.method === null">
        <Btn variant="primary" size="sm" @click="open('totpSetup')">
          Set up authenticator app
        </Btn>
        <Btn variant="ghost" size="sm" @click="open('emailEnable')">
          Use email codes
        </Btn>
      </template>
      <template v-else-if="tf.method === 'email'">
        <Btn variant="primary" size="sm" @click="open('totpSetup')">
          Switch to authenticator app
        </Btn>
        <Btn variant="danger" size="sm" @click="open('emailDisable')">Turn off</Btn>
      </template>
      <template v-else>
        <Btn variant="ghost" size="sm" @click="open('backup')">
          Regenerate backup codes
        </Btn>
        <Btn variant="danger" size="sm" @click="open('totpDisable')">
          Turn off
        </Btn>
      </template>
    </div>

    <!-- Enable email codes -->
    <BaseModal :open="modal === 'emailEnable'" title="Enable email codes" @close="close">
      <Alert v-if="error" class="mb-4">{{ error }}</Alert>
      <p class="text-text-dim text-[0.9rem] mb-4">
        We'll email a one-time code to <strong>{{ auth.user?.email }}</strong> each
        time you log in. Confirm your password to continue.
      </p>
      <form @submit.prevent="emailEnable">
        <FormField label="Current password" input-id="ee-pw">
          <PasswordInput id="ee-pw" v-model="form.password" autocomplete="current-password" required />
        </FormField>
        <Btn type="submit" variant="primary" block :disabled="loading">
          {{ loading ? "Enabling…" : "Enable email codes" }}
        </Btn>
      </form>
    </BaseModal>

    <!-- Disable email codes -->
    <BaseModal :open="modal === 'emailDisable'" title="Turn off email codes" @close="close">
      <Alert v-if="error" class="mb-4">{{ error }}</Alert>
      <p class="text-text-dim text-[0.9rem] mb-4">
        Confirm your password to stop requiring an email code at login.
      </p>
      <form @submit.prevent="emailDisable">
        <FormField label="Current password" input-id="ed-pw">
          <PasswordInput id="ed-pw" v-model="form.password" autocomplete="current-password" required />
        </FormField>
        <Btn type="submit" variant="danger" block :disabled="loading">
          {{ loading ? "Turning off…" : "Turn off email codes" }}
        </Btn>
      </form>
    </BaseModal>

    <!-- Authenticator app setup -->
    <BaseModal :open="modal === 'totpSetup'" title="Set up authenticator app" @close="close">
      <Alert v-if="error" class="mb-4">{{ error }}</Alert>

      <form v-if="setup.step === 'password'" @submit.prevent="totpStart">
        <p class="text-text-dim text-[0.9rem] mb-4">
          Confirm your password to generate a new secret key.
        </p>
        <FormField label="Current password" input-id="ts-pw">
          <PasswordInput id="ts-pw" v-model="form.password" autocomplete="current-password" required />
        </FormField>
        <Btn type="submit" variant="primary" block :disabled="loading">
          {{ loading ? "Loading…" : "Continue" }}
        </Btn>
      </form>

      <form v-else-if="setup.step === 'verify'" @submit.prevent="totpVerify">
        <p class="text-text-dim text-[0.9rem] mb-4">
          Scan this QR code with your authenticator app, or enter the key
          manually, then type the 6-digit code it shows.
        </p>
        <div class="flex justify-center mb-4">
          <img :src="setup.qr" alt="Authenticator QR code"
            class="size-[200px] rounded-card border border-border bg-white p-2" />
        </div>
        <FormField label="Manual key">
          <CopyField :value="setup.secret" wrap />
        </FormField>
        <FormField label="6-digit code" input-id="ts-code">
          <input id="ts-code" class="input" v-model="form.code" inputmode="numeric"
            autocomplete="one-time-code" placeholder="123456" required />
        </FormField>
        <Btn type="submit" variant="primary" block :disabled="loading">
          {{ loading ? "Verifying…" : "Verify & enable" }}
        </Btn>
      </form>

      <div v-else>
        <Alert variant="success" class="mb-4">Authenticator app enabled.</Alert>
        <p class="text-text-dim text-[0.9rem] mb-3">
          Save these backup codes somewhere safe. Each one works once if you lose
          access to your authenticator. They won't be shown again.
        </p>
        <ul class="grid grid-cols-2 gap-2 font-mono text-[0.9rem] mb-4">
          <li v-for="c in codes" :key="c"
            class="bg-bg-soft border border-border rounded-field px-3 py-2 text-center">
            {{ c }}
          </li>
        </ul>
        <div class="flex gap-2">
          <Btn variant="ghost" size="sm" class="shrink-0" @click="copyCodes">Copy codes</Btn>
          <Btn variant="primary" size="sm" class="flex-1" @click="close">I've saved my codes</Btn>
        </div>
      </div>
    </BaseModal>

    <!-- Disable authenticator app -->
    <BaseModal :open="modal === 'totpDisable'" title="Turn off authenticator app" @close="close">
      <Alert v-if="error" class="mb-4">{{ error }}</Alert>
      <p class="text-text-dim text-[0.9rem] mb-4">
        Confirm your password and a current code (or a backup code) to turn off
        the authenticator app.
      </p>
      <form @submit.prevent="totpDisable">
        <FormField label="Current password" input-id="td-pw">
          <PasswordInput id="td-pw" v-model="form.password" autocomplete="current-password" required />
        </FormField>
        <FormField label="Authenticator or backup code" input-id="td-code">
          <input id="td-code" class="input" v-model="form.code"
            autocomplete="one-time-code" required />
        </FormField>
        <Btn type="submit" variant="danger" block :disabled="loading">
          {{ loading ? "Turning off…" : "Turn off" }}
        </Btn>
      </form>
    </BaseModal>

    <!-- Regenerate backup codes -->
    <BaseModal :open="modal === 'backup'" title="Regenerate backup codes" @close="close">
      <Alert v-if="error" class="mb-4">{{ error }}</Alert>

      <form v-if="backupStep === 'form'" @submit.prevent="backupRegenerate">
        <p class="text-text-dim text-[0.9rem] mb-4">
          This invalidates your old backup codes. Confirm your password and a
          current authenticator code to generate a new set.
        </p>
        <FormField label="Current password" input-id="bk-pw">
          <PasswordInput id="bk-pw" v-model="form.password" autocomplete="current-password" required />
        </FormField>
        <FormField label="6-digit code" input-id="bk-code">
          <input id="bk-code" class="input" v-model="form.code" inputmode="numeric"
            autocomplete="one-time-code" placeholder="123456" required />
        </FormField>
        <Btn type="submit" variant="primary" block :disabled="loading">
          {{ loading ? "Generating…" : "Generate new codes" }}
        </Btn>
      </form>

      <div v-else>
        <p class="text-text-dim text-[0.9rem] mb-3">
          Save these backup codes somewhere safe. They won't be shown again.
        </p>
        <ul class="grid grid-cols-2 gap-2 font-mono text-[0.9rem] mb-4">
          <li v-for="c in codes" :key="c"
            class="bg-bg-soft border border-border rounded-field px-3 py-2 text-center">
            {{ c }}
          </li>
        </ul>
        <div class="flex gap-2">
          <Btn variant="ghost" size="sm" class="shrink-0" @click="copyCodes">Copy codes</Btn>
          <Btn variant="primary" size="sm" class="flex-1" @click="close">I've saved my codes</Btn>
        </div>
      </div>
    </BaseModal>
  </Card>
</template>
