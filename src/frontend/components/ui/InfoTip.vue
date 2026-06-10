<script setup lang="ts">
defineProps<{ text: string }>()
</script>

<template>
  <span class="infotip" tabindex="0" role="note" :aria-label="text">
    <svg class="infotip__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4" />
      <path d="M12 8h.01" />
    </svg>
    <span class="infotip__bubble">{{ text }}</span>
  </span>
</template>
