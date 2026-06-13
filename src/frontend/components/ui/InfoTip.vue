<script setup lang="ts">
defineProps<{ text: string; centered?: boolean }>()
</script>

<template>
  <span
    class="group relative inline-flex align-middle text-muted cursor-help outline-none hover:text-accent focus-visible:text-accent"
    tabindex="0" role="note" :aria-label="text">
    <svg class="size-[15px]" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4" />
      <path d="M12 8h.01" />
    </svg>
    <span
      class="absolute bottom-[calc(100%_+_8px)] w-max px-[0.7rem] py-[0.55rem] bg-bg-soft border border-border rounded-field shadow-card text-text-dim text-[0.8rem] font-normal leading-[1.4] whitespace-normal opacity-0 invisible transition-opacity duration-[120ms] z-20 pointer-events-none group-hover:opacity-100 group-hover:visible group-focus-within:opacity-100 group-focus-within:visible"
      :class="centered ? 'left-1/2 -translate-x-1/2 max-w-[210px]' : 'left-0 max-w-[240px]'">{{ text }}</span>
  </span>
</template>
