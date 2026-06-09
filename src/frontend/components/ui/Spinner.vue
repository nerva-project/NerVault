<script setup lang="ts">
defineProps<{ label?: string }>()
</script>

<template>
  <div class="center" role="status" :aria-label="label || 'Loading'">
    <div class="spinner"></div>
    <p v-if="label" class="dim">{{ label }}</p>
  </div>
</template>
