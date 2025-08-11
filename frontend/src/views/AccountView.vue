<template>
  <div class="account-view">
    <h1>Mon Compte</h1>
    
    <!-- Informations utilisateur -->
    <div class="section">
      <h2>Informations</h2>
      <div class="info-grid">
        <div class="info-item">
          <label>Nom d'utilisateur :</label>
          <span>{{ user?.username }}</span>
          <span v-if="isDev" class="badge dev">MODE DEV</span>
        </div>
        <div class="info-item">
          <label>Email :</label>
          <span>{{ user?.email }}</span>
        </div>
      </div>
    </div>
    
    <!-- Configuration IA -->
    <div class="section">
      <h2>Assistant IA</h2>
      <div class="form-group">
        <label>Fournisseur :</label>
        <div class="switch-group">
          <div class="switch-item">
            <label>OpenRouter</label>
            <label class="switch">
              <input 
                type="checkbox" 
                :checked="preferences.ai_provider === 'openrouter' && preferences.ai_enabled"
                @change="toggleAI('openrouter')"
              >
              <span class="slider"></span>
            </label>
          </div>
          <div class="switch-item">
            <label>Ollama (local)</label>
            <label class="switch">
              <input 
                type="checkbox" 
                :checked="preferences.ai_provider === 'ollama' && preferences.ai_enabled"
                @change="toggleAI('ollama')"
              >
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>
      
      <div v-if="preferences.ai_provider === 'openrouter'" class="form-group">
        <label>Cle API OpenRouter :</label>
        <input 
          type="password" 
          v-model="preferences.ai_api_key"
          placeholder="sk-or-..."
        >
      </div>
      
      <div v-if="preferences.ai_provider === 'ollama'" class="form-group">
        <label>URL Ollama :</label>
        <input 
          type="url" 
          v-model="preferences.ai_endpoint_url"
          placeholder="http://localhost:11434"
        >
      </div>
    </div>
    
    <!-- Preferences d'affichage -->
    <div class="section">
      <h2>Affichage</h2>
      <div class="form-group">
        <label>Theme :</label>
        <select v-model="preferences.theme">
          <option value="dark">Sombre (avec couleurs neon)</option>
          <option value="light">Clair</option>
        </select>
      </div>
      <div class="form-group">
        <label>Fuseau horaire :</label>
        <select v-model="preferences.display_timezone">
          <option value="UTC">UTC</option>
          <option value="local">Fuseau horaire local ({{ localTimezone }})</option>
        </select>
      </div>
    </div>
    
    <!-- Brokers -->
    <div class="section">
      <h2>Exchanges / Brokers</h2>
      <button @click="showAddBroker = true" class="btn btn-primary">
        + Ajouter un Broker
      </button>
      
      <div class="brokers-table">
        <table>
          <thead>
            <tr>
              <th>Exchange</th>
              <th>Description</th>
              <th>Cle API</th>
              <th>Defaut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="broker in brokers" :key="broker.id">
              <td>{{ broker.exchange.toUpperCase() }}</td>
              <td>{{ broker.name }}</td>
              <td>
                <span v-if="broker.last_connection_success" class="status-dot success"></span>
                <span v-else-if="broker.last_connection_test" class="status-dot error"></span>
                <span v-else class="status-dot unknown"></span>
                {{ broker.api_key ? '••••••••••' : 'Non configure' }}
              </td>
              <td>
                <span v-if="broker.is_default" class="badge success">✓</span>
              </td>
              <td>
                <button @click="testBrokerConnection(broker)" class="btn btn-sm btn-test">
                  Test Exchange
                </button>
                <button @click="editBroker(broker)" class="btn btn-sm">
                  Modifier
                </button>
                <button @click="deleteBroker(broker)" class="btn btn-sm btn-danger">
                  Supprimer
                </button>
                <button @click="updateSymbols(broker)" class="btn btn-sm">
                  MAJ Paires
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- Modal Broker -->
    <div v-if="showBrokerModal" class="modal">
      <div class="modal-content">
        <h3>{{ editingBroker ? 'Modifier' : 'Ajouter' }} un Broker</h3>
        
        <div class="form-group">
          <label>Exchange :</label>
          <select v-model="brokerForm.exchange" @change="onExchangeChange">
            <option v-for="exchange in availableExchanges" :key="exchange.id" :value="exchange.id">
              {{ exchange.name }} 
              <span v-if="exchange.has_testnet">📱</span>
              <span v-if="exchange.has_future">🔮</span>
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Nom personnalise :</label>
          <input 
            type="text" 
            v-model="brokerForm.name"
            placeholder="Ex: Binance Principal"
          >
        </div>
        
        <div class="form-group">
          <label>Description :</label>
          <textarea 
            v-model="brokerForm.description"
            placeholder="Notes optionnelles..."
          ></textarea>
        </div>
        
        <div class="form-group">
          <label>Cle API :</label>
          <input 
            type="text" 
            v-model="brokerForm.api_key"
            placeholder="Votre cle API"
          >
        </div>
        
        <div class="form-group">
          <label>Secret API :</label>
          <input 
            type="password" 
            v-model="brokerForm.api_secret"
            placeholder="Votre secret API"
          >
        </div>
        
        <div v-if="selectedExchange?.required_credentials?.includes('api_password')" class="form-group">
          <label>Passphrase API :</label>
          <input 
            type="password" 
            v-model="brokerForm.api_password"
            placeholder="Passphrase API (requis pour certains exchanges)"
          >
        </div>
        
        <div class="form-group">
          <label>Nom du sous-compte :</label>
          <input 
            type="text" 
            v-model="brokerForm.subaccount_name"
            placeholder="Optionnel"
          >
        </div>
        
        <div v-if="selectedExchange?.has_testnet" class="form-group">
          <label>
            <input 
              type="checkbox" 
              v-model="brokerForm.is_testnet"
            >
            Mode Testnet
          </label>
        </div>
        
        <div class="modal-actions">
          <button @click="saveBroker" class="btn btn-primary">
            Sauvegarder
          </button>
          <button @click="closeBrokerModal" class="btn btn-secondary">
            Annuler
          </button>
        </div>
      </div>
    </div>
    
    <!-- Modale Test Exchange -->
    <div v-if="showTestModal" class="modal">
      <div class="modal-content test-modal">
        <h3>Test de connexion - {{ testingBroker?.name }}</h3>
        
        <div v-if="testInProgress" class="test-loading">
          <div class="spinner"></div>
          <p>Test de la connexion en cours...</p>
        </div>
        
        <div v-else-if="testResult" class="test-result">
          <div class="alert" :class="testResult.success ? 'success' : 'error'">
            {{ testResult.message }}
            
            <div v-if="testResult.success && testResult.balance" class="balance-info">
              <h4>Solde du compte:</h4>
              <div v-if="testResult.balance.total_usd_equivalent > 0" class="total-balance">
                Total (équivalent USD): ${{ testResult.balance.total_usd_equivalent }}
              </div>
              <div class="balance-details">
                <div v-for="(amount, symbol) in testResult.balance.total" :key="symbol" class="balance-item">
                  {{ symbol }}: {{ amount }}
                </div>
              </div>
              
              <div v-if="testResult.connection_info" class="connection-info">
                <small>
                  Exchange: {{ testResult.connection_info.exchange }} 
                  <span v-if="testResult.connection_info.testnet">(Testnet)</span>
                  | {{ new Date(testResult.connection_info.timestamp).toLocaleString() }}
                </small>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button @click="closeTestModal" class="btn btn-secondary">
            Fermer
          </button>
        </div>
      </div>
    </div>
    
    <!-- Bouton sauvegarder -->
    <div class="actions">
      <button @click="savePreferences" class="btn btn-primary">
        Sauvegarder les preferences
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const isDev = computed(() => authStore.isDev)

