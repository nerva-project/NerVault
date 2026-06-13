<script setup lang="ts">
defineProps<{ label: string }>()
</script>

<template>
  <div class="bg-surface border border-border rounded-card px-5 py-[1.1rem]">
    <div class="text-muted text-[0.8rem] uppercase tracking-[0.05em]">{{ label }}</div>
    <div class="text-[1.4rem] font-bold mt-1"><slot /></div>
  </div>
</template>
