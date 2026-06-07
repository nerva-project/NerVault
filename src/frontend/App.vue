<script setup lang="ts">
import { onMounted, ref } from "vue"
import { RouterView, useRouter } from "vue-router"

import TheNavbar from "./components/TheNavbar.vue"
import TheFooter from "./components/TheFooter.vue"
import SupportModal from "./components/SupportModal.vue"
import { useToast } from "./composables/useToast"
import { api } from "./lib/api"

const supportOpen = ref(false)
const { toasts, remove } = useToast()
const router = useRouter()

onMounted(async () => {
  try {
    const res = await api.get<{ maintenance: boolean }>("/meta/maintenance")
    if (res.result?.maintenance) {
      router.replace({ name: "maintenance" })
    }
  } catch {
    /* ignore */
  }
})
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
    <div v-for="t in toasts" :key="t.id" class="toast" :class="`toast--${t.kind}`" role="status"
      @click="remove(t.id)">
      {{ t.text }}
    </div>
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
