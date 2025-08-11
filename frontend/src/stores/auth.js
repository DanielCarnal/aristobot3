import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/index.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const debugConfig = ref({ enabled: false, active: false })
  
  const isAuthenticated = computed(() => !!user.value)
  const debugEnabled = computed(() => debugConfig.value.enabled)
  const debugActive = computed(() => debugConfig.value.active)
  
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
      user.value = null
      debugConfig.value = { enabled: false, active: false }
    } catch (err) {
      console.error('Erreur de déconnexion:', err)
      // Forcer la déconnexion côté client même si erreur serveur
      user.value = null
      debugConfig.value = { enabled: false, active: false }
    }
  }
  
  async function checkDebugConfig() {
    try {
      const response = await api.get('/api/auth/debug-config/')
      debugConfig.value = response.data
      return response.data
    } catch (err) {
      console.error('Erreur debug config:', err)
      debugConfig.value = { enabled: false, active: false }
      return debugConfig.value
    }
  }
  
  async function toggleDebugMode() {
    try {
      const response = await api.post('/api/auth/toggle-debug/')
      debugConfig.value.active = response.data.active
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur toggle debug'
      throw err
    }
  }
  
  async function debugLogin() {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await api.post('/api/auth/debug-login/')
      user.value = response.data.user
      return true
    } catch (err) {
      error.value = err.response?.data?.error || 'Debug login non disponible'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function checkAuth() {
    try {
      const response = await api.get('/api/auth/status/')
      user.value = response.data.user
      debugConfig.value = response.data.debug
      // Retourner true seulement si l'utilisateur est connecté
      return !!response.data.user
    } catch (err) {
      user.value = null
      debugConfig.value = { enabled: false, active: false }
      return false
    }
  }
  
  async function ensureCsrfToken() {
    // Récupérer le token CSRF au début de l'application
    try {
      await api.get('/api/auth/csrf-token/')
    } catch (err) {
      console.error('Erreur récupération CSRF token:', err)
    }
  }

  async function ensureAuth() {
    // S'assurer qu'on a le token CSRF
    await ensureCsrfToken()
    
    // Vérifier d'abord si on est connecté
    const isAuth = await checkAuth()
    if (isAuth) return true
    
    // Si pas connecté, vérifier la config debug
    await checkDebugConfig()
    return false
  }
  
  async function updatePreferences(preferences) {
    try {
      await api.put('/api/accounts/preferences/', preferences)
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
    debugConfig,
    isAuthenticated,
    debugEnabled,
    debugActive,
    login,
    logout,
    checkAuth,
    ensureAuth,
    ensureCsrfToken,
    checkDebugConfig,
    toggleDebugMode,
    debugLogin,
    updatePreferences
  }
})