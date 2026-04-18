import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { message, notification } from 'ant-design-vue'

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

const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 30_000,
})

http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (resp) => {
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
    const status = error.response?.status
    const data = error.response?.data
    const msg = data?.message || error.message || '网络异常'
    if (status === 401) {
      setAccessToken(null)
      notification.warning({
        message: '登录已失效',
        description: '请重新登录后继续操作',
      })
      if (location.pathname !== '/login') {
        location.replace('/login')
      }
    } else if (status === 403) {
      notification.error({ message: '无权限', description: msg })
    } else {
      message.error(msg)
    }
    return Promise.reject(error)
  },
)

export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return (await http.get(url, config)).data as T
}
export async function post<T>(url: string, body?: any, config?: AxiosRequestConfig): Promise<T> {
  return (await http.post(url, body, config)).data as T
}
export async function put<T>(url: string, body?: any, config?: AxiosRequestConfig): Promise<T> {
  return (await http.put(url, body, config)).data as T
}
export async function patch<T>(url: string, body?: any, config?: AxiosRequestConfig): Promise<T> {
  return (await http.patch(url, body, config)).data as T
}
export async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return (await http.delete(url, config)).data as T
}

export default http
