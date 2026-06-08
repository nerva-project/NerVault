<script setup lang="ts">
defineProps<{ label?: string; inputId?: string; error?: string }>()
</script>

<template>
  <div class="field">
    <label v-if="label" :for="inputId">{{ label }}</label>
    <slot />
    <p v-if="error" class="field__error">{{ error }}</p>
  </div>
</template>
