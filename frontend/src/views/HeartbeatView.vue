<template>
  <div class="heartbeat-view">
    <div class="header-section">
      <h1>Heartbeat</h1>
      <div class="explanation">
        <p>Surveillance temps réel des signaux de trading Binance par timeframe avec données historiques (orange) et flux live (vert)</p>
      </div>
    </div>
    
    
    <div class="main-container">
      <!-- Stream Temps Reel - Donnees brutes WebSocket -->
      <div class="raw-stream-section">
        <h2>Stream Temps Reel - Donnees Brutes Binance</h2>
        <div class="stream-info">
          <span class="stream-count">Messages: {{ rawStreamData.length }}</span>
          <span class="stream-rate">Taux: {{ streamRate }}/min</span>
        </div>
        
        <div class="raw-stream-list">
          <div 
            v-for="(item, index) in rawStreamData" 
            :key="item.id"
            :class="['raw-stream-item', { 'newest': index === 0 }]"
          >
            <span class="raw-index">{{ index + 1 }}</span>
            <span class="raw-timestamp">{{ formatTime(item.timestamp) }}</span>
            <span class="raw-timeframe">{{ item.timeframe }}</span>
          </div>
        </div>
      </div>
      
      <!-- Enhanced Timeframe Grid - Listes defilantes -->
      <div class="heartbeat-section">
        <h2>Signaux Heartbeat par Timeframe</h2>
        <div class="timeframe-grid">
          <div 
            v-for="tf in timeframes" 
            :key="tf"
            class="timeframe-card"
          >
            <div class="timeframe-label">{{ tf }}</div>
            <div class="timeframe-signals-list">
              <div 
                v-for="(signal, index) in getTimeframeSignals(tf)" 
                :key="signal.id || signal.unique_key"
                :class="[
                  'timeframe-signal-item',
                  signal.is_historical ? 'historical' : 'realtime',
                  { 'newest': index === 0 && !signal.is_historical }
                ]"
              >
                <span class="signal-datetime">{{ formatDateTime(signal.dhm_candle || signal.timestamp) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// Reactive data
const heartbeatSignals = ref({})
const timeframeStats = ref({})

// Stream brut temps reel
const rawStreamData = ref([])
const streamRate = ref(0)
const streamCounter = ref({ count: 0, lastMinute: new Date().getMinutes() })

// Signaux par timeframe (historique + temps reel)
const timeframeSignals = ref({
  '1m': [],
  '3m': [],
  '5m': [],
  '15m': [],
  '1h': [],
  '4h': []
})

const timeframes = ['1m', '3m', '5m', '15m', '1h', '4h']
let websocket = null
let streamWebsocket = null

// Computed properties

// Lifecycle hooks
onMounted(() => {
  connectWebSocket()
  connectRawStream()
  loadHistoricalDataForTimeframes()
  
  // Update stream rate every minute
  setInterval(updateStreamRate, 60000)
})

onUnmounted(() => {
  if (websocket) {
    websocket.close()
  }
  if (streamWebsocket) {
    streamWebsocket.close()
  }
})

// WebSocket connection
function connectWebSocket() {
  websocket = new WebSocket('ws://localhost:8000/ws/heartbeat/')
  
  websocket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    // Update heartbeat signals tracking
    heartbeatSignals.value[data.timeframe] = {
      timestamp: new Date(),
      price: data.close_price,
      volume: data.volume
    }
    
    // Ajouter aux signaux par timeframe (temps reel - vert)
    const tf = data.timeframe
    if (timeframeSignals.value[tf]) {
      const realtimeSignal = {
        id: Date.now(),
        unique_key: `realtime_${tf}_${Date.now()}`,
        dhm_candle: data.dhm_candle || new Date().toISOString(),
        timestamp: new Date(),
        signal_type: tf,
        is_historical: false,
        type: 'realtime'
      }
      
      timeframeSignals.value[tf].unshift(realtimeSignal)
      
      // Garder seulement 60 signaux par timeframe
      if (timeframeSignals.value[tf].length > 60) {
        timeframeSignals.value[tf] = timeframeSignals.value[tf].slice(0, 60)
      }
    }
  }
  
  websocket.onopen = () => {
    console.log('WebSocket Heartbeat connecté')
  }
  
  websocket.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
}

// Raw Stream WebSocket connection
function connectRawStream() {
  streamWebsocket = new WebSocket('ws://localhost:8000/ws/stream/')
  
  streamWebsocket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    // Ajouter au stream brut (donnees live)
    if (data.k) {
      const rawItem = {
        id: Date.now() + Math.random(),
        timestamp: new Date(),
        symbol: data.k.s,
        timeframe: data.k.i,
        price: parseFloat(data.k.c),
        volume: parseFloat(data.k.v),
        is_closed: data.k.x,
        raw_data: data
      }
      
      rawStreamData.value.unshift(rawItem)
      
      // Garder seulement 60 elements
      if (rawStreamData.value.length > 60) {
        rawStreamData.value = rawStreamData.value.slice(0, 60)
      }
      
      // Compter pour le taux
      streamCounter.value.count++
    }
  }
  
  streamWebsocket.onopen = () => {
    console.log('Raw Stream WebSocket connecte')
  }
  
  streamWebsocket.onerror = (error) => {
    console.error('Raw Stream WebSocket error:', error)
  }
}

