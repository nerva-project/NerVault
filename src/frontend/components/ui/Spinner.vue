<script setup lang="ts">
defineProps<{ label?: string }>()
</script>

<template>
  <div class="center">
    <div class="spinner"></div>
    <p v-if="label" class="dim">{{ label }}</p>
  </div>
</template>
