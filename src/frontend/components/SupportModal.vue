<script setup lang="ts">
import CopyField from "./CopyField.vue"
import BaseModal from "./ui/BaseModal.vue"

defineProps<{ open: boolean }>()
defineEmits<{ (e: "close"): void }>()

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
</script>

<template>
  <BaseModal :open="open" @close="$emit('close')">
    <template #title>Support <b>NerVault</b></template>

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
  </BaseModal>
</template>
