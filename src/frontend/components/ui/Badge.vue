<script setup lang="ts">
defineProps<{ variant: "in" | "out" | "pending" }>()
</script>

<template>
  <span
    class="inline-flex items-center px-[0.55rem] py-[0.15rem] rounded-full text-[0.75rem] font-semibold capitalize"
    :class="variant === 'in' ? 'text-in bg-in/[0.14]' : variant === 'pending' ? 'text-warning bg-warning/[0.14]' : 'text-out bg-out/[0.14]'"
  >
    <slot />
  </span>
</template>
