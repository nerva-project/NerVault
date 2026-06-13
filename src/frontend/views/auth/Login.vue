<script setup lang="ts">
import { ref } from "vue"
import { RouterLink, useRoute, useRouter } from "vue-router"

import Alert from "../../components/ui/Alert.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import FormField from "../../components/ui/FormField.vue"
import PasswordInput from "../../components/ui/PasswordInput.vue"
import { api, ApiError } from "../../lib/api"
import { safeRedirect } from "../../router"
import { useAuthStore, type User } from "../../stores/auth"

type Challenge = { two_factor: true; method: "email" | "totp"; token: string }
type LoginResult = User | Challenge

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const step = ref<"credentials" | "challenge">("credentials")
const username = ref("")
const password = ref("")
const code = ref("")
const challenge = ref<Challenge | null>(null)
const loading = ref(false)
const resending = ref(false)
const error = ref("")

function proceed(user: User | null): void {
  auth.setUser(user)

  const next = safeRedirect(route.query.next)
  if (next) {
    router.push(next)
  } else if (auth.isConfirmed) {
    router.push({ name: "wallet-dashboard" })
  } else {
    router.push({ name: "unconfirmed" })
  }
}

async function submit(): Promise<void> {
  error.value = ""
  loading.value = true
  try {
    const res = await api.post<LoginResult>("/auth/login", {
      username: username.value,
      password: password.value,
    })

    if (res.result && "token" in res.result) {
      challenge.value = res.result
      code.value = ""
      step.value = "challenge"
    } else {
      proceed(res.result ?? null)
    }
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Login failed."
  } finally {
    loading.value = false
  }
}

async function submitCode(): Promise<void> {
  if (!challenge.value) return
  error.value = ""
  loading.value = true
  try {
    const res = await api.post<User>("/auth/login/2fa", {
      token: challenge.value.token,
      code: code.value,
    })
    proceed(res.result ?? null)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Verification failed."
  } finally {
    loading.value = false
  }
}

async function resend(): Promise<void> {
  if (!challenge.value || resending.value) return
  resending.value = true
  try {
    await api.post("/auth/login/2fa/resend", { token: challenge.value.token })
    error.value = ""
  } catch {
    /* ignore */
  } finally {
    resending.value = false
  }
}

function backToLogin(): void {
  step.value = "credentials"
  challenge.value = null
  code.value = ""
  password.value = ""
  error.value = ""
}
</script>

<template>
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[520px] mx-auto flex flex-col justify-center">
    <Card>
      <template v-if="step === 'credentials'">
        <h1 class="text-[1.1rem] font-bold mb-4">Login</h1>

        <Alert v-if="error" class="mb-4">{{ error }}</Alert>

        <form @submit.prevent="submit">
          <FormField label="Username" input-id="username">
            <input id="username" class="input" v-model="username" autocomplete="username" required />
          </FormField>
          <FormField label="Password" input-id="password">
            <PasswordInput id="password" v-model="password" autocomplete="current-password" required />
          </FormField>
          <Btn type="submit" variant="primary" block :disabled="loading">
            {{ loading ? "Logging in…" : "Login" }}
          </Btn>
        </form>

        <p class="text-text-dim mt-4 text-[0.9rem]">
          <RouterLink to="/reset">Forgot password?</RouterLink>
          &middot; No account? <RouterLink to="/register">Register</RouterLink>
        </p>
      </template>

      <template v-else>
        <h1 class="text-[1.1rem] font-bold mb-4">Two-step verification</h1>

        <Alert v-if="error" class="mb-4">{{ error }}</Alert>

        <p class="text-text-dim text-[0.9rem] mb-4">
          <template v-if="challenge?.method === 'email'">
            We emailed a 6-digit code to your address. Enter it below to finish
            signing in.
          </template>
          <template v-else>
            Enter the 6-digit code from your authenticator app, or one of your
            backup codes.
          </template>
        </p>

        <form @submit.prevent="submitCode">
          <FormField label="Verification code" input-id="code">
            <input id="code" class="input" v-model="code" autocomplete="one-time-code"
              inputmode="numeric" placeholder="123456" required autofocus />
          </FormField>
          <Btn type="submit" variant="primary" block :disabled="loading">
            {{ loading ? "Verifying…" : "Verify" }}
          </Btn>
        </form>

        <p class="text-text-dim mt-4 text-[0.9rem]">
          <template v-if="challenge?.method === 'email'">
            <a href="#" @click.prevent="resend">{{ resending ? "Sending…" : "Resend code" }}</a>
            &middot;
          </template>
          <a href="#" @click.prevent="backToLogin">Back to login</a>
        </p>
      </template>
    </Card>
  </section>
</template>
