<script setup lang="ts">
defineProps<{ variant: "in" | "out" }>()
</script>

<template>
  <span class="badge" :class="`badge--${variant}`">
    <slot />
  </span>
</template>
