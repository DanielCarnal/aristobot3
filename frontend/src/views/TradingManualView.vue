<template>
  <div class="trading-manual">
    <!-- Header avec selection broker -->
    <div class="header-section">
      <h1>Trading Manuel</h1>
      <div class="broker-selector">
        <label>Broker :</label>
        <select v-model="selectedBroker" @change="onBrokerChange">
          <option value="">Sélectionner un broker</option>
          <option v-for="broker in brokers" :key="broker.id" :value="broker.id">
            {{ broker.name }} ({{ broker.exchange }})
          </option>
        </select>
      </div>
    </div>

    <!-- Message d'erreur global -->
    <div v-if="error" class="error-message">
      {{ error }}
      <button @click="clearError" class="error-close" title="Fermer">&times;</button>
    </div>

    <!-- Contenu principal - 3 colonnes -->
    <div v-if="selectedBroker" class="main-content">
      
      <!-- Colonne 1: Portfolio -->
      <div class="portfolio-column">
        <div class="section-card">
          <h2>Portfolio</h2>
          <div v-if="portfolioLoading" class="loading">Chargement...</div>
          <div v-else-if="portfolio">
            <div class="portfolio-summary">
              <p><strong>Valeur totale:</strong> ${{ portfolio.total_value_usd }}</p>
            </div>
            
            <h3>Balance</h3>
            <div class="balance-list">
              <div v-for="(amount, asset) in portfolio.balance.total" :key="asset" class="balance-item">
                <span class="asset">{{ asset }}:</span>
                <span class="amount">{{ parseFloat(amount).toFixed(8) }}</span>
              </div>
            </div>
            
            <h3 v-if="Object.keys(portfolio.positions).length > 0">Positions ouvertes</h3>
            <div class="positions-list">
              <div v-for="(amount, asset) in portfolio.positions" :key="asset" class="position-item">
                <span class="asset">{{ asset }}:</span>
                <span class="amount">{{ parseFloat(amount).toFixed(8) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Capacités exchange -->
        <div class="section-card">
          <h2>Capacités Exchange</h2>
          <div v-if="exchangeInfoLoading" class="loading">Chargement...</div>
          <div v-else-if="exchangeInfo">
            <p><strong>{{ exchangeInfo.name }}</strong> ({{ exchangeInfo.exchange }})</p>
            <div class="capabilities-grid">
              <!-- Capacités principales -->
              <div class="capability-section">
                <h4>Types de Trading</h4>
                <div class="capability-item">
                  <span class="capability-label">Spot Trading:</span>
                  <span :class="exchangeInfo.spot_trading ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.spot_trading ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item">
                  <span class="capability-label">Futures:</span>
                  <span :class="exchangeInfo.futures_trading ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.futures_trading ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item">
                  <span class="capability-label">Margin:</span>
                  <span :class="exchangeInfo.margin_trading ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.margin_trading ? 'Oui' : 'Non' }}
                  </span>
                </div>
              </div>

              <!-- Types d'ordres -->
              <div class="capability-section">
                <h4>Types d'Ordres</h4>
                <div class="capability-item clickable" @click="openOrderTypeModal('market')">
                  <span class="capability-label">Market:</span>
                  <span :class="exchangeInfo.market_orders ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.market_orders ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item clickable" @click="openOrderTypeModal('limit')">
                  <span class="capability-label">Limite:</span>
                  <span :class="exchangeInfo.limit_orders ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.limit_orders ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item clickable" @click="openOrderTypeModal('stop')">
                  <span class="capability-label">Stop:</span>
                  <span :class="exchangeInfo.stop_orders ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.stop_orders ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item clickable" @click="openOrderTypeModal('stop_limit')">
                  <span class="capability-label">Stop Limite:</span>
                  <span :class="exchangeInfo.stop_limit_orders ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.stop_limit_orders ? 'Oui' : 'Non' }}
                  </span>
                </div>
              </div>

              <!-- Données de marché -->
              <div class="capability-section">
                <h4>Données de Marché</h4>
                <div class="capability-item">
                  <span class="capability-label">Balance:</span>
                  <span :class="exchangeInfo.fetch_balance ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.fetch_balance ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item">
                  <span class="capability-label">Prix (Ticker):</span>
                  <span :class="exchangeInfo.fetch_ticker ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.fetch_ticker ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item">
                  <span class="capability-label">Order Book:</span>
                  <span :class="exchangeInfo.fetch_order_book ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.fetch_order_book ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item">
                  <span class="capability-label">OHLCV:</span>
                  <span :class="exchangeInfo.fetch_ohlcv ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.fetch_ohlcv ? 'Oui' : 'Non' }}
                  </span>
                </div>
              </div>

              <!-- Gestion des ordres -->
              <div class="capability-section">
                <h4>Gestion des Ordres</h4>
                <div class="capability-item">
                  <span class="capability-label">Lister ordres:</span>
                  <span :class="exchangeInfo.fetch_orders ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.fetch_orders ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item">
                  <span class="capability-label">Ordres ouverts:</span>
                  <span :class="exchangeInfo.fetch_open_orders ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.fetch_open_orders ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item">
                  <span class="capability-label">Annuler ordre:</span>
                  <span :class="exchangeInfo.cancel_order ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.cancel_order ? 'Oui' : 'Non' }}
                  </span>
                </div>
              </div>

              <!-- Fonctionnalités avancées -->
              <div class="capability-section">
                <h4>Fonctionnalités</h4>
                <div class="capability-item">
                  <span class="capability-label">WebSocket:</span>
                  <span :class="exchangeInfo.websocket ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.websocket ? 'Oui' : 'Non' }}
                  </span>
                </div>
                <div class="capability-item">
                  <span class="capability-label">Sandbox:</span>
                  <span :class="exchangeInfo.sandbox ? 'enabled' : 'disabled'">
                    {{ exchangeInfo.sandbox ? 'Oui' : 'Non' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Colonne 2: Symboles et filtres -->
      <div class="symbols-column">
        <div class="section-card">
          <h2>Symboles disponibles</h2>
          
          <!-- Filtres -->
          <div class="filters">
            <div class="filter-checkboxes">
              <label>
                <input type="checkbox" v-model="filters.usdt" @change="loadSymbols">
                USDT
              </label>
              <label>
                <input type="checkbox" v-model="filters.usdc" @change="loadSymbols">
                USDC
              </label>
              <label>
                <input type="checkbox" v-model="filters.all" @change="loadSymbols">
                Tous
              </label>
            </div>
            <div class="search-box">
              <input 
                type="text" 
                v-model="filters.search" 
                @input="debouncedSearch"
                placeholder="Rechercher un symbole..."
              >
              <button 
                v-if="filters.search" 
                @click="clearSearch" 
                class="clear-search-btn"
                title="Effacer la recherche"
              >
                ×
              </button>
            </div>
          </div>

          <!-- Liste symboles avec virtual scroll -->
          <div class="symbols-container">
            <div v-if="symbolsLoading" class="loading">Chargement symboles...</div>
            <div v-else class="symbols-list">
              <div 
                v-for="symbol in symbols" 
                :key="symbol"
                :class="['symbol-item', { active: selectedSymbol === symbol }]"
                @click="selectSymbol(symbol)"
              >
                {{ symbol }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Colonne 3: Trading -->
      <div class="trading-column">
        <div class="section-card">
          <h2>Passer un ordre</h2>
          
          <div v-if="!selectedSymbol" class="no-symbol">
            Sélectionnez un symbole pour trader
          </div>
          
          <div v-else class="trading-form">
            <div class="symbol-info">
              <h3>{{ selectedSymbol }}</h3>
              <div class="price-info">
                <div v-if="priceTimestamp && currentPrice && !priceLoading" class="price-display">
                  <p class="current-price">
                    ${{ currentPrice }}
                  </p>
                  <p class="timestamp">
                    {{ formatTimestamp(priceTimestamp) }}
                  </p>
                </div>
                <div v-else-if="priceLoading" class="price-display">
                  <p class="current-price loading-price">
                    Chargement... <span class="price-refreshing">🔄</span>
                  </p>
                  <p class="timestamp loading-timestamp">
                    Mise à jour du prix...
                  </p>
                </div>
                <p v-else class="signal-timestamp error-timestamp">
                  Signal non disponible
                </p>
              </div>
            </div>

            <!-- Type d'ordre -->
            <div class="form-group">
              <label>Type d'ordre:</label>
              <div class="radio-group">
                <label>
                  <input type="radio" v-model="tradeForm.side" value="buy">
                  Achat
                </label>
                <label>
                  <input type="radio" v-model="tradeForm.side" value="sell">
                  Vente
                </label>
              </div>
            </div>

            <!-- Mode d'ordre -->
            <div class="form-group">
              <label>Mode:</label>
              <div class="radio-group">
                <label>
                  <input type="radio" v-model="tradeForm.order_type" value="market">
                  Marché
                </label>
                <label>
                  <input type="radio" v-model="tradeForm.order_type" value="limit">
                  Limite
                </label>
              </div>
            </div>

            <!-- Prix limite (si ordre limite) -->
            <div v-if="tradeForm.order_type === 'limit'" class="form-group">
              <label>Prix limite:</label>
              <input 
                type="number" 
                v-model="tradeForm.price" 
                step="0.00000001"
                placeholder="Prix"
              >
            </div>

            <!-- Quantité ou valeur -->
            <div class="form-group">
              <label>Mode de saisie:</label>
              <div class="radio-group">
                <label>
                  <input type="radio" v-model="inputMode" value="quantity">
                  Quantité
                </label>
                <label>
                  <input type="radio" v-model="inputMode" value="value">
                  Valeur USD
                </label>
              </div>
            </div>

            <div v-if="inputMode === 'quantity'" class="form-group">
              <label>Quantité:</label>
              <input 
                type="number" 
                v-model="tradeForm.quantity" 
                @input="calculateValue"
                step="0.00000001"
                placeholder="Quantité"
              >
            </div>

            <div v-if="inputMode === 'value'" class="form-group">
              <label>Valeur USD:</label>
              <input 
                type="number" 
                v-model="tradeForm.total_value" 
                @input="calculateQuantity"
                step="0.01"
                placeholder="Valeur en USD"
              >
            </div>

            <!-- Résumé calculé avec nouveau format -->
            <div v-if="formattedTradeSummary" :class="[
              'trade-summary', 
              {
                'execution-success': executionResult && executionResult.type === 'success',
                'execution-error': executionResult && executionResult.type === 'error'
              }
            ]">
              <p>{{ formattedTradeSummary.line1 }}</p>
              <p>{{ formattedTradeSummary.line2 }}</p>
            </div>

            <!-- Boutons d'action -->
            <div class="form-actions">
              <button 
                @click="validateTrade" 
                :disabled="!canValidate || validationLoading"
                :class="['btn-validate', { 'loading': validationLoading }]"
              >
                <span v-if="!validationLoading">Valider</span>
                <span v-else class="loading-spinner">
                  <span class="spinner"></span>
                  Validation...
                </span>
              </button>
              <button 
                @click="executeTrade" 
                :disabled="!canExecute"
                class="btn-execute"
              >
                Exécuter
              </button>
            </div>

            <!-- Message de statut de validation avec timer -->
            <div v-if="validationStatusMessage" :class="['validation-status', validationStatusClass]">
              {{ validationStatusMessage }}
            </div>
          </div>
        </div>

        <!-- Ordres avec toggle -->
        <div class="section-card">
          <div class="orders-header">
            <h2>{{ orderViewMode === 'open' ? 'Ordres ouverts' : 'Historique des ordres' }}</h2>
            <div class="orders-toggle">
              <button 
                :class="['toggle-btn', { 'active': orderViewMode === 'open' }]"
                @click="orderViewMode = 'open'; loadOrdersForCurrentMode()"
              >
                Ordres ouverts
              </button>
              <button 
                :class="['toggle-btn', { 'active': orderViewMode === 'history' }]"
                @click="orderViewMode = 'history'; loadOrdersForCurrentMode()"
              >
                Historique
              </button>
            </div>
          </div>
          <div v-if="ordersLoading" class="loading">Chargement...</div>
          <div v-else-if="currentOrdersList.length === 0" class="no-orders">
            {{ orderViewMode === 'open' ? 'Aucun ordre ouvert' : 'Aucun ordre dans l\'historique' }}
          </div>
          <div v-else class="orders-list">
            <div v-for="order in currentOrdersList" :key="order.id" class="order-item">
              <div class="order-header">
                <span :class="['order-side', order.side]">{{ order.side.toUpperCase() }}</span>
                <span class="order-symbol">{{ order.symbol }}</span>
                <span class="order-type">{{ order.type }}</span>
              </div>
              <div class="order-details">
                <div class="order-amounts">
                  <span class="order-amount">{{ parseFloat(order.amount).toFixed(8) }}</span>
                  <span class="order-price" v-if="order.price">@ {{ parseFloat(order.price).toFixed(2) }}</span>
                </div>
                <div class="order-actions">
                  <button 
                    @click="cancelOrder(order.id, order.symbol)" 
                    class="btn-cancel"
                    :disabled="orderActionLoading"
                    title="Annuler l'ordre"
                  >
                    ❌
                  </button>
                  <button 
                    @click="editOrder(order)" 
                    class="btn-edit"
                    :disabled="orderActionLoading"
                    title="Modifier l'ordre"
                  >
                    ✏️
                  </button>
                </div>
              </div>
              <div class="order-status">
                <span class="order-filled">{{ parseFloat(order.filled || 0).toFixed(8) }} / {{ parseFloat(order.amount).toFixed(8) }}</span>
                <span class="order-timestamp">{{ formatTimestamp(order.timestamp) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Historique des trades récents -->
        <div class="section-card">
          <h2>Trades récents</h2>
          <div v-if="tradesLoading" class="loading">Chargement...</div>
          <div v-else class="trades-list">
            <div v-for="trade in recentTrades" :key="trade.id" class="trade-item">
              <span :class="['trade-side', trade.side]">{{ trade.side.toUpperCase() }}</span>
              <span class="trade-symbol">{{ trade.symbol }}</span>
              <span class="trade-quantity">{{ trade.quantity }}</span>
              <span :class="['trade-status', trade.status]">{{ trade.status }}</span>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- Modale Types d'Ordres -->
    <div v-if="showOrderTypeModal" class="modal-overlay" @click="closeOrderTypeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ currentOrderType.groupName }} / {{ currentOrderType.orderName }}</h3>
          <button @click="closeOrderTypeModal" class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="coding-message">
            <div class="coding-icon">💻</div>
            <p>Vibe Coding en cours...</p>
            <div class="coding-animation">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modale de confirmation -->
    <div v-if="showConfirmModal" class="modal-overlay" @click="closeConfirmModal">
      <div class="confirm-modal-content" @click.stop>
        <div class="confirm-modal-header">
          <h3>{{ confirmModalData.title }}</h3>
          <button @click="closeConfirmModal" class="modal-close">&times;</button>
        </div>
        <div class="confirm-modal-body">
          <p class="confirm-message">{{ confirmModalData.message }}</p>
          
          <!-- Détails de l'ordre -->
          <div v-if="confirmModalData.orderDetails" class="order-details-summary">
            <div class="detail-row">
              <span class="label">Action:</span>
              <span :class="['value', 'action-' + confirmModalData.orderDetails.side?.toLowerCase()]">
                {{ confirmModalData.orderDetails.side }}
              </span>
            </div>
            <div class="detail-row" v-if="confirmModalData.orderDetails.quantity">
              <span class="label">Quantité:</span>
              <span class="value">{{ confirmModalData.orderDetails.quantity }}</span>
            </div>
            <div class="detail-row" v-if="confirmModalData.orderDetails.symbol">
              <span class="label">Symbole:</span>
              <span class="value">{{ confirmModalData.orderDetails.symbol }}</span>
            </div>
            <div class="detail-row" v-if="confirmModalData.orderDetails.type">
              <span class="label">Type:</span>
              <span class="value">{{ confirmModalData.orderDetails.type }}</span>
            </div>
            <div class="detail-row" v-if="confirmModalData.orderDetails.price">
              <span class="label">Prix:</span>
              <span class="value">{{ confirmModalData.orderDetails.price }}</span>
            </div>
            <div class="detail-row" v-if="confirmModalData.orderDetails.total">
              <span class="label">Total:</span>
              <span class="value">${{ confirmModalData.orderDetails.total }}</span>
            </div>
          </div>
        </div>
        <div class="confirm-modal-footer">
          <button @click="handleCancel" class="btn-cancel">
            Annuler
          </button>
          <button @click="handleConfirm" class="btn-confirm" :class="'btn-confirm-' + confirmModalData.type">
            {{ confirmModalData.type === 'execute' ? 'Exécuter' : 'Confirmer' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '@/api'

export default {
  name: 'TradingManualView',
  setup() {
    // État réactif
    const brokers = ref([])
    const selectedBroker = ref('')
    const error = ref('')
    const portfolio = ref(null)
    const portfolioLoading = ref(false)
    const exchangeInfo = ref(null)
    const exchangeInfoLoading = ref(false)
    
    // WebSocket pour les mises à jour de prix
    let tradingSocket = null
    
    // Symboles
    const symbols = ref([])
    const symbolsLoading = ref(false)
    const selectedSymbol = ref('')
    const currentPrice = ref(null)
    const priceTimestamp = ref(null)
    const priceLoading = ref(false)
    
    // Filtres
    const filters = reactive({
      usdt: true,
      usdc: false,
      all: false,
      search: ''
    })
    
    // Formulaire de trading
    const tradeForm = reactive({
      side: 'buy',
      order_type: 'market',
      price: null,
      quantity: null,
      total_value: null
    })
    
    const inputMode = ref('quantity')
    const calculatedTrade = ref(null)
    const validation = ref(null)
    const executionResult = ref(null)  // Résultat de l'exécution à afficher dans validation-status
    
    // Timer de validation
    const validationTimer = ref(null)
    const remainingTime = ref(0)
    const validationExpired = ref(false)
    const validationLoading = ref(false)
    
    // Trades récents
    const recentTrades = ref([])
    const tradesLoading = ref(false)
    
    // Ordres
    const openOrders = ref([])
    const closedOrders = ref([])
    const orderViewMode = ref('open') // 'open' ou 'history'
    const ordersLoading = ref(false)
    const orderActionLoading = ref(false)
    let openOrdersSocket = null
    
    // Modales
    const showOrderTypeModal = ref(false)
    const currentOrderType = reactive({
      groupName: '',
      orderName: ''
    })
    
    const showConfirmModal = ref(false)
    const confirmModalData = reactive({
      title: '',
      message: '',
      type: '', // 'execute' ou 'cancel'
      orderDetails: null,
      onConfirm: null,
      onCancel: null
    })
    
    // Propriétés calculées
    const canValidate = computed(() => {
      return selectedSymbol.value && 
             (tradeForm.quantity || tradeForm.total_value) &&
             tradeForm.side
    })
    
    const canExecute = computed(() => {
      return validation.value && validation.value.valid && !validationExpired.value
    })
    
    const currentOrdersList = computed(() => {
      if (orderViewMode.value === 'open') {
        return openOrders.value
      } else {
        // Historique = ordres ouverts + ordres fermés
        return [...openOrders.value, ...closedOrders.value].sort((a, b) => {
          // Trier par timestamp décroissant (plus récent en premier)
          return (b.timestamp || 0) - (a.timestamp || 0)
        })
      }
    })
    
    // Méthodes
    const loadBrokers = async () => {
      try {
        const response = await api.get('/api/brokers/')
        brokers.value = response.data.results || response.data
      } catch (err) {
        error.value = 'Erreur chargement brokers: ' + err.message
      }
    }
    
    
    const loadPortfolio = async () => {
      portfolioLoading.value = true
      try {
        const response = await api.get(`/api/trading-manual/portfolio/?broker_id=${selectedBroker.value}`)
        portfolio.value = response.data
      } catch (err) {
        error.value = 'Erreur chargement portfolio: ' + err.message
      } finally {
        portfolioLoading.value = false
      }
    }
    
    const loadExchangeInfo = async () => {
      exchangeInfoLoading.value = true
      try {
        const response = await api.get(`/api/trading-manual/exchange-info/${selectedBroker.value}/`)
        exchangeInfo.value = response.data
      } catch (err) {
        error.value = 'Erreur chargement capacités exchange: ' + err.message
      } finally {
        exchangeInfoLoading.value = false
      }
    }
    
    const loadSymbols = async () => {
      if (!selectedBroker.value) return
      
      symbolsLoading.value = true
      try {
        const params = new URLSearchParams({
          broker_id: selectedBroker.value,
          usdt: filters.usdt,
          usdc: filters.usdc,
          all: filters.all,
          search: filters.search,
          page_size: 200
        })
        
        const response = await api.get(`/api/trading-manual/symbols/filtered/?${params}`)
        symbols.value = response.data.symbols || []
      } catch (err) {
        error.value = 'Erreur chargement symboles: ' + err.message
      } finally {
        symbolsLoading.value = false
      }
    }
    
    // Debounce pour la recherche
    let searchTimeout
    const debouncedSearch = () => {
      clearTimeout(searchTimeout)
      searchTimeout = setTimeout(loadSymbols, 300)
    }
    
    const clearSearch = () => {
      filters.search = ''
      loadSymbols()
    }
    
    // Connexion WebSocket Heartbeat (comme HeartbeatView)
    const connectTradingSocket = () => {
      if (tradingSocket) {
        tradingSocket.close()
      }
      
      tradingSocket = new WebSocket('ws://localhost:8000/ws/heartbeat/')
      
      tradingSocket.onopen = () => {
        console.log('🔌 WebSocket Heartbeat connecté (Trading Manual)')
      }
      
      tradingSocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        // Traiter les signaux heartbeat comme HeartbeatView
        if (data.timeframe === '1m' && selectedSymbol.value && selectedBroker.value) {
          // Nouveau signal 1min reçu → rafraîchir le prix du symbole actif
          console.log('💓 Signal heartbeat 1min reçu, rafraîchissement prix...')
          loadCurrentPrice()
        }
      }
      
      tradingSocket.onclose = () => {
        console.log('🔌 WebSocket Heartbeat fermé')
      }
      
      tradingSocket.onerror = (error) => {
        console.error('❌ Erreur WebSocket Heartbeat:', error)
      }
    }
    
    const disconnectTradingSocket = () => {
      if (tradingSocket) {
        tradingSocket.close()
        tradingSocket = null
      }
    }
    
    const notifySymbolChange = () => {
      if (tradingSocket && tradingSocket.readyState === WebSocket.OPEN) {
        tradingSocket.send(JSON.stringify({
          action: 'track_symbol',
          broker_id: selectedBroker.value,
          symbol: selectedSymbol.value
        }))
      }
    }
    
    const selectSymbol = async (symbol) => {
      selectedSymbol.value = symbol
      tradeForm.symbol = symbol
      
      // Reset prix et afficher loading immédiatement
      currentPrice.value = null
      priceTimestamp.value = null
      priceLoading.value = true
      
      // Réinitialiser le résumé et la validation lors du changement de symbole
      calculatedTrade.value = null
      validation.value = null
      executionResult.value = null
      clearValidationTimer()
      
      // Charger le prix actuel immédiatement
      await loadCurrentPrice()
      
      // Notifier le changement de symbole au WebSocket
      notifySymbolChange()
    }
    
    const loadCurrentPrice = async () => {
      if (!selectedSymbol.value || !selectedBroker.value) return
      
      priceLoading.value = true
      try {
        const response = await api.get(`/api/trading-manual/price/${selectedSymbol.value}/?broker_id=${selectedBroker.value}`)
        currentPrice.value = response.data.current_price
        priceTimestamp.value = response.data.timestamp
        console.log(`Prix mis à jour pour ${selectedSymbol.value}: $${currentPrice.value} à ${priceTimestamp.value}`)
      } catch (err) {
        console.error('Erreur chargement prix:', err)
        currentPrice.value = null
        priceTimestamp.value = null
      } finally {
        priceLoading.value = false
      }
    }
    
    const calculateValue = async () => {
      if (!tradeForm.quantity || !selectedSymbol.value) return
      
      try {
        const payload = {
          broker_id: selectedBroker.value,
          symbol: selectedSymbol.value,
          quantity: tradeForm.quantity
        }
        
        // Pour les ordres limites, passer le prix limite pour le calcul
        if (tradeForm.order_type === 'limit' && tradeForm.price) {
          payload.price = tradeForm.price
        }
        
        const response = await api.post('/api/trading-manual/calculate-trade/', payload)
        
        calculatedTrade.value = response.data
        tradeForm.total_value = response.data.total_value
      } catch (err) {
        console.error('Erreur calcul valeur:', err)
      }
    }
    
    const calculateQuantity = async () => {
      if (!tradeForm.total_value || !selectedSymbol.value) return
      
      try {
        const payload = {
          broker_id: selectedBroker.value,
          symbol: selectedSymbol.value,
          total_value: tradeForm.total_value
        }
        
        // Pour les ordres limites, passer le prix limite pour le calcul
        if (tradeForm.order_type === 'limit' && tradeForm.price) {
          payload.price = tradeForm.price
        }
        
        const response = await api.post('/api/trading-manual/calculate-trade/', payload)
        
        calculatedTrade.value = response.data
        tradeForm.quantity = response.data.quantity
      } catch (err) {
        console.error('Erreur calcul quantité:', err)
      }
    }
    
    const validateTrade = async () => {
      try {
        // Démarrer l'effet de chargement
        validationLoading.value = true
        
        // Effacer le timer précédent
        clearValidationTimer()
        
        const response = await api.post('/api/trading-manual/validate-trade/', {
          broker_id: selectedBroker.value,
          symbol: selectedSymbol.value,
          side: tradeForm.side,
          order_type: tradeForm.order_type,
          quantity: tradeForm.quantity,
          price: tradeForm.price
        })
        
        validation.value = response.data
        
        // Si la validation est réussie, démarrer le timer
        if (response.data.valid) {
          startValidationTimer()
        }
      } catch (err) {
        error.value = 'Erreur validation: ' + err.message
        clearValidationTimer()
      } finally {
        // Arrêter l'effet après un délai pour que l'utilisateur le voie
        setTimeout(() => {
          validationLoading.value = false
        }, 500)
      }
    }
    
    const executeTrade = async () => {
      console.log('🚀 executeTrade appelé !')
      console.log('📊 validation.value:', validation.value)
      console.log('📊 validationExpired.value:', validationExpired.value)
      
      // Vérifier que la validation est valide et non expirée
      if (!validation.value || !validation.value.valid || validationExpired.value) {
        console.log('❌ Validation échouée !')
        error.value = 'Veuillez valider le trade avant de l\'exécuter'
        return
      }
      
      // Préparer les détails de l'ordre pour la modale
      const orderDetails = {
        side: tradeForm.side.toUpperCase(),
        quantity: tradeForm.quantity,
        symbol: selectedSymbol.value,
        type: tradeForm.order_type,
        price: tradeForm.order_type === 'limit' ? tradeForm.price : 'Au prix du marché',
        total: calculatedTrade.value?.total_value || 0
      }
      
      // Fonction d'exécution réelle du trade
      const executeTradeAction = async () => {
        console.log('🚀 Exécution du trade...', {
          broker_id: selectedBroker.value,
          symbol: selectedSymbol.value,
          side: tradeForm.side,
          order_type: tradeForm.order_type,
          quantity: tradeForm.quantity,
          price: tradeForm.price,
          total_value: calculatedTrade.value?.total_value
        })
        
        try {
          validationLoading.value = true
          
          const response = await api.post('/api/trading-manual/execute-trade/', {
            broker_id: selectedBroker.value,
            symbol: selectedSymbol.value,
            side: tradeForm.side,
            order_type: tradeForm.order_type,
            quantity: tradeForm.quantity,
            price: tradeForm.price,
            total_value: calculatedTrade.value?.total_value || tradeForm.total_value
          })
          
          console.log('✅ Trade exécuté avec succès:', response.data)
          
          // Réinitialiser le formulaire et l'état de validation
          tradeForm.quantity = null
          tradeForm.total_value = null
          tradeForm.price = null
          calculatedTrade.value = null
          validation.value = null
          validationExpired.value = false
          clearValidationTimer()
          
          // Recharger les données
          await Promise.all([
            loadPortfolio(),
            loadRecentTrades(),
            loadOrdersForCurrentMode()
          ])
          
          // Message de succès
          error.value = '' // Effacer les erreurs précédentes
          
          // Afficher le résultat dans la zone de validation
          const trade = response.data
          const successMessage = `✅ Ordre exécuté avec succès ! ${trade.side.toUpperCase()} ${trade.filled_quantity || trade.quantity} ${trade.symbol}${trade.exchange_order_id ? ` - ID: ${trade.exchange_order_id}` : ''}`
          
          executionResult.value = {
            type: 'success',
            message: successMessage,
            trade: trade
          }
          
        } catch (err) {
          console.error('❌ Erreur exécution trade:', err)
          console.error('📄 Détails erreur:', err.response?.data || err.message)
          
          // Afficher l'erreur dans la zone de validation
          const errorMessage = `❌ Erreur lors de l'exécution: ${err.response?.data?.error || err.message}`
          
          executionResult.value = {
            type: 'error',
            message: errorMessage
          }
        } finally {
          // Réinitialiser l'état de loading et de validation pour permettre une nouvelle validation
          validationLoading.value = false
          validation.value = null
          validationExpired.value = false
          clearValidationTimer()
        }
      }
      
      // Ouvrir la modale de confirmation
      openConfirmModal({
        title: 'Confirmer l\'exécution de l\'ordre',
        message: 'Êtes-vous sûr de vouloir exécuter cet ordre ?',
        type: 'execute',
        orderDetails: orderDetails,
        onConfirm: executeTradeAction,
        onCancel: () => {
          console.log('Exécution annulée par l\'utilisateur')
        }
      })
    }
    
    const loadRecentTrades = async () => {
      if (!selectedBroker.value) return
      
      tradesLoading.value = true
      try {
        const response = await api.get(`/api/trading-manual/trades/?broker=${selectedBroker.value}`)
        recentTrades.value = response.data.results || response.data
      } catch (err) {
        console.error('Erreur chargement trades:', err)
      } finally {
        tradesLoading.value = false
      }
    }
    
    // Fonctions de la modale Types d'Ordres
    const openOrderTypeModal = (orderType) => {
      const orderTypes = {
        market: {
          groupName: 'Types d\'Ordres',
          orderName: 'Market'
        },
        limit: {
          groupName: 'Types d\'Ordres',
          orderName: 'Limite'
        },
        stop: {
          groupName: 'Types d\'Ordres',
          orderName: 'Stop'
        },
        stop_limit: {
          groupName: 'Types d\'Ordres',
          orderName: 'Stop Limite'
        }
      }
      
      const orderInfo = orderTypes[orderType]
      if (orderInfo) {
        currentOrderType.groupName = orderInfo.groupName
        currentOrderType.orderName = orderInfo.orderName
        showOrderTypeModal.value = true
      }
    }
    
    const closeOrderTypeModal = () => {
      showOrderTypeModal.value = false
      currentOrderType.groupName = ''
      currentOrderType.orderName = ''
    }
    
    // Fonctions de modale de confirmation
    const openConfirmModal = (config) => {
      confirmModalData.title = config.title
      confirmModalData.message = config.message
      confirmModalData.type = config.type
      confirmModalData.orderDetails = config.orderDetails
      confirmModalData.onConfirm = config.onConfirm
      confirmModalData.onCancel = config.onCancel
      showConfirmModal.value = true
    }
    
    const closeConfirmModal = () => {
      showConfirmModal.value = false
      confirmModalData.title = ''
      confirmModalData.message = ''
      confirmModalData.type = ''
      confirmModalData.orderDetails = null
      confirmModalData.onConfirm = null
      confirmModalData.onCancel = null
    }
    
    const handleConfirm = () => {
      if (confirmModalData.onConfirm) {
        confirmModalData.onConfirm()
      }
      closeConfirmModal()
    }
    
    const handleCancel = () => {
      if (confirmModalData.onCancel) {
        confirmModalData.onCancel()
      }
      closeConfirmModal()
    }
    
    // Fonction pour formater le timestamp au format DD.MM.AA HH:MM:SS
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'N/A'
      
      const date = new Date(timestamp)
      
      const day = String(date.getDate()).padStart(2, '0')
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const year = date.getFullYear().toString().slice(-2)
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      
      return `${day}.${month}.${year} ${hours}:${minutes}:${seconds}`
    }
    
    // Fonction pour effacer l'erreur
    const clearError = () => {
      error.value = ''
    }
    
    // Fonctions pour gérer les ordres ouverts
    const connectOpenOrdersWebSocket = () => {
      if (!selectedBroker.value || openOrdersSocket) return
      
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      // Utiliser le port Django (8000) pour les WebSockets, pas le port Vite (5173)
      const wsUrl = `${protocol}//localhost:8000/ws/open-orders/?broker_id=${selectedBroker.value}`
      
      openOrdersSocket = new WebSocket(wsUrl)
      
      openOrdersSocket.onopen = () => {
        console.log('🔌 WebSocket ordres ouverts connecté')
        console.log('📡 URL WebSocket:', wsUrl)
      }
      
      openOrdersSocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('📨 Message WebSocket ordres ouverts:', data)
        
        if (data.type === 'open_orders') {
          console.log('📋 Ordres reçus:', data.orders.length, 'ordres')
          console.log('📄 Détail ordres:', data.orders)
          openOrders.value = data.orders
          openOrdersLoading.value = false
        } else if (data.type === 'order_cancelled') {
          console.log('✅ Ordre annulé:', data.order_id)
        } else if (data.type === 'order_edited') {
          console.log('✏️ Ordre modifié:', data.order_id)
        } else if (data.type === 'error') {
          console.error('❌ Erreur WebSocket ordres:', data.message)
          error.value = data.message
        }
      }
      
      openOrdersSocket.onclose = () => {
        console.log('🔌 WebSocket ordres ouverts déconnecté')
        openOrdersSocket = null
      }
      
      openOrdersSocket.onerror = (error) => {
        console.error('❌ Erreur WebSocket ordres:', error)
      }
    }
    
    const disconnectOpenOrdersWebSocket = () => {
      if (openOrdersSocket) {
        openOrdersSocket.close()
        openOrdersSocket = null
      }
    }
    
    const cancelOrder = async (orderId, symbol) => {
      // Trouver les détails de l'ordre à annuler
      const orderToCancel = currentOrdersList.value.find(order => order.id === orderId)
      const orderDetails = orderToCancel ? {
        side: orderToCancel.side?.toUpperCase(),
        quantity: orderToCancel.amount,
        symbol: orderToCancel.symbol,
        type: orderToCancel.type,
        price: orderToCancel.price || 'Au marché',
        id: orderId
      } : {
        id: orderId,
        symbol: symbol
      }
      
      // Fonction d'annulation réelle
      const cancelOrderAction = async () => {
        orderActionLoading.value = true
        try {
          if (openOrdersSocket && openOrdersSocket.readyState === WebSocket.OPEN) {
            // Utiliser WebSocket pour l'annulation en temps réel
            openOrdersSocket.send(JSON.stringify({
              action: 'cancel_order',
              order_id: orderId,
              symbol: symbol
            }))
          } else {
            // Fallback API si WebSocket non disponible
            await api.post('/api/trading-manual/cancel-order/', {
              broker_id: selectedBroker.value,
              order_id: orderId,
              symbol: symbol
            })
            // Recharger les ordres
            await loadOrdersForCurrentMode()
          }
        } catch (err) {
          console.error('Erreur annulation ordre:', err)
          error.value = 'Erreur lors de l\'annulation de l\'ordre'
        } finally {
          orderActionLoading.value = false
        }
      }
      
      // Ouvrir la modale de confirmation
      openConfirmModal({
        title: 'Confirmer l\'annulation de l\'ordre',
        message: 'Êtes-vous sûr de vouloir annuler cet ordre ?',
        type: 'cancel',
        orderDetails: orderDetails,
        onConfirm: cancelOrderAction,
        onCancel: () => {
          console.log('Annulation annulée par l\'utilisateur')
        }
      })
    }
    
    const editOrder = (order) => {
      // Pour l'instant, simple alerte - peut être étendu avec une modale d'édition
      alert(`Modification d'ordre à implémenter pour ordre ${order.id}`)
      // TODO: Implémenter la modale d'édition d'ordre
    }
    
    const loadOpenOrders = async () => {
      if (!selectedBroker.value) {
        console.log('❌ loadOpenOrders: pas de broker sélectionné')
        return
      }
      
      console.log('🔄 loadOpenOrders: chargement pour broker', selectedBroker.value)
      ordersLoading.value = true
      try {
        const url = `/api/trading-manual/open-orders/?broker_id=${selectedBroker.value}`
        console.log('📡 API URL:', url)
        const response = await api.get(url)
        console.log('📨 Réponse API ordres ouverts:', response.data)
        openOrders.value = response.data.orders || []
        console.log('📋 Ordres définis:', openOrders.value.length, 'ordres')
      } catch (err) {
        console.error('❌ Erreur chargement ordres ouverts:', err)
        console.error('📄 Détails erreur:', err.response?.data || err.message)
        openOrders.value = []
      } finally {
        ordersLoading.value = false
      }
    }
    
    const loadClosedOrders = async () => {
      if (!selectedBroker.value) {
        console.log('❌ loadClosedOrders: pas de broker sélectionné')
        return
      }
      
      console.log('🔄 loadClosedOrders: chargement pour broker', selectedBroker.value)
      ordersLoading.value = true
      try {
        // Charger les ordres fermés des 30 derniers jours
        const since30Days = Date.now() - (30 * 24 * 60 * 60 * 1000)
        const url = `/api/trading-manual/closed-orders/?broker_id=${selectedBroker.value}&since=${since30Days}&limit=100`
        console.log('📡 API URL ordres fermés:', url)
        const response = await api.get(url)
        console.log('📨 Réponse API ordres fermés:', response.data)
        closedOrders.value = response.data.orders || []
        console.log('📋 Ordres fermés définis:', closedOrders.value.length, 'ordres')
      } catch (err) {
        console.error('❌ Erreur chargement ordres fermés:', err)
        console.error('📄 Détails erreur:', err.response?.data || err.message)
        closedOrders.value = []
      } finally {
        ordersLoading.value = false
      }
    }
    
    const loadOrdersForCurrentMode = async () => {
      if (orderViewMode.value === 'open') {
        await loadOpenOrders()
      } else {
        // Mode historique: charger les ordres ouverts ET fermés
        ordersLoading.value = true
        try {
          await Promise.all([
            loadOpenOrders(),
            loadClosedOrders()
          ])
        } finally {
          ordersLoading.value = false
        }
      }
    }
    
    // Gestion du changement de broker
    const onBrokerChange = async () => {
      if (selectedBroker.value) {
        // Réinitialiser les états
        error.value = ''
        portfolio.value = null
        exchangeInfo.value = null
        symbols.value = []
        selectedSymbol.value = ''
        currentPrice.value = null
        priceTimestamp.value = null
        recentTrades.value = []
        openOrders.value = []
        
        // Déconnecter les anciens WebSockets
        disconnectTradingSocket()
        disconnectOpenOrdersWebSocket()
        
        // Charger les nouvelles données
        await Promise.all([
          loadPortfolio(),
          loadExchangeInfo(),
          loadSymbols(),
          loadRecentTrades(),
          loadOrdersForCurrentMode()
        ])
        
        // Reconnecter les WebSockets
        connectTradingSocket()
        connectOpenOrdersWebSocket()
      } else {
        // Déconnecter si aucun broker sélectionné
        disconnectTradingSocket()
        disconnectOpenOrdersWebSocket()
      }
    }
    
    // Fonctions de gestion du timer de validation
    const startValidationTimer = () => {
      // Réinitialiser
      clearValidationTimer()
      validationExpired.value = false
      remainingTime.value = 30
      
      validationTimer.value = setInterval(() => {
        remainingTime.value--
        if (remainingTime.value <= 0) {
          clearValidationTimer()
          validationExpired.value = true
        }
      }, 1000)
    }
    
    const clearValidationTimer = () => {
      if (validationTimer.value) {
        clearInterval(validationTimer.value)
        validationTimer.value = null
      }
      remainingTime.value = 0
    }
    
    // Message de statut de validation
    const validationStatusMessage = computed(() => {
      if (!validation.value) return ''
      
      if (!validation.value.valid) {
        return 'Trade invalide: ' + validation.value.errors?.join(', ')
      }
      
      if (validationExpired.value) {
        return 'Nouvelle validation nécessaire'
      }
      
      if (remainingTime.value > 0) {
        return `Trade valide! Vous pouvez l'exécuter dans les ${remainingTime.value} secondes restantes`
      }
      
      return 'Trade valide!'
    })
    
    const validationStatusClass = computed(() => {
      if (!validation.value) return ''
      
      if (!validation.value.valid) return 'error'
      if (validationExpired.value) return 'warning'
      return 'success'
    })
    
    // Nouveau format du résumé - toujours affiché si broker sélectionné
    const formattedTradeSummary = computed(() => {
      // Afficher seulement si un broker est sélectionné
      if (!selectedBroker.value) return null
      
      // Si un résultat d'exécution existe, l'afficher en priorité
      if (executionResult.value) {
        return {
          line1: executionResult.value.message,
          line2: executionResult.value.trade ? 
            `Status: ${executionResult.value.trade.status} - ${new Date(executionResult.value.trade.created_at).toLocaleString()}` : 
            ''
        }
      }
      
      const typeOrdre = tradeForm.side === 'buy' ? 'Achat' : 'Vente'
      const symbol = selectedSymbol.value ? selectedSymbol.value.split('/')[0] : '---'
      
      // Quantité : soit du formulaire, soit de calculatedTrade, soit 0
      let quantity = 0
      if (tradeForm.quantity) {
        quantity = tradeForm.quantity
      } else if (calculatedTrade.value?.quantity) {
        quantity = calculatedTrade.value.quantity
      }
      
      // Gestion du prix selon le type d'ordre
      let price = 0
      if (tradeForm.order_type === 'market') {
        // Ordre au marché → prix actuel du marché
        price = currentPrice.value || 0
      } else if (tradeForm.order_type === 'limit') {
        // Ordre limite → prix saisi dans le formulaire
        price = tradeForm.price || 0
      }
      
      // Total : calculé automatiquement ou depuis calculatedTrade
      let total = 0
      if (quantity && price) {
        total = (quantity * price).toFixed(2)
      } else if (tradeForm.total_value) {
        total = tradeForm.total_value
      } else if (calculatedTrade.value?.total_value) {
        total = calculatedTrade.value.total_value
      }
      
      // Gestion du mode avec/sans "au"
      let orderMode = ''
      if (tradeForm.order_type === 'market') {
        orderMode = 'au marché'
      } else if (tradeForm.order_type === 'limit') {
        orderMode = 'limite'
      }
      
      return {
        line1: `${typeOrdre} de ${quantity || 0} ${symbol} au prix de $${price || 0}`,
        line2: `Ordre ${orderMode}, total: $${total || 0}`
      }
    })
    
    // Watchers
    watch(inputMode, () => {
      calculatedTrade.value = null
      validation.value = null
      executionResult.value = null
    })
    
    // Clear execution results when user starts a new trade
    watch([() => tradeForm.side, () => tradeForm.order_type, selectedSymbol], () => {
      executionResult.value = null
    })
    
    // Initialisation
    onMounted(() => {
      loadBrokers()
      connectTradingSocket()
    })
    
    // Nettoyage
    onUnmounted(() => {
      disconnectTradingSocket()
      disconnectOpenOrdersWebSocket()
      clearValidationTimer()
    })
    
    return {
      brokers,
      selectedBroker,
      error,
      portfolio,
      portfolioLoading,
      exchangeInfo,
      exchangeInfoLoading,
      symbols,
      symbolsLoading,
      selectedSymbol,
      currentPrice,
      priceTimestamp,
      priceLoading,
      filters,
      tradeForm,
      inputMode,
      calculatedTrade,
      validation,
      executionResult,
      validationLoading,
      remainingTime,
      validationExpired,
      validationStatusMessage,
      validationStatusClass,
      formattedTradeSummary,
      recentTrades,
      tradesLoading,
      openOrders,
      closedOrders,
      orderViewMode,
      ordersLoading,
      orderActionLoading,
      currentOrdersList,
      canValidate,
      canExecute,
      onBrokerChange,
      loadSymbols,
      debouncedSearch,
      clearSearch,
      selectSymbol,
      calculateValue,
      calculateQuantity,
      validateTrade,
      executeTrade,
      cancelOrder,
      editOrder,
      loadOpenOrders,
      loadClosedOrders,
      loadOrdersForCurrentMode,
      showOrderTypeModal,
      currentOrderType,
      openOrderTypeModal,
      closeOrderTypeModal,
      showConfirmModal,
      confirmModalData,
      openConfirmModal,
      closeConfirmModal,
      handleConfirm,
      handleCancel,
      formatTimestamp,
      clearError
    }
  }
}
</script>

<style scoped>
/* Utilisation des variables CSS globales cohérentes avec les autres pages */

.trading-manual {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
  background: var(--color-background);
  min-height: 100vh;
  color: var(--color-text);
  font-family: 'Segoe UI', -apple-system, system-ui, sans-serif;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}

.header-section h1 {
  color: var(--color-primary);
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0;
}

.broker-selector {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.broker-selector label {
  color: var(--color-text-secondary);
  font-weight: 500;
}

.broker-selector select {
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  color: var(--color-text);
  min-width: 220px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.broker-selector select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.1);
}

.error-message {
  background: var(--color-surface);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  padding: 1rem 1.5rem;
  border-radius: 0.25rem;
  margin-bottom: 1.5rem;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
}

.error-close {
  background: none;
  border: none;
  color: var(--color-danger);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  line-height: 1;
  transition: all 0.2s ease;
  border-radius: 3px;
  margin-left: 1rem;
  flex-shrink: 0;
}

.error-close:hover {
  background: var(--color-danger);
  color: var(--color-text);
  transform: scale(1.1);
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 2rem;
  min-height: 600px;
}

.section-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  height: fit-content;
  transition: all 0.3s ease;
}


.section-card:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
}

.section-card h2 {
  margin: 0 0 1.5rem 0;
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.75rem;
  font-size: 1.3rem;
  font-weight: 600;
}

.loading {
  text-align: center;
  color: var(--color-text-secondary);
  font-style: italic;
  padding: 2rem;
}

/* Exchange Capabilities styles */
.capabilities-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-top: 1rem;
}

.capability-section {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  padding: 1rem;
}

.capability-section h4 {
  color: var(--color-primary);
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0 0 0.75rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.capability-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0;
  font-size: 0.85rem;
}

.capability-item:not(:last-child) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.capability-label {
  color: var(--color-text-secondary);
  font-weight: 500;
}

.enabled {
  color: var(--color-success);
  font-weight: 600;
  font-size: 0.8rem;
}

.disabled {
  color: var(--color-danger);
  font-weight: 500;
  font-size: 0.8rem;
  opacity: 0.7;
}

/* Portfolio styles */
.portfolio-summary {
  background: linear-gradient(135deg, var(--color-background), var(--color-surface));
  border: 1px solid var(--color-border);
  padding: 1.25rem;
  border-radius: 0.25rem;
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
}

.portfolio-summary::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, var(--color-success), var(--color-primary));
}

