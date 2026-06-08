<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: "primary" | "ghost" | "danger"
    size?: "sm" | "lg"
    block?: boolean
    type?: "button" | "submit"
  }>(),
  { type: "button" },
)
</script>

<template>
  <button
    :type="type"
    class="btn"
    :class="[variant && `btn--${variant}`, size && `btn--${size}`, block && 'btn--block']"
  >
    <slot />
  </button>
</template>
