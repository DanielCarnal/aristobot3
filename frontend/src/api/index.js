import axios from 'axios'

// Configuration de base axios
const API_BASE_URL = 'http://localhost:8000'

// Fonction pour récupérer le token CSRF depuis les cookies
function getCsrfToken() {
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrftoken') {
      return value
    }
  }
  return null
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 secondes pour permettre le chargement des symboles
  withCredentials: true, // Pour les sessions Django
  headers: {
    'Content-Type': 'application/json',
  }
})

// Intercepteur pour ajouter le token CSRF aux requêtes
api.interceptors.request.use(
  (config) => {
    // Ajouter le token CSRF pour les requêtes POST/PUT/DELETE/PATCH
    if (['post', 'put', 'delete', 'patch'].includes(config.method)) {
      const csrfToken = getCsrfToken()
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Intercepteur pour gérer les erreurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api
export { API_BASE_URL }