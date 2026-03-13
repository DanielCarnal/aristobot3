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
          <div class="portfolio-header">
            <h2>Portfolio</h2>
            <button 
              :class="['portfolio-auto-btn', { 'active': portfolioAutoUpdate }]"
              @click="togglePortfolioAutoUpdate"
              title="Mise à jour automatique des prix"
            >
              🔄 Auto
            </button>
          </div>
          <div v-if="portfolioLoading" class="loading">Chargement...</div>
          <div v-else-if="portfolio">
            <!-- Zone valeur totale optimisée -->
            <div class="portfolio-summary">
              <div class="portfolio-total-success">
                <strong>Valeur totale:</strong> ${{ portfolio.total_value_usd }}
              </div>
            </div>
            
            <h3>Balance</h3>
            <div class="portfolio-table-container">
              <table class="portfolio-table">
                <thead>
                  <tr>
                    <th>Asset</th>
                    <th>Quantité</th>
                    <th>Prix unitaire</th>
                    <th>Total USD</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(amount, asset) in portfolio.balance.total" :key="asset" class="balance-row">
                    <td class="asset-cell">{{ asset }}</td>
                    <td class="quantity-cell">{{ parseFloat(amount).toFixed(8) }}</td>
                    <td class="price-cell">
                      <span v-if="portfolio.prices && portfolio.prices[asset]">
                        ${{ formatPrice(portfolio.prices[asset]) }}
                      </span>
                      <span v-else-if="['USDT', 'USDC', 'USD'].includes(asset)">
                        $1.000
                      </span>
                      <span v-else class="no-price">-</span>
                    </td>
                    <td class="total-cell">
                      <span v-if="portfolio.prices && portfolio.prices[asset]" class="total-value">
                        ${{ formatValue(parseFloat(amount) * portfolio.prices[asset]) }}
                      </span>
                      <span v-else-if="['USDT', 'USDC', 'USD'].includes(asset)" class="total-value">
                        ${{ formatValue(parseFloat(amount)) }}
                      </span>
                      <span v-else class="no-total">-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- SECTION CAPACITÉS ÉCHANGES SUPPRIMÉE -->
        <!-- 🔧 Désormais disponible dans Mon Compte → Bouton "Capacités" -->
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
            <!-- Section info symbole et contrôles en ligne -->
            <div class="symbol-controls-row">
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
                      Mise à jour... <span class="price-refreshing">🔄</span>
                    </p>
                    <p class="timestamp loading-timestamp">
                      &nbsp;
                    </p>
                  </div>
                  <p v-else class="signal-timestamp error-timestamp">
                    Signal non disponible
                  </p>
                </div>
              </div>

              <!-- Section Direction uniquement -->
              <div class="direction-section">
                <div class="side-buttons-vertical">
                  <button 
                    :class="['side-btn', 'buy-btn', { 'active': tradeForm.side === 'buy' }]"
                    @click="tradeForm.side = 'buy'"
                  >
                    ACHETER
                  </button>
                  <button 
                    :class="['side-btn', 'sell-btn', { 'active': tradeForm.side === 'sell' }]"
                    @click="tradeForm.side = 'sell'"
                  >
                    VENDRE
                  </button>
                </div>
              </div>

            </div>

            <!-- Onglets types d'ordres (toute la largeur sous prix et boutons) -->
            <div class="order-tabs">
              <button 
                v-for="tab in orderTypeTabs" 
                :key="tab.value"
                :class="['order-tab', { 'active': tradeForm.order_type === tab.value, 'disabled': !tab.enabled }]"
                @click="selectOrderType(tab.value)"
                :disabled="!tab.enabled"
                :title="tab.tooltip"
              >
                {{ tab.label }}
              </button>
            </div>

            <!-- Champs dynamiques selon le type d'ordre sélectionné -->
            <div class="order-type-fields">
              
              <!-- Prix pour ordre limite -->
              <div v-if="tradeForm.order_type === 'limit'" class="form-field-row">
                <label>Prix limite:</label>
                <input 
                  type="number" 
                  v-model="tradeForm.price" 
                  step="0.00000001"
                  placeholder="Prix limite"
                  @input="calculateValue"
                >
              </div>
              
              <!-- Prix Stop Loss -->
              <div v-if="tradeForm.order_type === 'stop_loss'" class="form-field-row">
                <label>Prix Stop Loss:</label>
                <input 
                  type="number" 
                  v-model="tradeForm.stop_loss_price" 
                  step="0.00000001"
                  placeholder="Prix SL"
                >
              </div>
              
              <!-- Prix Take Profit -->
              <div v-if="tradeForm.order_type === 'take_profit'" class="form-field-row">
                <label>Prix Take Profit:</label>
                <input 
                  type="number" 
                  v-model="tradeForm.take_profit_price" 
                  step="0.00000001"
                  placeholder="Prix TP"
                >
              </div>
              
              <!-- Combo SL + TP -->
              <div v-if="tradeForm.order_type === 'sl_tp_combo'" class="combo-fields">
                <div class="form-field-row">
                  <label>Prix limite (optionnel):</label>
                  <input 
                    type="number" 
                    v-model="tradeForm.price" 
                    step="0.00000001"
                    placeholder="Marché si vide"
                    @input="calculateValue"
                  >
                </div>
                <div class="form-field-row">
                  <label>Stop Loss:</label>
                  <input 
                    type="number" 
                    v-model="tradeForm.stop_loss_price" 
                    step="0.00000001"
                    placeholder="Prix SL"
                  >
                </div>
                <div class="form-field-row">
                  <label>Take Profit:</label>
                  <input 
                    type="number" 
                    v-model="tradeForm.take_profit_price" 
                    step="0.00000001"
                    placeholder="Prix TP"
                  >
                </div>
              </div>
              
              <!-- Stop Limit -->
              <div v-if="tradeForm.order_type === 'stop_limit'" class="combo-fields">
                <div class="form-field-row">
                  <label>Prix limite:</label>
                  <input 
                    type="number" 
                    v-model="tradeForm.price" 
                    step="0.00000001"
                    placeholder="Prix limite"
                    @input="calculateValue"
                  >
                </div>
                <div class="form-field-row">
                  <label>Prix déclenchement:</label>
                  <input 
                    type="number" 
                    v-model="tradeForm.trigger_price" 
                    step="0.00000001"
                    placeholder="Prix trigger"
                  >
                </div>
              </div>
            </div>

            <!-- Mode de saisie -->
            <div class="input-mode-section">
              <div class="radio-group-horizontal">
                <label class="radio-label">
                  <input type="radio" v-model="inputMode" value="quantity">
                  <span>Quantité</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="inputMode" value="value">
                  <span>Valeur USD</span>
                </label>
              </div>
            </div>

            <!-- Champ quantité -->
            <div v-if="inputMode === 'quantity'" class="form-field-row">
              <label>Quantité:</label>
              <input 
                type="number" 
                v-model="tradeForm.quantity" 
                @input="calculateValue"
                step="0.00000001"
                placeholder="Quantité"
              >
            </div>

            <!-- Champ valeur USD -->
            <div v-if="inputMode === 'value'" class="form-field-row">
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
            
            <!-- Résultat d'exécution (succès/erreur/attente/annulé) -->
            <div v-if="executionResult && !formattedTradeSummary" :class="[
              'trade-summary',
              'execution-result',
              {
                'execution-success': executionResult.type === 'success',
                'execution-error': executionResult.type === 'error',
                'execution-waiting': executionResult.type === 'waiting',
                'execution-cancelled': executionResult.type === 'cancelled'
              }
            ]">
              <div class="execution-content">
                <p>{{ executionResult.message }}</p>
                <div v-if="executionResult.trade && executionResult.type === 'success'" class="execution-details">
                  <p><strong>Order ID:</strong> {{ executionResult.trade.exchange_order_id || 'N/A' }}</p>
                  <p><strong>Status:</strong> {{ executionResult.trade.status }}</p>
                  <p v-if="executionResult.trade.filled_quantity"><strong>Quantité:</strong> {{ executionResult.trade.filled_quantity }}</p>
                  <p v-if="executionResult.trade.filled_price"><strong>Prix:</strong> ${{ executionResult.trade.filled_price }}</p>
                </div>
                <div v-if="executionResult.error_details && executionResult.type === 'error'" class="error-details">
                  <p><small>{{ executionResult.error_details }}</small></p>
                </div>
                <p class="execution-timestamp">
                  <small>{{ new Date(executionResult.timestamp).toLocaleTimeString() }}</small>
                </p>
              </div>
              <!-- Bouton fermeture seulement si pas en attente -->
              <button 
                v-if="executionResult.type !== 'waiting'"
                @click="clearExecutionResult" 
                class="execution-close"
                title="Cliquez pour fermer ce message"
              >
                ✕
              </button>
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

        <!-- Section Ordres & Positions - INTERFACE BITGET UNIFIÉE -->
        <div class="section-card orders-section">
          <div class="orders-header">
            <h2>Ordres & Positions</h2>
            <div class="orders-toggle">
              <button 
                :class="['toggle-btn', { active: orderViewMode === 'open' }]"
                @click="orderViewMode = 'open'; loadOrdersForCurrentMode()"
              >
                Ordres Ouverts
              </button>
              <button 
                :class="['toggle-btn', { active: orderViewMode === 'history' }]"
                @click="orderViewMode = 'history'; loadOrdersForCurrentMode()"
              >
                Historique
              </button>
            </div>
          </div>

          <!-- NOUVEAU: Filtres avancés style Bitget -->
          <div class="orders-filters" v-if="orderViewMode === 'history'">
            <!-- Onglets types d'ordres -->
            <div class="order-type-filters">
              <button 
                v-for="typeFilter in orderTypeFilters" 
                :key="typeFilter.value"
                :class="['type-filter-btn', { active: selectedOrderTypeFilter === typeFilter.value }]"
                @click="applyOrderTypeFilter(typeFilter.value)"
              >
                {{ typeFilter.label }}
              </button>
            </div>
            
            <!-- Filtres période et options -->
            <div class="period-and-options">
              <div class="period-selector">
                <label>Période:</label>
                <select v-model="selectedPeriod" @change="loadOrdersForCurrentMode">
                  <option value="90">90 jours</option>
                  <option value="30">30 jours</option>
                  <option value="7">7 jours</option>
                  <option value="1">24 heures</option>
                </select>
              </div>
              
              <div class="order-options">
                <label>
                  <input type="checkbox" v-model="showExecutedOnly" @change="loadOrdersForCurrentMode">
                  Ordres exécutés uniquement
                </label>
              </div>
            </div>
          </div>

          <div v-if="ordersLoading" class="loading">
            <div class="loading-spinner-container">
              <div class="spinner-inline"></div>
              Chargement {{ orderViewMode === 'open' ? 'ordres ouverts' : 'historique' }}...
            </div>
          </div>
          
          <div v-else-if="currentOrdersList.length === 0" class="no-orders">
            <div class="no-data-illustration">
              <div class="no-data-icon">{{ orderViewMode === 'open' ? '📋' : '📚' }}</div>
              <p class="no-data-message">{{ orderViewMode === 'open' ? 'Aucun ordre ouvert' : 'Aucun ordre dans l\'historique' }}</p>
              <p class="no-data-hint">{{ orderViewMode === 'open' ? 'Aucun ordre en attente' : 'Aucun ordre exécuté récemment' }}</p>
            </div>
          </div>
          
          <div v-else class="orders-container">
            <!-- En-tête des colonnes - ALIGNEMENT PARFAIT -->
            <div class="order-item-header unified-header">
              <span class="col-datetime">Date/Heure</span>
              <span class="col-symbol">Symbole</span>
              <span class="col-type">Type</span>
              <span class="col-side">Side</span>
              <span class="col-quantity">Quantité</span>
              <span class="col-price">Prix/Trigger</span>
              <span class="col-total">Total</span>
              <span class="col-status">Status</span>
              <span class="col-actions" v-if="orderViewMode === 'open'">Actions</span>
            </div>

            <!-- Liste des ordres - ALIGNEMENT PARFAIT -->
            <div 
              v-for="order in currentOrdersList" 
              :key="order.id || order.order_id" 
              class="order-item-unified unified-row"
              :class="{ 'new-order': isNewOrder(order) }"
            >
              <!-- Date/Heure -->
              <span class="col-datetime">{{ formatOrderDateTime(order) }}</span>
              
              <!-- Symbole -->
              <span class="col-symbol">{{ order.symbol || 'N/A' }}</span>
              
              <!-- Type avec style -->
              <span class="col-type">
                <span :class="['order-type-badge', formatOrderType(order).class]">
                  {{ formatOrderType(order).label }}
                </span>
              </span>
              
              <!-- Side -->
              <span class="col-side">
                <span :class="['order-side-badge', order.side?.toLowerCase()]">
                  {{ (order.side || 'N/A').toUpperCase() }}
                </span>
              </span>
              
              <!-- Quantité -->
              <span class="col-quantity">{{ formatOrderQuantity(order) }}</span>
              
              <!-- Prix/Trigger avec CORRECTION TRIGGER -->
              <span class="col-price">{{ formatOrderDisplayPrice(order) }}</span>
              
              <!-- Total avec CORRECTION TRIGGER -->
              <span class="col-total">${{ formatOrderTotal(order) }}</span>
              
              <!-- Status -->
              <span class="col-status">
                <span :class="['order-status-badge', 'status-' + (order.status || 'unknown').toLowerCase()]">
                  {{ (order.status || 'unknown').toUpperCase() }}
                </span>
              </span>
              
              <!-- Actions (seulement pour ordres ouverts) -->
              <span class="col-actions" v-if="orderViewMode === 'open'">
                <button 
                  @click="cancelOrder(order.id || order.order_id, order.symbol)"
                  class="action-btn cancel-btn"
                  :disabled="orderActionLoading"
                  title="Annuler l'ordre"
                >
                  ❌
                </button>
                <button 
                  @click="editOrder(order)"
                  class="action-btn edit-btn"
                  :disabled="orderActionLoading"
                  title="Modifier l'ordre"
                >
                  ✏️
                </button>
              </span>
            </div>
          </div>
        </div>

        <!-- Historique des trades récents -->
        <div class="section-card recent-trades">
          <h2>Trades récents</h2>
          <div v-if="tradesLoading" class="loading">Chargement...</div>
          <div v-else class="trades-list">
            <div v-for="trade in recentTrades" :key="trade.id" class="trade-item">
              <!-- Date et heure -->
              <span class="trade-datetime">
                {{ formatTradeDateTime(trade.created_at) }}
              </span>
              <!-- Side (BUY/SELL) -->
              <span :class="['trade-side', trade.side]">
                {{ trade.side.toUpperCase() }}
              </span>
              <!-- Symbole -->
              <span class="trade-symbol">{{ trade.symbol }}</span>
              <!-- Quantité -->
              <span class="trade-quantity">{{ trade.quantity }}</span>
              <!-- Prix -->
              <span class="trade-price">
                {{ trade.price ? `$${parseFloat(trade.price).toFixed(2)}` : '-' }}
              </span>
              <!-- Montant total -->
              <span class="trade-amount">
                {{ formatTradeAmount(trade) }}
              </span>
              <!-- Status -->
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
      total_value: null,
      // Nouveaux champs pour ordres avancés
      stop_loss_price: null,
      take_profit_price: null,
      trigger_price: null
    })
    
    const inputMode = ref('quantity')
    const calculatedTrade = ref(null)
    const validation = ref(null)
    const executionResult = ref(null)  // Résultat de l'exécution à afficher dans validation-status
    
    // Variables portfolio pricing
    const portfolioPrices = ref(null)  // Prix des assets portfolio
    const portfolioAutoUpdate = ref(false)  // Toggle mise à jour auto
    const portfolioPricesError = ref(null)  // Message d'erreur
    
    // Timer de validation
    const validationTimer = ref(null)
    const remainingTime = ref(0)
    const validationExpired = ref(false)
    const validationLoading = ref(false)
    
    // État d'exécution pour UX améliorée
    const executionLoading = ref(false)
    
    // Trades récents
    const recentTrades = ref([])
    const tradesLoading = ref(false)
    
    // Ordres + Positions - ARCHITECTURE TERMINAL 7 INTÉGRÉE + FILTRES BITGET
    const openOrders = ref([])
    const closedOrders = ref([])
    const orderViewMode = ref('open') // 'open', 'history' 
    const ordersLoading = ref(false)
    
    // NOUVEAU: Filtres avancés style Bitget
    const selectedOrderTypeFilter = ref('all') // 'all', 'limit', 'market', 'trigger', 'tpsl', 'oco', 'trailing', 'iceberg', 'twap'
    const selectedPeriod = ref(90) // Période en jours
    const showExecutedOnly = ref(false) // Checkbox ordres exécutés uniquement
    
    // Types de filtres d'ordres Bitget
    const orderTypeFilters = ref([
      { value: 'all', label: 'Tous' },
      { value: 'limit', label: 'Limit' },
      { value: 'market', label: 'Market' },
      { value: 'trigger', label: 'Trigger' },
      { value: 'tpsl', label: 'TP/SL' },
      { value: 'oco', label: 'OCO' },
      { value: 'trailing', label: 'Trailing Stop' },
      { value: 'iceberg', label: 'Iceberg' },
      { value: 'twap', label: 'TWAP' }
    ])
    
    // WebSocket pour notifications de trading (uniquement pour trade-summary maintenant)
    const notificationSocket = ref(null)  // WebSocket pour notifications
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
      return selectedBroker.value &&  // Broker obligatoire
             selectedSymbol.value &&   // Symbole obligatoire
             tradeForm.side &&         // Side obligatoire (défaut: 'buy')
             !executionLoading.value   // Pas pendant l'exécution
      // Note: quantité/valeur sera validée côté serveur lors de la validation
    })
    
    const canExecute = computed(() => {
      return validation.value && validation.value.valid && !validationExpired.value &&
             !executionLoading.value  // NOUVEAU: Désactivé pendant l'exécution
    })

    // Propriété calculée pour la liste d'ordres courante - ARCHITECTURE TERMINAL 7
    const currentOrdersList = computed(() => {
      if (orderViewMode.value === 'open') {
        return openOrders.value || []
      } else if (orderViewMode.value === 'history') {
        return closedOrders.value || []
      }
      return []
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
      console.log('🔍 loadSymbols - DEBUT - selectedBroker:', selectedBroker.value)
      if (!selectedBroker.value) {
        console.log('❌ loadSymbols - Pas de broker sélectionné')
        return
      }
      
      symbolsLoading.value = true
      console.log('🔄 loadSymbols - symbolsLoading = true')
      
      try {
        const params = new URLSearchParams({
          broker_id: selectedBroker.value,
          usdt: filters.usdt,
          usdc: filters.usdc,
          all: filters.all,
          search: filters.search,
          page_size: 200
        })
        
        console.log('📡 loadSymbols - URL:', `/api/trading-manual/symbols/filtered/?${params}`)
        console.log('📊 loadSymbols - Paramètres:', Object.fromEntries(params))
        
        const response = await api.get(`/api/trading-manual/symbols/filtered/?${params}`)
        console.log('✅ loadSymbols - Réponse reçue:', response.data)
        
        symbols.value = response.data.symbols || []
        console.log(`✅ loadSymbols - ${symbols.value.length} symboles chargés`)
        
      } catch (err) {
        console.error('❌ loadSymbols - Erreur:', err)
        console.error('❌ loadSymbols - Response:', err.response?.data)
        console.error('❌ loadSymbols - Status:', err.response?.status)
        error.value = 'Erreur chargement symboles: ' + err.message
      } finally {
        symbolsLoading.value = false
        console.log('✅ loadSymbols - FIN - symbolsLoading = false')
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
      
      tradingSocket = new WebSocket(`ws://${window.location.hostname}:8000/ws/heartbeat/`)
      
      tradingSocket.onopen = () => {
        console.log('🔌 WebSocket Heartbeat connecté (Trading Manual)')
      }
      
      tradingSocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        // Traiter les signaux heartbeat comme HeartbeatView
        if (data.timeframe === '1m') {
          console.log('💓 Signal heartbeat 1min reçu...')
          
          // Prix symbole actuel (ORIGINAL - toujours fonctionnel)
          if (selectedSymbol.value && selectedBroker.value) {
            console.log('🔄 Rafraîchissement prix symbole...')
            loadCurrentPrice()
          }
          
          // NOUVEAU: Portfolio complet (si auto activé)
          if (portfolioAutoUpdate.value && selectedBroker.value) {
            console.log('💰 Rafraîchissement portfolio complet...')
            loadPortfolio()  // Quantités + prix
            if (portfolio.value) {
              loadPortfolioPrices()  // Prix détaillés pour calculs USD
            }
          }
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
    
    // === Fonctions Notifications WebSocket ===
    
    const connectNotificationsSocket = () => {
      if (notificationSocket.value) {
        notificationSocket.value.close()
      }
      
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/trading-notifications/`
      
      notificationSocket.value = new WebSocket(wsUrl)
      
      notificationSocket.value.onopen = () => {
        console.log('✅ WebSocket notifications connecté')
      }
      
      notificationSocket.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('📬 Notification reçue:', data)
          
          handleNotification(data)
        } catch (error) {
          console.error('❌ Erreur parsing notification:', error)
        }
      }
      
      notificationSocket.value.onclose = () => {
        console.log('🔌 WebSocket notifications fermé')
      }
      
      notificationSocket.value.onerror = (error) => {
        console.error('❌ Erreur WebSocket notifications:', error)
      }
    }
    
    const disconnectNotificationsSocket = () => {
      if (notificationSocket.value) {
        notificationSocket.value.close()
        notificationSocket.value = null
      }
    }
    
    const handleNotification = (data) => {
      console.log('🔔 Notification reçue:', data)
      
      // Pour les notifications de trading (succès/erreur d'exécution), 
      // afficher dans trade-summary
      if (data.type === 'trade_execution_success' || data.type === 'trade_execution_error') {
        // Afficher le résultat dans la zone trade-summary
        executionResult.value = {
          type: data.type === 'trade_execution_success' ? 'success' : 'error',
          message: data.message,
          trade: data.trade_data,
          error_details: data.error_details,
          timestamp: data.timestamp || Date.now(),
          trade_id: data.trade_id
        }
        
        console.log('✅ Message affiché dans trade-summary:', executionResult.value)
        return
      }
      
      // Pour les autres types de notifications (connection_status, etc.), 
      // on les ignore maintenant car la zone notifications est supprimée
      console.log('ℹ️ Notification ignorée (zone notifications supprimée):', data.type, data.message)
    }
    
    // Fonctions de notifications supprimées - plus besoin car zone notifications supprimée
    
    const clearExecutionResult = () => {
      executionResult.value = null
      console.log('✅ Message d\'exécution fermé depuis trade-summary')
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
      
      // PERSISTENCE: Sauvegarder le symbole sélectionné
      localStorage.setItem('selectedSymbol', symbol)
      
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
        // Logs pour débugger le problème de symbole
        console.log('🔍 VALIDATE - selectedSymbol.value:', selectedSymbol.value)
        console.log('🔍 VALIDATE - selectedBroker.value:', selectedBroker.value)
        
        // Vérification préalable : ne valider que si les champs requis sont remplis
        if (!selectedBroker.value || !selectedSymbol.value || !tradeForm.quantity || tradeForm.quantity <= 0) {
          console.log('⏭️ VALIDATE - Champs requis manquants, validation ignorée')
          validationLoading.value = false
          validationMessage.value = null
          validationStatus.value = null
          return
        }
        
        // Démarrer l'effet de chargement
        validationLoading.value = true
        
        // Effacer le timer précédent
        clearValidationTimer()
        
        const requestData = {
          broker_id: selectedBroker.value,
          symbol: selectedSymbol.value,
          side: tradeForm.side,
          order_type: tradeForm.order_type,
          quantity: tradeForm.quantity,
          price: tradeForm.price,
          // Nouveaux champs pour ordres avancés (même structure qu'executeTrade)
          stop_loss_price: tradeForm.stop_loss_price,
          take_profit_price: tradeForm.take_profit_price,
          trigger_price: tradeForm.trigger_price
        }
        
        // Vérifier cohérence entre selectedSymbol et tradeForm.symbol
        if (tradeForm.symbol && tradeForm.symbol !== selectedSymbol.value) {
          console.warn('⚠️ INCOHÉRENCE - selectedSymbol:', selectedSymbol.value, 'tradeForm.symbol:', tradeForm.symbol)
        }
        
        console.log('🔍 VALIDATE - Données envoyées:', requestData)
        
        const response = await api.post('/api/trading-manual/validate-trade/', requestData)
        
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
      
      // NOUVEAU: Réinitialiser immédiatement la validation dès le clic sur Exécuter
      // Cela efface le timer, remet le bouton Valider "prêt" et efface validation-status
      console.log('🔄 Réinitialisation validation dès le clic Exécuter')
      validation.value = null
      validationExpired.value = false
      clearValidationTimer()
      // validationLoading sera automatiquement false via clearValidationTimer
      
      // Préparer les détails de l'ordre pour la modale
      const orderDetails = {
        side: tradeForm.side.toUpperCase(),
        quantity: tradeForm.quantity,
        symbol: selectedSymbol.value,
        type: tradeForm.order_type,
        price: ['limit', 'sl_tp_combo', 'stop_limit'].includes(tradeForm.order_type) && tradeForm.price 
          ? tradeForm.price 
          : tradeForm.order_type === 'market' ? 'Au prix du marché' : null,
        stop_loss_price: tradeForm.stop_loss_price,
        take_profit_price: tradeForm.take_profit_price,
        trigger_price: tradeForm.trigger_price,
        total: calculatedTrade.value?.total_value || 0
      }
      
      // Fonction d'exécution réelle du trade
      const executeTradeAction = async () => {
        // Logs pour débugger le problème de symbole  
        console.log('🚀 EXECUTE - selectedSymbol.value:', selectedSymbol.value)
        console.log('🚀 EXECUTE - selectedBroker.value:', selectedBroker.value)
        
        // NOUVEAU: Activer l'état d'exécution et afficher le message d'attente
        executionLoading.value = true
        
        // Déterminer le nom de l'exchange pour le message
        const exchangeName = selectedBroker.value ? 
          brokers.value.find(b => b.id === selectedBroker.value)?.exchange || 'Exchange' : 
          'Exchange'
        
        // Afficher le message d'attente dans trade-summary
        executionResult.value = {
          type: 'waiting',
          message: `⏳ Attente de la confirmation de ${exchangeName}...`,
          timestamp: Date.now()
        }
        
        console.log(`⏳ Message d'attente affiché pour ${exchangeName}`)
        
        const executeData = {
          broker_id: selectedBroker.value,
          symbol: selectedSymbol.value,
          side: tradeForm.side,
          order_type: tradeForm.order_type,
          quantity: tradeForm.quantity,
          price: tradeForm.price,
          total_value: calculatedTrade.value?.total_value || tradeForm.total_value,
          // Nouveaux champs pour ordres avancés
          stop_loss_price: tradeForm.stop_loss_price,
          take_profit_price: tradeForm.take_profit_price,
          trigger_price: tradeForm.trigger_price
        }
        
        // Vérifier cohérence entre selectedSymbol et tradeForm.symbol
        if (tradeForm.symbol && tradeForm.symbol !== selectedSymbol.value) {
          console.warn('⚠️ INCOHÉRENCE EXECUTE - selectedSymbol:', selectedSymbol.value, 'tradeForm.symbol:', tradeForm.symbol)
        }
        
        console.log('🚀 EXECUTE - Données envoyées:', executeData)
        
        try {
          // NOTE: validation.value = null et clearValidationTimer() ont déjà été appelés dans executeTrade()
          
          const response = await api.post('/api/trading-manual/execute-trade/', executeData)
          
          console.log('✅ Trade exécuté avec succès:', response.data)
          
          // Réinitialiser le formulaire après succès
          tradeForm.quantity = null
          tradeForm.total_value = null
          tradeForm.price = null
          tradeForm.stop_loss_price = null
          tradeForm.take_profit_price = null
          tradeForm.trigger_price = null
          calculatedTrade.value = null
          
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
          
          console.log('✅ executionResult défini:', executionResult.value)
          console.log('📊 formattedTradeSummary:', formattedTradeSummary.value)
          
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
          // NOUVEAU: Réactiver les boutons après réponse de l'Exchange
          executionLoading.value = false
          console.log('✅ executionLoading désactivé - boutons réactivés')
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
          
          // NOUVEAU: Afficher les paramètres d'ordre après annulation
          const typeOrdre = tradeForm.side === 'buy' ? 'Achat' : 'Vente'
          const symbol = selectedSymbol.value ? selectedSymbol.value.split('/')[0] : '---'
          const quantity = tradeForm.quantity || calculatedTrade.value?.quantity || 0
          const orderMode = tradeForm.order_type === 'market' ? 'au marché' : `limite à $${tradeForm.price}`
          const total = calculatedTrade.value?.total_value || tradeForm.total_value || 0
          
          executionResult.value = {
            type: 'cancelled',
            message: `❌ Ordre annulé : ${typeOrdre} de ${quantity} ${symbol} ${orderMode} (total: $${total})`,
            timestamp: Date.now()
          }
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

    // NOUVELLES FONCTIONS FORMATAGE ORDRES - CORRECTION CRITIQUE TRIGGER
    
    // Fonction pour formater le total d'un ordre - CORRECTION ORDRE LIMIT
    const formatOrderTotal = (order) => {
      const amount = order.amount || order.quantity || order.size || 0
      
      // CORRECTION CRITIQUE: Suivre même logique que BitgetNativeClient._extract_order_price()
      let price = null
      
      // 1. Priorité 1: priceAvg (ordres LIMIT) - DOC BITGET ligne 81
      if (order.priceAvg && order.priceAvg !== "0" && order.priceAvg !== "") {
        price = parseFloat(order.priceAvg)
      }
      // 2. Priorité 2: triggerPrice (ordres TRIGGER/TP/SL)
      else if (order.triggerPrice && order.triggerPrice !== "0" && order.triggerPrice !== "") {
        price = parseFloat(order.triggerPrice)
      }
      else if (order.trigger_price && order.trigger_price !== "0" && order.trigger_price !== "") {
        price = parseFloat(order.trigger_price)
      }
      // 3. Priorité 3: presetTakeProfitPrice (ordres TP)
      else if (order.presetTakeProfitPrice && order.presetTakeProfitPrice !== "0" && order.presetTakeProfitPrice !== "") {
        price = parseFloat(order.presetTakeProfitPrice)
      }
      else if (order.preset_take_profit_price && order.preset_take_profit_price !== "0" && order.preset_take_profit_price !== "") {
        price = parseFloat(order.preset_take_profit_price)
      }
      // 4. Priorité 4: presetStopLossPrice (ordres SL)
      else if (order.presetStopLossPrice && order.presetStopLossPrice !== "0" && order.presetStopLossPrice !== "") {
        price = parseFloat(order.presetStopLossPrice)
      }
      else if (order.preset_stop_loss_price && order.preset_stop_loss_price !== "0" && order.preset_stop_loss_price !== "") {
        price = parseFloat(order.preset_stop_loss_price)
      }
      // 5. Fallback: price (compatibilité)
      else if (order.price && order.price !== "0" && order.price !== "") {
        price = parseFloat(order.price)
      }
      
      if (!amount || !price) return '0.00'
      try {
        const total = parseFloat(amount) * parseFloat(price)
        return total.toFixed(2)
      } catch (error) {
        return '0.00'
      }
    }

    // Fonction pour formater l'affichage du prix avec indicateurs - CORRECTION ORDRE LIMIT
    const formatOrderDisplayPrice = (order) => {
      let price = null
      let indicator = ''
      
      // MÊME LOGIQUE que formatOrderTotal et BitgetNativeClient._extract_order_price()
      
      // 1. Priorité 1: priceAvg (ordres LIMIT) - DOC BITGET ligne 81
      if (order.priceAvg && order.priceAvg !== "0" && order.priceAvg !== "") {
        price = parseFloat(order.priceAvg)
        // Pas d'indicateur pour ordre LIMIT standard
      }
      // 2. Priorité 2: triggerPrice (ordres TRIGGER/TP/SL)
      else if (order.triggerPrice && order.triggerPrice !== "0" && order.triggerPrice !== "") {
        price = parseFloat(order.triggerPrice)
        indicator = ' (T)' // (T) = Trigger
      }
      else if (order.trigger_price && order.trigger_price !== "0" && order.trigger_price !== "") {
        price = parseFloat(order.trigger_price)
        indicator = ' (T)'
      }
      // 3. Priorité 3: presetTakeProfitPrice (ordres TP)
      else if (order.presetTakeProfitPrice && order.presetTakeProfitPrice !== "0" && order.presetTakeProfitPrice !== "") {
        price = parseFloat(order.presetTakeProfitPrice)
        indicator = ' (TP)' // (TP) = Take Profit
      }
      else if (order.preset_take_profit_price && order.preset_take_profit_price !== "0" && order.preset_take_profit_price !== "") {
        price = parseFloat(order.preset_take_profit_price)
        indicator = ' (TP)'
      }
      // 4. Priorité 4: presetStopLossPrice (ordres SL)
      else if (order.presetStopLossPrice && order.presetStopLossPrice !== "0" && order.presetStopLossPrice !== "") {
        price = parseFloat(order.presetStopLossPrice)
        indicator = ' (SL)' // (SL) = Stop Loss
      }
      else if (order.preset_stop_loss_price && order.preset_stop_loss_price !== "0" && order.preset_stop_loss_price !== "") {
        price = parseFloat(order.preset_stop_loss_price)
        indicator = ' (SL)'
      }
      // 5. Fallback: price (compatibilité)
      else if (order.price && order.price !== "0" && order.price !== "") {
        price = parseFloat(order.price)
        // Pas d'indicateur pour price générique
      }
      
      if (!price) return '-'
      return `${price.toFixed(2)}${indicator}`
    }

    // Fonction pour formater le type d'ordre avec classes CSS
    const formatOrderType = (order) => {
      const orderType = order.type || order.order_type || order.orderType || 'unknown'
      const tpslType = order.tpslType || 'normal'
      
      const type_map = {
        'market': { label: 'MARKET', class: 'type-market' },
        'limit': { label: 'LIMIT', class: 'type-limit' },
        'stop_loss': { label: 'STOP LOSS', class: 'type-stop-loss' },
        'take_profit': { label: 'TAKE PROFIT', class: 'type-take-profit' },
        'stop_limit': { label: 'STOP LIMIT', class: 'type-stop-limit' },
        'sl_tp_combo': { label: 'SL+TP', class: 'type-combo' },
        'stop': { label: 'STOP', class: 'type-stop-loss' },
        'take_profit_limit': { label: 'TP LIMIT', class: 'type-take-profit' },
        'stop_loss_limit': { label: 'SL LIMIT', class: 'type-stop-loss' },
        'oco': { label: 'OCO', class: 'type-combo' },
        'trigger': { label: 'TRIGGER', class: 'type-trigger' },
        'unknown': { label: 'AUTRE', class: 'type-unknown' }
      }
      
      const normalized_type = String(orderType).toLowerCase()
      
      // Détecter les ordres TP/SL de Bitget
      if (tpslType === 'tpsl') {
        return { label: 'TP/SL', class: 'type-tpsl' }
      }
      
      return type_map[normalized_type] || type_map['unknown']
    }

    // Fonction pour formater la quantité
    const formatOrderQuantity = (order) => {
      const quantity = order.amount || order.quantity || order.size || 0
      if (!quantity) return '-'
      return parseFloat(quantity).toFixed(8).replace(/\.?0+$/, '')
    }

    // Fonction pour détecter les nouveaux ordres (animation)
    const isNewOrder = (order) => {
      const orderTime = new Date(order.created_at || order.cTime || 0).getTime()
      const now = Date.now()
      return (now - orderTime) < 10000 // Nouveau si moins de 10 secondes
    }

    // Fonction pour formater la date/heure d'un ordre
    const formatOrderDateTime = (order) => {
      const timestamp = order.created_at || order.cTime || order.timestamp
      if (!timestamp) return '-'
      
      try {
        // Gérer format ISO du backend (ex: "2025-09-09T21:10:18.290000")
        const date = new Date(timestamp)
        
        // Format AA-MM-JJ hh:mm:ss demandé
        const yy = date.getFullYear().toString().slice(-2)
        const mm = (date.getMonth() + 1).toString().padStart(2, '0')
        const dd = date.getDate().toString().padStart(2, '0')
        const hh = date.getHours().toString().padStart(2, '0')
        const min = date.getMinutes().toString().padStart(2, '0')
        const ss = date.getSeconds().toString().padStart(2, '0')
        
        return `${yy}-${mm}-${dd} ${hh}:${min}:${ss}`
      } catch (error) {
        console.error('Erreur formatage date:', error, 'timestamp:', timestamp)
        return '-'
      }
    }
    
    // Fonctions pour gérer les ordres ouverts
    const connectOpenOrdersWebSocket = () => {
      if (!selectedBroker.value || openOrdersSocket) return
      
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      // Utiliser le port Django (8000) pour les WebSockets, pas le port Vite (5173)
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/open-orders/?broker_id=${selectedBroker.value}`
      
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
        ordersLoading.value = false
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
        error.value = `Erreur chargement ordres: ${err.response?.data?.error || err.message}`
      } finally {
        ordersLoading.value = false
        console.log('✅ loadOpenOrders: ordersLoading mis à false')
      }
    }
    
    const loadClosedOrders = async () => {
      if (!selectedBroker.value) {
        console.log('❌ loadClosedOrders: pas de broker sélectionné')
        ordersLoading.value = false
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
        error.value = `Erreur chargement historique: ${err.response?.data?.error || err.message}`
      } finally {
        ordersLoading.value = false
        console.log('✅ loadClosedOrders: ordersLoading mis à false')
      }
    }
    
    // NOUVELLE FONCTION: Chargement Positions P&L Terminal 7
    
    const loadOrdersForCurrentMode = async () => {
      if (orderViewMode.value === 'open') {
        await loadOpenOrders()
      } else {
        // Mode historique: charger avec filtres Bitget étendus
        await loadClosedOrdersWithFilters()
      }
    }
    
    // NOUVELLE FONCTION: Chargement ordres fermés avec filtres Bitget
    const loadClosedOrdersWithFilters = async () => {
      if (!selectedBroker.value) {
        console.log('❌ loadClosedOrdersWithFilters: pas de broker sélectionné')
        ordersLoading.value = false
        return
      }
      
      console.log('🔄 loadClosedOrdersWithFilters: chargement avec filtres Bitget')
      ordersLoading.value = true
      
      try {
        // Construire la période (jours → timestamp)
        const daysAgo = selectedPeriod.value
        const startTime = Date.now() - (daysAgo * 24 * 60 * 60 * 1000)
        const endTime = Date.now()
        
        // Paramètres étendus Terminal 5 + filtres Bitget
        const params = new URLSearchParams({
          broker_id: selectedBroker.value,
          start_time: startTime.toString(),
          end_time: endTime.toString(),
          limit: 100
        })
        
        // Ajouter filtres type d'ordre si spécifique
        if (selectedOrderTypeFilter.value !== 'all') {
          if (selectedOrderTypeFilter.value === 'tpsl') {
            params.append('tpsl_type', 'tpsl')  // Bitget tpslType filter
          }
          // Autres filtres peuvent être ajoutés via type_filter si Exchange supporte
          params.append('order_type_filter', selectedOrderTypeFilter.value)
        }
        
        // Filtre ordres exécutés uniquement
        if (showExecutedOnly.value) {
          params.append('status_filter', 'filled,closed')
        }
        
        const url = `/api/trading-manual/closed-orders/?${params.toString()}`
        console.log('📡 API URL ordres fermés avec filtres:', url)
        
        const response = await api.get(url)
        console.log('📨 Réponse API ordres fermés filtrés:', response.data)
        
        let orders = response.data.orders || []
        
        // FILTRAGE CÔTÉ CLIENT pour types non supportés par Terminal 5
        if (selectedOrderTypeFilter.value !== 'all') {
          orders = orders.filter(order => filterOrderByType(order, selectedOrderTypeFilter.value))
        }
        
        closedOrders.value = orders
        console.log(`📋 Ordres fermés filtrés: ${orders.length} ordres (${selectedOrderTypeFilter.value}, ${daysAgo} jours)`)
        
      } catch (err) {
        console.error('❌ Erreur chargement ordres fermés filtrés:', err)
        closedOrders.value = []
        error.value = `Erreur chargement historique: ${err.response?.data?.error || err.message}`
      } finally {
        ordersLoading.value = false
      }
    }
    
    // Fonction de filtrage côté client par type d'ordre
    const filterOrderByType = (order, typeFilter) => {
      const orderType = (order.type || order.orderType || '').toLowerCase()
      
      switch (typeFilter) {
        case 'market':
          return orderType === 'market'
        case 'limit':
          return orderType === 'limit'
        case 'trigger':
          return orderType.includes('trigger') || orderType.includes('stop')
        case 'tpsl':
          return orderType.includes('take_profit') || orderType.includes('stop_loss') || 
                 order.tpslType === 'tpsl' || order.preset_take_profit_price || order.preset_stop_loss_price
        case 'oco':
          return orderType.includes('oco') || orderType.includes('one_cancel_other')
        case 'trailing':
          return orderType.includes('trailing')
        case 'iceberg':
          return orderType.includes('iceberg')
        case 'twap':
          return orderType.includes('twap') || orderType.includes('time_weighted')
        default:
          return true // 'all' case
      }
    }
    
    // Fonction pour appliquer le filtre de type d'ordre
    const applyOrderTypeFilter = async (typeFilter) => {
      selectedOrderTypeFilter.value = typeFilter
      console.log(`🎯 Filtre type d'ordre appliqué: ${typeFilter}`)
      await loadOrdersForCurrentMode()
    }
    
    // Gestion du changement de broker
    const onBrokerChange = async () => {
      console.log('🔄 onBrokerChange - DEBUT - selectedBroker:', selectedBroker.value)
      console.log('🔄 onBrokerChange - AVANT reset - selectedSymbol:', selectedSymbol.value)
      
      if (selectedBroker.value) {
        // Réinitialiser les états
        error.value = ''
        portfolio.value = null
        exchangeInfo.value = null
        symbols.value = []
        selectedSymbol.value = ''
        tradeForm.symbol = ''  // Cohérence avec selectedSymbol
        localStorage.removeItem('selectedSymbol')  // Nettoyer la persistance
        tradeForm.quantity = null    // Reset form complet
        tradeForm.price = null
        tradeForm.total_value = null
        currentPrice.value = null
        priceTimestamp.value = null
        recentTrades.value = []
        openOrders.value = []
        closedOrders.value = []       // Reset ordres fermés
        ordersLoading.value = false   // Reset état chargement ordres
        calculatedTrade.value = null  // Reset données calculées
        validation.value = null       // Reset validation
        executionResult.value = null  // Reset résultat exécution
        clearValidationTimer()        // Clear timer validation
        
        console.log('🔄 onBrokerChange - APRES reset - selectedSymbol:', selectedSymbol.value)
        
        // Déconnecter les anciens WebSockets
        disconnectTradingSocket()
        disconnectOpenOrdersWebSocket()
        disconnectNotificationsSocket()
        
        // Charger les nouvelles données - SÉPARÉMENT pour debug
        console.log('🔄 onBrokerChange - Début chargement données...')
        
        try {
          console.log('🔄 onBrokerChange - loadPortfolio()...')
          await loadPortfolio()
          console.log('✅ onBrokerChange - loadPortfolio() OK')
        } catch (err) {
          console.error('❌ onBrokerChange - loadPortfolio() ERREUR:', err)
        }
        
        try {
          console.log('🔄 onBrokerChange - loadExchangeInfo()...')
          await loadExchangeInfo()
          console.log('✅ onBrokerChange - loadExchangeInfo() OK')
        } catch (err) {
          console.error('❌ onBrokerChange - loadExchangeInfo() ERREUR:', err)
        }
        
        try {
          console.log('🔄 onBrokerChange - loadSymbols()...')
          await loadSymbols()
          console.log('✅ onBrokerChange - loadSymbols() OK')
        } catch (err) {
          console.error('❌ onBrokerChange - loadSymbols() ERREUR:', err)
        }
        
        try {
          console.log('🔄 onBrokerChange - loadRecentTrades()...')
          await loadRecentTrades()
          console.log('✅ onBrokerChange - loadRecentTrades() OK')
        } catch (err) {
          console.error('❌ onBrokerChange - loadRecentTrades() ERREUR:', err)
        }
        
        try {
          console.log('🔄 onBrokerChange - loadOrdersForCurrentMode()...')
          await loadOrdersForCurrentMode()
          console.log('✅ onBrokerChange - loadOrdersForCurrentMode() OK')
        } catch (err) {
          console.error('❌ onBrokerChange - loadOrdersForCurrentMode() ERREUR:', err)
        }
        
        // Charger les prix du portfolio après avoir chargé le portfolio
        await loadPortfolioPrices()
        
        // Restaurer le symbole sélectionné depuis localStorage après chargement des symboles
        const savedSymbol = localStorage.getItem('selectedSymbol')
        if (savedSymbol && symbols.value.some(s => s.symbol === savedSymbol)) {
          console.log('🔄 onBrokerChange - Restauration symbole depuis localStorage:', savedSymbol)
          selectedSymbol.value = savedSymbol
          tradeForm.symbol = savedSymbol
          await loadCurrentPrice()
        }
        
        // Reconnecter les WebSockets
        connectTradingSocket()
        connectOpenOrdersWebSocket()
        connectNotificationsSocket()
        
        console.log('🔄 onBrokerChange - FIN - selectedSymbol:', selectedSymbol.value)
      } else {
        // Déconnecter si aucun broker sélectionné
        disconnectTradingSocket()
        disconnectOpenOrdersWebSocket()
        disconnectNotificationsSocket()
        console.log('🔄 onBrokerChange - Aucun broker - selectedSymbol:', selectedSymbol.value)
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
      validationLoading.value = false  // NOUVEAU: Réinitialiser le loading du bouton Valider
    }
    
    // Fonctions Portfolio Pricing
    const togglePortfolioAutoUpdate = () => {
      portfolioAutoUpdate.value = !portfolioAutoUpdate.value
      console.log(`🔄 Portfolio Auto Update: ${portfolioAutoUpdate.value ? 'ON' : 'OFF'}`)
    }
    
    const loadPortfolioPrices = async () => {
      if (!selectedBroker.value || !portfolio.value) return
      
      // Re-calculer les assets avec quantité > 0 (à chaque heartbeat)
      const assets = Object.keys(portfolio.value.balance.total || {})
        .filter(asset => parseFloat(portfolio.value.balance.total[asset]) > 0)
      
      if (assets.length === 0) {
        portfolioPrices.value = {}
        return
      }
      
      console.log(`💰 Chargement prix portfolio pour assets: ${assets}`)
      
      try {
        const response = await api.post('/api/trading-manual/portfolio-prices/', {
          broker_id: selectedBroker.value,
          assets: assets
        })
        
        portfolioPrices.value = response.data.prices
        portfolioPricesError.value = null
        console.log(`✅ Prix portfolio reçus:`, response.data.prices)
      } catch (err) {
        console.error('❌ Erreur prix portfolio:', err)
        portfolioPricesError.value = 'Erreur récupération prix'
        portfolioPrices.value = null
      }
    }
    
    const calculatePortfolioTotal = () => {
      if (!portfolio.value || !portfolioPrices.value) return '0.00'
      
      let total = 0
      for (const [asset, amount] of Object.entries(portfolio.value.balance.total || {})) {
        const quantity = parseFloat(amount)
        const price = portfolioPrices.value[asset]
        
        if (quantity > 0 && price) {
          total += quantity * price
        }
      }
      
      return total.toFixed(2)
    }
    
    const formatValue = (value) => {
      if (!value || isNaN(value)) return '0.00'
      return parseFloat(value).toFixed(2)
    }
    
    const formatPrice = (value) => {
      if (!value || isNaN(value)) return '0.000'
      return parseFloat(value).toFixed(3)
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
      const currentPriceValue = currentPrice.value || 0
      
      // Quantité : soit du formulaire, soit de calculatedTrade, soit 0
      let quantity = 0
      if (tradeForm.quantity) {
        quantity = tradeForm.quantity
      } else if (calculatedTrade.value?.quantity) {
        quantity = calculatedTrade.value.quantity
      }
      
      // === EXPLICATIONS DYNAMIQUES POUR ORDRES AVANCÉS ===
      if (tradeForm.order_type === 'stop_loss') {
        const stopPrice = tradeForm.stop_loss_price || 0
        let explanation = ''
        
        if (tradeForm.side === 'sell') {
          // VENDRE Stop Loss = Protection position longue
          const priceDiff = currentPriceValue - stopPrice
          explanation = `🛡️ Protection: Si ${symbol} chute sous $${stopPrice} → vente automatique`
          if (priceDiff > 0) {
            explanation += ` (perte limitée à -$${(priceDiff * quantity).toFixed(2)})`
          }
        } else {
          // ACHETER Stop Loss = Protection position courte  
          const priceDiff = stopPrice - currentPriceValue
          explanation = `🛡️ Protection: Si ${symbol} monte au-dessus de $${stopPrice} → achat automatique`
          if (priceDiff > 0) {
            explanation += ` (perte limitée à -$${(priceDiff * quantity).toFixed(2)})`
          }
        }
        
        return {
          line1: `${typeOrdre} Stop Loss: ${quantity || 0} ${symbol} (trigger: $${stopPrice})`,
          line2: explanation
        }
      }
      
      if (tradeForm.order_type === 'take_profit') {
        const tpPrice = tradeForm.take_profit_price || 0
        let explanation = ''
        
        if (tradeForm.side === 'sell') {
          // VENDRE Take Profit = Sécuriser gains position longue
          const profit = tpPrice - currentPriceValue
          explanation = `💰 Gains: Si ${symbol} monte à $${tpPrice} → vente automatique`
          if (profit > 0) {
            explanation += ` (profit: +$${(profit * quantity).toFixed(2)})`
          }
        } else {
          // ACHETER Take Profit = Sécuriser gains position courte
          const profit = currentPriceValue - tpPrice  
          explanation = `💰 Gains: Si ${symbol} descend à $${tpPrice} → achat automatique`
          if (profit > 0) {
            explanation += ` (profit: +$${(profit * quantity).toFixed(2)})`
          }
        }
        
        return {
          line1: `${typeOrdre} Take Profit: ${quantity || 0} ${symbol} (trigger: $${tpPrice})`,
          line2: explanation
        }
      }
      
      if (tradeForm.order_type === 'sl_tp_combo') {
        const slPrice = tradeForm.stop_loss_price || 0
        const tpPrice = tradeForm.take_profit_price || 0
        
        let explanation = ''
        
        if (tradeForm.side === 'sell') {
          explanation = `🛡️💰 Protection: vente si < $${slPrice} | Gains: vente si > $${tpPrice}`
        } else {
          explanation = `🛡️💰 Protection: achat si > $${slPrice} | Gains: achat si < $${tpPrice}`
        }
        
        return {
          line1: `${typeOrdre} SL+TP Combo: ${quantity || 0} ${symbol}`,
          line2: explanation
        }
      }
      
      if (tradeForm.order_type === 'stop_limit') {
        const triggerPrice = tradeForm.trigger_price || 0
        const limitPrice = tradeForm.price || 0
        
        const explanation = `⚡ Déclenchement: à $${triggerPrice} → ordre limite à $${limitPrice}`
        
        return {
          line1: `${typeOrdre} Stop Limit: ${quantity || 0} ${symbol}`,
          line2: explanation
        }
      }
      
      // === ORDRES CLASSIQUES (MARKET, LIMIT) ===
      // Gestion du prix selon le type d'ordre
      let price = 0
      if (tradeForm.order_type === 'market') {
        // Ordre au marché → prix actuel du marché
        price = currentPriceValue
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
    
    // SÉCURITÉ: Watcher pour garantir le reset d'executionLoading
    watch(executionResult, (newResult) => {
      if (newResult && (newResult.type === 'success' || newResult.type === 'error')) {
        console.log('🔒 WATCHER SÉCURITÉ - Remise à zéro executionLoading après notification')
        executionLoading.value = false
      }
    })
    
    // === FONCTIONS UX ENHANCED - SOLUTION 2 PHASE 3 ===
    
    const switchToTab = async (tabName) => {
      orderViewMode.value = tabName
      await loadOrdersForCurrentMode()
    }
    
    // Fonctions pour l'UX améliorée des positions
    const getPositionClass = (position) => {
      const pnl = position.realized_pnl || 0
      if (pnl > 0) return 'profit-position'
      if (pnl < 0) return 'loss-position'
      return 'neutral-position'
    }
    
    const getPnlClass = (pnl) => {
      if (pnl > 0) return 'profit'
      if (pnl < 0) return 'loss'
      return 'neutral'
    }
    
    const formatPnL = (pnl) => {
      if (!pnl) return '$0.00'
      const formatted = Math.abs(pnl).toFixed(2)
      return pnl > 0 ? `+$${formatted}` : `-$${formatted}`
    }
    
    const formatQuantity = (quantity) => {
      if (!quantity) return '0'
      return parseFloat(quantity).toFixed(8).replace(/\.?0+$/, '')
    }
    
    const calculatePnlPercentage = (position) => {
      const percentage = calculatePnlPercentageRaw(position)
      if (percentage === 0) return '0.0%'
      return percentage > 0 ? `+${percentage.toFixed(1)}%` : `${percentage.toFixed(1)}%`
    }
    
    const calculatePnlPercentageRaw = (position) => {
      if (!position.price || !position.quantity || !position.realized_pnl) return 0
      const invested = position.price * position.quantity
      return (position.realized_pnl / invested) * 100
    }
    
    const getSourceLabel = (source) => {
      switch (source) {
        case 'order_monitor': return '🤖 Auto'
        case 'manual': return '👤 Manuel'
        case 'trading_manual': return '👤 Manuel'
        case 'webhook': return '🔗 Webhook'
        case 'strategy': return '🧠 Stratégie'
        default: return source || 'Inconnu'
      }
    }
    
    // Fonctions pour les états vides et les messages
    const getCurrentLoadingState = () => {
      return ordersLoading.value
    }
    
    const getLoadingMessage = () => {
      if (orderViewMode.value === 'open') return 'Chargement ordres ouverts...'
      if (orderViewMode.value === 'history') return 'Chargement historique...'
      return 'Chargement...'
    }
    
    const getEmptyMessage = () => {
      if (orderViewMode.value === 'open') return 'Aucun ordre ouvert'
      if (orderViewMode.value === 'history') return 'Aucun historique'
      return 'Aucun élément'
    }
    
    const getEmptyStateIcon = () => {
      if (orderViewMode.value === 'open') return '📋'
      if (orderViewMode.value === 'history') return '📚'
      return '📄'
    }
    
    const getEmptyStateHint = () => {
      if (orderViewMode.value === 'open') return 'Les ordres que vous passez apparaîtront ici'
      if (orderViewMode.value === 'history') return 'L\'historique de vos trades s\'affichera ici'
      return ''
    }
    
    const getSectionTitle = () => {
      if (orderViewMode.value === 'open') return 'Ordres ouverts'
      if (orderViewMode.value === 'history') return 'Historique des trades'
      return 'Trading'
    }

    // Fonctions de formatage pour l'historique des trades
    const formatTradeDateTime = (dateString) => {
      if (!dateString) return '-'
      try {
        const date = new Date(dateString)
        const now = new Date()
        const diffInHours = (now - date) / (1000 * 60 * 60)
        
        if (diffInHours < 24) {
          // Aujourd'hui : afficher seulement l'heure
          return date.toLocaleTimeString('fr-FR', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })
        } else {
          // Plus ancien : afficher date + heure
          return date.toLocaleDateString('fr-FR', { 
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit', 
            minute: '2-digit'
          })
        }
      } catch (error) {
        return '-'
      }
    }

    const formatTradeAmount = (trade) => {
      if (!trade.quantity || !trade.price) return '-'
      try {
        const amount = parseFloat(trade.quantity) * parseFloat(trade.price)
        return `$${amount.toFixed(2)}`
      } catch (error) {
        return '-'
      }
    }


    // Fonction pour restaurer et charger le symbole
    const restoreSelectedSymbol = async () => {
      const savedSymbol = localStorage.getItem('selectedSymbol')
      if (savedSymbol && selectedBroker.value) {
        selectedSymbol.value = savedSymbol
        tradeForm.symbol = savedSymbol
        console.log('✅ Symbole restauré:', savedSymbol)
        
        // Charger le prix du symbole restauré
        await loadCurrentPrice()
      }
    }
    
    // Initialisation
    onMounted(() => {
      console.log('🔄 onMounted - selectedSymbol initial:', selectedSymbol.value)
      
      // RESTAURATION: Récupérer le symbole depuis localStorage
      const savedSymbol = localStorage.getItem('selectedSymbol')
      if (savedSymbol) {
        selectedSymbol.value = savedSymbol
        tradeForm.symbol = savedSymbol
        console.log('✅ onMounted - Symbole restauré:', savedSymbol)
      }
      
      loadBrokers()
      // Ne pas connecter WebSocket au démarrage - seulement quand broker sélectionné
    })
    
    // Configuration des onglets de types d'ordres
    const orderTypeTabs = computed(() => {
      const baseTypes = [
        {
          value: 'market',
          label: 'Marché',
          enabled: true,
          tooltip: 'Ordre exécuté immédiatement au prix du marché'
        },
        {
          value: 'limit',
          label: 'Limite',
          enabled: true,
          tooltip: 'Ordre exécuté à un prix spécifique ou meilleur'
        },
        {
          value: 'stop_loss',
          label: 'Stop Loss',
          enabled: exchangeInfo.value?.stop_orders || false,
          tooltip: 'Ordre de protection contre les pertes'
        },
        {
          value: 'take_profit',
          label: 'Take Profit',
          enabled: exchangeInfo.value?.stop_orders || false,
          tooltip: 'Ordre de prise de bénéfices automatique'
        },
        {
          value: 'sl_tp_combo',
          label: 'SL+TP',
          enabled: exchangeInfo.value?.raw_has?.createOrderWithTakeProfitAndStopLoss || false,
          tooltip: 'Ordre avec Stop Loss et Take Profit combinés'
        },
        {
          value: 'stop_limit',
          label: 'Stop Limit',
          enabled: exchangeInfo.value?.stop_limit_orders || false,
          tooltip: 'Ordre Stop avec prix limite spécifique'
        }
      ]
      
      return baseTypes
    })
    
    // Sélection d'un type d'ordre
    const selectOrderType = (orderType) => {
      const tab = orderTypeTabs.value.find(t => t.value === orderType)
      if (tab && tab.enabled) {
        tradeForm.order_type = orderType
        
        // Réinitialiser les champs spécifiques lors du changement de type
        if (orderType !== 'limit' && orderType !== 'sl_tp_combo' && orderType !== 'stop_limit') {
          tradeForm.price = null
        }
        if (orderType !== 'stop_loss' && orderType !== 'sl_tp_combo') {
          tradeForm.stop_loss_price = null
        }
        if (orderType !== 'take_profit' && orderType !== 'sl_tp_combo') {
          tradeForm.take_profit_price = null
        }
        if (orderType !== 'stop_limit') {
          tradeForm.trigger_price = null
        }
        
        // Recalculer si nécessaire
        if (tradeForm.quantity && selectedSymbol.value) {
          calculateValue()
        }
      }
    }

    
    // Nettoyage
    onUnmounted(() => {
      disconnectTradingSocket()
      disconnectOpenOrdersWebSocket()
      disconnectNotificationsSocket()
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
      portfolioPrices,
      portfolioAutoUpdate,
      portfolioPricesError,
      validationLoading,
      executionLoading,
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
      orderTypeTabs,
      selectOrderType,
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
      clearError,
      togglePortfolioAutoUpdate,
      loadPortfolioPrices,
      calculatePortfolioTotal,
      formatValue,
      formatPrice,
      // NOUVELLES FONCTIONS 3 ONGLETS
      getSectionTitle,
      getCurrentLoadingState,
      getLoadingMessage,
      getEmptyMessage,
      switchToTab,  // FONCTION MANQUANTE pour les clics onglets
      // NOUVELLES FONCTIONS FORMATAGE ORDRES
      formatOrderDateTime,
      formatOrderTotal,
      formatOrderDisplayPrice,
      formatOrderType,
      formatOrderQuantity,
      isNewOrder,
      // FONCTIONS FORMATAGE TRADES
      formatTradeDateTime,
      formatTradeAmount,
      clearExecutionResult,
      // NOUVELLES VARIABLES FILTRES BITGET
      selectedOrderTypeFilter,
      selectedPeriod,
      showExecutedOnly,
      orderTypeFilters,
      // NOUVELLES FONCTIONS FILTRES BITGET
      applyOrderTypeFilter,
      loadClosedOrdersWithFilters,
      filterOrderByType
    }
  }
}
</script>

<style scoped>
/* NOUVEAU CSS SECTION ORDRES - ARCHITECTURE TERMINAL 7 */

/* Section ordres */
.orders-section {
  margin-top: 1.5rem;
  max-width: 100%;
}

.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  border-bottom: 2px solid var(--color-primary);
  padding-bottom: 0.5rem;
}

.orders-header h2 {
  margin: 0;
  color: var(--color-primary);
  font-size: 1.2rem;
}

.orders-toggle {
  display: flex;
  gap: 0.5rem;
}

.toggle-btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem;
  font-weight: 500;
}

.toggle-btn:hover {
  background: var(--color-primary);
  color: var(--color-background);
}

.toggle-btn.active {
  background: var(--color-primary);
  color: var(--color-background);
  border-color: var(--color-primary);
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
}

/* NOUVEAU: Filtres avancés style Bitget */
.orders-filters {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.order-type-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.type-filter-btn {
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text-secondary);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
}

.type-filter-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-text);
  transform: translateY(-1px);
}

.type-filter-btn.active {
  background: linear-gradient(135deg, var(--color-primary) 0%, rgba(0, 212, 255, 0.8) 100%);
  color: var(--color-background);
  border-color: var(--color-primary);
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
  font-weight: 600;
}

.period-and-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.period-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.period-selector label {
  color: var(--color-text);
  font-weight: 500;
  font-size: 0.9rem;
}

.period-selector select {
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: border-color 0.2s ease;
  font-size: 0.9rem;
}

.period-selector select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 4px rgba(0, 212, 255, 0.3);
}

.order-options {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.order-options label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text);
  font-size: 0.9rem;
  cursor: pointer;
  user-select: none;
}

.order-options input[type="checkbox"] {
  width: 16px;
  height: 16px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.order-options input[type="checkbox"]:checked {
  background: var(--color-primary);
  border-color: var(--color-primary);
  box-shadow: 0 0 4px rgba(0, 212, 255, 0.3);
}

/* Container ordres avec scrollbar améliorer */
.orders-container {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

/* CORRECTION SCROLLBAR DARK THEME */
.orders-container::-webkit-scrollbar {
  width: 8px;
  background: var(--color-background);
}

.orders-container::-webkit-scrollbar-track {
  background: var(--color-surface);
  border-radius: 4px;
  margin: 2px;
}

.orders-container::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--color-primary) 0%, rgba(0, 212, 255, 0.6) 100%);
  border-radius: 4px;
  border: 1px solid var(--color-border);
}

