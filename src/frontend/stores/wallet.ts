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

export interface Transfer {
  txid: string
  type: string
  amount: number
  fee: number
  timestamp: number
  payment_id?: string
  height?: number
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
  transfers: Transfer[]
  sorted_transactions: Record<string, SortedTx>
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
    reset(): void {
      this.status = null
      this.overview = null
    },
  },
})
