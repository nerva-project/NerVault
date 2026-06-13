<script setup lang="ts">
defineProps<{ title: string; lead?: string }>()
</script>

<template>
  <header class="mb-8">
    <h1 class="mb-[0.4rem]">{{ title }}</h1>
    <p v-if="lead || $slots.lead" class="m-0 text-muted text-[1.05rem]">
      <slot name="lead">{{ lead }}</slot>
    </p>
  </header>
</template>
