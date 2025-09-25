# REFACTORISATION ORDRES & POSITIONS - Plan d'Implémentation

## 🎯 **OBJECTIF**

Transformer le container "Ordres & Positions" actuel pour reproduire l'interface Bitget :
- **90 jours d'historique** (limite API Bitget)
- **10 lignes visibles + scroll** 
- **Tous types d'ordres** dans une liste unifiée (Normal + TP/SL)
- **Colonnes adaptatives** selon les types
- **Utilisation plein écran** (90% largeur disponible)
- **Multi-exchange** (Bitget, Binance, Kraken)

## 📊 **ANALYSE BITGET API**

### Types d'ordres identifiés :
1. **Normal** (`tpslType: "normal"`) : LIMIT, MARKET standards
2. **TP/SL** (`tpslType: "tpsl"`) : Ordres Take Profit / Stop Loss avec `triggerPrice`
3. **OCO** (`orderSource: "strategy_oco_limit"`) : One-Cancels-Other
4. **Preset TP/SL** : Ordres avec `presetTakeProfitPrice` / `presetStopLossPrice`

### Paramètres API requis :
- **startTime** : 90 jours en arrière (timestamp milliseconds)
- **limit** : 100 ordres max par requête
- **tpslType** : "normal" ou "tpsl" (requêtes séparées nécessaires)

## 🔧 **IMPLÉMENTATION TECHNIQUE**

### **PHASE 0 : CORRECTION SIGNATURES _make_request() (15 minutes) 🚨 CRITIQUE**

#### **🔧 PROBLÈME CRITIQUE DÉCOUVERT**

Lors de l'analyse approfondie de `BitgetNativeClient`, **7 appels incorrects** à `_make_request()` ont été identifiés. Ces appels ne respectent pas la signature de `BaseExchangeClient` et **DOIVENT être corrigés avant toute nouvelle fonctionnalité**.

**Signature correcte attendue :**
```python
async def _make_request(self, method: str, path: str, params: Dict = None, retries: int = None) -> Dict:
```

#### **🎯 CORRECTIONS NÉCESSAIRES**

**Fichier** : `backend/apps/core/services/bitget_native_client.py`

```python
# === CORRECTION 1 : test_connection() - Ligne 183 ===
# AVANT (incorrect):
response_data = await self._make_request('GET', path)

# APRÈS (correct):
response_data = await self._make_request('GET', path, {})

# === CORRECTION 2 : get_balance() - Ligne 213 ===
# AVANT (incorrect):
response_data = await self._make_request('GET', path)

# APRÈS (correct):
response_data = await self._make_request('GET', path, {})

# === CORRECTION 3 : get_markets() - Ligne 264 ===
# AVANT (incorrect):
response_data = await self._make_request('GET', path)

# APRÈS (correct):
response_data = await self._make_request('GET', path, {})

# === CORRECTION 4 : get_open_orders() - Ligne 646 ===
# AVANT (incorrect - query string manuel):
query_string = '&'.join([f"{k}={v}" for k, v in normal_params.items()])
full_path = f"{path}?{query_string}"
normal_response = await self._make_request('GET', full_path)

# APRÈS (correct - utilise params):
normal_response = await self._make_request('GET', path, normal_params)

# === CORRECTION 5 : get_open_orders() - Ligne 667 ===
# AVANT (incorrect - query string manuel):
query_string = '&'.join([f"{k}={v}" for k, v in tpsl_params.items()])
full_path = f"{path}?{query_string}"
tpsl_response = await self._make_request('GET', full_path)

# APRÈS (correct - utilise params):
tpsl_response = await self._make_request('GET', path, tpsl_params)

# === CORRECTION 6 : get_order_history() - Ligne 853 ===
# AVANT (incorrect - query string manuel):
query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
full_path = f"{path}?{query_string}"
response_data = await self._make_request('GET', full_path)

# APRÈS (correct - utilise params):
response_data = await self._make_request('GET', path, params)

# === CORRECTION 7 : fetch_tickers() - Ligne 921 ===
# AVANT (incorrect):
response_data = await self._make_request('GET', path)

# APRÈS (correct):
response_data = await self._make_request('GET', path, {})
```

