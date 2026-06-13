<script setup lang="ts">
withDefaults(defineProps<{ variant?: "error" | "warning" | "success" }>(), { variant: "error" })
</script>

<template>
  <div
    class="flex gap-[0.6rem] px-4 py-[0.8rem] rounded-field border text-[0.92rem]"
    :class="
      {
        error: 'text-danger bg-danger-bg border-danger/30',
        success: 'text-accent bg-accent/[0.12] border-accent/30',
        warning: 'text-warning bg-warning/[0.12] border-warning/30',
      }[variant]
    "
  >
    <slot />
  </div>
</template>