.portfolio-summary strong {
  color: var(--color-success);
  font-size: 1.1rem;
}

.balance-list, .positions-list {
  max-height: 250px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) var(--color-background);
}

.balance-list::-webkit-scrollbar, .positions-list::-webkit-scrollbar {
  width: 6px;
}

.balance-list::-webkit-scrollbar-track, .positions-list::-webkit-scrollbar-track {
  background: var(--color-background);
  border-radius: 3px;
}

.balance-list::-webkit-scrollbar-thumb, .positions-list::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.balance-item, .position-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-border);
  transition: all 0.2s ease;
}

.balance-item:hover, .position-item:hover {
  background: var(--color-background);
  border-radius: 6px;
  border-bottom: 1px solid var(--color-border);
}

.balance-item:last-child, .position-item:last-child {
  border-bottom: none;
}

.asset {
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.95rem;
}

.amount {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: var(--color-primary);
  font-weight: 500;
  font-size: 0.9rem;
}

/* Capacités exchange */
.capabilities-grid {
  display: grid;
  gap: 0.75rem;
}

.capability-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  transition: all 0.2s ease;
}

.capability-item:hover {
  background: var(--crypto-bg-primary);
  border-color: var(--color-primary);
}

.capability-label {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.enabled {
  color: var(--color-success);
  font-weight: 600;
  }

.disabled {
  color: var(--color-danger);
  font-weight: 500;
}

/* Symboles styles */
.filters {
  margin-bottom: 1.5rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--color-border);
}