// Update stream rate calculation
function updateStreamRate() {
  const currentMinute = new Date().getMinutes()
  if (currentMinute !== streamCounter.value.lastMinute) {
    streamRate.value = streamCounter.value.count
    streamCounter.value = { count: 0, lastMinute: currentMinute }
  }
}

// API functions

// Nouvelle fonction simplifiée pour charger uniquement les timeframes
async function loadHistoricalDataForTimeframes() {
  try {
    console.log('Chargement des données historiques pour timeframes...')
    
    for (const tf of timeframes) {
      const response = await fetch(`http://localhost:8000/api/heartbeat-history/?signal_type=${tf}&limit=40`)
      if (response.ok) {
        const data = await response.json()
        const signals = data.results || []
        console.log(`${tf}: reçu ${signals.length} signaux historiques`, signals.slice(0, 2))
        
        // Mapper les signaux historiques (orange)
        const historicalSignalsForTf = signals.map(signal => ({
          ...signal,
          unique_key: `historical_${tf}_${signal.id}`,
          timestamp: new Date(signal.dhm_candle || signal.timestamp),
          timeframe: signal.signal_type,
          is_historical: true,
          type: 'historical'
        }))
        
        // Initialiser avec les signaux historiques
        timeframeSignals.value[tf] = [...historicalSignalsForTf].slice(0, 60)
        console.log(`${tf}: initialisé avec ${timeframeSignals.value[tf].length} signaux`)
      } else {
        console.error(`Erreur HTTP pour ${tf}: ${response.status} ${response.statusText}`)
      }
    }
    
  } catch (error) {
    console.error('Erreur chargement timeframes:', error)
  }
}

// Utility functions
function formatTime(timestamp) {
  if (!timestamp) return 'N/A'
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return date.toLocaleTimeString('fr-FR', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  })
}

function formatVolume(volume) {
  if (!volume) return 'N/A'
  const num = parseFloat(volume)
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toFixed(2)
}

function getLastSignal(timeframe) {
  // Try latest from stats first
  if (timeframeStats.value.latest && timeframeStats.value.latest[timeframe]) {
    const signal = timeframeStats.value.latest[timeframe]
    return `${signal.close_price} (${formatTime(signal.dhm_candle)})`
  }
  
  // Fallback to heartbeat signals
  const signal = heartbeatSignals.value[timeframe]
  return signal ? `${signal.price} (${formatTime(signal.timestamp)})` : 'Aucun signal'
}

function getTimeframeCount(timeframe) {
  if (!timeframeStats.value.counts) return 0
  const count = timeframeStats.value.counts.find(c => c.signal_type === timeframe)
  return count ? count.count : 0
}

// Nouvelle fonction pour recuperer les signaux d'un timeframe
function getTimeframeSignals(timeframe) {
  if (!timeframeSignals.value[timeframe]) return []
  
  // Retourner seulement les 20 premiers (plus recents)
  return timeframeSignals.value[timeframe].slice(0, 20)
}

// Fonction pour formater la date/heure au format DD.MM.YY HH:MM:SS
function formatDateTime(timestamp) {
  if (!timestamp) return 'N/A'
  
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  
  const day = String(date.getDate()).padStart(2, '0') // DD
  const month = String(date.getMonth() + 1).padStart(2, '0') // MM
  const year = date.getFullYear().toString().slice(-2) // YY
  const hours = String(date.getHours()).padStart(2, '0') // HH
  const minutes = String(date.getMinutes()).padStart(2, '0') // MM
  const seconds = String(date.getSeconds()).padStart(2, '0') // SS
  
  return `${day}.${month}.${year} ${hours}:${minutes}:${seconds}`
}
</script>

<style scoped>
.heartbeat-view {
  padding: 1rem;
}

/* Header Section */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: linear-gradient(135deg, var(--color-background), #2a2a2a);
  border-radius: 0.5rem;
  border: 1px solid var(--color-border);
}