#### **💡 EXPLICATION TECHNIQUE**

`BaseExchangeClient._make_request()` (lignes 222-302) fournit **déjà** une implémentation complète :
- ✅ **Session HTTP réutilisable** avec `aiohttp.ClientSession`
- ✅ **Authentification automatique** via `_prepare_headers()`
- ✅ **Rate limiting intelligent** avec retry exponential backoff
- ✅ **Gestion d'erreurs** avec mapping des codes d'erreur Bitget
- ✅ **Logging détaillé** pour debugging
- ✅ **Construction URL automatique** avec query parameters

**Pourquoi les corrections sont nécessaires :**
1. **Paramètres manquants** : Les appels sans `params={}` échouent car la signature attend ce paramètre
2. **Query string manuel** : BaseExchangeClient construit automatiquement les URLs avec les params
3. **Cohérence architecture** : Toutes les méthodes doivent utiliser la même interface

#### **✅ VALIDATION**
Après ces corrections, **tous les appels respecteront la signature standardisée** et bénéficieront de :
- Authentification automatique Bitget V2
- Rate limiting optimisé
- Retry logic robuste
- Logging uniforme

### **PHASE 1 : BACKEND - Extension API (2h)**

#### 1.1 Modification BitgetNativeClient
**Fichier** : `backend/apps/core/services/bitget_native_client.py`

```python
async def get_order_history_unified(
    self, 
    symbol: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    days: int = None,
    limit_per_type: int = 1000,
    include_normal: bool = True,
    include_tpsl: bool = True
) -> Dict:
    """
    📚 HISTORIQUE UNIFIÉ FLEXIBLE - RÉUTILISABLE PAR TOUTES LES APPS DJANGO
    
    Args:
        symbol: Filtre par symbole (optionnel)
        start_date: Date de début (datetime object)
        end_date: Date de fin (datetime object)  
        days: Alternative simple - derniers X jours (ex: 90)
        limit_per_type: Max ordres per type (normal/tpsl)
        include_normal: Inclure ordres normal (LIMIT/MARKET)
        include_tpsl: Inclure ordres TP/SL/TRIGGER
    
    Logique de dates (par priorité):
    1. start_date + end_date si fournis
    2. days si fourni (depuis maintenant)
    3. Par défaut : 90 derniers jours
    
    Usage exemples:
    - Trading Manual: days=90 (simple)
    - Backtest: start_date + end_date (précis)  
    - Stats: days=365, include_tpsl=False (performance)
    - Webhooks: days=7, symbol='BTCUSDT' (monitoring)
    """
    
    # === CALCUL DES TIMESTAMPS ===
    if start_date and end_date:
        # Priorité 1: Dates explicites
        start_time = int(start_date.timestamp() * 1000)
        end_time = int(end_date.timestamp() * 1000)
        
    elif days:
        # Priorité 2: Nombre de jours
        end_time = int(time.time() * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)
        
    else:
        # Priorité 3: Par défaut 90 jours
        end_time = int(time.time() * 1000)
        start_time = end_time - (90 * 24 * 60 * 60 * 1000)
    
    # === REQUÊTES CONDITIONNELLES ===
    tasks = []
    
    if include_normal:
        tasks.append(
            self._fetch_orders_by_type('normal', symbol, start_time, end_time, limit_per_type)
        )
    
    if include_tpsl:
        tasks.append(
            self._fetch_orders_by_type('tpsl', symbol, start_time, end_time, limit_per_type)
        )
    
    if not tasks:
        return {'success': True, 'orders': [], 'total': 0}
    
    # === EXÉCUTION PARALLÈLE ===
    results = await asyncio.gather(*tasks)
    
    # === FUSION ET MÉTADONNÉES ===
    all_orders = []
    for orders_batch in results:
        all_orders.extend(orders_batch)
    
    # Tri par date (plus récent d'abord)
    all_orders.sort(key=lambda x: x.get('cTime', 0), reverse=True)
    
    return {
        'success': True,
        'orders': all_orders,
        'total': len(all_orders),
        'metadata': {
            'start_time': start_time,
            'end_time': end_time,
            'period_days': (end_time - start_time) // (24 * 60 * 60 * 1000),
            'types_included': {
                'normal': include_normal,
                'tpsl': include_tpsl
            },
            'symbol_filter': symbol
        }
    }

async def _fetch_orders_by_type(self, tpsl_type: str, symbol: str, start_time: int, end_time: int, limit_per_type: int = 1000) -> List[Dict]:
    """Récupère ordres d'un type spécifique avec pagination automatique"""
    all_orders = []
    limit = 100
    
    while len(all_orders) < limit_per_type:
        params = {
            'tpslType': tpsl_type,
            'startTime': str(start_time),
            'endTime': str(end_time),
            'limit': str(min(limit, limit_per_type - len(all_orders)))
        }
        if symbol:
            params['symbol'] = symbol
        if all_orders:
            # Pagination avec idLessThan
            params['idLessThan'] = all_orders[-1]['orderId']
        
        response = await self._make_request('GET', '/api/v2/spot/trade/history-orders', params)
        
        if not response.get('data'):
            break
            
        batch_orders = [self._transform_order_data(order, is_tpsl=(tpsl_type=='tpsl')) 
                       for order in response['data']]
        all_orders.extend(batch_orders)
        
        # Arrêter si moins de 100 ordres (fin des données)
        if len(response['data']) < limit:
            break
    
    return all_orders
```

