import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = sessionStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const payload = response.data

    if (payload && typeof payload.code === 'number') {
      if (payload.code === 0) {
        return payload.data as never
      }

      if (payload.code === 40101) {
        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('refresh_token')
        const onLoginPage = window.location.pathname.startsWith('/login')
        if (!onLoginPage) {
          window.location.href = '/login'
        }
        const loginMsg = '你的账号或密码错误！'
        ElMessage.error(onLoginPage ? loginMsg : payload.message || loginMsg)
        return Promise.reject(new Error(onLoginPage ? loginMsg : payload.message || loginMsg))
      }

      ElMessage.error(payload.message || '请求失败')
      return Promise.reject(new Error(payload.message || '请求失败'))
    }

    return response.data as never
  },
  (error) => {
    const message = error.response?.data?.message || error.message || '网络错误'
    ElMessage.error(message)

    if (error.response?.status === 401) {
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('refresh_token')
    }

    return Promise.reject(error)
  },
)

export default request