const preferences = ref({
  ai_provider: 'none',
  ai_enabled: false,
  ai_api_key: '',
  ai_endpoint_url: 'http://localhost:11434',
  theme: 'dark',
  display_timezone: 'local'
})

// Detecter le fuseau horaire local
const localTimezone = ref(Intl.DateTimeFormat().resolvedOptions().timeZone)

const brokers = ref([])
const availableExchanges = ref([])
const showBrokerModal = ref(false)
const showTestModal = ref(false)
const testingBroker = ref(null)
const testResult = ref(null)
const testInProgress = ref(false)
const showAddBroker = computed({
  get: () => showBrokerModal.value,
  set: (val) => {
    if (val) {
      editingBroker.value = null
      resetBrokerForm()
    }
    showBrokerModal.value = val
  }
})

const editingBroker = ref(null)
const brokerForm = ref({
  exchange: 'binance',
  name: '',
  description: '',
  api_key: '',
  api_secret: '',
  api_password: '',
  subaccount_name: '',
  is_testnet: false
})

const connectionTest = ref(null)

// Computed pour l'exchange selectionne
const selectedExchange = computed(() => {
  return availableExchanges.value.find(ex => ex.id === brokerForm.value.exchange)
})

onMounted(async () => {
  // Charger les preferences utilisateur
  if (user.value) {
    preferences.value = {
      ai_provider: user.value.ai_provider || 'none',
      ai_enabled: user.value.ai_enabled || false,
      ai_api_key: '',
      ai_endpoint_url: user.value.ai_endpoint_url || 'http://localhost:11434',
      theme: user.value.theme || 'dark',
      display_timezone: user.value.display_timezone || 'local'
    }
    
    // Appliquer le theme
    document.documentElement.setAttribute('data-theme', preferences.value.theme)
  }
  
  // Charger les brokers et exchanges
  await loadBrokers()
  await loadExchanges()
})