#### 1.2 Extension NativeExchangeManager
**Fichier** : `backend/apps/core/services/native_exchange_manager.py`

```python
async def handle_fetch_orders_unified(self, params: Dict) -> Dict:
    """
    🔄 GESTIONNAIRE ORDRES UNIFIÉS
    
    Nouvelle action pour récupérer ordres Normal + TP/SL combinés
    """
    broker_id = params.get('broker_id')
    symbol = params.get('symbol')
    days = params.get('days', 90)
    
    client = await self.get_client(broker_id)
    
    if hasattr(client, 'get_order_history_unified'):
        return await client.get_order_history_unified(symbol, days)
    else:
        # Fallback vers ancienne méthode pour Binance/Kraken
        return await client.get_order_history(symbol)
```

#### 1.3 Extension ExchangeClient
**Fichier** : `backend/apps/core/services/exchange_client.py`

```python
async def fetch_orders_unified(
    self, 
    broker_id: int, 
    symbol: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    days: int = None,
    include_normal: bool = True,
    include_tpsl: bool = True
) -> Dict:
    """
    📋 FETCH ORDRES UNIFIÉS - FLEXIBLE POUR TOUTES LES APPS
    
    Interface standardisée pour tous les exchanges
    """
    params = {
        'broker_id': broker_id,
        'symbol': symbol,
        'include_normal': include_normal,
        'include_tpsl': include_tpsl
    }
    
    # Conversion dates pour le transport
    if start_date:
        params['start_timestamp'] = int(start_date.timestamp() * 1000)
    if end_date:
        params['end_timestamp'] = int(end_date.timestamp() * 1000)
    if days:
        params['days'] = days
    
    return await self._send_request('fetch_orders_unified', params)
```

#### 1.4 Extension TradingService
**Fichier** : `backend/apps/trading_manual/services/trading_service.py`

```python
async def get_orders_unified(
    self, 
    broker_id: int, 
    symbol: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    days: int = None,
    include_normal: bool = True,
    include_tpsl: bool = True
) -> Dict:
    """
    🎯 SERVICE ORDRES UNIFIÉS - FLEXIBLE POUR TOUTES LES APPS
    
    Récupère historique via ExchangeClient avec tous les paramètres
    """
    try:
        client = get_global_exchange_client()
        result = await client.fetch_orders_unified(
            broker_id=broker_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            days=days,
            include_normal=include_normal,
            include_tpsl=include_tpsl
        )
        
        # Enrichir avec calculs frontend
        for order in result.get('orders', []):
            order['formatted_total'] = self._calculate_order_total(order)
            order['order_category'] = self._get_order_category(order)
            
        return result
        
    except Exception as e:
        logger.error(f"Erreur get_orders_unified: {e}")
        return {'success': False, 'error': str(e), 'orders': []}

def _get_order_category(self, order: Dict) -> str:
    """Détermine la catégorie d'affichage de l'ordre"""
    tpsl_type = order.get('tpslType', 'normal')
    order_source = order.get('orderSource', '')
    
    if 'oco' in order_source.lower():
        return 'OCO'
    elif tpsl_type == 'tpsl':
        return 'Trigger TP/SL'
    elif order.get('presetTakeProfitPrice') or order.get('presetStopLossPrice'):
        return 'Preset TP/SL'
    else:
        order_type = order.get('orderType', '').upper()
        force = order.get('force', 'GTC').upper()
        return f"{force} {order_type}" if force != 'GTC' else order_type
```