.filter-checkboxes {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.filter-checkboxes label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text-secondary);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-checkboxes label:hover {
  color: var(--color-primary);
}

.filter-checkboxes input[type="checkbox"] {
  width: 18px;
  height: 18px;
  background: var(--color-background);
  border: 2px solid var(--color-border);
  border-radius: 3px;
  cursor: pointer;
  appearance: none;
  position: relative;
  transition: all 0.2s ease;
}

.filter-checkboxes input[type="checkbox"]:checked {
  background: var(--color-primary);
  border-color: var(--color-primary);
  box-shadow: 0 0 8px var(--color-primary)50;
}

.filter-checkboxes input[type="checkbox"]:checked::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-weight: bold;
  font-size: 12px;
}

.search-box {
  position: relative;
}

.search-box input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  color: var(--color-text);
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.search-box input::placeholder {
  color: var(--color-text-secondary);
}

.search-box input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.1);
}

.clear-search-btn {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 50%;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.clear-search-btn:hover {
  background: var(--color-danger);
  color: white;
  transform: translateY(-50%) scale(1.1);
}

.symbols-container {
  height: 400px;
  overflow-y: auto;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) var(--color-background);
}

.symbols-container::-webkit-scrollbar {
  width: 6px;
}

.symbols-container::-webkit-scrollbar-track {
  background: var(--color-background);
}

