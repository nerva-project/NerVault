<script setup lang="ts">
import { ref } from "vue"
import { RouterView } from "vue-router"

import TheNavbar from "./components/TheNavbar.vue"
import TheFooter from "./components/TheFooter.vue"
import SupportModal from "./components/SupportModal.vue"
import { useToast } from "./composables/useToast"

const supportOpen = ref(false)
const { toasts, remove } = useToast()
</script>

<template>
  <TheNavbar @support="supportOpen = true" />

  <main class="flex-[1_0_auto] flex flex-col">
    <RouterView v-slot="{ Component }">
      <Transition
        enter-active-class="transition-opacity duration-150"
        leave-active-class="transition-opacity duration-150"
        enter-from-class="opacity-0" leave-to-class="opacity-0" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>
  </main>

  <TheFooter />

  <SupportModal :open="supportOpen" @close="supportOpen = false" />

  <div class="fixed bottom-5 right-5 z-[80] flex flex-col gap-2 max-w-[min(360px,calc(100vw_-_2rem))]"
    aria-live="polite">
    <button v-for="t in toasts" :key="t.id" type="button"
      class="w-full text-left px-4 py-3 rounded-field border bg-surface text-text shadow-card text-[0.92rem] cursor-pointer animate-[toast-in_0.18s_ease]"
      :class="{ success: 'border-accent/40', error: 'border-danger/45', warning: 'border-warning/45' }[t.kind] ?? 'border-border'"
      :role="t.kind === 'success' ? 'status' : 'alert'" aria-label="Dismiss notification"
      @click="remove(t.id)">
      {{ t.text }}
    </button>
  </div>
</template>
