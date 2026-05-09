import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { post, get, getToken, isAuthRequiredError, setToken } from '@/utils/request'

interface RoleInfo {
  code: string
  scope_code?: string | null
}

interface UserInfo {
  id: number
  display_name: string
  avatar_url?: string | null
  student_no?: string | null
  student_id?: number | null
  roles: RoleInfo[]
}

interface TokenResponse {
  access_token: string
  refresh_token: string
  user: UserInfo
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const tokenPresent = ref(!!getToken())
  const isLoggedIn = computed(() => tokenPresent.value && !!user.value)
  let meInFlight: Promise<UserInfo | null> | null = null

  const eventBus = uni as unknown as { $on?: (event: string, callback: () => void) => void }
  eventBus.$on?.('sip:auth-invalid', () => {
    tokenPresent.value = false
    user.value = null
  })

  async function wxLogin(code: string, studentNo?: string) {
    const resp = await post<TokenResponse>('/auth/wx-login', {
      code,
      student_no: studentNo?.trim() || undefined,
    })
    setToken(resp.data.access_token)
    uni.setStorageSync('sip.refresh_token', resp.data.refresh_token)
    tokenPresent.value = true
    user.value = resp.data.user
  }

  async function fetchMe() {
    if (!getToken()) {
      tokenPresent.value = false
      user.value = null
      return null
    }
    tokenPresent.value = true
    if (user.value) return user.value
    if (!meInFlight) {
      meInFlight = get<UserInfo>('/auth/me')
        .then((resp) => {
          user.value = resp.data
          return resp.data
        })
        .catch((error) => {
          const message = error instanceof Error ? error.message : ''
          if (isAuthRequiredError(error) || message === '登录已失效') {
            tokenPresent.value = false
            user.value = null
            return null
          }
          throw error
        })
        .finally(() => {
          meInFlight = null
        })
    }
    return meInFlight
  }

  function logout() {
    user.value = null
    tokenPresent.value = false
    setToken(null)
    uni.removeStorageSync('sip.refresh_token')
  }

  return { user, isLoggedIn, wxLogin, fetchMe, logout }
})
