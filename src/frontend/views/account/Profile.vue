<script setup lang="ts">
import { reactive, ref } from "vue"

import TwoFactorSettings from "./TwoFactorSettings.vue"
import Alert from "../../components/ui/Alert.vue"
import Btn from "../../components/ui/Btn.vue"
import Card from "../../components/ui/Card.vue"
import BaseModal from "../../components/ui/BaseModal.vue"
import FormField from "../../components/ui/FormField.vue"
import PageHeader from "../../components/ui/PageHeader.vue"
import { api, ApiError } from "../../lib/api"
import { useToast } from "../../composables/useToast"
import { useAuthStore } from "../../stores/auth"

const auth = useAuthStore()
const toast = useToast()

const emailModal = ref(false)
const emailForm = reactive({ password: "", new_email: "" })
const emailError = ref("")
const emailLoading = ref(false)

const pwModal = ref(false)
const pwForm = reactive({ current: "", password: "", confirm: "" })
const pwError = ref("")
const pwLoading = ref(false)

function openEmail(): void {
  emailForm.password = ""
  emailForm.new_email = ""
  emailError.value = ""
  emailModal.value = true
}

function openPassword(): void {
  pwForm.current = ""
  pwForm.password = ""
  pwForm.confirm = ""
  pwError.value = ""
  pwModal.value = true
}

async function submitEmail(): Promise<void> {
  emailError.value = ""
  emailLoading.value = true
  try {
    const res = await api.post("/auth/change-email", {
      password: emailForm.password,
      new_email: emailForm.new_email,
    })
    toast.success(res.message || "Confirmation link sent to your new email.")
    emailModal.value = false
  } catch (e) {
    emailError.value = e instanceof ApiError ? e.message : "Could not change email."
  } finally {
    emailLoading.value = false
  }
}

async function submitPassword(): Promise<void> {
  pwError.value = ""

  if (pwForm.password !== pwForm.confirm) {
    pwError.value = "Passwords do not match."
    return
  }

  pwLoading.value = true
  try {
    await api.post("/auth/change-password", {
      current_password: pwForm.current,
      password: pwForm.password,
      confirm_password: pwForm.confirm,
    })
    toast.success("Your password has been changed.")
    pwModal.value = false
  } catch (e) {
    pwError.value = e instanceof ApiError ? e.message : "Could not change password."
  } finally {
    pwLoading.value = false
  }
}
</script>

<template>
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[640px] mx-auto">
    <PageHeader title="Profile" lead="Manage your account details and security." />

    <div class="flex flex-col gap-6">
      <Card title="Account">
        <div class="flex flex-col gap-5">
          <div>
            <div class="text-[0.85rem] font-semibold text-text-dim mb-1">Username</div>
            <div class="font-mono">{{ auth.user?.username }}</div>
          </div>
          <div class="flex items-end justify-between gap-3">
            <div class="min-w-0">
              <div class="text-[0.85rem] font-semibold text-text-dim mb-1">Email</div>
              <div class="truncate">{{ auth.user?.email }}</div>
            </div>
            <Btn variant="ghost" size="sm" @click="openEmail">Change</Btn>
          </div>
        </div>
      </Card>

      <Card title="Password">
        <div class="flex items-center justify-between gap-3">
          <p class="text-text-dim text-[0.9rem] m-0">
            Use a strong, unique password to protect your account.
          </p>
          <Btn variant="ghost" size="sm" class="shrink-0" @click="openPassword">
            Change
          </Btn>
        </div>
      </Card>

      <TwoFactorSettings />
    </div>

    <!-- Change email -->
    <BaseModal :open="emailModal" title="Change email" @close="emailModal = false">
      <Alert v-if="emailError" class="mb-4">{{ emailError }}</Alert>
      <p class="text-text-dim text-[0.9rem] mb-4">
        We'll send a confirmation link to the new address. Your email only changes
        once you click that link.
      </p>
      <form @submit.prevent="submitEmail">
        <FormField label="New email" input-id="new-email">
          <input id="new-email" class="input" type="email" v-model="emailForm.new_email"
            autocomplete="email" required />
        </FormField>
        <FormField label="Current password" input-id="ce-pw">
          <input id="ce-pw" class="input" type="password" v-model="emailForm.password"
            autocomplete="current-password" required />
        </FormField>
        <Btn type="submit" variant="primary" block :disabled="emailLoading">
          {{ emailLoading ? "Sending…" : "Send confirmation link" }}
        </Btn>
      </form>
    </BaseModal>

    <!-- Change password -->
    <BaseModal :open="pwModal" title="Change password" @close="pwModal = false">
      <Alert v-if="pwError" class="mb-4">{{ pwError }}</Alert>
      <form @submit.prevent="submitPassword">
        <FormField label="Current password" input-id="cp-current">
          <input id="cp-current" class="input" type="password" v-model="pwForm.current"
            autocomplete="current-password" required />
        </FormField>
        <FormField label="New password" input-id="cp-password">
          <input id="cp-password" class="input" type="password" v-model="pwForm.password"
            autocomplete="new-password" required />
        </FormField>
        <FormField label="Confirm new password" input-id="cp-confirm">
          <input id="cp-confirm" class="input" type="password" v-model="pwForm.confirm"
            autocomplete="new-password" required />
        </FormField>
        <Btn type="submit" variant="primary" block :disabled="pwLoading">
          {{ pwLoading ? "Saving…" : "Change password" }}
        </Btn>
      </form>
    </BaseModal>
  </section>
</template>