.orders-container::-webkit-scrollbar-thumb:hover {
  background: var(--color-primary);
  box-shadow: 0 0 6px rgba(0, 212, 255, 0.5);
}

.orders-container::-webkit-scrollbar-corner {
  background: var(--color-surface);
}

/* NOUVEAU: En-tête des colonnes - ALIGNEMENT PARFAIT UNIFIÉ */
.order-item-header.unified-header {
  display: grid;
  grid-template-columns: 1fr 1fr 80px 60px 120px 120px 80px 80px 100px;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 2px solid var(--color-primary);
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--color-primary);
  text-transform: uppercase;
}

/* NOUVEAU: Ligne ordre - ALIGNEMENT PARFAIT UNIFIÉ */
.order-item-unified.unified-row {
  display: grid;
  grid-template-columns: 1fr 1fr 80px 60px 120px 120px 80px 80px 100px;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  transition: background-color 0.2s ease;
}

.order-item-unified.unified-row:hover {
  background: var(--color-surface-light);
}

.order-item-unified.unified-row.new-order {
  animation: highlight-new 2s ease-out;
}

/* NOUVEAU: Classes colonnes unifiées */
.col-datetime {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  text-align: left;
}

.col-symbol {
  font-weight: 600;
  color: var(--color-text);
  text-align: left;
}

