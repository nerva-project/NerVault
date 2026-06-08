<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from "vue"

import CopyField from "./CopyField.vue"

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: "close"): void }>()

interface Coin {
  label: string
  ticker: string
  address: string
}

const coins: Coin[] = [
  {
    label: "Nerva",
    ticker: "XNV",
    address:
      "NV1PqtQwRik7FFeAJ5n7iKbHtve3nkeM99x3Q31wjBAm7twvRv6NYkbbP7vSG3n8N3fsUh2gpfZG2PRi4gYhxL4h2r2SnhUoX",
  },
  {
    label: "Monero",
    ticker: "XMR",
    address:
      "48SSQzEcvQPK7H69vUvwReFT7tCDESdRhPFGubTgJ8WeXUUPQRWjY8oZk3wHfLhsUnChJ1BYyYfoLKQh8epYsupAAWCnDKh",
  },
  {
    label: "Bitcoin",
    ticker: "BTC",
    address: "bc1qzg4jjtxq6cg22pmlaesyva64nrjzcaqud968vf",
  },
  {
    label: "Ethereum",
    ticker: "ETH",
    address: "0x97173e82df1d9Cc76946241D63A9f9231Dea1566",
  },
]

const fiat = [
  { label: "GitHub Sponsors", url: "https://github.com/sponsors/sn1f3rt" },
  { label: "Patreon", url: "https://www.patreon.com/sn1f3rt" },
  { label: "Buy Me a Coffee", url: "https://www.buymeacoffee.com/sn1f3rt" },
]

const closeEl = ref<HTMLButtonElement | null>(null)

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

onUnmounted(() => window.removeEventListener("keydown", onKey))
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal" role="dialog" aria-modal="true" aria-labelledby="support-title"
        @click.self="$emit('close')">
        <div class="modal__panel">
          <button ref="closeEl" class="modal__close" type="button" aria-label="Close" @click="$emit('close')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
              stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>

          <h2 id="support-title" class="modal__title">Support <b>NerVault</b></h2>
          <p class="modal__lead">
            NerVault is free to use, but its development and hosting are not. If you find it useful,
            please consider chipping in.
          </p>

          <div class="donate">
            <div v-for="c in coins" :key="c.ticker" class="donate__row">
              <span class="donate__coin">{{ c.label }} <span class="donate__tick">{{ c.ticker }}</span></span>
              <CopyField :value="c.address" wrap />
            </div>
          </div>

          <div class="donate__fiat">
            <span class="donate__fiatlabel">Prefer fiat?</span>
            <a v-for="f in fiat" :key="f.url" :href="f.url" target="_blank" rel="noopener">{{ f.label }}</a>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
