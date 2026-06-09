import { defineStore } from "pinia"

import { api } from "../lib/api"

export interface WalletStatus {
  created: boolean
  connected: boolean
  port: number | null
  container: string | null
  volume: boolean
  initializing: boolean
  ready: boolean
}

export interface SortedTx {
  type: string
  amount: number
  timestamp: number
  total: number
}

export interface WalletOverview {
  address: string
  email: string
  balance: number
  unlocked_balance: number
  sorted_transactions: Record<string, SortedTx>
  price: number
  wallet_height: number
  network_height: number
  expires_at: string | null
}

interface WalletState {
  status: WalletStatus | null
  overview: WalletOverview | null
}

export const useWalletStore = defineStore("wallet", {
  state: (): WalletState => ({
    status: null,
    overview: null,
  }),
  actions: {
    async fetchStatus(): Promise<WalletStatus | null> {
      const res = await api.get<WalletStatus>("/wallet/status")
      this.status = res.result ?? null
      return this.status
    },
    async fetchOverview(): Promise<WalletOverview | null> {
      const res = await api.get<WalletOverview>("/wallet")
      this.overview = res.result ?? null
      return this.overview
    },
    async setup(mode: "create" | "restore", seed?: string): Promise<void> {
      await api.post("/wallet/setup", { mode, seed })
    },
    async connect(): Promise<void> {
      await api.post("/wallet/connect")
    },
    async keepAlive(): Promise<string | null> {
      const res = await api.post<{ expires_at: string }>("/wallet/keepalive")
      const exp = res.result?.expires_at ?? null
      if (this.overview && exp) this.overview.expires_at = exp
      return exp
    },
    reset(): void {
      this.status = null
      this.overview = null
    },
  },
})
