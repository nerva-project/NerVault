<script setup lang="ts">
import { nextTick, onUnmounted, ref, useId, watch } from "vue"

const props = defineProps<{ open: boolean; title?: string }>()
const emit = defineEmits<{ (e: "close"): void }>()

const closeEl = ref<HTMLButtonElement | null>(null)
const panel = ref<HTMLElement | null>(null)
const titleId = useId()

let lastFocused: HTMLElement | null = null

function close(): void {
  emit("close")
}

function focusables(): HTMLElement[] {
  if (!panel.value) return []
  return Array.from(
    panel.value.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((el) => el.offsetParent !== null || el === document.activeElement)
}

function onKey(e: KeyboardEvent): void {
  if (e.key === "Escape") {
    emit("close")
    return
  }
  if (e.key !== "Tab") return

  const items = focusables()
  if (!items.length) {
    e.preventDefault()
    return
  }
  const first = items[0]
  const last = items[items.length - 1]
  const active = document.activeElement as HTMLElement | null

  if (e.shiftKey) {
    if (active === first || !panel.value?.contains(active)) {
      e.preventDefault()
      last.focus()
    }
  } else if (active === last || !panel.value?.contains(active)) {
    e.preventDefault()
    first.focus()
  }
}

watch(
  () => props.open,
  async (o) => {
    document.body.classList.toggle("modal-open", o)
    if (o) {
      lastFocused = document.activeElement as HTMLElement | null
      window.addEventListener("keydown", onKey)
      await nextTick()
      closeEl.value?.focus()
    } else {
      window.removeEventListener("keydown", onKey)
      lastFocused?.focus()
      lastFocused = null
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
      <div v-if="open" class="modal" role="dialog" aria-modal="true"
        :aria-labelledby="title || $slots.title ? titleId : undefined" @click.self="close">
        <div ref="panel" class="modal__panel">
          <button ref="closeEl" class="modal__close" type="button" aria-label="Close" @click="close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>

          <h2 v-if="title || $slots.title" :id="titleId" class="modal__title">
            <slot name="title">{{ title }}</slot>
          </h2>

          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
