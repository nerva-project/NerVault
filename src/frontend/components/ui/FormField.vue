<script setup lang="ts">
import InfoTip from "./InfoTip.vue"

defineProps<{ label?: string; inputId?: string; error?: string; hint?: string }>()
</script>

<template>
  <div class="flex flex-col gap-[0.4rem] mb-4">
    <div v-if="label" class="flex items-center gap-[0.4rem]">
      <label :for="inputId" class="text-[0.9rem] font-semibold text-text-dim">{{ label }}</label>
      <InfoTip v-if="hint" :text="hint" />
    </div>
    <slot />
    <p v-if="error" class="m-0 mt-[0.1rem] text-[0.82rem] text-danger">{{ error }}</p>
  </div>
</template>
