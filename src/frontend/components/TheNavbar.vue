<script setup lang="ts">
import { ref } from "vue"
import { RouterLink, useRouter } from "vue-router"

import { useTheme } from "../composables/useTheme"
import { useToast } from "../composables/useToast"
import { useAuthStore } from "../stores/auth"
import { useWalletStore } from "../stores/wallet"

defineEmits<{ (e: "support"): void }>()

const { theme, toggle } = useTheme()
const auth = useAuthStore()
const wallet = useWalletStore()
const toast = useToast()
const router = useRouter()

const menuOpen = ref(false)

function closeMenu(): void {
  menuOpen.value = false
}

async function logout(): Promise<void> {
  closeMenu()
  await auth.logout()
  wallet.reset()
  toast.success("You have been logged out.")
  router.push({ name: "home" })
}
</script>

<template>
  <header class="nav">
    <div class="container nav__inner">
      <RouterLink to="/" class="nav__brand" @click="closeMenu">
        <img src="/nerva.png" alt="" />
        <span>NerVault</span>
      </RouterLink>

      <button class="icon-btn nav__toggle" type="button" aria-label="Toggle menu"
        @click="menuOpen = !menuOpen">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      <nav class="nav__links" :class="{ open: menuOpen }">
        <RouterLink class="nav__link" to="/" @click="closeMenu">Home</RouterLink>
        <RouterLink class="nav__link" to="/faq" @click="closeMenu">FAQ</RouterLink>

        <template v-if="auth.isAuthenticated">
          <RouterLink class="nav__link" to="/wallet/dashboard" @click="closeMenu">Wallet</RouterLink>
          <button class="nav__link" type="button" @click="logout">Logout</button>
        </template>
        <template v-else>
          <RouterLink class="nav__link" to="/login" @click="closeMenu">Login</RouterLink>
          <RouterLink class="nav__link" to="/register" @click="closeMenu">Register</RouterLink>
        </template>

        <button class="icon-btn" type="button" aria-label="Support NerVault" @click="$emit('support'); closeMenu()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
            stroke-linejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 1 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
        </button>

        <button class="icon-btn" type="button" :aria-label="theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'"
          @click="toggle">
          <svg v-if="theme === 'dark'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5" />
            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
            stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        </button>
      </nav>
    </div>
  </header>
</template>
