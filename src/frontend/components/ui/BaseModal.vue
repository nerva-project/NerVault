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

function onPanelClick(e: MouseEvent): void {
  // Clicking anything that isn't an actual control (padding, title, labels,
  // gaps) blurs the focused field so its highlight clears on the first click.
  // preventDefault cancels a label's default action so it doesn't instead
  // shift focus to its own input.
  const target = e.target as HTMLElement | null
  if (target && !target.closest("input, textarea, select, button, a, [tabindex]")) {
    e.preventDefault()
    ;(document.activeElement as HTMLElement | null)?.blur()
  }
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

function lockScroll(): void {
  // Pad the body by the removed scrollbar's width so the page doesn't shift.
  const gap = window.innerWidth - document.documentElement.clientWidth
  if (gap > 0) document.body.style.paddingRight = `${gap}px`
  document.body.classList.add("modal-open")
}

function unlockScroll(): void {
  document.body.classList.remove("modal-open")
  document.body.style.paddingRight = ""
}

watch(
  () => props.open,
  async (o) => {
    if (o) {
      lockScroll()
      lastFocused = document.activeElement as HTMLElement | null
      window.addEventListener("keydown", onKey)
      await nextTick()
      closeEl.value?.focus()
    } else {
      unlockScroll()
      window.removeEventListener("keydown", onKey)
      lastFocused?.focus()
      lastFocused = null
    }
  },
)

onUnmounted(() => {
  window.removeEventListener("keydown", onKey)
  unlockScroll()
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-[180ms]"
      leave-active-class="transition-opacity duration-[180ms]"
      enter-from-class="opacity-0" leave-to-class="opacity-0">
      <div v-if="open"
        class="fixed inset-0 z-[60] flex items-center justify-center p-5 bg-black/60 backdrop-blur-[4px]"
        role="dialog" aria-modal="true"
        :aria-labelledby="title || $slots.title ? titleId : undefined" @click.self="close">
        <div ref="panel"
          class="relative w-full max-w-[540px] max-h-[90vh] overflow-y-auto bg-surface border border-border rounded-card p-7 shadow-card"
          @click="onPanelClick">
          <button ref="closeEl"
            class="absolute top-4 right-4 size-[32px] inline-flex items-center justify-center border-none bg-transparent text-muted cursor-pointer"
            type="button" aria-label="Close" @click="close">
            <svg class="size-[20px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>

          <h2 v-if="title || $slots.title" :id="titleId" class="text-[1.3rem] mb-2">
            <slot name="title">{{ title }}</slot>
          </h2>

          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
