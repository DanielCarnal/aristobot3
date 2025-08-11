import axios from 'axios'

// Configuration de base pour les appels API
const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // Important pour les cookies de session
  headers: {
    'Content-Type': 'application/json',
  }
})

// Intercepteur pour gérer les erreurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirection vers la page de login si non authentifié
      console.error('Non authentifié')
    }
    return Promise.reject(error)
  }
)

export default api