<template>
  <div class="status-bar">
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const activeStrategy = ref(null)
const heartbeatActive = ref(false)
const heartbeatCoherent = ref(false)

const heartbeatStatus = computed(() => heartbeatActive.value ? 'active' : 'inactive')
const coherenceStatus = computed(() => heartbeatCoherent.value ? 'ok' : 'error')
</script>

<style scoped>
.status-bar {
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: 0.75rem 1rem;
  display: flex;
  gap: 2rem;
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
</style>