.symbols-container::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.symbols-list {
  padding: 0.5rem;
}

.symbol-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
  color: var(--color-text-secondary);
  font-weight: 500;
  font-family: 'JetBrains Mono', monospace;
  border: 1px solid transparent;
}

.symbol-item:hover {
  background: var(--color-surface);
  color: var(--color-text);
  border-color: var(--color-border);
}

.symbol-item.active {
  background: linear-gradient(135deg, var(--color-primary)20, var(--color-surface));
  color: var(--color-primary);
  border-color: var(--color-primary);
  font-weight: 600;
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.1);
}

/* Trading styles */
.no-symbol {
  text-align: center;
  color: var(--color-text-secondary);
  font-style: italic;
  padding: 3rem 2rem;
  background: var(--color-background);
  border: 1px dashed var(--color-border);
  border-radius: 0.25rem;
  margin: 2rem 0;
}

.symbol-info {
  text-align: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, var(--color-background), var(--color-surface));
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  position: relative;
  overflow: hidden;
}

.symbol-info::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, var(--color-primary), var(--color-success));
}

.symbol-info h3 {
  margin: 0 0 0.5rem 0;
  color: var(--color-text);
  font-size: 1.4rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

.price-display {
  text-align: center;
}

.current-price {
  margin: 0 0 0.5rem 0;
  font-size: 1.8rem;
  font-weight: bold;
  color: var(--color-success);
  font-family: 'JetBrains Mono', monospace;
}

.timestamp {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}

.signal-timestamp {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-primary);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}