async function loadExchanges() {
  try {
    const response = await api.get('/api/brokers/exchanges/')
    availableExchanges.value = response.data.exchanges || []
  } catch (error) {
    console.error('Erreur chargement exchanges:', error)
    // Fallback avec les exchanges de base
    availableExchanges.value = [
      { id: 'binance', name: 'Binance', required_credentials: ['api_key', 'api_secret'], has_testnet: true },
      { id: 'kucoin', name: 'KuCoin', required_credentials: ['api_key', 'api_secret'], has_testnet: true },
      { id: 'bitget', name: 'Bitget', required_credentials: ['api_key', 'api_secret'], has_testnet: true },
      { id: 'okx', name: 'OKX', required_credentials: ['api_key', 'api_secret', 'api_password'], has_testnet: true },
      { id: 'bybit', name: 'Bybit', required_credentials: ['api_key', 'api_secret'], has_testnet: true }
    ]
  }
}

async function loadBrokers() {
  try {
    const response = await api.get('/api/brokers/')
    brokers.value = response.data.results || response.data
  } catch (error) {
    console.error('Erreur chargement brokers:', error)
  }
}

async function savePreferences() {
  try {
    await authStore.updatePreferences(preferences.value)
    alert('Preferences sauvegardees')
  } catch (error) {
    alert('Erreur lors de la sauvegarde')
  }
}

function editBroker(broker) {
  editingBroker.value = broker
  brokerForm.value = {
    exchange: broker.exchange,
    name: broker.name,
    description: broker.description || '',
    api_key: '',  // Ne pas afficher la cle existante pour securite
    api_secret: '',  // Ne pas afficher le secret existant
    api_password: broker.api_password ? '••••••••' : '',
    subaccount_name: broker.subaccount_name || '',
    is_testnet: broker.is_testnet || false
  }
  showBrokerModal.value = true
}

async function deleteBroker(broker) {
  if (confirm(`Supprimer ${broker.name} ?`)) {
    try {
      await api.delete(`/api/brokers/${broker.id}/`)
      await loadBrokers()
    } catch (error) {
      alert('Erreur lors de la suppression')
    }
  }
}

async function updateSymbols(broker) {
  try {
    const response = await api.post(`/api/brokers/${broker.id}/update_symbols/`)
    alert(response.data.message)
  } catch (error) {
    alert('Erreur lors de la mise a jour des symboles')
  }
}

async function testBrokerConnection(broker) {
  testingBroker.value = broker
  testResult.value = null
  testInProgress.value = true
  showTestModal.value = true
  
  try {
    const response = await api.post(`/api/brokers/${broker.id}/test_connection/`)
    testResult.value = response.data
  } catch (error) {
    testResult.value = {
      success: false,
      message: error.response?.data?.message || 'Erreur de connexion'
    }
  } finally {
    testInProgress.value = false
  }
}

function closeTestModal() {
  showTestModal.value = false
  testingBroker.value = null
  testResult.value = null
  testInProgress.value = false
}

async function testConnection() {
  connectionTest.value = null
  
  // Validation temps reel des cles
  if (!brokerForm.value.api_key || !brokerForm.value.api_secret) {
    connectionTest.value = {
      success: false,
      message: 'Veuillez entrer les cles API'
    }
    return
  }
  
  // Sauvegarder d'abord si nouveau broker
  let brokerId = editingBroker.value?.id
  
  if (!brokerId) {
    try {
      const response = await api.post('/api/brokers/', brokerForm.value)
      brokerId = response.data.id
    } catch (error) {
      connectionTest.value = {
        success: false,
        message: 'Erreur lors de la creation du broker'
      }
      return
    }
  }
  
  try {
    const response = await api.post(`/api/brokers/${brokerId}/test_connection/`)
    connectionTest.value = response.data
  } catch (error) {
    connectionTest.value = {
      success: false,
      message: error.response?.data?.message || 'Erreur de connexion'
    }
  }
}

