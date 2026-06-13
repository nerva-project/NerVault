<script setup lang="ts">
import { ref } from "vue"

defineOptions({ inheritAttrs: false })

const model = defineModel<string>({ required: true })
const show = ref(false)
</script>

<template>
  <div class="relative">
    <input v-bind="$attrs" v-model="model" class="input pr-11!"
      :type="show ? 'text' : 'password'" />
    <button type="button" tabindex="-1" :aria-pressed="show"
      :aria-label="show ? 'Hide password' : 'Show password'"
      class="absolute inset-y-0 right-0 flex items-center px-3 text-text-dim cursor-pointer hover:text-text [&_svg]:size-[18px]"
      @click="show = !show">
      <svg v-if="show" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
        <line x1="1" y1="1" x2="23" y2="23" />
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    </button>
  </div>
</template>
