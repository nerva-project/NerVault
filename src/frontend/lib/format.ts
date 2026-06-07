const DECIMALS = 12

export function fromAtomic(atomic: number | string): string {
  const value = BigInt(
    typeof atomic === "number" ? Math.trunc(atomic) : atomic || "0",
  )
  const negative = value < 0n
  const abs = negative ? -value : value
  const base = 10n ** BigInt(DECIMALS)
  const whole = abs / base
  const frac = (abs % base).toString().padStart(DECIMALS, "0").replace(/0+$/, "")
  const formatted = frac ? `${whole}.${frac}` : `${whole}`
  return negative ? `-${formatted}` : formatted
}

export function shortenAddress(address: string, lead = 8, tail = 8): string {
  if (!address || address.length <= lead + tail) return address
  return `${address.slice(0, lead)}…${address.slice(-tail)}`
}

export function formatTimestamp(unix: number): string {
  if (!unix) return "—"
  return new Date(unix * 1000).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}
