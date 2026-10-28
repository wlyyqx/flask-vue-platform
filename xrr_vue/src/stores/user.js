import { defineStore } from 'pinia'
import api from '@/utils/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  actions: {
    async login(payload) {
      const data = await api.post('/auth/login', payload)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      this.user = data.user
    },
    logout() {
      localStorage.clear()
      this.user = null
    }
  }
})