async function saveBroker() {
  try {
    // Ne pas envoyer les champs vides ou masques lors de l'edition
    const dataToSend = { ...brokerForm.value }
    if (editingBroker.value) {
      // En mode edition, ne pas envoyer les cles si elles sont masquees
      if (dataToSend.api_key === '') delete dataToSend.api_key
      if (dataToSend.api_secret === '') delete dataToSend.api_secret
      if (dataToSend.api_password === '••••••••') delete dataToSend.api_password
      
      await api.patch(`/api/brokers/${editingBroker.value.id}/`, dataToSend)
    } else {
      await api.post('/api/brokers/', dataToSend)
    }
    await loadBrokers()
    closeBrokerModal()
  } catch (error) {
    alert('Erreur lors de la sauvegarde')
  }
}

function onExchangeChange() {
  // Reset les champs optionnels lors du changement d'exchange
  if (!selectedExchange.value?.required_credentials?.includes('api_password')) {
    brokerForm.value.api_password = ''
  }
  if (!selectedExchange.value?.has_testnet) {
    brokerForm.value.is_testnet = false
  }
}

function toggleAI(provider) {
  if (preferences.value.ai_provider === provider && preferences.value.ai_enabled) {
    // Desactiver
    preferences.value.ai_enabled = false
    preferences.value.ai_provider = 'none'
  } else {
    // Activer ce provider et desactiver l'autre
    preferences.value.ai_enabled = true
    preferences.value.ai_provider = provider
  }
}

function closeBrokerModal() {
  showBrokerModal.value = false
  editingBroker.value = null
  resetBrokerForm()
  connectionTest.value = null
}

function resetBrokerForm() {
  brokerForm.value = {
    exchange: 'binance',
    name: '',
    description: '',
    api_key: '',
    api_secret: '',
    api_password: '',
    subaccount_name: '',
    is_testnet: false
  }
}
</script>

<style scoped>
/* Styles adaptes au theme dark avec couleurs neon */
.account-view {
  padding: 2rem;
}

.section {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--color-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  color: var(--color-text);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.1);
}

.switch-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.switch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--color-background);
  border-radius: 0.25rem;
}

.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--color-border);
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--color-primary);
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 0.5rem;
}

.status-dot.success {
  background-color: var(--color-success);
}

.status-dot.error {
  background-color: var(--color-danger);
}

.status-dot.unknown {
  background-color: var(--color-border);
}

.brokers-table {
  margin-top: 1rem;
  overflow-x: auto;
}

.brokers-table table {
  width: 100%;
  border-collapse: collapse;
}

.brokers-table th,
.brokers-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.brokers-table th {
  color: var(--color-primary);
  font-weight: 600;
}

.btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s;
}

.btn:hover {
  background: var(--color-background);
  border-color: var(--color-primary);
}

.btn-primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-background);
}

.btn-primary:hover {
  background: var(--color-primary-dark);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.btn-danger {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: white;
}

.btn-danger:hover {
  background: var(--color-danger-dark);
  box-shadow: 0 0 10px rgba(255, 0, 85, 0.5);
}

.btn-test {
  background: var(--color-success);
  border-color: var(--color-success);
  color: var(--color-background);
}

.btn-test:hover {
  background: var(--color-success);
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge.dev {
  background: var(--color-warning);
  color: var(--color-background);
}

.badge.success {
  color: var(--color-success);
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 2rem;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.alert {
  padding: 1rem;
  border-radius: 0.25rem;
  margin-top: 1rem;
}

.alert.success {
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid var(--color-success);
  color: var(--color-success);
}

.alert.error {
  background: rgba(255, 0, 85, 0.1);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
}

.balance-info {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.balance-info h4 {
  margin: 0 0 0.5rem 0;
  color: var(--color-primary);
}

.total-balance {
  font-size: 1.1em;
  font-weight: 600;
  color: var(--color-success);
  margin-bottom: 0.5rem;
}

.balance-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.5rem;
}

.balance-item {
  background: var(--color-background);
  padding: 0.5rem;
  border-radius: 0.25rem;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.test-modal {
  max-width: 500px;
}

.test-loading {
  text-align: center;
  padding: 2rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-border);
  border-top: 4px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.connection-info {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  text-align: center;
}

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 2rem;
}
</style>
