<script setup lang="ts">
withDefaults(defineProps<{ variant?: "error" | "warning" | "success" }>(), { variant: "error" })
</script>

<template>
  <div class="alert" :class="`alert--${variant}`">
    <slot />
  </div>
</template>
