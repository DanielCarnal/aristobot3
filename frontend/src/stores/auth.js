import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  
  const isAuthenticated = computed(() => !!user.value)
  const isDev = computed(() => user.value?.is_dev || false)
  
  async function login(username = null, password = null) {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await api.post('/api/auth/login/', {
        username,
        password
      })
      user.value = response.data.user
      return true
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur de connexion'
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  async function logout() {
    try {
      await api.post('/api/auth/logout/')
      // En mode dev, on sera reconnecté automatiquement
      await checkAuth()
    } catch (err) {
      console.error('Erreur de déconnexion:', err)
    }
  }
  
  async function checkAuth() {
    try {
      const response = await api.get('/api/auth/current/')
      user.value = response.data
      return true
    } catch (err) {
      // En mode DEBUG, essayer de se connecter automatiquement
      if (import.meta.env.DEV) {
        return await login()
      }
      user.value = null
      return false
    }
  }
  
  async function updatePreferences(preferences) {
    try {
      await api.put('/api/auth/preferences/', preferences)
      // Recharger les infos utilisateur
      await checkAuth()
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur de mise à jour'
      throw err
    }
  }
  
  return {
    user,
    isLoading,
    error,
    isAuthenticated,
    isDev,
    login,
    logout,
    checkAuth,
    updatePreferences
  }
})