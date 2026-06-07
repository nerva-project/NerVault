import { ref } from "vue"

export type Theme = "dark" | "light"

const THEME_KEY = "nerva-vault-theme"

function read(): Theme {
  try {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved === "light" || saved === "dark") return saved
  } catch {
    /* ignore */
  }
  const attr = document.documentElement.getAttribute("data-theme")
  return attr === "light" ? "light" : "dark"
}

function apply(t: Theme): void {
  document.documentElement.setAttribute("data-theme", t)
}

const theme = ref<Theme>(read())
apply(theme.value)

export function useTheme() {
  function toggle(): void {
    theme.value = theme.value === "light" ? "dark" : "light"
    apply(theme.value)
    try {
      localStorage.setItem(THEME_KEY, theme.value)
    } catch {
      /* ignore */
    }
  }
  return { theme, toggle }
}
