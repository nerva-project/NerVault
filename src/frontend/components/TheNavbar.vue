<script setup lang="ts">
import { ref } from "vue"
import { RouterLink, useRouter } from "vue-router"

import IconBtn from "./ui/IconBtn.vue"
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
const loggingOut = ref(false)

const navLink =
  "text-text-dim px-[0.7rem] py-[0.45rem] rounded-field font-medium text-[0.95rem] hover:text-text hover:bg-surface hover:no-underline [&.router-link-active]:text-accent"

function closeMenu(): void {
  menuOpen.value = false
}

async function logout(): Promise<void> {
  if (loggingOut.value) return
  loggingOut.value = true
  try {
    await auth.logout()
    wallet.reset()
    toast.success("You have been logged out.")
    closeMenu()
    router.push({ name: "home" })
  } finally {
    loggingOut.value = false
  }
}
</script>

<template>
  <header class="sticky top-0 z-40 bg-bg/88 backdrop-blur-[10px] border-b border-border-soft">
    <div class="w-full max-w-[1080px] mx-auto px-5 flex items-center gap-4 h-16">
      <RouterLink
        to="/"
        class="flex items-center gap-[0.6rem] font-extrabold text-text tracking-[-0.02em] hover:opacity-85 hover:no-underline"
        @click="closeMenu"
      >
        <img src="/nerva.png" alt="" class="size-[30px]" />
        <span>NerVault</span>
      </RouterLink>

      <button
        class="hidden max-[720px]:inline-flex max-[720px]:ml-auto items-center justify-center size-[38px] rounded-field border border-border bg-surface text-text-dim cursor-pointer hover:text-text hover:border-accent [&_svg]:size-[18px]"
        type="button"
        aria-label="Toggle menu"
        :aria-expanded="menuOpen"
        aria-controls="nav-links"
        @click="menuOpen = !menuOpen"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      <nav
        id="nav-links"
        class="flex items-center gap-[0.35rem] ml-auto max-[720px]:fixed max-[720px]:inset-x-0 max-[720px]:top-16 max-[720px]:bottom-auto max-[720px]:flex-col max-[720px]:items-stretch max-[720px]:bg-bg-soft max-[720px]:border-b max-[720px]:border-border max-[720px]:px-5 max-[720px]:py-3 max-[720px]:gap-1 max-[720px]:transition-transform"
        :class="menuOpen ? 'max-[720px]:translate-y-0' : 'max-[720px]:-translate-y-[120%]'"
      >
        <RouterLink :class="navLink" to="/" @click="closeMenu">Home</RouterLink>
        <RouterLink :class="navLink" to="/faq" @click="closeMenu">FAQ</RouterLink>

        <template v-if="auth.isAuthenticated">
          <RouterLink :class="navLink" to="/wallet/dashboard" @click="closeMenu">Wallet</RouterLink>
          <RouterLink :class="navLink" to="/profile" @click="closeMenu">Profile</RouterLink>
          <button
            :class="[navLink, loggingOut && 'opacity-70 cursor-wait']"
            type="button"
            :disabled="loggingOut"
            @click="logout"
          >
            <span v-if="loggingOut" class="inline-flex items-center gap-2">
              <span class="size-[13px] rounded-full border-2 border-border border-t-accent animate-spin"></span>
              Logging out…
            </span>
            <template v-else>Logout</template>
          </button>
        </template>
        <template v-else>
          <RouterLink :class="navLink" to="/login" @click="closeMenu">Login</RouterLink>
          <RouterLink :class="navLink" to="/register" @click="closeMenu">Register</RouterLink>
        </template>

        <div
          class="contents max-[720px]:flex max-[720px]:gap-2 max-[720px]:mt-2 max-[720px]:pt-3 max-[720px]:border-t max-[720px]:border-border"
        >
          <IconBtn aria-label="Support NerVault" @click="$emit('support'), closeMenu()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 1 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </IconBtn>

          <IconBtn href="https://github.com/nerva-project/NerVault" target="_blank" rel="noopener" aria-label="GitHub repository">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 .5C5.73.5.5 5.73.5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.34-1.3-1.7-1.3-1.7-1.06-.72.08-.71.08-.71 1.17.08 1.78 1.2 1.78 1.2 1.04 1.78 2.74 1.27 3.4.97.11-.75.41-1.27.74-1.56-2.55-.29-5.23-1.28-5.23-5.68 0-1.25.45-2.28 1.19-3.08-.12-.29-.51-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.05 11.05 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.24 2.76.12 3.05.74.8 1.18 1.83 1.18 3.08 0 4.41-2.69 5.39-5.25 5.67.42.36.8 1.08.8 2.18v3.23c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5z" />
            </svg>
          </IconBtn>

          <IconBtn :aria-label="theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'" @click="toggle">
            <svg v-if="theme === 'dark'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5" />
              <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          </IconBtn>
        </div>
      </nav>
    </div>
  </header>
</template>
