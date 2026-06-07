const BASE = `${window.location.origin}/v1`

const CSRF_COOKIE = "csrf_token"
const CSRF_HEADER = "X-CSRF-Token"

export interface ApiEnvelope<T> {
  status: "success" | "error"
  result?: T
  message?: string
  error?: string
}

export class ApiError extends Error {
  status: number
  code?: string

  constructor(message: string, status: number, code?: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.code = code
  }
}

function readCookie(name: string): string | null {
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") + "=([^;]*)"),
  )
  return match ? decodeURIComponent(match[1]) : null
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<ApiEnvelope<T>> {
  const headers: Record<string, string> = {}

  if (body !== undefined) {
    headers["Content-Type"] = "application/json"
  }

  if (method !== "GET" && method !== "HEAD") {
    const token = readCookie(CSRF_COOKIE)
    if (token) headers[CSRF_HEADER] = token
  }

  const res = await fetch(BASE + path, {
    method,
    headers,
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  let data: ApiEnvelope<T> = { status: "error" }
  try {
    data = (await res.json()) as ApiEnvelope<T>
  } catch {
    /* non-JSON response */
  }

  if (!res.ok || data.status === "error") {
    throw new ApiError(
      data.error || `Request failed (${res.status})`,
      res.status,
      (data as { code?: string }).code,
    )
  }

  return data
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body ?? {}),
}

export { BASE as API_BASE }