.price-info {
  margin-top: 0.5rem;
}

.loading-price {
  color: var(--color-text-secondary) !important;
  font-style: italic;
  font-size: 1.2rem;
}

.loading-timestamp {
  color: var(--color-text-secondary) !important;
  font-style: italic;
  font-size: 0.75rem;
}

.error-price, .error-timestamp {
  color: var(--color-danger) !important;
  font-style: italic;
}

.price-refreshing {
  margin-left: 0.5rem;
  font-size: 0.9rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 0.95rem;
}

.radio-group {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.radio-group label:hover {
  color: var(--color-primary);
}

.radio-group input[type="radio"] {
  width: 18px;
  height: 18px;
  background: var(--color-background);
  border: 2px solid var(--color-border);
  border-radius: 50%;
  cursor: pointer;
  appearance: none;
  position: relative;
  transition: all 0.2s ease;
}

.radio-group input[type="radio"]:checked {
  border-color: var(--color-primary);
  box-shadow: 0 0 8px var(--color-primary)50;
}

.radio-group input[type="radio"]:checked::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  transform: translate(-50%, -50%);
}

.form-group input[type="number"] {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  color: var(--color-text);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.form-group input[type="number"]::placeholder {
  color: var(--color-text-secondary);
}

.form-group input[type="number"]:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.1);
}

