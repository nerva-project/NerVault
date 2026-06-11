<script setup lang="ts">
import { ref } from "vue"

defineProps<{
  value: string
  display?: string
  wrap?: boolean
  loading?: boolean
}>()

const copied = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined

async function copy(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => (copied.value = false), 1500)
  } catch {
    /* ignore */
  }
}
</script>

<template>
  <div class="copyfield" :class="{ 'copyfield--loading': loading }">
    <span v-if="loading" class="copyfield__skel" aria-hidden="true"></span>
    <span v-else class="copyfield__text" :class="{ 'copyfield__text--wrap': wrap }">{{ display ?? value }}</span>
    <button
      class="copyfield__btn"
      :class="{ 'copyfield__btn--ok': copied }"
      type="button"
      :disabled="loading"
      :aria-label="copied ? 'Copied' : 'Copy'"
      @click="copy(value)"
    >
      <svg v-if="copied" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
      </svg>
    </button>
  </div>
</template>
