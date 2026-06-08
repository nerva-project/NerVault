<script setup lang="ts">
defineProps<{ title: string; lead?: string }>()
</script>

<template>
  <header class="pagehead">
    <h1>{{ title }}</h1>
    <p v-if="lead || $slots.lead" class="pagehead__lead">
      <slot name="lead">{{ lead }}</slot>
    </p>
  </header>
</template>
