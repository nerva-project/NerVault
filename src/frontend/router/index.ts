import { createRouter, createWebHistory } from "vue-router"

import { api } from "../lib/api"
import { useAuthStore } from "../stores/auth"

const MAINTENANCE_TTL = 10000
let maintenanceCache: { value: boolean; at: number } | null = null

async function isMaintenance(): Promise<boolean> {
  if (maintenanceCache && Date.now() - maintenanceCache.at < MAINTENANCE_TTL) {
    return maintenanceCache.value
  }
  try {
    const res = await api.get<{ maintenance: boolean }>("/meta/maintenance")
    const value = res.result?.maintenance ?? false
    maintenanceCache = { value, at: Date.now() }
    return value
  } catch {
    return false
  }
}

export function clearMaintenanceCache(): void {
  maintenanceCache = null
}

export function safeRedirect(next: unknown): string | null {
  if (typeof next !== "string") return null
  if (!next.startsWith("/") || next.startsWith("//")) return null
  return next
}

export const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: "/", name: "home", component: () => import("../views/Home.vue") },
    { path: "/faq", name: "faq", component: () => import("../views/Faq.vue") },
    {
      path: "/privacy",
      name: "privacy",
      component: () => import("../views/Privacy.vue"),
    },
    { path: "/terms", name: "terms", component: () => import("../views/Terms.vue") },
    {
      path: "/maintenance",
      name: "maintenance",
      component: () => import("../views/Maintenance.vue"),
    },
    {
      path: "/login",
      name: "login",
      component: () => import("../views/auth/Login.vue"),
      meta: { guestOnly: true },
    },
    {
      path: "/register",
      name: "register",
      component: () => import("../views/auth/Register.vue"),
      meta: { guestOnly: true },
    },
    {
      path: "/reset",
      name: "reset",
      component: () => import("../views/auth/ResetRequest.vue"),
      meta: { guestOnly: true },
    },
    {
      path: "/reset/:token",
      name: "reset-token",
      component: () => import("../views/auth/ResetPassword.vue"),
    },
    {
      path: "/confirm/:token",
      name: "confirm",
      component: () => import("../views/auth/Confirm.vue"),
    },
    {
      path: "/unconfirmed",
      name: "unconfirmed",
      component: () => import("../views/auth/Unconfirmed.vue"),
      meta: { requiresAuth: true },
    },
    { path: "/change-password", redirect: { name: "profile" } },
    {
      path: "/profile",
      name: "profile",
      component: () => import("../views/account/Profile.vue"),
      meta: { requiresAuth: true, requiresConfirmed: true },
    },
    {
      path: "/profile/email/:token",
      name: "confirm-email-change",
      component: () => import("../views/account/ConfirmEmailChange.vue"),
      meta: { requiresAuth: true, requiresConfirmed: true },
    },
    {
      path: "/wallet/setup",
      name: "wallet-setup",
      component: () => import("../views/wallet/Setup.vue"),
      meta: { requiresAuth: true, requiresConfirmed: true },
    },
    {
      path: "/wallet/loading",
      name: "wallet-loading",
      component: () => import("../views/wallet/Loading.vue"),
      meta: { requiresAuth: true, requiresConfirmed: true },
    },
    {
      path: "/wallet/dashboard",
      name: "wallet-dashboard",
      component: () => import("../views/wallet/Dashboard.vue"),
      meta: { requiresAuth: true, requiresConfirmed: true },
    },
    { path: "/:pathMatch(.*)*", redirect: { name: "home" } },
  ],
})

router.beforeEach(async (to) => {
  if (to.name !== "maintenance" && (await isMaintenance())) {
    return { name: "maintenance" }
  }

  const auth = useAuthStore()

  if (!auth.ready) {
    // Only block navigation on the session check for routes that actually
    // gate on auth; public routes render immediately while it resolves.
    if (to.meta.requiresAuth || to.meta.requiresConfirmed) {
      await auth.fetchMe()
    } else {
      void auth.fetchMe()
    }
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: "login", query: { next: to.fullPath } }
  }

  if (
    to.meta.requiresConfirmed &&
    auth.isAuthenticated &&
    !auth.isConfirmed
  ) {
    return { name: "unconfirmed" }
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: "wallet-dashboard" }
  }

  return true
})
