<script setup lang="ts">
import { RouterLink } from "vue-router"

const year = new Date().getFullYear()
const version = __APP_VERSION__
</script>

<template>
  <footer class="footer">
    <span>&copy; {{ year }} <a href="https://nerva.one" target="_blank" rel="noopener">The Nerva Project</a></span>
    <span class="sep">&middot;</span>
    <RouterLink to="/terms">Terms</RouterLink>
    <span class="sep">&middot;</span>
    <RouterLink to="/privacy">Privacy</RouterLink>
    <span class="sep">&middot;</span>
    <RouterLink to="/faq">FAQ</RouterLink>
    <span class="sep">&middot;</span>
    <span class="muted">v{{ version }}</span>
  </footer>
</template>
