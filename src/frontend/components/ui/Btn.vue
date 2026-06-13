<script setup lang="ts">
import { computed } from "vue"

const props = withDefaults(
  defineProps<{
    variant?: "primary" | "ghost" | "danger"
    size?: "sm" | "lg"
    block?: boolean
    type?: "button" | "submit"
  }>(),
  { type: "button" },
)

const classes = computed(() => [
  "inline-flex items-center justify-center gap-2 border font-semibold cursor-pointer transition active:translate-y-px disabled:opacity-[0.55] disabled:cursor-not-allowed",
  props.size === "lg"
    ? "px-8 py-4 text-[1.05rem] rounded-card"
    : props.size === "sm"
      ? "px-[0.8rem] py-[0.4rem] text-[0.85rem] rounded-field"
      : "px-[1.4rem] py-[0.8rem] rounded-field",
  props.variant === "primary"
    ? "bg-accent text-accent-contrast border-transparent enabled:hover:bg-accent-strong"
    : props.variant === "ghost"
      ? "bg-surface border-border text-text enabled:hover:border-accent"
      : props.variant === "danger"
        ? "bg-danger-bg text-danger border-danger/35 enabled:hover:border-danger"
        : "border-transparent",
  props.block && "w-full",
])
</script>

<template>
  <button :type="type" :class="classes">
    <slot />
  </button>
</template>
