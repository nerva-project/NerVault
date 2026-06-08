<script setup lang="ts">
import { RouterLink } from "vue-router"

const year = new Date().getFullYear()
</script>

<template>
  <footer class="footer">
    <span>&copy; {{ year }} <a href="https://sn1f3rt.dev" target="_blank" rel="noopener">Sayan "sn1f3rt" Bhattacharyya</a></span>
    <span class="sep">&middot;</span>
    <a href="https://nerva.one" target="_blank" rel="noopener">The Nerva Project</a>
    <span class="sep">&middot;</span>
    <RouterLink to="/terms">Terms</RouterLink>
    <span class="sep">&middot;</span>
    <RouterLink to="/privacy">Privacy</RouterLink>
    <span class="sep">&middot;</span>
    <RouterLink to="/faq">FAQ</RouterLink>
  </footer>
</template>
