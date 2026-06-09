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
        :aria-expanded="menuOpen" aria-controls="nav-links" @click="menuOpen = !menuOpen">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      <nav id="nav-links" class="nav__links" :class="{ open: menuOpen }">
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

        <a class="icon-btn" href="https://github.com/nerva-project/NerVault" target="_blank" rel="noopener"
          aria-label="GitHub repository">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 .5C5.73.5.5 5.73.5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.34-1.3-1.7-1.3-1.7-1.06-.72.08-.71.08-.71 1.17.08 1.78 1.2 1.78 1.2 1.04 1.78 2.74 1.27 3.4.97.11-.75.41-1.27.74-1.56-2.55-.29-5.23-1.28-5.23-5.68 0-1.25.45-2.28 1.19-3.08-.12-.29-.51-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.05 11.05 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.24 2.76.12 3.05.74.8 1.18 1.83 1.18 3.08 0 4.41-2.69 5.39-5.25 5.67.42.36.8 1.08.8 2.18v3.23c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5z" />
          </svg>
        </a>

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
