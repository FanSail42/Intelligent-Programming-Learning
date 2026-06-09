import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getMe, type UserInfo } from '@/api/auth'

const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(sessionStorage.getItem(ACCESS_KEY) || '')
  const refreshToken = ref(sessionStorage.getItem(REFRESH_KEY) || '')
  const user = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!accessToken.value)
  const role = computed(() => user.value?.role || '')

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    sessionStorage.setItem(ACCESS_KEY, access)
    sessionStorage.setItem(REFRESH_KEY, refresh)
  }

  function clearAuth() {
    accessToken.value = ''
    refreshToken.value = ''
    user.value = null
    sessionStorage.removeItem(ACCESS_KEY)
    sessionStorage.removeItem(REFRESH_KEY)
  }

  async function login(username: string, password: string) {
    const data = await loginApi(username, password)
    setTokens(data.access_token, data.refresh_token)
    await fetchMe()
    return user.value
  }

  async function fetchMe() {
    if (!accessToken.value) return null
    user.value = await getMe()
    return user.value
  }

  function logout() {
    clearAuth()
  }

  return {
    accessToken,
    refreshToken,
    user,
    isLoggedIn,
    role,
    login,
    fetchMe,
    logout,
    clearAuth,
  }
})
