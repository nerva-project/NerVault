<script setup lang="ts">
defineProps<{ title?: string }>()
</script>

<template>
  <div class="bg-surface border border-border rounded-card p-6 shadow-card">
    <div v-if="title || $slots.title" class="text-[1.1rem] font-bold mb-4">
      <slot name="title">{{ title }}</slot>
    </div>
    <slot />
  </div>
</template>
