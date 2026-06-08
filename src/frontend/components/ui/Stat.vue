<script setup lang="ts">
defineProps<{ label: string }>()
</script>

<template>
  <div class="stat">
    <div class="stat__label">{{ label }}</div>
    <div class="stat__value"><slot /></div>
  </div>
</template>