#### 1.5 Nouvelle Vue API
**Fichier** : `backend/apps/trading_manual/views.py`

```python
class UnifiedOrdersView(APIView):
    """
    🎯 API ORDRES UNIFIÉS - FLEXIBLE POUR TOUTES LES APPS
    
    GET /api/trading-manual/orders-unified/
    
    Query params:
    - broker_id (required): ID du broker
    - symbol (optional): Filtre par symbole  
    - start_date (optional): Date début ISO format (2024-01-01)
    - end_date (optional): Date fin ISO format (2024-03-31)
    - days (optional): Nombre de jours depuis maintenant (ex: 90)
    - include_normal (optional): true/false, défaut true
    - include_tpsl (optional): true/false, défaut true
    """
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        try:
            # === PARAMÈTRES OBLIGATOIRES ===
            broker_id = request.GET.get('broker_id')
            if not broker_id:
                return Response({'error': 'broker_id required'}, status=400)
            
            # === PARAMÈTRES OPTIONNELS ===
            symbol = request.GET.get('symbol')
            
            # Gestion des dates
            start_date = None
            end_date = None
            days = None
            
            if request.GET.get('start_date'):
                try:
                    start_date = datetime.fromisoformat(request.GET.get('start_date'))
                except ValueError:
                    return Response({'error': 'start_date format invalide (YYYY-MM-DD)'}, status=400)
            
            if request.GET.get('end_date'):
                try:
                    end_date = datetime.fromisoformat(request.GET.get('end_date'))
                except ValueError:
                    return Response({'error': 'end_date format invalide (YYYY-MM-DD)'}, status=400)
            
            if request.GET.get('days'):
                try:
                    days = int(request.GET.get('days'))
                    if days <= 0 or days > 365:
                        return Response({'error': 'days doit être entre 1 et 365'}, status=400)
                except ValueError:
                    return Response({'error': 'days doit être un nombre entier'}, status=400)
            
            # Types d'ordres
            include_normal = request.GET.get('include_normal', 'true').lower() == 'true'
            include_tpsl = request.GET.get('include_tpsl', 'true').lower() == 'true'
            
            if not include_normal and not include_tpsl:
                return Response({'error': 'Au moins un type d\'ordre doit être inclus'}, status=400)
            
            # === EXÉCUTION SERVICE ===
            service = TradingService()
            result = await service.get_orders_unified(
                broker_id=int(broker_id),
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                days=days,
                include_normal=include_normal,
                include_tpsl=include_tpsl
            )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Erreur UnifiedOrdersView: {e}")
            return Response({'error': str(e)}, status=500)
```

#### 1.6 URL Backend
**Fichier** : `backend/apps/trading_manual/urls.py`

```python
# Ajouter à urlpatterns :
path('orders-unified/', UnifiedOrdersView.as_view(), name='orders-unified'),
```

### **PHASE 2 : FRONTEND - Refactorisation Interface (3h)**

#### 2.1 Nouvelles Variables Réactives
**Fichier** : `frontend/src/views/TradingManualView.vue`

```javascript
// SECTION ORDRES UNIFIÉS - AJOUTS
const unifiedOrders = ref([])
const ordersLoading = ref(false)
const ordersError = ref('')
const currentPage = ref(1)
const itemsPerPage = 10
const totalOrders = ref(0)

// Données calculées pour pagination
const paginatedOrders = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return unifiedOrders.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(unifiedOrders.value.length / itemsPerPage)
})
```

