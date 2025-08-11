<template>
  <div class="login-view">
    <div class="login-container">
      <h1>Aristobot3</h1>
      <p class="subtitle">Connexion</p>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">Nom d'utilisateur</label>
          <input 
            id="username"
            type="text" 
            v-model="username"
            placeholder="Entrez votre nom d'utilisateur"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="password">Mot de passe</label>
          <input 
            id="password"
            type="password" 
            v-model="password"
            placeholder="Entrez votre mot de passe"
            required
          />
        </div>
        
        <button type="submit" :disabled="isLoading" class="login-btn">
          {{ isLoading ? 'Connexion...' : 'Se connecter' }}
        </button>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <!-- Section Debug (si DEBUG_ARISTOBOT activé) -->
        <div v-if="authStore.debugEnabled" class="debug-section">
          <div class="debug-header">
            <h3>Mode Debug</h3>
            <button 
              type="button" 
              @click="toggleDebug" 
              class="debug-toggle"
              :class="{ active: authStore.debugActive }"
            >
              {{ authStore.debugActive ? 'ON' : 'OFF' }}
            </button>
          </div>
          
        </div>
        
        <div class="dev-hint">
          <p>Utilisateur par défaut :</p>
          <p><strong>dac</strong> / <strong>aristobot</strong></p>
          <p><strong>dev</strong> / <strong>dev123</strong></p>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const isLoading = ref(false)
const error = ref('')

onMounted(async () => {
  // Charger la config debug au démarrage
  await authStore.checkDebugConfig()
})

async function handleLogin() {
  isLoading.value = true
  error.value = ''
  
  try {
    const success = await authStore.login(username.value, password.value)
    if (success) {
      router.push('/')
    } else {
      error.value = authStore.error || 'Erreur de connexion'
    }
  } catch (err) {
    error.value = 'Erreur de connexion'
  } finally {
    isLoading.value = false
  }
}

async function toggleDebug() {
  try {
    await authStore.toggleDebugMode()
    
    // Si le mode debug vient d'être activé, login automatique avec 'dev'
    if (authStore.debugActive) {
      isLoading.value = true
      error.value = ''
      
      try {
        const success = await authStore.debugLogin()
        if (success) {
          router.push('/')
        } else {
          error.value = authStore.error || 'Debug login automatique échoué'
        }
      } catch (debugErr) {
        error.value = 'Debug login automatique échoué'
      } finally {
        isLoading.value = false
      }
    }
  } catch (err) {
    error.value = authStore.error || 'Erreur toggle debug'
  }
}
</script>

<style scoped>
.login-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%);
  padding: 1rem;
}

.login-container {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 1rem;
  padding: 2.5rem;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

h1 {
  color: var(--color-primary);
  font-size: 2rem;
  font-weight: 700;
  text-align: center;
  margin-bottom: 0.5rem;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.subtitle {
  color: var(--color-text-secondary);
  text-align: center;
  margin-bottom: 2rem;
  font-size: 1.1rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: var(--color-primary);
  font-weight: 500;
  font-size: 0.9rem;
}

.form-group input {
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-background);
  color: var(--color-text);
  font-size: 1rem;
  transition: all 0.2s ease;
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

.login-btn {
  background: linear-gradient(135deg, var(--color-primary), #0099CC);
  color: var(--color-background);
  border: none;
  padding: 0.875rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 0.5rem;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 212, 255, 0.3);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  background: rgba(255, 0, 85, 0.1);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  text-align: center;
}

.dev-hint {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 0.85rem;
}

.dev-hint strong {
  color: var(--color-primary);
  font-family: 'Courier New', monospace;
}

/* Styles Debug Section */
.debug-section {
  margin-top: 1.5rem;
  padding: 1rem;
  border: 1px solid var(--color-warning);
  border-radius: 0.5rem;
  background: rgba(255, 193, 7, 0.05);
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.debug-header h3 {
  color: var(--color-warning);
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0;
}

.debug-toggle {
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--color-warning);
  border-radius: 0.25rem;
  background: transparent;
  color: var(--color-warning);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 50px;
}

.debug-toggle:hover {
  background: rgba(255, 193, 7, 0.1);
}

.debug-toggle.active {
  background: var(--color-warning);
  color: var(--color-background);
}

</style>