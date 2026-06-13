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
  <div
    class="flex items-center gap-2 bg-bg-soft border border-border rounded-field py-[0.35rem] pr-[0.35rem] pl-[0.7rem] font-mono text-[0.82rem]"
  >
    <span v-if="loading" aria-hidden="true" class="flex-1 h-[0.95rem] rounded-[4px] skel"></span>
    <span
      v-else
      class="flex-1 min-w-0 text-left"
      :class="wrap ? 'whitespace-normal break-all' : 'whitespace-nowrap overflow-hidden text-ellipsis'"
      >{{ display ?? value }}</span
    >
    <button
      type="button"
      :disabled="loading"
      :aria-label="copied ? 'Copied' : 'Copy'"
      class="shrink-0 inline-flex items-center justify-center size-[30px] rounded-field bg-transparent cursor-pointer enabled:hover:text-text enabled:hover:bg-surface disabled:opacity-40 disabled:cursor-default"
      :class="copied ? 'text-accent' : 'text-text-dim'"
      @click="copy(value)"
    >
      <svg v-if="copied" class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
      <svg v-else class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
      </svg>
    </button>
  </div>
</template>
