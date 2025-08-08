<template>
  <div class="heartbeat-view">
    <h1>Heartbeat</h1>
    
    <div class="stream-container">
      <div class="stream-section">
        <h2>Stream Temps Réel</h2>
        <div class="stream-list">
          <div 
            v-for="item in streamData" 
            :key="item.id"
            :class="['stream-item', item.type]"
          >
            <span class="timestamp">{{ formatTime(item.timestamp) }}</span>
            <span class="symbol">{{ item.symbol }}</span>
            <span class="timeframe">{{ item.timeframe }}</span>
            <span class="price">{{ item.price }}</span>
          </div>
        </div>
      </div>
      
      <div class="heartbeat-section">
        <h2>Signaux Heartbeat</h2>
        <div class="timeframe-grid">
          <div 
            v-for="tf in timeframes" 
            :key="tf"
            class="timeframe-card"
          >
            <div class="timeframe-label">{{ tf }}</div>
            <div class="last-signal">
              {{ getLastSignal(tf) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const streamData = ref([])
const heartbeatSignals = ref({})
const timeframes = ['1m', '3m', '5m', '15m', '1h', '4h']

let websocket = null

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (websocket) {
    websocket.close()
  }
})

function connectWebSocket() {
  websocket = new WebSocket('ws://localhost:8000/ws/heartbeat/')
  
  websocket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    // Add to stream
    streamData.value.unshift({
      id: Date.now(),
      timestamp: new Date(),
      symbol: data.symbol,
      timeframe: data.timeframe,
      price: data.close_price,
      type: 'heartbeat'
    })
    
    // Keep only last 20 items
    if (streamData.value.length > 20) {
      streamData.value = streamData.value.slice(0, 20)
    }
    
    // Update heartbeat signals
    heartbeatSignals.value[data.timeframe] = {
      timestamp: new Date(),
      price: data.close_price
    }
  }
}

function formatTime(timestamp) {
  return timestamp.toLocaleTimeString()
}

function getLastSignal(timeframe) {
  const signal = heartbeatSignals.value[timeframe]
  return signal ? `${signal.price} (${formatTime(signal.timestamp)})` : 'Aucun'
}
</script>

<style scoped>
.heartbeat-view {
  padding: 1rem;
}

.stream-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-top: 1rem;
}

.stream-section, .heartbeat-section {
  background-color: var(--color-surface);
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
}

.stream-list {
  max-height: 500px;
  overflow-y: auto;
  margin-top: 1rem;
}

.stream-item {
  display: grid;
  grid-template-columns: 80px 100px 60px 1fr;
  gap: 1rem;
  padding: 0.5rem;
  border-bottom: 1px solid var(--color-border);
  font-family: monospace;
}

.stream-item.heartbeat {
  background-color: rgba(0, 255, 136, 0.1);
  color: var(--color-success);
}

.timeframe-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-top: 1rem;
}

.timeframe-card {
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  padding: 1rem;
  text-align: center;
}

.timeframe-label {
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: 0.5rem;
}

.last-signal {
  font-family: monospace;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}
</style>