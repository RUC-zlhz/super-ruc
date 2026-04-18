import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { post, get, setToken } from '@/utils/request'

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
  const isLoggedIn = computed(() => !!user.value)

  async function wxLogin(code: string) {
    const resp = await post<TokenResponse>('/auth/wx-login', { code })
    setToken(resp.data.access_token)
    uni.setStorageSync('sip.refresh_token', resp.data.refresh_token)
    user.value = resp.data.user
  }

  async function fetchMe() {
    const resp = await get<UserInfo>('/auth/me')
    user.value = resp.data
    return resp.data
  }

  function logout() {
    user.value = null
    setToken(null)
    uni.removeStorageSync('sip.refresh_token')
  }

  return { user, isLoggedIn, wxLogin, fetchMe, logout }
})
