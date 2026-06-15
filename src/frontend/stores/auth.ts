import { defineStore } from "pinia"

import { api } from "../lib/api"

export interface TwoFactorState {
  email: boolean
  totp: boolean
  method: "email" | "totp" | null
}

export interface User {
  username: string
  email: string
  confirmed: boolean
  two_factor?: TwoFactorState
}

interface AuthState {
  user: User | null
  ready: boolean
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    user: null,
    ready: false,
  }),
  getters: {
    isAuthenticated: (s): boolean => s.user !== null,
    isConfirmed: (s): boolean => s.user?.confirmed ?? false,
  },
  actions: {
    setUser(user: User | null): void {
      this.user = user
    },
    async fetchMe(): Promise<void> {
      try {
        const res = await api.get<User>("/auth/me")
        this.user = res.result ?? null
      } catch {
        this.user = null
      } finally {
        this.ready = true
      }
    },
    async logout(): Promise<void> {
      try {
        await api.post("/auth/logout")
      } catch {
        /* ignore */
      }
      this.user = null
    },
  },
})
