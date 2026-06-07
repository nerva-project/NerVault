import { reactive } from "vue"

export type ToastKind = "success" | "error" | "warning"

export interface Toast {
  id: number
  kind: ToastKind
  text: string
}

const toasts = reactive<Toast[]>([])
let seq = 0

function remove(id: number): void {
  const index = toasts.findIndex((t) => t.id === id)
  if (index >= 0) toasts.splice(index, 1)
}

function push(text: string, kind: ToastKind = "success", ttl = 4500): void {
  const id = ++seq
  toasts.push({ id, kind, text })
  window.setTimeout(() => remove(id), ttl)
}

export function useToast() {
  return {
    toasts,
    remove,
    success: (text: string) => push(text, "success"),
    error: (text: string) => push(text, "error"),
    warning: (text: string) => push(text, "warning"),
  }
}