.trade-summary {
  background: linear-gradient(135deg, var(--color-success)10, var(--color-surface));
  border: 1px solid var(--color-success);
  padding: 1.5rem;
  border-radius: 0.25rem;
  margin: 1.5rem 0;
  position: relative;
  overflow: hidden;
}

.trade-summary::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: var(--color-success);
}

.trade-summary p {
  margin: 0.5rem 0;
  color: var(--color-text);
  font-weight: 500;
}

.trade-summary strong {
  color: var(--color-success);
}

/* Styles pour les résultats d'exécution dans trade-summary */
.trade-summary.execution-success {
  background: linear-gradient(135deg, var(--color-success)15, var(--color-surface));
  border-color: var(--color-success);
  animation: pulse-success 2s ease-in-out;
}

.trade-summary.execution-success::before {
  background: var(--color-success);
  height: 3px;
}

.trade-summary.execution-error {
  background: linear-gradient(135deg, var(--color-danger)15, var(--color-surface));
  border-color: var(--color-danger);
  animation: pulse-error 2s ease-in-out;
}

.trade-summary.execution-error::before {
  background: var(--color-danger);
  height: 3px;
}

.trade-summary.execution-success p:first-child {
  color: var(--color-success);
  font-weight: 600;
}

.trade-summary.execution-error p:first-child {
  color: var(--color-danger);
  font-weight: 600;
}

