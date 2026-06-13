<script setup lang="ts">
defineProps<{ href?: string }>()

const cls =
  "inline-flex items-center justify-center size-[38px] rounded-field border border-border bg-surface text-text-dim cursor-pointer hover:text-text hover:border-accent [&_svg]:size-[18px]"
</script>

<template>
  <a v-if="href" :class="cls" :href="href"><slot /></a>
  <button v-else :class="cls" type="button"><slot /></button>
</template>
