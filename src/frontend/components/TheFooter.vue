<script setup lang="ts">
import { RouterLink } from "vue-router"

const START_YEAR = 2024
const currentYear = new Date().getFullYear()
const year =
  currentYear > START_YEAR ? `${START_YEAR}–${currentYear}` : `${START_YEAR}`
</script>

<template>
  <footer
    class="shrink-0 flex flex-wrap justify-center gap-2 border-t border-border-soft px-5 py-6 text-center text-[0.9rem] text-muted [&_a]:text-text-dim [&_a:hover]:text-text [&_a:hover]:no-underline"
  >
    <span>&copy; {{ year }} <a href="https://sn1f3rt.dev" target="_blank" rel="noopener">Sayan "sn1f3rt" Bhattacharyya</a></span>
    <span class="text-border">&middot;</span>
    <a href="https://nerva.one" target="_blank" rel="noopener">The Nerva Project</a>
    <span class="text-border">&middot;</span>
    <RouterLink to="/terms">Terms of Service</RouterLink>
    <span class="text-border">&middot;</span>
    <RouterLink to="/privacy">Privacy Policy</RouterLink>
    <span class="text-border">&middot;</span>
    <RouterLink to="/faq">FAQ</RouterLink>
  </footer>
</template>
