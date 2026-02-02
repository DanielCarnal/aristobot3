<template>
  <div class="webhooks-view">
    <!-- Header -->
    <div class="header-section">
      <h1>Webhooks TradingView</h1>
      <div class="broker-selector">
        <label>Filtrer par broker :</label>
        <select v-model="selectedBrokerId">
          <option value="">Tous les brokers</option>
          <option v-for="broker in brokers" :key="broker.id" :value="broker.id">
            {{ broker.name }} ({{ broker.exchange }})
          </option>
        </select>
      </div>
    </div>

    <!-- Message d'erreur global -->
    <div v-if="error" class="error-message">
      {{ error }}
      <button @click="clearError" class="error-close">&times;</button>
    </div>

    <!-- Statistiques -->
    <div class="stats-section">
      <div class="stat-card">
        <h3>Total Webhooks</h3>
        <div class="stat-value">{{ stats.total_webhooks || 0 }}</div>
        <div class="stat-label">dernières 24h</div>
      </div>

      <div class="stat-card">
        <h3>Taux de Succès</h3>
        <div class="stat-value success">{{ stats.success_rate || 0 }}%</div>
        <div class="stat-label">{{ stats.processed || 0 }} traités</div>
      </div>

      <div class="stat-card">
        <h3>Erreurs</h3>
        <div class="stat-value" :class="stats.errors > 0 ? 'error' : ''">{{ stats.errors || 0 }}</div>
        <div class="stat-label">échecs</div>
      </div>

      <div class="stat-card">
        <h3>Positions Ouvertes</h3>
        <div class="stat-value">{{ positionsSummary.open_positions_count || 0 }}</div>
        <div class="stat-label">P&L: ${{ positionsSummary.total_unrealized_pnl?.toFixed(2) || '0.00' }}</div>
      </div>
    </div>

    <!-- Contenu principal - 2 sections -->
    <div class="main-content">

      <!-- Section Webhooks Récents -->
      <div class="webhooks-section">
        <div class="section-card">
          <div class="section-header">
            <h2>Webhooks Récents</h2>
            <div class="period-selector">
              <button
                v-for="period in ['24h', '7d', '30d']"
                :key="period"
                :class="['period-btn', { active: selectedPeriod === period }]"
                @click="selectedPeriod = period"
              >
                {{ period }}
              </button>
            </div>
          </div>

          <div v-if="webhooksLoading" class="loading">Chargement...</div>
          <div v-else class="webhooks-table-container">
            <table class="webhooks-table">
              <thead>
                <tr>
                  <th>Date/Heure</th>
                  <th>Exchange</th>
                  <th>Symbole</th>
                  <th>Action</th>
                  <th>Prix</th>
                  <th>%</th>
                  <th>Status</th>
                  <th>Order ID</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="recentWebhooks.length === 0">
                  <td colspan="8" class="no-data">Aucun webhook reçu</td>
                </tr>
                <tr
                  v-for="webhook in recentWebhooks"
                  :key="webhook.id"
                  :class="[getWebhookRowClass(webhook), { 'new-webhook': webhook._isNew }]"
                >
                  <td>{{ formatDateTime(webhook.received_at) }}</td>
                  <td>{{ webhook.exchange_name }}</td>
                  <td class="symbol">{{ webhook.symbol }}</td>
                  <td>
                    <span :class="['action-badge', getActionClass(webhook.action)]">
                      {{ webhook.action }}
                    </span>
                  </td>
                  <td>{{ webhook.prix ? `$${webhook.prix}` : '-' }}</td>
                  <td>{{ webhook.pour_cent }}%</td>
                  <td>
                    <span :class="['status-badge', webhook.status]">
                      {{ getStatusLabel(webhook.status) }}
                    </span>
                  </td>
                  <td class="order-id">{{ webhook.order_id || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Section Positions Ouvertes -->
      <div class="positions-section">
        <div class="section-card">
          <h2>Positions Ouvertes</h2>

          <div v-if="positionsLoading" class="loading">Chargement...</div>
          <div v-else class="positions-table-container">
            <table class="positions-table">
              <thead>
                <tr>
                  <th>Symbole</th>
                  <th>Side</th>
                  <th>Quantité</th>
                  <th>Prix Entrée</th>
                  <th>Prix Actuel</th>
                  <th>SL</th>
                  <th>TP</th>
                  <th>P&L</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="openPositions.length === 0">
                  <td colspan="8" class="no-data">Aucune position ouverte</td>
                </tr>
                <tr v-for="position in openPositions" :key="position.id">
                  <td class="symbol">{{ position.symbol }}</td>
                  <td>
                    <span :class="['side-badge', position.side]">
                      {{ position.side.toUpperCase() }}
                    </span>
                  </td>
                  <td>{{ position.quantity }}</td>
                  <td>${{ position.entry_price }}</td>
                  <td>${{ position.current_price || '-' }}</td>
                  <td>${{ position.stop_loss_price || '-' }}</td>
                  <td>${{ position.take_profit_price || '-' }}</td>
                  <td :class="['pnl', position.unrealized_pnl >= 0 ? 'positive' : 'negative']">
                    ${{ position.unrealized_pnl?.toFixed(2) || '0.00' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

export default {
  name: 'WebhooksView',
  setup() {
    const authStore = useAuthStore()

    // State
    const error = ref('')
    const brokers = ref([])
    const selectedBrokerId = ref('')
    const selectedPeriod = ref('24h')

    // Stats
    const stats = ref({
      total_webhooks: 0,
      success_rate: 0,
      processed: 0,
      errors: 0,
    })

    // Webhooks
    const recentWebhooks = ref([])
    const webhooksLoading = ref(false)
    const lastWebhookId = ref(null) // Pour polling incremental

    // Positions
    const openPositions = ref([])
    const positionsSummary = ref({
      open_positions_count: 0,
      total_unrealized_pnl: 0,
    })
    const positionsLoading = ref(false)

    // API instance
    const api = axios.create({
      baseURL: 'http://localhost:8000',
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Methods
    const clearError = () => {
      error.value = ''
    }

    const loadBrokers = async () => {
      try {
        const response = await api.get('/api/brokers/')
        brokers.value = response.data.results || response.data
      } catch (err) {
        error.value = 'Erreur chargement brokers: ' + (err.response?.data?.detail || err.message)
      }
    }

    const loadStats = async () => {
      try {
        const params = { period: selectedPeriod.value }
        if (selectedBrokerId.value) {
          params.broker_id = selectedBrokerId.value
        }

        const response = await api.get('/api/webhooks/stats/', { params })
        stats.value = response.data
      } catch (err) {
        error.value = 'Erreur chargement stats: ' + (err.response?.data?.detail || err.message)
      }
    }

    const loadRecentWebhooks = async () => {
      webhooksLoading.value = true
      try {
        const params = {}
        if (selectedBrokerId.value) {
          params.broker = selectedBrokerId.value
        }

        const response = await api.get('/api/webhooks/recent/', { params })
        recentWebhooks.value = response.data

        // Stocker le dernier ID pour polling incremental
        if (response.data.length > 0) {
          lastWebhookId.value = response.data[0].id
        }
      } catch (err) {
        error.value = 'Erreur chargement webhooks: ' + (err.response?.data?.detail || err.message)
      } finally {
        webhooksLoading.value = false
      }
    }

    const loadNewWebhooks = async () => {
      // Polling incremental - charge seulement les nouveaux webhooks
      try {
        const params = {}
        if (selectedBrokerId.value) {
          params.broker = selectedBrokerId.value
        }

        const response = await api.get('/api/webhooks/recent/', { params })
        const newWebhooks = response.data

        if (newWebhooks.length === 0) return

        // Filtrer seulement les webhooks plus recents que le dernier connu
        const newerWebhooks = lastWebhookId.value
          ? newWebhooks.filter(w => w.id > lastWebhookId.value)
          : newWebhooks

        if (newerWebhooks.length > 0) {
          // Ajouter au debut (comme Heartbeat)
          newerWebhooks.reverse().forEach(webhook => {
            // Marquer comme nouveau pour animation
            webhook._isNew = true
            recentWebhooks.value.unshift(webhook)

            // Retirer le marqueur apres 3 secondes
            setTimeout(() => {
              webhook._isNew = false
            }, 3000)
          })

          // Mettre a jour le dernier ID
          lastWebhookId.value = newerWebhooks[newerWebhooks.length - 1].id

          // Limiter a 100 webhooks max
          if (recentWebhooks.value.length > 100) {
            recentWebhooks.value = recentWebhooks.value.slice(0, 100)
          }
        }
      } catch (err) {
        // Erreur silencieuse pour polling - ne pas polluer l'UI
        console.error('Erreur polling webhooks:', err)
      }
    }

    const loadPositions = async () => {
      positionsLoading.value = true
      try {
        const params = {}
        if (selectedBrokerId.value) {
          params.broker = selectedBrokerId.value
        }

        // Charger positions ouvertes
        const positionsResponse = await api.get('/api/webhook-states/open/', { params })
        openPositions.value = positionsResponse.data.results || positionsResponse.data

        // Charger résumé
        const summaryResponse = await api.get('/api/webhook-states/summary/', { params })
        positionsSummary.value = summaryResponse.data
      } catch (err) {
        error.value = 'Erreur chargement positions: ' + (err.response?.data?.detail || err.message)
      } finally {
        positionsLoading.value = false
      }
    }

    const loadAllData = async () => {
      await Promise.all([
        loadStats(),
        loadRecentWebhooks(),
        loadPositions()
      ])
    }

    const refreshData = async () => {
      // Refresh incremental - seulement les nouveaux webhooks et stats/positions
      await Promise.all([
        loadStats(),
        loadNewWebhooks(),  // Incremental - pas de flash!
        loadPositions()
      ])
    }

    const formatDateTime = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }

    const getWebhookRowClass = (webhook) => {
      if (webhook.status === 'error') return 'row-error'
      if (webhook.status === 'miss') return 'row-miss'
      if (webhook.action === 'PING') return 'row-ping'
      return ''
    }

    const getActionClass = (action) => {
      const map = {
        'BuyMarket': 'buy',
        'BuyLimit': 'buy',
        'SellMarket': 'sell',
        'SellLimit': 'sell',
        'MAJ': 'update',
        'PING': 'ping',
        'MISS': 'miss'
      }
      return map[action] || ''
    }

    const getStatusLabel = (status) => {
      const map = {
        'received': 'Reçu',
        'processing': 'En cours',
        'processed': 'Traité',
        'error': 'Erreur',
        'miss': 'Manquant'
      }
      return map[status] || status
    }

    // Watchers
    watch([selectedBrokerId, selectedPeriod], () => {
      // Reset le lastWebhookId car on change de filtre
      lastWebhookId.value = null
      loadAllData()
    })

    // Lifecycle
    onMounted(async () => {
      if (!authStore.isAuthenticated) {
        error.value = 'Vous devez être connecté'
        return
      }

      await loadBrokers()
      await loadAllData()

      // Auto-refresh incremental toutes les 5 secondes (sans flash!)
      setInterval(refreshData, 5000)
    })

    return {
      error,
      clearError,
      brokers,
      selectedBrokerId,
      selectedPeriod,
      stats,
      recentWebhooks,
      webhooksLoading,
      openPositions,
      positionsSummary,
      positionsLoading,
      formatDateTime,
      getWebhookRowClass,
      getActionClass,
      getStatusLabel,
    }
  }
}
</script>

<style scoped>
.webhooks-view {
  padding: 1.5rem;
  max-width: 1800px;
  margin: 0 auto;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.broker-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.broker-selector label {
  font-weight: 500;
  color: #00D4FF;
}

.broker-selector select {
  background: #1a1a2e;
  border: 1px solid #00D4FF;
  color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

/* Stats Section */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: #1a1a2e;
  border: 1px solid #00D4FF;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.stat-card h3 {
  font-size: 0.9rem;
  color: #00D4FF;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #fff;
  margin-bottom: 0.25rem;
}

.stat-value.success {
  color: #00FF88;
}

.stat-value.error {
  color: #FF0055;
}

.stat-label {
  font-size: 0.8rem;
  color: #999;
}

/* Main Content */
.main-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.section-card {
  background: #1a1a2e;
  border: 1px solid #00D4FF;
  border-radius: 8px;
  padding: 1.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.period-selector {
  display: flex;
  gap: 0.5rem;
}

.period-btn {
  background: #16213e;
  border: 1px solid #00D4FF;
  color: #00D4FF;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.period-btn:hover {
  background: #00D4FF;
  color: #0f1729;
}

.period-btn.active {
  background: #00D4FF;
  color: #0f1729;
}

/* Tables */
.webhooks-table-container,
.positions-table-container {
  overflow-x: auto;
  max-height: 600px;
  overflow-y: auto;
}

.webhooks-table,
.positions-table {
  width: 100%;
  border-collapse: collapse;
}

.webhooks-table th,
.positions-table th {
  background: #16213e;
  color: #00D4FF;
  padding: 0.75rem;
  text-align: left;
  font-size: 0.85rem;
  position: sticky;
  top: 0;
  z-index: 10;
}

.webhooks-table td,
.positions-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #2a2a40;
  font-size: 0.85rem;
}

.symbol {
  font-weight: 600;
  color: #00D4FF;
}

.order-id {
  font-family: monospace;
  font-size: 0.75rem;
  color: #999;
}

/* Badges */
.action-badge,
.status-badge,
.side-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.action-badge.buy {
  background: rgba(0, 255, 136, 0.2);
  color: #00FF88;
}

.action-badge.sell {
  background: rgba(255, 0, 85, 0.2);
  color: #FF0055;
}

.action-badge.update {
  background: rgba(0, 212, 255, 0.2);
  color: #00D4FF;
}

.action-badge.ping {
  background: rgba(153, 153, 153, 0.2);
  color: #999;
}

.status-badge.processed {
  background: rgba(0, 255, 136, 0.2);
  color: #00FF88;
}

.status-badge.error,
.status-badge.miss {
  background: rgba(255, 0, 85, 0.2);
  color: #FF0055;
}

.status-badge.processing {
  background: rgba(255, 204, 0, 0.2);
  color: #FFCC00;
}

.side-badge.buy {
  background: rgba(0, 255, 136, 0.2);
  color: #00FF88;
}

.side-badge.sell {
  background: rgba(255, 0, 85, 0.2);
  color: #FF0055;
}

/* Row colors */
.row-error {
  background: rgba(255, 0, 85, 0.1);
}

.row-miss {
  background: rgba(255, 204, 0, 0.1);
}

.row-ping {
  opacity: 0.6;
}

/* Nouveau webhook - animation highlight */
.new-webhook {
  animation: highlight-new 3s ease-out;
  border-left: 3px solid #00FF88 !important;
}

@keyframes highlight-new {
  0% {
    background: rgba(0, 255, 136, 0.3);
  }
  100% {
    background: transparent;
  }
}

/* P&L */
.pnl.positive {
  color: #00FF88;
  font-weight: 600;
}

.pnl.negative {
  color: #FF0055;
  font-weight: 600;
}

/* Messages */
.error-message {
  background: rgba(255, 0, 85, 0.2);
  border: 1px solid #FF0055;
  color: #FF0055;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-close {
  background: none;
  border: none;
  color: #FF0055;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #00D4FF;
  font-style: italic;
}

.no-data {
  text-align: center;
  padding: 2rem;
  color: #999;
  font-style: italic;
}

/* Responsive */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}
</style>
