import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  changePassword as changePasswordApi,
  getMe,
  loginByWorkNo,
  logoutSession,
} from '@/api/auth'
import type { UserInfo } from '@/api/types'
import { setAccessToken, getAccessToken } from '@/utils/request'

const REFRESH_KEY = 'sip.refresh_token'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(getAccessToken())
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_KEY))
  const user = ref<UserInfo | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value)
  const roleCodes = computed(() => user.value?.roles?.map((r) => r.code) ?? [])

  async function login(work_no: string, password: string) {
    const resp = await loginByWorkNo(work_no, password)
    applyTokens(resp.data.access_token, resp.data.refresh_token)
    user.value = resp.data.user
  }

  async function fetchMe() {
    if (!accessToken.value) return null
    const resp = await getMe()
    user.value = resp.data
    return resp.data
  }

  async function changePassword(oldPassword: string, newPassword: string) {
    const resp = await changePasswordApi(oldPassword, newPassword)
    user.value = resp.data
    return resp.data
  }

  function applyTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    setAccessToken(access)
    localStorage.setItem(REFRESH_KEY, refresh)
  }

  function clearLocalSession() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    setAccessToken(null)
    localStorage.removeItem(REFRESH_KEY)
  }

  function logout() {
    const accessSnapshot = accessToken.value
    const refreshSnapshot = refreshToken.value
    clearLocalSession()
    if (accessSnapshot) {
      void logoutSession(refreshSnapshot, accessSnapshot).catch(() => undefined)
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    roleCodes,
    login,
    fetchMe,
    changePassword,
    logout,
  }
})