@keyframes pulse-success {
  0%, 100% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.4); }
  50% { box-shadow: 0 0 20px 5px rgba(0, 255, 0, 0.1); }
}

@keyframes pulse-error {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.4); }
  50% { box-shadow: 0 0 20px 5px rgba(255, 0, 0, 0.1); }
}

.form-actions {
  display: flex;
  gap: 1.25rem;
  margin-top: 2rem;
}

.btn-validate, .btn-execute {
  flex: 1;
  padding: 1rem 1.5rem;
  border: none;
  border-radius: 0.25rem;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: relative;
  overflow: hidden;
}

.btn-validate {
  background: linear-gradient(135deg, var(--color-warning), #FFB800);
  color: var(--crypto-bg-primary);
  border: 1px solid var(--color-warning);
}

.btn-validate:hover:not(:disabled) {
  background: linear-gradient(135deg, #FFB800, var(--color-warning));
  box-shadow: 0 0 20px var(--color-warning)50;
  transform: translateY(-1px);
}

.btn-execute {
  background: linear-gradient(135deg, var(--color-success), #00CC66);
  color: var(--crypto-bg-primary);
  border: 1px solid var(--color-success);
}

.btn-execute:hover:not(:disabled) {
  background: linear-gradient(135deg, #00CC66, var(--color-success));
  box-shadow: 0 0 20px var(--color-success)50;
  transform: translateY(-1px);
}

.btn-validate:disabled, .btn-execute:disabled {
  background: var(--color-background);
  color: var(--color-text-secondary);
  border-color: var(--color-border);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.validation-errors {
  background: linear-gradient(135deg, var(--color-danger)15, var(--color-surface));
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  padding: 1.25rem;
  border-radius: 0.25rem;
  margin-top: 1.5rem;
  box-shadow: 0 0 15px var(--color-danger)25;
}

.validation-errors strong {
  color: var(--color-danger);
  font-weight: 600;
}

.validation-errors ul {
  margin: 0.75rem 0 0 0;
  padding-left: 1.5rem;
}

.validation-errors li {
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.validation-success {
  background: linear-gradient(135deg, var(--color-success)15, var(--color-surface));
  border: 1px solid var(--color-success);
  color: var(--color-success);
  padding: 1.25rem;
  border-radius: 0.25rem;
  margin-top: 1.5rem;
  font-weight: 600;
    }

/* Trades récents */
.trades-list {
  max-height: 350px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) var(--color-background);
}

.trades-list::-webkit-scrollbar {
  width: 6px;
}

.trades-list::-webkit-scrollbar-track {
  background: var(--color-background);
}

.trades-list::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.trade-item {
  display: grid;
  grid-template-columns: 65px 1fr 90px 85px;
  gap: 0.75rem;
  padding: 0.75rem;
  border-bottom: 1px solid var(--color-border);
  align-items: center;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  border-radius: 6px;
  margin-bottom: 2px;
}

.trade-item:hover {
  background: var(--color-background);
  border-color: var(--color-primary);
}

.trade-item:last-child {
  border-bottom: none;
}

.trade-side {
  font-weight: 600;
  text-align: center;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.trade-side.buy {
  background: linear-gradient(135deg, var(--color-success)20, var(--color-surface));
  color: var(--color-success);
  border: 1px solid var(--color-success);
  box-shadow: 0 0 8px var(--color-success)25;
}

.trade-side.sell {
  background: linear-gradient(135deg, var(--color-danger)20, var(--color-surface));
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
  box-shadow: 0 0 8px var(--color-danger)25;
}

.trade-symbol {
  font-weight: 600;
  color: var(--color-text);
  font-family: 'JetBrains Mono', monospace;
}

.trade-quantity {
  font-family: 'JetBrains Mono', monospace;
  text-align: right;
  color: var(--color-primary);
  font-weight: 500;
}

.trade-status {
  text-align: center;
  font-size: 0.75rem;
  padding: 0.3rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.trade-status.filled {
  background: linear-gradient(135deg, var(--color-success)20, var(--color-surface));
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

.trade-status.pending {
  background: linear-gradient(135deg, var(--color-warning)20, var(--color-surface));
  color: var(--color-warning);
  border: 1px solid var(--color-warning);
}

.trade-status.failed {
  background: linear-gradient(135deg, var(--color-danger)20, var(--color-surface));
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
}

/* Éléments cliquables dans Types d'Ordres */
.capability-item.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0.6rem 0.5rem;
  margin: 0 -0.5rem;
  border-radius: 4px;
}

.capability-item.clickable:hover {
  background: var(--color-surface);
  transform: translateX(3px);
  border-color: var(--color-primary);
}

/* Modale Types d'Ordres */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: modalFadeIn 0.3s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  animation: modalSlideIn 0.3s ease-out;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.modal-header h3 {
  margin: 0;
  color: var(--color-primary);
  font-size: 1.2rem;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.8rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  line-height: 1;
  transition: color 0.2s ease;
}

.modal-close:hover {
  color: var(--color-danger);
}

.modal-body {
  padding: 2rem;
}

.coding-message {
  text-align: center;
  color: var(--color-text-secondary);
}

.coding-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  animation: codingBounce 2s ease-in-out infinite;
}

@keyframes codingBounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

.coding-message p {
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
  color: var(--color-primary);
  font-weight: 500;
}

.coding-animation {
  display: flex;
  justify-content: center;
  gap: 0.3rem;
}

.coding-animation span {
  width: 8px;
  height: 8px;
  background-color: var(--color-primary);
  border-radius: 50%;
  animation: codingDots 1.4s ease-in-out infinite;
}

.coding-animation span:nth-child(1) { animation-delay: -0.32s; }
.coding-animation span:nth-child(2) { animation-delay: -0.16s; }
.coding-animation span:nth-child(3) { animation-delay: 0s; }

@keyframes codingDots {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Effet de chargement pour le bouton Valider */
.btn-validate.loading {
  background: linear-gradient(135deg, var(--color-primary)60, var(--color-primary)80);
  position: relative;
  overflow: hidden;
}

.btn-validate.loading::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  animation: shimmer 1.5s infinite;
}

.loading-spinner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Styles pour le système de validation avec timer */
.validation-status {
  padding: 1rem 1.5rem;
  border-radius: 0.5rem;
  margin: 1rem 0;
  font-weight: 600;
  text-align: center;
  border: 2px solid;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.validation-status.success {
  background: linear-gradient(135deg, var(--color-success)15, var(--color-surface));
  color: var(--color-success);
  border-color: var(--color-success);
  box-shadow: 0 0 20px rgba(0, 200, 100, 0.1);
}

.validation-status.warning {
  background: linear-gradient(135deg, var(--color-warning)15, var(--color-surface));
  color: var(--color-warning);
  border-color: var(--color-warning);
  box-shadow: 0 0 20px rgba(255, 165, 0, 0.1);
  animation: warningPulse 2s infinite;
}

.validation-status.error {
  background: linear-gradient(135deg, var(--color-danger)15, var(--color-surface));
  color: var(--color-danger);
  border-color: var(--color-danger);
  box-shadow: 0 0 20px rgba(255, 59, 48, 0.1);
}

.validation-errors-detail {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: var(--color-surface);
  border: 1px solid var(--color-danger);
  border-radius: 0.25rem;
  font-size: 0.9rem;
}

.validation-errors-detail ul {
  margin: 0;
  padding-left: 1.2rem;
  color: var(--color-danger);
}

.validation-errors-detail li {
  margin-bottom: 0.25rem;
}

@keyframes warningPulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(255, 165, 0, 0.1);
  }
  50% {
    box-shadow: 0 0 30px rgba(255, 165, 0, 0.2);
  }
}

/* Styles pour les ordres ouverts */
.orders-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  background: var(--color-surface);
}

.order-item {
  padding: 0.75rem;
  border-bottom: 1px solid var(--color-border);
  background: linear-gradient(135deg, var(--color-background), var(--color-surface));
  transition: all 0.2s ease;
}

.order-item:hover {
  background: var(--color-surface);
  transform: translateY(-1px);
}

.order-item:last-child {
  border-bottom: none;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.order-side {
  padding: 0.2rem 0.5rem;
  border-radius: 0.2rem;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.order-side.buy {
  background: var(--color-success);
  color: white;
}

.order-side.sell {
  background: var(--color-danger);
  color: white;
}

.order-symbol {
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.9rem;
}

.order-type {
  background: var(--color-primary);
  color: white;
  padding: 0.2rem 0.4rem;
  border-radius: 0.2rem;
  font-size: 0.7rem;
  text-transform: uppercase;
  font-weight: 500;
}

.order-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.order-amounts {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.order-amount {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.85rem;
}

.order-price {
  font-family: 'JetBrains Mono', monospace;
  color: var(--color-text-secondary);
  font-size: 0.8rem;
}

.order-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-cancel, .btn-edit {
  background: none;
  border: 1px solid;
  border-radius: 0.25rem;
  padding: 0.3rem 0.5rem;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
  opacity: 0.7;
}

.btn-cancel {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.btn-cancel:hover:not(:disabled) {
  background: var(--color-danger);
  color: white;
  opacity: 1;
}

.btn-edit {
  border-color: var(--color-warning);
  color: var(--color-warning);
}

.btn-edit:hover:not(:disabled) {
  background: var(--color-warning);
  color: white;
  opacity: 1;
}

.btn-cancel:disabled, .btn-edit:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.order-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.order-filled {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
}

.order-timestamp {
  font-family: 'JetBrains Mono', monospace;
  opacity: 0.8;
}

.no-orders {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-secondary);
  font-style: italic;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
}

/* Styles pour le toggle des ordres */
.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border);
}

.orders-header h2 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--color-text);
}

.orders-toggle {
  display: flex;
  gap: 0;
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  overflow: hidden;
  background: var(--color-background);
}

.toggle-btn {
  background: var(--color-background);
  border: none;
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  border-right: 1px solid var(--color-border);
  white-space: nowrap;
}

.toggle-btn:last-child {
  border-right: none;
}

.toggle-btn:hover:not(.active) {
  background: var(--color-surface);
  color: var(--color-text);
}

.toggle-btn.active {
  background: var(--color-primary);
  color: white;
  font-weight: 600;
}

.toggle-btn:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

/* Styles pour la modale de confirmation */
.confirm-modal-content {
  background: var(--color-surface);
  border-radius: 0.75rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  border: 1px solid var(--color-border);
  max-width: 500px;
  width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  position: relative;
}

.confirm-modal-header {
  padding: 1.5rem 1.5rem 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.confirm-modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.confirm-modal-body {
  padding: 1.5rem;
}

.confirm-message {
  font-size: 1rem;
  color: var(--color-text);
  margin: 0 0 1.5rem 0;
  line-height: 1.5;
}

.order-details-summary {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--color-border);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row .label {
  font-weight: 500;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.detail-row .value {
  font-weight: 600;
  color: var(--color-text);
  font-family: 'JetBrains Mono', monospace;
}

.detail-row .value.action-buy {
  color: var(--color-success);
}

.detail-row .value.action-sell {
  color: var(--color-danger);
}

.confirm-modal-footer {
  padding: 1rem 1.5rem 1.5rem 1.5rem;
  background: var(--color-background);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-cancel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-cancel:hover {
  background: var(--color-border);
  color: var(--color-text);
}

.btn-confirm {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
  border: none;
  color: white;
}

.btn-confirm-execute {
  background: var(--color-success);
}

.btn-confirm-execute:hover {
  background: var(--color-success-dark, #16a34a);
}

.btn-confirm-cancel {
  background: var(--color-danger);
}

.btn-confirm-cancel:hover {
  background: var(--color-danger-dark, #dc2626);
}

.btn-confirm:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

/* Responsive */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .trading-manual {
    padding: 0.5rem;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .radio-group {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>