.header-section h1 {
  margin: 0;
  color: var(--color-primary);
  font-size: 1.8rem;
}

.explanation {
  max-width: 500px;
  text-align: right;
}

.explanation p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
  font-style: italic;
}


/* Main Container */
.main-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-top: 1rem;
}

.heartbeat-section, .raw-stream-section {
  background-color: var(--color-surface);
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
}

/* Raw Stream Section */
.raw-stream-section {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  border-color: #00ff88;
}

.stream-info {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
  font-family: monospace;
  font-size: 0.85rem;
}

.stream-count, .stream-rate {
  color: #00ff88;
  font-weight: bold;
}

.raw-stream-list {
  max-height: 600px;
  overflow-y: auto;
  margin-top: 1rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.25rem;
  padding: 0.5rem;
}

.raw-stream-item {
  display: grid;
  grid-template-columns: 30px 120px 80px;
  gap: 1rem;
  padding: 0.5rem;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
  font-family: monospace;
  font-size: 0.9rem;
  color: #a0a0a0;
  transition: all 0.3s ease;
}

.raw-stream-item.newest {
  background-color: rgba(0, 255, 136, 0.2);
  color: #00ff88;
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.3);
  animation: rawPulse 1s ease-in-out;
}

@keyframes rawPulse {
  0% { opacity: 0.5; transform: translateX(-5px); }
  50% { opacity: 1; transform: translateX(0); }
  100% { opacity: 0.8; transform: translateX(0); }
}

.raw-stream-item:hover {
  background-color: rgba(0, 255, 136, 0.1);
  color: #ffffff;
}

.raw-index {
  color: #666;
  text-align: center;
  font-size: 0.7rem;
}

.raw-timestamp {
  color: #00ff88;
  font-weight: bold;
}

.raw-timeframe {
  background: rgba(0, 255, 136, 0.2);
  padding: 4px 8px;
  border-radius: 4px;
  text-align: center;
  font-size: 0.8rem;
  color: #00ff88;
  font-weight: bold;
}


/* Enhanced Timeframe Grid - Listes defilantes */
.timeframe-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-top: 1rem;
}

.timeframe-card {
  background: linear-gradient(135deg, var(--color-background), #2a2a2a);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 0.75rem;
  transition: transform 0.2s ease;
  min-height: 300px;
  display: flex;
  flex-direction: column;
}

.timeframe-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.timeframe-label {
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: 0.5rem;
  font-size: 1rem;
  text-align: center;
  background: var(--color-primary);
  color: white;
  padding: 0.25rem;
  border-radius: 0.25rem;
}

/* Liste defilante des signaux par timeframe */
.timeframe-signals-list {
  flex: 1;
  max-height: 250px;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.25rem;
  padding: 0.25rem;
}

.timeframe-signal-item {
  padding: 0.3rem 0.5rem;
  margin-bottom: 2px;
  border-radius: 0.2rem;
  font-family: monospace;
  font-size: 0.75rem;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

/* Signaux historiques (orange) */
.timeframe-signal-item.historical {
  background-color: rgba(255, 165, 0, 0.1);
  border-left-color: #ff8c00;
  color: #ffaa00;
}

/* Signaux temps reel (vert) */
.timeframe-signal-item.realtime {
  background-color: rgba(0, 255, 136, 0.15);
  border-left-color: #00ff88;
  color: #00ff88;
  font-weight: bold;
}

/* Animation pour les nouveaux signaux */
.timeframe-signal-item.newest {
  background-color: rgba(0, 255, 136, 0.3);
  animation: timeframePulse 2s ease-in-out;
  box-shadow: 0 0 6px rgba(0, 255, 136, 0.4);
}

@keyframes timeframePulse {
  0% { opacity: 0.5; transform: scale(0.95); }
  50% { opacity: 1; transform: scale(1.02); }
  100% { opacity: 0.9; transform: scale(1); }
}

.timeframe-signal-item:hover {
  background-color: rgba(255, 255, 255, 0.08);
  transform: translateX(2px);
}

.signal-datetime {
  font-weight: bold;
}

/* Responsive */
@media (max-width: 1400px) {
  .main-container {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .timeframe-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1000px) {
  .main-container {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .timeframe-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .raw-stream-item {
    font-size: 0.75rem;
    padding: 0.25rem;
  }
  
  .raw-stream-item {
    grid-template-columns: 25px 100px 60px;
  }
}

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .explanation {
    max-width: none;
    text-align: center;
  }
  
  .timeframe-grid {
    grid-template-columns: 1fr;
  }
  
  .timeframe-card {
    min-height: 200px;
  }
}
</style>