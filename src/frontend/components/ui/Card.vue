<script setup lang="ts">
defineProps<{ title?: string }>()
</script>

<template>
  <div class="card">
    <div v-if="title || $slots.title" class="card__title">
      <slot name="title">{{ title }}</slot>
    </div>
    <slot />
  </div>
</template>