#### 2.2 Fonction de Chargement Unifiée
```javascript
const loadUnifiedOrders = async () => {
  if (!selectedBroker.value?.id) {
    console.warn('Aucun broker sélectionné')
    return
  }
  
  ordersLoading.value = true
  ordersError.value = ''
  
  try {
    const params = {
      broker_id: selectedBroker.value.id,
      symbol: selectedSymbol.value || undefined
    }
    
    const response = await apiClient.get('/api/trading-manual/orders-unified/', { params })
    
    if (response.data.success) {
      unifiedOrders.value = response.data.orders || []
      totalOrders.value = unifiedOrders.value.length
      currentPage.value = 1 // Reset à la première page
      
      console.log(`✅ ${totalOrders.value} ordres chargés (90 jours)`)
    } else {
      throw new Error(response.data.error || 'Erreur inconnue')
    }
    
  } catch (error) {
    console.error('Erreur chargement ordres unifiés:', error)
    ordersError.value = error.response?.data?.error || error.message
    unifiedOrders.value = []
    
  } finally {
    ordersLoading.value = false
  }
}
```

#### 2.3 Fonctions de Formatage Étendues
```javascript
const formatOrderCategory = (order) => {
  const category = order.order_category || 'UNKNOWN'
  
  // Icônes selon catégorie
  const icons = {
    'LIMIT': '',
    'MARKET': '🏃',
    'Trigger TP/SL': '🎯',
    'Preset TP/SL': '🛡️',
    'OCO': '🔄',
    'GTC LIMIT': '⏰',
    'IOC LIMIT': '⚡',
    'FOK LIMIT': '💥'
  }
  
  return icons[category] ? `${icons[category]} ${category}` : category
}

const formatOrderDate = (order) => {
  const timestamp = order.cTime || order.created_at
  if (!timestamp) return '-'
  
  try {
    const date = new Date(parseInt(timestamp))
    return date.toLocaleDateString('fr-FR') + ' ' + date.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return '-'
  }
}

const getOrderStatusStyle = (status) => {
  const styles = {
    'filled': { color: '#00FF88', background: 'rgba(0,255,136,0.1)' },
    'cancelled': { color: '#FF0055', background: 'rgba(255,0,85,0.1)' },
    'live': { color: '#00D4FF', background: 'rgba(0,212,255,0.1)' },
    'partially_filled': { color: '#FFA500', background: 'rgba(255,165,0,0.1)' }
  }
  return styles[status] || styles.live
}
```

