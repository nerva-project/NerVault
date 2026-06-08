<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from "vue"

const props = defineProps<{ open: boolean; title?: string }>()
const emit = defineEmits<{ (e: "close"): void }>()

const closeEl = ref<HTMLButtonElement | null>(null)

function close(): void {
  emit("close")
}

function onKey(e: KeyboardEvent): void {
  if (e.key === "Escape") emit("close")
}

watch(
  () => props.open,
  async (o) => {
    document.body.classList.toggle("modal-open", o)
    if (o) {
      window.addEventListener("keydown", onKey)
      await nextTick()
      closeEl.value?.focus()
    } else {
      window.removeEventListener("keydown", onKey)
    }
  },
)

onUnmounted(() => {
  window.removeEventListener("keydown", onKey)
  document.body.classList.remove("modal-open")
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal" role="dialog" aria-modal="true" @click.self="close">
        <div class="modal__panel">
          <button ref="closeEl" class="modal__close" type="button" aria-label="Close" @click="close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>

          <h2 v-if="title || $slots.title" class="modal__title">
            <slot name="title">{{ title }}</slot>
          </h2>

          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
