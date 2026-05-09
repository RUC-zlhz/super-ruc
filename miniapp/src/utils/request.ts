const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8080/api/v1'
const API_BASE_URL_STORAGE_KEY = 'sip.api_base_url'
const API_BASE_URL_ENV_KEYS = ['VITE_MINIAPP_API_BASE_URL', 'VITE_API_BASE_URL']
export const TOKEN_KEY = 'sip.access_token'
const REFRESH_TOKEN_KEY = 'sip.refresh_token'
const LOGIN_PAGE_URL = '/pages/profile/index'

let loginRedirectPending = false

export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}

export class AuthRequiredError extends Error {
  code = 'AUTH_REQUIRED'

  constructor(message = '请先登录') {
    super(message)
    this.name = 'AuthRequiredError'
  }
}

export function isAuthRequiredError(error: unknown): error is AuthRequiredError {
  return !!error && typeof error === 'object' && (error as { code?: unknown }).code === 'AUTH_REQUIRED'
}

function getEnvApiBaseUrl(): string | null {
  const env = (import.meta as unknown as { env?: Record<string, string | undefined> }).env
  for (const key of API_BASE_URL_ENV_KEYS) {
    const value = env?.[key]?.trim()
    if (value) return value
  }
  return null
}

function normalizeApiBaseUrl(baseUrl: string): string {
  return baseUrl.trim().replace(/\/+$/, '')
}

export function getApiBaseUrl(): string {
  const runtimeValue = uni.getStorageSync(API_BASE_URL_STORAGE_KEY)
  const runtimeBaseUrl = typeof runtimeValue === 'string' ? runtimeValue.trim() : ''
  return normalizeApiBaseUrl(runtimeBaseUrl || getEnvApiBaseUrl() || DEFAULT_API_BASE_URL)
}

export function setApiBaseUrl(baseUrl: string | null) {
  if (baseUrl?.trim()) uni.setStorageSync(API_BASE_URL_STORAGE_KEY, normalizeApiBaseUrl(baseUrl))
  else uni.removeStorageSync(API_BASE_URL_STORAGE_KEY)
}

export function getToken(): string | null {
  return uni.getStorageSync(TOKEN_KEY) || null
}

export function hasToken(): boolean {
  return !!getToken()
}

export function getAuthHeader(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function setToken(token: string | null) {
  if (token) uni.setStorageSync(TOKEN_KEY, token)
  else uni.removeStorageSync(TOKEN_KEY)
}

function getCurrentRoute(): string {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  return current?.route || ''
}

function isLoginPageActive(): boolean {
  return getCurrentRoute() === LOGIN_PAGE_URL.replace(/^\//, '')
}

function isAuthEndpoint(url: string): boolean {
  const path = (url.startsWith('/') ? url : `/${url}`).split('?')[0]
  return path.startsWith('/auth/')
}

function redirectToLoginOnce() {
  if (loginRedirectPending || isLoginPageActive()) return
  loginRedirectPending = true
  uni.reLaunch({
    url: LOGIN_PAGE_URL,
    complete() {
      setTimeout(() => {
        loginRedirectPending = false
      }, 800)
    },
  })
}

export function clearAuthSession() {
  setToken(null)
  uni.removeStorageSync(REFRESH_TOKEN_KEY)
  const eventBus = uni as unknown as { $emit?: (event: string) => void }
  eventBus.$emit?.('sip:auth-invalid')
}

export function handleUnauthorized(redirect = true) {
  clearAuthSession()
  if (redirect) redirectToLoginOnce()
}

function ensureAuthorized(url: string): boolean {
  if (isAuthEndpoint(url) || hasToken()) return true
  handleUnauthorized(true)
  return false
}

export function request<T>(
  url: string,
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' = 'GET',
  data?: any,
): Promise<ApiEnvelope<T>> {
  return new Promise((resolve, reject) => {
    if (!ensureAuthorized(url)) {
      reject(new AuthRequiredError())
      return
    }
    uni.request({
      url: buildApiUrl(url),
      // uni-app runtime accepts PATCH here, but the shipped type definition does not.
      method: method as 'GET' | 'POST' | 'PUT' | 'DELETE',
      data,
      header: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      success(res) {
        const payload = res.data as ApiEnvelope<T>
        if (res.statusCode === 401) {
          handleUnauthorized(true)
          reject(new Error('登录已失效'))
          return
        }
        if (payload && payload.code === 0) {
          resolve(payload)
        } else {
          uni.showToast({ title: payload?.message || '请求失败', icon: 'none' })
          reject(payload)
        }
      },
      fail(err) {
        uni.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      },
    })
  })
}

function buildQuery(params?: Record<string, any>) {
  return params
    ? Object.entries(params)
      .filter(([, v]) => v != null)
      .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
      .join('&')
    : ''
}

export function buildApiUrl(url: string, params?: Record<string, any>) {
  const path = url.startsWith('/') ? url : `/${url}`
  const query = buildQuery(params)
  return `${getApiBaseUrl()}${path}${query ? `?${query}` : ''}`
}

function withQuery(url: string, params?: Record<string, any>) {
  const qs = buildQuery(params)
  return `${url}${qs ? `?${qs}` : ''}`
}

export function get<T>(url: string, params?: Record<string, any>) {
  return request<T>(withQuery(url, params), 'GET')
}

export function post<T>(url: string, data?: any) {
  return request<T>(url, 'POST', data)
}

export function put<T>(url: string, data?: any) {
  return request<T>(url, 'PUT', data)
}

export function download(url: string, params?: Record<string, any>) {
  return new Promise<{ tempFilePath: string; statusCode: number }>((resolve, reject) => {
    if (!ensureAuthorized(url)) {
      reject(new AuthRequiredError())
      return
    }
    uni.downloadFile({
      url: buildApiUrl(url, params),
      header: getAuthHeader(),
      success(res) {
        if (res.statusCode === 401) {
          handleUnauthorized(true)
          reject(new Error('登录已失效'))
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300 && res.tempFilePath) {
          resolve({ tempFilePath: res.tempFilePath, statusCode: res.statusCode })
          return
        }
        uni.showToast({ title: '文件下载失败', icon: 'none' })
        reject(res)
      },
      fail(err) {
        uni.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      },
    })
  })
}
