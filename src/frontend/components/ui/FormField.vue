<script setup lang="ts">
import InfoTip from "./InfoTip.vue"

defineProps<{ label?: string; inputId?: string; error?: string; hint?: string }>()
</script>

<template>
  <div class="field">
    <div v-if="label" class="field__label">
      <label :for="inputId">{{ label }}</label>
      <InfoTip v-if="hint" :text="hint" />
    </div>
    <slot />
    <p v-if="error" class="field__error">{{ error }}</p>
  </div>
</template>
