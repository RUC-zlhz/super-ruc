const BASE_URL = 'http://localhost:8080/api/v1'
const TOKEN_KEY = 'sip.access_token'

export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}

function getToken(): string | null {
  return uni.getStorageSync(TOKEN_KEY) || null
}

export function setToken(token: string | null) {
  if (token) uni.setStorageSync(TOKEN_KEY, token)
  else uni.removeStorageSync(TOKEN_KEY)
}

export function request<T>(
  url: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  data?: any,
): Promise<ApiEnvelope<T>> {
  return new Promise((resolve, reject) => {
    const token = getToken()
    uni.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success(res) {
        const payload = res.data as ApiEnvelope<T>
        if (res.statusCode === 401) {
          setToken(null)
          uni.reLaunch({ url: '/pages/profile/index' })
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

function withQuery(url: string, params?: Record<string, any>) {
  const qs = params
    ? '?' + Object.entries(params)
      .filter(([, v]) => v != null)
      .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
      .join('&')
    : ''
  return `${url}${qs}`
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
    const token = getToken()
    uni.downloadFile({
      url: `${BASE_URL}${withQuery(url, params)}`,
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success(res) {
        if (res.statusCode === 401) {
          setToken(null)
          uni.reLaunch({ url: '/pages/profile/index' })
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