.col-type .order-type-badge {
  display: inline-block;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  font-weight: 600;
  text-align: center;
}

.col-side .order-side-badge {
  display: inline-block;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  font-weight: 600;
  text-align: center;
  text-transform: uppercase;
}

.col-quantity {
  text-align: right;
  font-weight: 500;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.col-price {
  text-align: right;
  font-weight: 600;
  color: var(--color-text-light);
  font-variant-numeric: tabular-nums;
}

.col-total {
  text-align: right;
  font-weight: 600;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}

.col-status .order-status-badge {
  display: inline-block;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  font-weight: 600;
  text-align: center;
  text-transform: uppercase;
}

.col-actions {
  display: flex;
  gap: 0.25rem;
  justify-content: center;
  align-items: center;
}


/* STYLES SPÉCIFIQUES TYPES D'ORDRES - CORRECTION TRIGGER */
.type-market {
  background: linear-gradient(135deg, #007acc 0%, #005c99 100%);
  color: white;
  border: 1px solid #005c99;
}

.type-limit {
  background: linear-gradient(135deg, #6b46c1 0%, #553c9a 100%);
  color: white;
  border: 1px solid #553c9a;
}

.type-trigger {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border: 1px solid #d97706;
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.3);
}

.type-tpsl {
  background: linear-gradient(135deg, #10b981 0%, #047857 100%);
  color: white;
  border: 1px solid #047857;
}

.type-stop-loss {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: white;
  border: 1px solid #b91c1c;
}

.type-take-profit {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: white;
  border: 1px solid #047857;
}

.type-combo, .type-oco {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  color: white;
  border: 1px solid #6d28d9;
}

.type-unknown {
  background: var(--color-surface-light);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

.order-side {
  font-weight: 600;
  text-transform: uppercase;
  text-align: center;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
}

.order-side.buy {
  background: rgba(0, 255, 136, 0.15);
  color: var(--color-success);
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.order-side.sell {
  background: rgba(255, 0, 85, 0.15);
  color: var(--color-danger);
  border: 1px solid rgba(255, 0, 85, 0.3);
}

.order-quantity,
.order-price,
.order-total {
  text-align: right;
  font-weight: 500;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

/* CORRECTION AFFICHAGE PRIX TRIGGER */
.order-price {
  color: var(--color-text-light);
  font-weight: 600;
}

.order-total {
  color: var(--color-primary);
  font-weight: 600;
}

.order-status {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  text-align: center;
  text-transform: uppercase;
}

.status-open, .status-new, .status-live {
  background: rgba(0, 255, 136, 0.15);
  color: var(--color-success);
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.status-filled, .status-closed {
  background: rgba(0, 212, 255, 0.15);
  color: var(--color-primary);
  border: 1px solid rgba(0, 212, 255, 0.3);
}

.status-partially_filled {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.status-cancelled {
  background: rgba(255, 0, 85, 0.15);
  color: var(--color-danger);
  border: 1px solid rgba(255, 0, 85, 0.3);
}

.order-created {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  text-align: center;
}

.order-actions {
  display: flex;
  gap: 0.25rem;
  justify-content: center;
}

.action-btn {
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cancel-btn {
  background: rgba(255, 0, 85, 0.1);
  color: var(--color-danger);
  border: 1px solid rgba(255, 0, 85, 0.3);
}

.cancel-btn:hover:not(:disabled) {
  background: var(--color-danger);
  color: white;
  box-shadow: 0 2px 8px rgba(255, 0, 85, 0.3);
}

.edit-btn {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.edit-btn:hover:not(:disabled) {
  background: #f59e0b;
  color: white;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.no-orders {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-muted);
  font-style: italic;
}

/* STYLES UNIFIÉS - ALIGNEMENT PARFAIT DES COLONNES */
.order-item-header.unified-header {
  display: grid;
  grid-template-columns: 1fr 1fr 80px 60px 120px 120px 80px 80px 100px;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 2px solid var(--color-primary);
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  margin-bottom: 0.5rem;
}

.order-item-unified.unified-row {
  display: grid;
  grid-template-columns: 1fr 1fr 80px 60px 120px 120px 80px 80px 100px;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  margin-bottom: 0.25rem;
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.2s ease;
  font-size: 0.8rem;
}

.order-item-unified.unified-row:hover {
  background: rgba(0, 212, 255, 0.05);
  border-color: var(--color-primary);
}

/* Animation pour les nouveaux ordres - UNIFIÉE */
.order-item-unified.unified-row.new-order {
  animation: newOrderGlow 2s ease-in-out;
  border-color: var(--color-success);
}

@keyframes newOrderGlow {
  0% {
    background: rgba(0, 255, 136, 0.1);
    border-color: var(--color-success);
    box-shadow: 0 0 15px rgba(0, 255, 136, 0.4);
  }
  100% {
    background: rgba(255, 255, 255, 0.02);
    border-color: var(--color-border);
    box-shadow: none;
  }
}

/* Classes CSS pour alignement exact des colonnes */
.col-datetime {
  color: var(--color-text-secondary);
  font-weight: 500;
  text-align: left;
}

.col-symbol {
  color: var(--color-text);
  font-weight: 600;
  text-align: left;
}

.col-type {
  text-align: center;
}

.col-side {
  text-align: center;
}

.col-quantity {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.col-price {
  text-align: right;
  font-variant-numeric: tabular-nums;
  color: var(--color-text-light);
}

.col-total {
  text-align: right;
  font-variant-numeric: tabular-nums;
  color: var(--color-primary);
  font-weight: 600;
}

.col-status {
  text-align: center;
}

.col-actions {
  text-align: center;
  display: flex;
  justify-content: center;
  gap: 0.25rem;
}

/* Badges pour les sides avec couleurs améliorées */
.order-side-badge {
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  border: 1px solid;
}

.order-side-badge.buy {
  background: rgba(0, 255, 136, 0.15);
  color: var(--color-success);
  border-color: rgba(0, 255, 136, 0.3);
}

.order-side-badge.sell {
  background: rgba(255, 0, 85, 0.15);
  color: var(--color-danger);
  border-color: rgba(255, 0, 85, 0.3);
}

/* Badges pour les status avec couleurs améliorées */
.order-status-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  text-align: center;
  text-transform: uppercase;
  border: 1px solid;
}

.order-status-badge.status-open,
.order-status-badge.status-new, 
.order-status-badge.status-live {
  background: rgba(0, 255, 136, 0.15);
  color: var(--color-success);
  border-color: rgba(0, 255, 136, 0.3);
}

.order-status-badge.status-filled,
.order-status-badge.status-closed {
  background: rgba(0, 212, 255, 0.15);
  color: var(--color-primary);
  border-color: rgba(0, 212, 255, 0.3);
}

.order-status-badge.status-partially_filled {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.3);
}

.order-status-badge.status-cancelled {
  background: rgba(255, 0, 85, 0.15);
  color: var(--color-danger);
  border-color: rgba(255, 0, 85, 0.3);
}

/* Responsive pour les ordres - CORRIGÉ */
@media (max-width: 1400px) {
  .order-item-header.unified-header,
  .order-item-unified.unified-row {
    font-size: 0.65rem;
    padding: 0.5rem 0.75rem;
    grid-template-columns: 1fr 70px 50px 100px 100px 80px 70px 100px 80px;
  }
  
  .orders-container {
    max-height: 350px;
  }
}

@media (max-width: 1200px) {
  .order-item-header.unified-header,
  .order-item-unified.unified-row {
    grid-template-columns: 1fr 60px 45px 90px 90px 70px 60px 90px 70px;
    font-size: 0.6rem;
    gap: 0.25rem;
  }
}

/* Utilisation des variables CSS globales cohérentes avec les autres pages */

.trading-manual {
  padding: 1rem 1.5rem;
  width: 100%;
  max-width: none;
  margin: 0;
  background: var(--color-background);
  min-height: 100vh;
  color: var(--color-text);
  font-family: 'Segoe UI', -apple-system, system-ui, sans-serif;
  box-sizing: border-box;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: linear-gradient(135deg, var(--color-background), #2a2a2a);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  box-sizing: border-box;
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
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-close {
  background: none;
  border: none;
  color: var(--color-danger);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.error-close:hover {
  background: var(--color-danger);
  color: var(--color-text);
  transform: scale(1.1);
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  gap: 1.5rem;
  min-height: 600px;
  width: 100%;
  box-sizing: border-box;
  margin-top: 1rem;
}

.section-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
  min-height: 400px;
  overflow-y: auto;
  box-sizing: border-box;
}

.portfolio-column, .symbols-column, .trading-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Styles spécifiques des colonnes - inspirés du Heartbeat */
.portfolio-column .section-card {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  border-color: #00d4ff;
}

.symbols-column .section-card {
  background: linear-gradient(135deg, #2e1a2e, #3e1a3e);
  border-color: #ff0055;
}

.trading-column .section-card {
  background: linear-gradient(135deg, #1a2e1a, #1e3e1e);
  border-color: #00ff88;
}

.exchange-capabilities {
  background: linear-gradient(135deg, #2e2e1a, #3e3e1e) !important;
  border-color: #ffaa00 !important;
}

/* Styles des titres - inspirés du Heartbeat */
.section-card h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.2rem;
  font-weight: 600;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 0.75rem;
}

/* Titres spécifiques par section avec couleurs néon */
.portfolio-column h2 {
  color: #00d4ff;
}

.symbols-column h2 {
  color: #ff0055;
}

.trading-column h2 {
  color: #00ff88;
}

.exchange-capabilities h2 {
  color: #ffaa00;
}


.section-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

/* Hover spécifique par section avec leurs couleurs */
.portfolio-column .section-card:hover {
  border-color: #00d4ff;
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}

.symbols-column .section-card:hover {
  border-color: #ff0055;
  box-shadow: 0 4px 12px rgba(255, 0, 85, 0.3);
}

.trading-column .section-card:hover {
  border-color: #00ff88;
  box-shadow: 0 4px 12px rgba(0, 255, 136, 0.3);
}

.exchange-capabilities:hover {
  border-color: #ffaa00 !important;
  box-shadow: 0 4px 12px rgba(255, 170, 0, 0.3) !important;
}

/* Animation pour les éléments actifs */
@keyframes pulseGlow {
  0% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.3); }
  50% { box-shadow: 0 0 15px rgba(0, 212, 255, 0.6); }
  100% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.3); }
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
  opacity: 0.5;
  pointer-events: none;
}

/* Portfolio styles */
.portfolio-summary {
  background: var(--color-surface);
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
  background: var(--color-success);
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

/* Portfolio Table styles */
.portfolio-table-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  background: var(--color-background);
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) var(--color-background);
}

.portfolio-table-container::-webkit-scrollbar {
  width: 6px;
}

.portfolio-table-container::-webkit-scrollbar-track {
  background: var(--color-background);
  border-radius: 3px;
}

.portfolio-table-container::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.portfolio-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.portfolio-table thead {
  background: var(--color-surface);
  position: sticky;
  top: 0;
  z-index: 1;
}

.portfolio-table th {
  padding: 0.75rem 0.5rem;
  text-align: left;
  font-weight: 600;
  color: var(--color-text);
  border-bottom: 2px solid var(--color-border);
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.portfolio-table tbody tr {
  transition: all 0.2s ease;
}

.portfolio-table tbody tr:hover {
  background: var(--color-surface);
}

.portfolio-table td {
  padding: 0.75rem 0.5rem;
  border-bottom: 1px solid var(--color-border);
}

.portfolio-table tbody tr:last-child td {
  border-bottom: none;
}

.asset-cell {
  font-weight: 600;
  color: var(--color-text);
  min-width: 60px;
}

.quantity-cell {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: var(--color-primary);
  font-weight: 500;
  text-align: right;
  min-width: 100px;
}

.price-cell {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: var(--color-text-secondary);
  text-align: right;
  min-width: 80px;
}

.total-cell {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-weight: 600;
  text-align: right;
  min-width: 90px;
}

.total-value {
  color: var(--color-success);
}

.no-price, .no-total {
  color: var(--color-text-secondary);
  opacity: 0.6;
  font-style: italic;
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
  box-shadow: 0 0 8px rgba(from var(--color-primary) r g b / 0.5);
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
  border-radius: 3px;
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
  background: var(--color-surface);
  color: var(--color-primary);
  border-color: var(--color-primary);
  font-weight: 600;
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.1);
}

/* Order Tabs Styles - Alignement complet sur la largeur */
.order-tabs {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.5rem;
  width: 100%;
  justify-content: space-between;
}

.order-tab {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  padding: 0.6rem 0.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 0.85rem;
  flex: 1;
  text-align: center;
  position: relative;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.order-tab:hover:not(.disabled) {
  background: var(--color-surface);
  border-color: var(--color-primary);
  color: var(--color-text);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.15);
}

.order-tab.active {
  background: linear-gradient(135deg, var(--color-primary), #0099cc);
  border-color: var(--color-primary);
  color: white;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
  transform: translateY(-1px);
}

.order-tab.disabled {
  background: var(--color-surface);
  border-color: var(--color-border);
  color: var(--color-text-muted);
  cursor: not-allowed;
  opacity: 0.5;
}

.order-tab.disabled:hover {
  transform: none;
  box-shadow: none;
}

/* Price and Direction Section */
.price-direction-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  align-items: stretch;
}

.price-zone {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.direction-zone {
  flex: 1;
  display: flex;
  align-items: center;
}

/* Side Buttons Vertical */
.side-buttons-vertical {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.side-btn {
  padding: 0.8rem 1rem;
  border: 2px solid transparent;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.buy-btn {
  background: rgba(0, 255, 136, 0.1);
  color: var(--color-success);
  border-color: rgba(0, 255, 136, 0.3);
}

.buy-btn:hover,
.buy-btn.active {
  background: var(--color-success);
  color: var(--color-background);
  border-color: var(--color-success);
  box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
  transform: translateY(-2px);
}

.sell-btn {
  background: rgba(255, 0, 85, 0.1);
  color: var(--color-danger);
  border-color: rgba(255, 0, 85, 0.3);
}

.sell-btn:hover,
.sell-btn.active {
  background: var(--color-danger);
  color: white;
  border-color: var(--color-danger);
  box-shadow: 0 4px 15px rgba(255, 0, 85, 0.3);
  transform: translateY(-2px);
}

/* Order Type Fields */
.order-type-fields {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.combo-fields {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Form Field Row - Label à gauche, Input à droite */
.form-field-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-field-row label {
  flex: 1;
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: 0.9rem;
  text-align: left;
  white-space: nowrap;
}

.form-field-row input {
  flex: 2;
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  color: var(--color-text);
  font-size: 1rem;
  transition: all 0.3s ease;
  font-family: 'JetBrains Mono', monospace;
}

.form-field-row input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.1);
  transform: translateY(-1px);
}

.form-field-row input::placeholder {
  color: var(--color-text-muted);
  font-style: italic;
}

/* Input Mode Section */
.input-mode-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}

.radio-group-horizontal {
  display: flex;
  gap: 2rem;
  justify-content: center;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  color: var(--color-text-secondary);
  font-weight: 500;
  transition: all 0.3s ease;
}

.radio-label:hover {
  color: var(--color-text);
}

.radio-label input[type="radio"] {
  width: 18px;
  height: 18px;
  accent-color: var(--color-primary);
  cursor: pointer;
}

.radio-label span {
  font-size: 1rem;
  user-select: none;
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
  background: var(--color-surface);
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
  background: var(--color-primary);
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

/* Form group inline pour libellé et input côte à côte */
.form-group-inline {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.form-group-inline label {
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  margin-bottom: 0;
  min-width: 100px;
  flex-shrink: 0;
}

.form-group-inline input[type="number"] {
  flex: 1;
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  color: var(--color-text);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

/* Layout symbole et contrôles côte à côte */
.symbol-controls-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.symbol-info {
  flex: 1;
  min-width: 0;
}

.trading-controls {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.control-group {
  margin-bottom: 0.75rem;
}

.control-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.control-group .radio-group {
  gap: 1rem;
}

/* Header Portfolio avec bouton toggle */
.portfolio-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.portfolio-auto-btn {
  padding: 0.5rem 0.75rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.portfolio-auto-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.portfolio-auto-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
}

/* Zone valeur totale avec états */
.portfolio-total-error {
  color: var(--color-danger);
  font-weight: 500;
}

.portfolio-total-success {
  color: var(--color-success);
}

.portfolio-total-loading {
  color: var(--color-text-secondary);
}

/* Valeurs USD dans les balances */
.usd-value {
  color: var(--color-success);
  font-size: 0.9rem;
  margin-left: 0.5rem;
  font-weight: 500;
}

/* Filtres symboles sur une ligne */
.filters {
  margin-bottom: 1rem;
}

.filter-checkboxes {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.filter-checkboxes label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.filter-checkboxes label:hover {
  color: var(--color-primary);
}

.filter-checkboxes input[type="checkbox"] {
  width: 16px;
  height: 16px;
  background: var(--color-background);
  border: 2px solid var(--color-border);
  border-radius: 3px;
  cursor: pointer;
  appearance: none;
  position: relative;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.filter-checkboxes input[type="checkbox"]:checked {
  border-color: var(--color-primary);
  background: var(--color-primary);
}

.filter-checkboxes input[type="checkbox"]:checked::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 11px;
  font-weight: bold;
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
  box-shadow: 0 0 8px rgba(from var(--color-primary) r g b / 0.5);
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
  background: var(--color-surface);
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
  background: var(--color-surface);
  border-color: var(--color-success);
  animation: pulse-success 2s ease-in-out;
}

.trade-summary.execution-success::before {
  background: var(--color-success);
  height: 3px;
}

.trade-summary.execution-error {
  background: var(--color-surface);
  border: 1px solid var(--color-danger);
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

/* Styles pour l'état d'attente */
.trade-summary.execution-waiting {
  background: var(--color-surface);
  border-color: var(--color-primary);
  animation: pulse-waiting 2s ease-in-out infinite;
}

.trade-summary.execution-waiting::before {
  background: var(--color-primary);
  height: 3px;
}

.trade-summary.execution-waiting p:first-child {
  color: var(--color-primary);
  font-weight: 600;
}

/* Styles pour l'ordre annulé */
.trade-summary.execution-cancelled {
  background: var(--color-surface);
  border-color: var(--color-warning);
  animation: pulse-cancelled 2s ease-in-out;
}

.trade-summary.execution-cancelled::before {
  background: var(--color-warning);
  height: 3px;
}

.trade-summary.execution-cancelled p:first-child {
  color: var(--color-warning);
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

@keyframes pulse-waiting {
  0%, 100% { box-shadow: 0 0 0 0 rgba(0, 212, 255, 0.4); }
  50% { box-shadow: 0 0 15px 3px rgba(0, 212, 255, 0.2); }
}

@keyframes pulse-cancelled {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.4); }
  50% { box-shadow: 0 0 15px 3px rgba(255, 193, 7, 0.1); }
}

/* Styles pour la nouvelle structure avec bouton de fermeture */
.trade-summary.execution-result {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  position: relative;
}

.execution-content {
  flex: 1;
}

.execution-close {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 50%;
  transition: all 0.3s ease;
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.execution-close:hover {
  background: var(--color-danger);
  color: white;
}

.execution-timestamp {
  margin-top: 0.5rem !important;
  opacity: 0.7;
}

.error-details {
  margin-top: 0.5rem;
  opacity: 0.8;
}

.error-details p {
  margin: 0.25rem 0 !important;
  font-style: italic;
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
  background: var(--color-warning);
  color: var(--crypto-bg-primary);
  border: 1px solid var(--color-warning);
}

.btn-validate:hover:not(:disabled) {
  background: var(--color-warning);
  box-shadow: 0 0 20px rgba(from var(--color-warning) r g b / 0.5);
  transform: translateY(-1px);
}

.btn-execute {
  background: var(--color-success);
  color: var(--crypto-bg-primary);
  border: 1px solid var(--color-success);
}

.btn-execute:hover:not(:disabled) {
  background: var(--color-success);
  box-shadow: 0 0 20px rgba(from var(--color-success) r g b / 0.5);
  transform: translateY(-1px);
}

/* Effets de clic (active state) */
.btn-validate:active:not(:disabled) {
  background: var(--color-warning);
  transform: translateY(1px) scale(0.98);
  box-shadow: 0 2px 8px rgba(from var(--color-warning) r g b / 0.4);
  transition: all 0.1s ease;
}

.btn-execute:active:not(:disabled) {
  background: var(--color-success);
  transform: translateY(1px) scale(0.98);
  box-shadow: 0 2px 8px rgba(from var(--color-success) r g b / 0.4);
  transition: all 0.1s ease;
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
  background: var(--color-surface);
  border: 1px solid var(--color-danger);
  padding: 1rem;
  border-radius: 0.5rem;
  margin-top: 1rem;
}

.validation-errors strong {
  font-weight: 600;
  color: var(--color-danger);
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
  background: var(--color-surface);
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
  border-radius: 3px;
}

.trades-list::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.trade-item {
  display: grid;
  grid-template-columns: 80px 50px 80px 90px 70px 90px 70px;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--color-border);
  align-items: center;
  font-size: 0.85rem;
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
  background: var(--color-surface);
  color: var(--color-success);
  border: 1px solid var(--color-success);
  box-shadow: 0 0 8px rgba(from var(--color-success) r g b / 0.25);
}

.trade-side.sell {
  background: var(--color-surface);
  color: var(--color-danger);
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
  background: var(--color-surface);
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

.trade-status.pending {
  background: var(--color-surface);
  color: var(--color-warning);
  border: 1px solid var(--color-warning);
}

.trade-status.failed {
  background: var(--color-surface);
  border: 1px solid var(--color-danger);
  animation: warningPulse 2s infinite;
}

/* Nouveaux styles pour les éléments de trades */
.trade-datetime {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  text-align: center;
}

.trade-price {
  font-family: 'JetBrains Mono', monospace;
  text-align: right;
  color: var(--color-text);
  font-weight: 500;
}

.trade-amount {
  font-family: 'JetBrains Mono', monospace;
  text-align: right;
  color: var(--color-primary);
  font-weight: 600;
  background: rgba(0, 212, 255, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
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
  background: var(--color-primary);
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
  background: rgba(255,255,255,0.1);
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
  background: var(--color-surface);
  color: var(--color-success);
  border-color: var(--color-success);
  box-shadow: 0 0 20px rgba(0, 200, 100, 0.1);
}

.validation-status.warning {
  background: var(--color-surface);
  color: var(--color-warning);
  border-color: var(--color-warning);
  box-shadow: 0 0 20px rgba(255, 165, 0, 0.1);
  animation: warningPulse 2s infinite;
}

.validation-status.error {
  background: var(--color-surface);
  border: 1px solid var(--color-danger);
  animation: warningPulse 2s infinite;
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
  background: var(--color-surface);
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
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
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
  color: var(--color-error);
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

/* === NOUVEAUX STYLES POUR COLONNE TYPE D'ORDRE === */

/* En-tête des colonnes pour ordres */
.order-item-header {
  display: grid;
  grid-template-columns: 110px 50px 90px 90px 90px 80px 80px 70px 100px;
  gap: 0.75rem;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Ligne d'ordre unifiée avec nouvelle colonne type - CORRIGÉ ALIGNEMENT */
.order-item-unified {
  display: grid;
  grid-template-columns: 1fr 60px 100px 80px 120px 120px 100px 80px 120px;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  transition: all 0.2s ease;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
}

/* Header avec même alignement que les lignes */
.order-item-header {
  display: grid;
  grid-template-columns: 1fr 60px 100px 80px 120px 120px 100px 80px 120px;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 2px solid var(--color-primary);
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.order-item-unified:hover {
  border-color: var(--color-primary);
  background: rgba(0, 212, 255, 0.05);
  transform: translateY(-1px);
}

/* Styles des colonnes individuelles */
.order-datetime {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  font-family: 'JetBrains Mono', monospace;
}

.order-side {
  font-weight: 600;
  text-align: center;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
}

.order-side.buy {
  color: var(--color-success);
  background: rgba(0, 255, 136, 0.1);
}

.order-side.sell {
  color: var(--color-danger);
  background: rgba(255, 0, 85, 0.1);
}

/* NOUVEAUX STYLES POUR TYPES D'ORDRES */
.order-type {
  font-weight: 500;
  text-align: center;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  border: 1px solid transparent;
}

/* Styles par type d'ordre */
.type-market {
  color: #00d4ff;
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.3);
}

.type-limit {
  color: #ffaa00;
  background: rgba(255, 170, 0, 0.1);
  border-color: rgba(255, 170, 0, 0.3);
}

.type-stop-loss {
  color: #ff0055;
  background: rgba(255, 0, 85, 0.1);
  border-color: rgba(255, 0, 85, 0.3);
}

.type-take-profit {
  color: #00ff88;
  background: rgba(0, 255, 136, 0.1);
  border-color: rgba(0, 255, 136, 0.3);
}

.type-stop-limit {
  color: #ff8800;
  background: rgba(255, 136, 0, 0.1);
  border-color: rgba(255, 136, 0, 0.3);
}

.type-combo {
  color: #8800ff;
  background: rgba(136, 0, 255, 0.1);
  border-color: rgba(136, 0, 255, 0.3);
}

.type-trigger {
  color: #00ffaa;
  background: rgba(0, 255, 170, 0.1);
  border-color: rgba(0, 255, 170, 0.3);
}

.type-unknown {
  color: var(--color-text-secondary);
  background: rgba(128, 128, 128, 0.1);
  border-color: rgba(128, 128, 128, 0.3);
}

/* Autres colonnes */
.order-symbol {
  font-weight: 500;
  color: var(--color-text);
}

.order-quantity {
  text-align: right;
  font-family: 'JetBrains Mono', monospace;
  color: var(--color-text-secondary);
}

.order-price {
  text-align: right;
  font-family: 'JetBrains Mono', monospace;
  color: var(--color-text);
}

.order-total {
  text-align: right;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
  color: var(--color-text);
}

.order-status {
  font-weight: 500;
  text-align: center;
  font-size: 0.65rem;
}

.order-status.open,
.order-status.new,
.order-status.pending {
  color: var(--color-warning);
}

.order-status.filled,
.order-status.closed {
  color: var(--color-success);
}

.order-status.canceled,
.order-status.cancelled,
.order-status.rejected {
  color: var(--color-danger);
}

/* Actions en mini boutons */
.order-actions {
  display: flex;
  gap: 0.25rem;
  justify-content: center;
}

.btn-cancel-mini,
.btn-edit-mini {
  background: none;
  border: none;
  padding: 0.2rem;
  cursor: pointer;
  font-size: 0.8rem;
  border-radius: 0.2rem;
  transition: all 0.2s ease;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-cancel-mini:hover:not(:disabled) {
  background: rgba(255, 0, 85, 0.2);
  transform: scale(1.1);
}

.btn-edit-mini:hover:not(:disabled) {
  background: rgba(255, 170, 0, 0.2);
  transform: scale(1.1);
}

.btn-cancel-mini:disabled,
.btn-edit-mini:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* Responsive pour écrans plus petits */
@media (max-width: 1200px) {
  .order-item-header,
  .order-item-unified {
    grid-template-columns: 100px 45px 75px 75px 75px 70px 70px 60px 90px;
    font-size: 0.7rem;
  }
}

@media (max-width: 1000px) {
  .order-item-header,
  .order-item-unified {
    grid-template-columns: 90px 40px 70px 70px 70px 65px 65px 55px 80px;
    font-size: 0.65rem;
    gap: 0.5rem;
  }
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

/* === STYLES POUR 2 ONGLETS SIMPLIFIÉS === */
/* Système d'onglets pour Ordres ouverts / Historique */

.orders-toggle {
  display: flex;
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 212, 255, 0.1);
}

/* Support pour 2 onglets (open/history) */
.orders-toggle.two-tabs .toggle-btn {
  flex: 1;
  min-width: 150px;
}

.toggle-btn {
  flex: 1;
  padding: 12px 20px;
  background: #1a1a1a;
  color: #888;
  border: 1px solid #333;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 0.9rem;
  text-align: center;
  border-radius: 0;
}

.toggle-btn:first-child {
  border-radius: 8px 0 0 8px;
  border-right: none;
}

.toggle-btn:not(:first-child):not(:last-child) {
  border-left: none;
  border-right: none;
}

.toggle-btn:last-child {
  border-radius: 0 8px 8px 0;
  border-left: none;
}

.toggle-btn.active {
  background: linear-gradient(135deg, #00d4ff, #0099cc);
  color: white;
  border-color: #00d4ff;
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.4);
}

.toggle-btn:hover:not(.active) {
  background: #2a2a2a;
  color: #00d4ff;
  border-color: #444;
}

/* === STYLES POSITIONS P&L TERMINAL 7 === */

.positions-list {
  max-height: 300px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) var(--color-background);
}

.positions-list::-webkit-scrollbar {
  width: 6px;
}

.positions-list::-webkit-scrollbar-track {
  background: var(--color-background);
  border-radius: 3px;
}

.positions-list::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.position-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-bottom: 1px solid var(--color-border);
  transition: all 0.2s ease;
  border-radius: 6px;
  margin-bottom: 2px;
  background: var(--color-surface);
}

.position-item:hover {
  background: var(--color-background);
  border-color: var(--color-primary);
  transform: translateX(2px);
}

.position-item:last-child {
  border-bottom: none;
}

.position-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.position-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.position-symbol {
  font-weight: 600;
  color: var(--color-text);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.95rem;
}

.position-side {
  font-weight: 600;
  text-align: center;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.position-side.buy {
  background: rgba(0, 255, 136, 0.1);
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

.position-side.sell {
  background: rgba(255, 0, 85, 0.1);
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
}

.position-details {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  font-family: 'JetBrains Mono', monospace;
}

.position-pnl {
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 80px;
}

.position-pnl-value {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 0.9rem;
}

.position-pnl-percent {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  opacity: 0.8;
}

/* Couleurs P&L */
.profit {
  color: var(--color-success);
}

.loss {
  color: var(--color-danger);
}

.neutral {
  color: var(--color-text-secondary);
}

.position-method {
  background: rgba(0, 212, 255, 0.1);
  color: var(--color-primary);
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* Animation pour les positions qui se mettent à jour */
.position-item.updating {
  animation: positionUpdate 1s ease-in-out;
}

@keyframes positionUpdate {
  0% { background: var(--color-surface); }
  50% { background: rgba(0, 212, 255, 0.1); }
  100% { background: var(--color-surface); }
}

/* Message si pas de positions */
.no-positions {
  text-align: center;
  color: var(--color-text-secondary);
  font-style: italic;
  padding: 2rem;
  background: var(--color-background);
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  margin: 1rem 0;
}

.no-positions .icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

/* === ENHANCED UX STYLES - SOLUTION 2 PHASE 3 === */

/* Onglets avec icônes et différenciation visuelle */
.three-tabs .toggle-btn {
  position: relative;
  padding: 0.75rem 1.25rem;
  font-weight: 500;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.three-tabs .tab-open.active {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(0, 212, 255, 0.05));
  border-color: var(--color-primary);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
}

.three-tabs .tab-positions.active {
  background: linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(0, 255, 136, 0.05));
  border-color: var(--color-success);
  box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
}

.three-tabs .tab-history.active {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.05));
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
}

/* États de chargement améliorés */
.loading-spinner-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
}

.spinner-inline {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 212, 255, 0.3);
  border-top: 2px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* États vides améliorés */
.no-data-illustration {
  text-align: center;
  padding: 3rem 2rem;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.1));
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  margin: 1rem 0;
}

.no-data-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.6;
  filter: grayscale(0.5);
}

.no-data-message {
  color: var(--color-text);
  font-size: 1.1rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.no-data-hint {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  font-style: italic;
  opacity: 0.8;
}

/* Positions Enhanced - Layout et visibilité */
.positions-list.enhanced {
  gap: 1rem;
}

.position-item {
  transition: all 0.3s ease;
  border-radius: 8px;
  overflow: hidden;
}

.position-item.profit-position {
  background: linear-gradient(135deg, rgba(0, 255, 136, 0.08), rgba(0, 255, 136, 0.02));
  border: 1px solid rgba(0, 255, 136, 0.2);
  box-shadow: 0 2px 8px rgba(0, 255, 136, 0.1);
}

.position-item.loss-position {
  background: linear-gradient(135deg, rgba(255, 0, 85, 0.08), rgba(255, 0, 85, 0.02));
  border: 1px solid rgba(255, 0, 85, 0.2);
  box-shadow: 0 2px 8px rgba(255, 0, 85, 0.1);
}

.position-item.neutral-position {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.position-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

/* Header Enhanced */
.position-header.enhanced {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.position-main-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.position-symbol-enhanced {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: 0.5px;
}

.position-side-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.position-side-badge.buy {
  background: rgba(0, 255, 136, 0.2);
  color: var(--color-success);
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.position-side-badge.sell {
  background: rgba(255, 0, 85, 0.2);
  color: var(--color-danger);
  border: 1px solid rgba(255, 0, 85, 0.3);
}

.position-pnl-container {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.position-pnl-enhanced {
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.position-pnl-enhanced.profit {
  color: var(--color-success);
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
}

.position-pnl-enhanced.loss {
  color: var(--color-danger);
  text-shadow: 0 0 10px rgba(255, 0, 85, 0.5);
}

.position-pnl-enhanced.neutral {
  color: var(--color-text-secondary);
}

.pnl-percentage {
  font-size: 0.9rem;
  font-weight: 500;
  opacity: 0.8;
}

.pnl-percentage.profit {
  color: var(--color-success);
}

.pnl-percentage.loss {
  color: var(--color-danger);
}

/* Détails Enhanced */
.position-details-enhanced {
  padding: 1rem 1.25rem;
}

.position-trade-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.metric-label {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
}

.metric-value {
  color: var(--color-text);
  font-weight: 600;
  font-size: 0.9rem;
}

/* Barre de progression P&L */
.pnl-progress-bar {
  margin-top: 0.75rem;
}

.pnl-bar-background {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.pnl-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}

.pnl-bar-fill.profit {
  background: linear-gradient(90deg, rgba(0, 255, 136, 0.5), var(--color-success));
}

.pnl-bar-fill.loss {
  background: linear-gradient(90deg, rgba(255, 0, 85, 0.5), var(--color-danger));
}

/* === SCROLLBARS THÈME DARK AMÉLIORÉ === */

/* Scrollbars pour la section des ordres */
.orders-section {
  max-height: 70vh;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 212, 255, 0.5) rgba(255, 255, 255, 0.1);
}

/* Webkit scrollbars pour Chrome/Safari/Edge */
.orders-section::-webkit-scrollbar {
  width: 8px;
}

.orders-section::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.orders-section::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, 
    rgba(0, 212, 255, 0.6) 0%, 
    rgba(0, 212, 255, 0.4) 50%, 
    rgba(0, 212, 255, 0.8) 100%);
  border-radius: 4px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.orders-section::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, 
    rgba(0, 212, 255, 0.8) 0%, 
    rgba(0, 212, 255, 0.6) 50%, 
    rgba(0, 212, 255, 1.0) 100%);
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.4);
}

.orders-section::-webkit-scrollbar-corner {
  background: rgba(255, 255, 255, 0.05);
}

/* Scrollbars globaux pour l'application */
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: var(--color-background);
  border-radius: 5px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, 
    rgba(0, 212, 255, 0.3) 0%, 
    rgba(0, 212, 255, 0.5) 50%, 
    rgba(0, 212, 255, 0.3) 100%);
  border-radius: 5px;
  border: 1px solid rgba(0, 212, 255, 0.1);
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, 
    rgba(0, 212, 255, 0.5) 0%, 
    rgba(0, 212, 255, 0.7) 50%, 
    rgba(0, 212, 255, 0.5) 100%);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
}

/* === AMÉLIORATION AFFICHAGE ORDRES TRIGGER === */

/* Indicateurs visuels pour ordres avec prix de déclenchement */
.order-price:has-text("(T)"), 
.order-price:has-text("(SL)"), 
.order-price:has-text("(TP)") {
  color: var(--color-primary);
  font-weight: 600;
  text-shadow: 0 0 5px rgba(0, 212, 255, 0.3);
}

/* Style spécial pour ordres TRIGGER */
.order-item-unified:has(.type-trigger) {
  border-left: 3px solid rgba(0, 255, 170, 0.8);
  background: linear-gradient(135deg, 
    rgba(0, 255, 170, 0.03) 0%, 
    rgba(0, 255, 170, 0.01) 100%);
}

.order-item-unified:has(.type-trigger):hover {
  border-left: 3px solid rgba(0, 255, 170, 1.0);
  box-shadow: 0 4px 15px rgba(0, 255, 170, 0.15);
}

/* Animation pulse pour nouveaux ordres */
@keyframes newOrderPulse {
  0% { 
    box-shadow: 0 0 0 0 rgba(0, 212, 255, 0.7);
    border-color: var(--color-primary);
  }
  50% { 
    box-shadow: 0 0 0 4px rgba(0, 212, 255, 0.3);
  }
  100% { 
    box-shadow: 0 0 0 0 rgba(0, 212, 255, 0);
    border-color: var(--color-border);
  }
}

.order-item-unified.new-order {
  animation: newOrderPulse 2s ease-out;
}

/* Footer Enhanced */
.position-footer-enhanced {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.25rem;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.position-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.position-time {
  color: var(--color-text-secondary);
  font-size: 0.8rem;
  font-family: 'Courier New', monospace;
}

.position-method-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid;
}

.position-method-badge.order_monitor {
  background: rgba(0, 212, 255, 0.1);
  color: var(--color-primary);
  border-color: rgba(0, 212, 255, 0.3);
}

.position-method-badge.manual {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text);
  border-color: rgba(255, 255, 255, 0.2);
}

.position-calculation {
  color: var(--color-text-secondary);
  font-size: 0.8rem;
  font-style: italic;
}

.calculation-method {
  font-family: 'Courier New', monospace;
  background: rgba(0, 0, 0, 0.3);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Responsive Design - Écrans moyens à petits */
@media (max-width: 1200px) {
  .main-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    width: 100%;
  }
  
  /* Ordre d'affichage vertical demandé selon spécifications */
  .portfolio-column {
    order: 1; /* Portfolio en premier */
  }
  
  .symbols-column {
    order: 2; /* Symboles disponibles en deuxième */
  }
  
  .trading-column {
    order: 3; /* Passer un ordre en troisième */
  }
  
  /* Contrôle précis des sections individuelles */
  .section-card {
    width: 100%;
  }
  
  /* Sections dans trading-column - ordre spécifique demandé */
  .trading-column .section-card:first-child {
    order: 1; /* Passer un ordre */
  }
  
  .orders-section {
    order: 4; /* Ordres ouverts après "Passer un ordre" */
  }
  
  .recent-trades {
    order: 5; /* Trades récents */
  }
  
  .exchange-capabilities {
    order: 6; /* Capacités exchange en dernier */
  }
}

/* === STYLES AFFICHAGE UNIFORME ORDRES === */
.orders-list.unified {
  max-height: 300px;
  overflow-y: auto;
}

.order-item-unified {
  display: grid;
  grid-template-columns: auto auto auto 1fr auto auto auto auto;
  gap: 1rem;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: background-color 0.2s ease;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
}

.order-item-unified:hover {
  background-color: rgba(0, 212, 255, 0.05);
}

.order-datetime {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  min-width: 120px;
}

.order-side.buy {
  color: var(--color-success);
  font-weight: 600;
  background: rgba(0, 255, 136, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-align: center;
  min-width: 60px;
}

.order-side.sell {
  color: var(--color-danger);
  font-weight: 600;
  background: rgba(255, 0, 85, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-align: center;
  min-width: 60px;
}

.order-symbol {
  color: var(--color-primary);
  font-weight: 500;
  min-width: 80px;
}

.order-quantity {
  text-align: right;
  color: rgba(255, 255, 255, 0.9);
  min-width: 100px;
}

.order-price {
  text-align: right;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  min-width: 80px;
}

.order-total {
  text-align: right;
  color: var(--color-primary);
  font-weight: 600;
  min-width: 80px;
}

.order-status.completed {
  color: var(--color-success);
  background: rgba(0, 255, 136, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-align: center;
  font-size: 0.8rem;
  min-width: 80px;
}

.order-status.pending, .order-status.open {
  color: var(--color-warning, #fbbf24);
  background: rgba(251, 191, 36, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-align: center;
  font-size: 0.8rem;
  min-width: 80px;
}

.order-status.canceled, .order-status.cancelled {
  color: var(--color-danger);
  background: rgba(255, 0, 85, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-align: center;
  font-size: 0.8rem;
  min-width: 80px;
}

.order-actions {
  display: flex;
  gap: 0.5rem;
  min-width: 80px;
  justify-content: center;
}

.btn-cancel-mini, .btn-edit-mini {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s ease;
  font-size: 0.9rem;
}

.btn-cancel-mini:hover {
  background: rgba(255, 0, 85, 0.2);
}

.btn-edit-mini:hover {
  background: rgba(0, 212, 255, 0.2);
}

.btn-cancel-mini:disabled,
.btn-edit-mini:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

/* Styles pour les résultats d'exécution */
.trade-summary.execution-success {
  background: var(--color-success);
  border: 1px solid var(--color-success);
  color: white;
}

.trade-summary.execution-error {
  background: var(--color-danger);
  border: 1px solid var(--color-error);
  color: white;
}

.execution-details {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  font-size: 0.9rem;
}

.execution-details p {
  margin: 0.25rem 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.execution-details strong {
  font-weight: 600;
  margin-right: 1rem;
}

/* Form Field Row - Label à gauche, Input à droite */
.form-field-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-field-row label {
  flex: 0 0 150px;
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: 0.9rem;
  text-align: left;
}

.form-field-row input {
  flex: 1;
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  color: var(--color-text);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.form-field-row input::placeholder {
  color: var(--color-text-secondary);
}

.form-field-row input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.1);
}

.form-field-row input:disabled {
  background: var(--color-surface);
  color: var(--color-text-secondary);
  opacity: 0.6;
}

/* === Zone notifications supprimée === */

/* Responsive Design */
@media (max-width: 1200px) {
  .main-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    width: 100%;
  }
  
  /* Ordre d'affichage vertical selon spécifications */
  .portfolio-column {
    order: 1; /* Portfolio en premier */
  }
  
  .symbols-column {
    order: 2; /* Symboles disponibles en deuxième */
  }
  
  .trading-column {
    order: 3; /* Passer un ordre en troisième */
  }
  
  /* Sections individuelles avec ordre spécifique */
  .section-card {
    width: 100%;
    min-height: auto;
  }
  
  /* Sections dans trading-column - ordre demandé */
  .trading-column .section-card:first-child {
    order: 1; /* Passer un ordre */
  }
  
  .orders-section {
    order: 4; /* Ordres ouverts */
  }
  
  .recent-trades {
    order: 5; /* Trades récents */
  }
  
  .exchange-capabilities {
    order: 6; /* Capacités exchange en dernier */
  }
}

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
    text-align: center;
  }
  
  .trading-manual {
    padding: 0.5rem 1rem;
  }
  
  .section-card {
    padding: 0.75rem;
    min-height: 300px;
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