#### 2.4 Template HTML - Remplacement Complet
```vue
<template>
  <!-- SECTION ORDRES & POSITIONS - PLEIN ÉCRAN -->
  <div class="orders-positions-container">
    
    <!-- EN-TÊTE -->
    <div class="orders-header">
      <div class="orders-title">
        <h2>📊 Ordres & Positions - Historique 90 jours</h2>
        <div class="orders-stats" v-if="totalOrders > 0">
          <span class="stat-item">{{ totalOrders }} ordres</span>
          <span class="stat-item">{{ selectedBroker?.exchange_display_name }}</span>
          <span class="stat-item" v-if="selectedSymbol">{{ selectedSymbol }}</span>
        </div>
      </div>
      
      <div class="orders-actions">
        <button @click="loadUnifiedOrders" :disabled="ordersLoading" class="refresh-btn">
          <span v-if="ordersLoading">🔄</span>
          <span v-else>♻️</span>
          Actualiser
        </button>
      </div>
    </div>
    
    <!-- ÉTAT DE CHARGEMENT -->
    <div v-if="ordersLoading" class="loading-state">
      <div class="loader">🔄 Chargement des ordres...</div>
    </div>
    
    <!-- ÉTAT D'ERREUR -->
    <div v-else-if="ordersError" class="error-state">
      <div class="error-message">❌ {{ ordersError }}</div>
      <button @click="loadUnifiedOrders" class="retry-btn">Réessayer</button>
    </div>
    
    <!-- TABLEAU PRINCIPAL -->
    <div v-else-if="unifiedOrders.length > 0" class="orders-table-container">
      
      <!-- EN-TÊTE COLONNES -->
      <div class="orders-table-header">
        <div class="col-date">Date/Heure</div>
        <div class="col-symbol">Symbole</div>
        <div class="col-category">Type/Catégorie</div>
        <div class="col-side">Side</div>
        <div class="col-quantity">Quantité</div>
        <div class="col-price">Prix/Trigger</div>
        <div class="col-avg-price">Prix Moyen</div>
        <div class="col-total">Total</div>
        <div class="col-status">Status</div>
      </div>
      
      <!-- LIGNES ORDRES (10 visibles) -->
      <div class="orders-table-body">
        <div 
          v-for="order in paginatedOrders" 
          :key="order.order_id"
          class="order-row"
          :class="`order-${order.status}`"
        >
          <div class="col-date">{{ formatOrderDate(order) }}</div>
          <div class="col-symbol">{{ order.symbol }}</div>
          <div class="col-category">{{ formatOrderCategory(order) }}</div>
          <div class="col-side" :class="`side-${order.side}`">
            {{ order.side?.toUpperCase() }}
          </div>
          <div class="col-quantity">{{ formatOrderQuantity(order) }}</div>
          <div class="col-price">{{ formatOrderDisplayPrice(order) }}</div>
          <div class="col-avg-price">
            {{ order.priceAvg && order.priceAvg !== '0' ? parseFloat(order.priceAvg).toFixed(2) : '-' }}
          </div>
          <div class="col-total">{{ formatOrderTotal(order) }}</div>
          <div class="col-status">
            <span 
              class="status-badge" 
              :style="getOrderStatusStyle(order.status)"
            >
              {{ order.status }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- PAGINATION -->
      <div class="orders-pagination">
        <div class="pagination-info">
          Page {{ currentPage }} sur {{ totalPages }} 
          ({{ (currentPage - 1) * itemsPerPage + 1 }}-{{ Math.min(currentPage * itemsPerPage, totalOrders) }} sur {{ totalOrders }})
        </div>
        
        <div class="pagination-controls">
          <button 
            @click="currentPage = Math.max(1, currentPage - 1)" 
            :disabled="currentPage === 1"
            class="page-btn"
          >
            ⬅️ Précédent
          </button>
          
          <button 
            @click="currentPage = Math.min(totalPages, currentPage + 1)" 
            :disabled="currentPage === totalPages"
            class="page-btn"
          >
            Suivant ➡️
          </button>
        </div>
      </div>
    </div>
    
    <!-- ÉTAT VIDE -->
    <div v-else class="empty-state">
      <div class="empty-message">
        📭 Aucun ordre trouvé sur les 90 derniers jours
      </div>
      <div class="empty-suggestion">
        Vérifiez votre broker sélectionné ou effectuez quelques trades
      </div>
    </div>
  </div>
</template>
```

#### 2.5 CSS Styles - Interface Bitget-like
```css
<style scoped>
/* CONTAINER PRINCIPAL - PLEIN ÉCRAN */
.orders-positions-container {
  width: 90%;
  max-width: none;
  margin: 0 auto;
  background: var(--color-background-secondary, #1a1a1a);
  border: 1px solid var(--color-primary, #00D4FF);
  border-radius: 8px;
  overflow: hidden;
}

/* EN-TÊTE */
.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--color-background, #0d0d0d);
  border-bottom: 1px solid var(--color-primary, #00D4FF);
}

.orders-title h2 {
  margin: 0;
  color: var(--color-primary, #00D4FF);
  font-size: 1.2rem;
}

.orders-stats {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.stat-item {
  color: var(--color-text-secondary, #888);
  font-size: 0.9rem;
}

/* TABLEAU */
.orders-table-container {
  min-height: 600px;
}

.orders-table-header,
.order-row {
  display: grid;
  grid-template-columns: 140px 80px 120px 50px 100px 100px 80px 80px 80px;
  gap: 1rem;
  align-items: center;
  padding: 0.75rem 1.5rem;
}

.orders-table-header {
  background: var(--color-background, #0d0d0d);
  border-bottom: 2px solid var(--color-primary, #00D4FF);
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--color-primary, #00D4FF);
  text-transform: uppercase;
}

.order-row {
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
  transition: background-color 0.2s;
}

.order-row:hover {
  background: rgba(0, 212, 255, 0.05);
}

/* STYLES PAR STATUT */
.order-filled { background: rgba(0, 255, 136, 0.02); }
.order-cancelled { background: rgba(255, 0, 85, 0.02); }
.order-live { background: rgba(0, 212, 255, 0.02); }

/* SIDES */
.side-buy { color: var(--color-success, #00FF88); font-weight: 600; }
.side-sell { color: var(--color-danger, #FF0055); font-weight: 600; }

/* STATUS BADGES */
.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}

/* PAGINATION */
.orders-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--color-background, #0d0d0d);
  border-top: 1px solid var(--color-primary, #00D4FF);
}

.pagination-controls {
  display: flex;
  gap: 1rem;
}

.page-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid var(--color-primary, #00D4FF);
  color: var(--color-primary, #00D4FF);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: var(--color-primary, #00D4FF);
  color: var(--color-background, #0d0d0d);
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* ÉTATS */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--color-text-secondary, #888);
}

.loader {
  font-size: 1.2rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.refresh-btn {
  padding: 0.5rem 1rem;
  background: var(--color-primary, #00D4FF);
  color: var(--color-background, #0d0d0d);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.2s;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* RESPONSIVE */
@media (max-width: 1200px) {
  .orders-table-header,
  .order-row {
    grid-template-columns: 120px 70px 100px 40px 80px 80px 60px 60px 60px;
    font-size: 0.8rem;
  }
}
</style>
```

