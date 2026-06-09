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

  <main class="main">
    <RouterView v-slot="{ Component }">
      <Transition name="fade" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>
  </main>

  <TheFooter />

  <SupportModal :open="supportOpen" @close="supportOpen = false" />

  <div class="toasts" aria-live="polite">
    <button v-for="t in toasts" :key="t.id" type="button" class="toast" :class="`toast--${t.kind}`"
      :role="t.kind === 'success' ? 'status' : 'alert'" aria-label="Dismiss notification"
      @click="remove(t.id)">
      {{ t.text }}
    </button>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
