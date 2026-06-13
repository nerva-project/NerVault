<script setup lang="ts">
defineProps<{ label?: string }>()
</script>

<template>
  <div class="text-center" role="status" :aria-label="label || 'Loading'">
    <div class="size-[42px] rounded-full border-[3px] border-border border-t-accent animate-spin mx-auto my-6"></div>
    <p v-if="label" class="text-text-dim">{{ label }}</p>
  </div>
</template>
