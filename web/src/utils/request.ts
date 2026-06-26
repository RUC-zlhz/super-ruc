import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
} from 'axios'
import { message, notification } from 'ant-design-vue'
import { doneProgress, startProgress } from './progress'

const TOKEN_KEY = 'sip.access_token'

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}
export function setAccessToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}

function isAuthLoginRequest(url?: string): boolean {
  if (!url) return false
  const path = url.split('?')[0]?.replace(/\/+$/, '')
  return path === '/auth/login' || path.endsWith('/api/v1/auth/login')
}

const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 30_000,
})

// ── 路由切换取消：仅跟踪 GET（只读）请求的 AbortController，
//    离开页面时取消尚未返回的旧请求，避免迟到响应覆盖新页面状态。
//    变更类请求（POST/PUT/PATCH/DELETE）不纳入自动取消，保证写操作不被打断。
const pending = new Set<AbortController>()
const controllers = new WeakMap<object, AbortController>()

function untrack(config?: object | null): void {
  if (!config) return
  const c = controllers.get(config)
  if (c) {
    pending.delete(c)
    controllers.delete(config)
  }
}

export function cancelPendingRequests(): void {
  pending.forEach((c) => c.abort())
  pending.clear()
}

http.interceptors.request.use(
  (config) => {
    startProgress()
    const method = (config.method || 'get').toLowerCase()
    if (method === 'get' && !config.signal) {
      const controller = new AbortController()
      config.signal = controller.signal
      controllers.set(config, controller)
      pending.add(controller)
    }
    const token = getAccessToken()
    if (token) {
      config.headers = config.headers ?? {}
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    doneProgress()
    return Promise.reject(error)
  },
)

http.interceptors.response.use(
  (resp) => {
    doneProgress()
    untrack(resp.config)
    // 下载类响应直接透传
    if (resp.config.responseType === 'blob') return resp
    const payload = resp.data as ApiEnvelope<unknown>
    if (payload && typeof payload.code === 'number') {
      if (payload.code !== 0) {
        message.error(payload.message || '请求失败')
        return Promise.reject(payload)
      }
      return resp
    }
    return resp
  },
  (error: AxiosError<ApiEnvelope<unknown>>) => {
    doneProgress()
    untrack(error.config)
    // 路由切换主动取消的请求：静默丢弃，不打扰用户
    if (axios.isCancel(error)) return Promise.reject(error)
    const status = error.response?.status
    const data = error.response?.data
    const msg = data?.message || error.message || '网络异常'
    if (status === 401) {
      if (isAuthLoginRequest(error.config?.url)) {
        message.error(msg)
        return Promise.reject(error)
      }
      setAccessToken(null)
      notification.warning({
        message: '登录已失效',
        description: '请重新登录后继续操作',
      })
      if (location.pathname !== '/login') {
        const currentPath = location.pathname + location.search + location.hash
        location.replace(`/login?redirect=${encodeURIComponent(currentPath)}`)
      }
    } else if (status === 403) {
      notification.error({ message: '无权限', description: msg })
    } else {
      message.error(msg)
    }
    return Promise.reject(error)
  },
)

// 永不 settle 的 promise：被取消的请求落到这里，让卸载中的组件 await 静默挂起，
// 既不会跑成功分支（拿到脏数据），也不会冒出 unhandledrejection 噪声。
const NEVER: Promise<never> = new Promise<never>(() => {})

function unwrap<T>(raw: Promise<AxiosResponse>): Promise<T> {
  return raw.then(
    (r) => r.data as T,
    (e) => {
      if (axios.isCancel(e)) return NEVER as Promise<T>
      throw e
    },
  )
}

// ── GET 去重：同一 url+params 的并发只读请求复用同一个在途 promise，
//    避免重复点击 / 组件重挂导致的冗余往返。
const inflightGet = new Map<string, Promise<unknown>>()

function dedupeKey(url: string, config?: AxiosRequestConfig): string | null {
  if (config?.signal) return null
  if (config?.responseType && config.responseType !== 'json') return null
  return `${url}::${config?.params ? JSON.stringify(config.params) : ''}`
}

export function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const key = dedupeKey(url, config)
  if (key) {
    const existing = inflightGet.get(key)
    if (existing) return existing as Promise<T>
  }
  const raw = http.get(url, config)
  const result = unwrap<T>(raw)
  if (key) {
    inflightGet.set(key, result)
    // 用底层 raw 的 settle（含取消时的 reject）清理，避免被取消时 key 永久残留
    const cleanup = () => {
      if (inflightGet.get(key) === result) inflightGet.delete(key)
    }
    raw.then(cleanup, cleanup)
  }
  return result
}
export function post<T>(url: string, body?: any, config?: AxiosRequestConfig): Promise<T> {
  return unwrap<T>(http.post(url, body, config))
}
export function put<T>(url: string, body?: any, config?: AxiosRequestConfig): Promise<T> {
  return unwrap<T>(http.put(url, body, config))
}
export function patch<T>(url: string, body?: any, config?: AxiosRequestConfig): Promise<T> {
  return unwrap<T>(http.patch(url, body, config))
}
export function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return unwrap<T>(http.delete(url, config))
}

export default http
