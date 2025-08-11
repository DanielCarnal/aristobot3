<template>
  <div class="status-bar">
    <div class="status-left">
      <div class="status-item">
        <span class="label">Stratégie Live:</span>
        <span class="value">{{ activeStrategy || 'Aucune' }}</span>
      </div>
      
      <div class="status-item">
        <span class="label">Heartbeat:</span>
        <span :class="['value', 'status', heartbeatStatus]">
          {{ heartbeatActive ? 'Actif' : 'Inactif' }}
        </span>
      </div>
      
      <div class="status-item">
        <span class="label">Cohérence:</span>
        <span :class="['value', 'status', coherenceStatus]">
          {{ heartbeatCoherent ? 'OK' : 'NOK' }}
        </span>
      </div>
      
      <!-- Affichage debug actif si DEBUG=ON -->
      <div v-if="authStore.debugActive" class="status-item">
        <span class="value debug-active">Debug actif</span>
      </div>
    </div>
    
    <div class="status-right">
      <div class="status-item">
        <span class="label">Utilisateur:</span>
        <span class="value">{{ authStore.user?.username }}</span>
        <button @click="logout" class="logout-btn">
          Déconnexion
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const activeStrategy = ref(null)
const heartbeatActive = ref(false)
const heartbeatCoherent = ref(false)

const heartbeatStatus = computed(() => heartbeatActive.value ? 'active' : 'inactive')
const coherenceStatus = computed(() => heartbeatCoherent.value ? 'ok' : 'error')

async function logout() {
  try {
    await authStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('Erreur de déconnexion:', error)
    router.push('/login')
  }
}
</script>

<style scoped>
.status-bar {
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-left {
  display: flex;
  gap: 2rem;
}

.status-right {
  display: flex;
  gap: 1rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.label {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

.value {
  color: var(--color-text);
  font-weight: 500;
}

.status.active {
  color: var(--color-success);
}

.status.inactive {
  color: var(--color-danger);
}

.status.ok {
  color: var(--color-success);
}

.status.error {
  color: var(--color-danger);
}

.logout-btn {
  margin-left: 0.75rem;
  padding: 0.25rem 0.75rem;
  background: var(--color-danger);
  color: white;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background: var(--color-danger-dark);
  transform: translateY(-1px);
}

.debug-active {
  color: var(--color-warning) !important;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  background: rgba(255, 184, 0, 0.1);
  border: 1px solid var(--color-warning);
  border-radius: 0.25rem;
}
</style>