### **PHASE 3 : INTÉGRATION & TESTS (1h)**

#### 3.1 Modification des Hooks
```javascript
// Charger les ordres unifiés au lieu des anciens
watch([selectedBroker, selectedSymbol], () => {
  if (selectedBroker.value?.id) {
    loadUnifiedOrders()
  }
}, { immediate: true })

// Actualisation automatique périodique (optionnel)
let refreshInterval = null

onMounted(() => {
  // Actualiser toutes les 2 minutes si en mode ordres ouverts
  refreshInterval = setInterval(() => {
    if (selectedBroker.value?.id && !ordersLoading.value) {
      loadUnifiedOrders()
    }
  }, 120000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
```

#### 3.2 Suppression Ancien Code
```javascript
// SUPPRIMER ces variables/fonctions devenues obsolètes :
// - openOrders, closedOrders  
// - orderViewMode, currentOrdersList
// - loadOpenOrders, loadClosedOrders
// - Anciens templates avec boutons Ordres Ouverts/Historique
```

## 🔗 **EXEMPLES D'UTILISATION PAR D'AUTRES APPS DJANGO**

### **1. TRADING MANUAL (actuel)**
```javascript
// Simple : 90 derniers jours tous types
const response = await apiClient.get('/api/trading-manual/orders-unified/', {
  params: { broker_id: 1, days: 90 }
})
```

### **2. BACKTEST APP**
```javascript
// Précis : période exacte pour analyse
const response = await apiClient.get('/api/trading-manual/orders-unified/', {
  params: {
    broker_id: 1,
    start_date: '2024-01-01',
    end_date: '2024-03-31',
    symbol: 'BTCUSDT',
    include_tpsl: false  // Seulement ordres normaux pour perfs
  }
})
```

### **3. STATS APP**
```javascript
// Performance : 1 an, normal seulement
const response = await apiClient.get('/api/trading-manual/orders-unified/', {
  params: {
    broker_id: 1,
    days: 365,
    include_normal: true,
    include_tpsl: false  // Ignorer TP/SL pour calculs P&L
  }
})
```

### **4. WEBHOOKS APP**
```javascript
// Monitoring : 7 derniers jours, symbole spécifique
const response = await apiClient.get('/api/trading-manual/orders-unified/', {
  params: {
    broker_id: 1,
    days: 7,
    symbol: 'ETHUSDT',
    include_normal: false,
    include_tpsl: true  // Seulement ordres automatiques
  }
})
```

### **5. SERVICE PYTHON (Backend)**
```python
# Usage depuis un autre service Django
from apps.trading_manual.services.trading_service import TradingService
from datetime import datetime

service = TradingService()

# Exemple 1: Stats annuelles
result = await service.get_orders_unified(
    broker_id=1,
    days=365,
    include_normal=True,
    include_tpsl=False
)

# Exemple 2: Analyse période spécifique
result = await service.get_orders_unified(
    broker_id=1,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 3, 31),
    symbol='BTCUSDT'
)
```

## ✅ **CHECKLIST D'IMPLÉMENTATION**

### Phase 0 : Corrections Critiques (15 min) 🚨 PRIORITÉ ABSOLUE
- [ ] **CORRECTION 1** : `test_connection()` ligne 183 - Ajouter `params={}`
- [ ] **CORRECTION 2** : `get_balance()` ligne 213 - Ajouter `params={}`
- [ ] **CORRECTION 3** : `get_markets()` ligne 264 - Ajouter `params={}`
- [ ] **CORRECTION 4** : `get_open_orders()` ligne 646 - Remplacer query string manuel par `params`
- [ ] **CORRECTION 5** : `get_open_orders()` ligne 667 - Remplacer query string manuel par `params`
- [ ] **CORRECTION 6** : `get_order_history()` ligne 853 - Remplacer query string manuel par `params`
- [ ] **CORRECTION 7** : `fetch_tickers()` ligne 921 - Ajouter `params={}`
- [ ] **TEST Phase 0** : Vérifier que toutes les méthodes BitgetNativeClient fonctionnent

### Phase 1 : Backend (2h)
- [ ] `BitgetNativeClient.get_order_history_unified()` - Requêtes parallèles Normal+TP/SL
- [ ] `NativeExchangeManager.handle_fetch_orders_unified()` - Nouvelle action
- [ ] `ExchangeClient.fetch_orders_unified()` - Interface standardisée  
- [ ] `TradingService.get_orders_unified()` - Logique métier + formatage
- [ ] `UnifiedOrdersView` - Nouvelle API REST
- [ ] URL `/api/trading-manual/orders-unified/`
- [ ] Tests API avec Postman/curl

### Frontend (3h)
- [ ] Variables réactives (unifiedOrders, pagination, loading, error)
- [ ] `loadUnifiedOrders()` - Fonction de chargement
- [ ] Fonctions formatage étendues (catégorie, date, statut)
- [ ] Template HTML complet (en-tête + tableau + pagination)
- [ ] CSS styles Bitget-like (plein écran + couleurs)
- [ ] Intégration hooks (watch, onMounted, onUnmounted)
- [ ] Suppression ancien code obsolète

### Phase 2 : Tests & Validation (1h)
- [ ] **Test Phase 0** : Validation corrections signatures `_make_request()`
- [ ] Test avec broker Bitget réel
- [ ] Validation pagination (10 lignes visibles)
- [ ] Test filtrage par symbole
- [ ] Vérification 90 jours d'historique
- [ ] Test tous types ordres (Normal, TP/SL, OCO)
- [ ] Test responsive design
- [ ] Test performance avec 1000+ ordres

**⏱️ DURÉE TOTALE ESTIMÉE : 6h15 (Phase 0: 15min + Backend: 2h + Frontend: 3h + Tests: 1h)**

## 🎯 **RÉSULTAT ATTENDU**

Interface finale identique à Bitget :
- ✅ **90 jours d'historique** automatiquement chargés
- ✅ **10 lignes visibles** + pagination fluide
- ✅ **Tous types d'ordres** dans une seule liste
- ✅ **Colonnes adaptatives** avec icônes et couleurs
- ✅ **Plein écran** (90% largeur)
- ✅ **Multi-exchange** prêt (Bitget validé, Binance/Kraken à tester)

## 📝 **NOTES DE DÉVELOPPEMENT**

- **🚨 CRITIQUE** : **PHASE 0 OBLIGATOIRE** avant toute autre modification - Les signatures incorrectes bloquent l'architecture
- **Priorité** : Phase 0 → Bitget d'abord → puis extension Binance/Kraken  
- **Performance** : Pagination frontend pour 1000+ ordres
- **UX** : Loading states + error handling complets
- **Maintenance** : Code modulaire et commenté pour évolutions futures
- **Architecture** : BaseExchangeClient fournit déjà toute l'infrastructure HTTP nécessaire