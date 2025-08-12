# MODULE 2 IMPLEMENTATION - HEARTBEAT AMÉLIORÉ

## 🎯 OBJECTIFS DU MODULE 2

1. **Persistance des données** : Sauvegarder les bougies et signaux en PostgreSQL
2. **Monitoring avancé** : Tracking démarrage/arrêt + état connexion
3. **Interface améliorée** : Historique 60 éléments avec couleurs différentielles
4. **APIs REST** : Endpoints pour récupérer l'historique des signaux

---

## 📊 ÉTAT ACTUEL - ANALYSE DE L'EXISTANT

### ✅ **Ce qui fonctionne déjà (Module 1)**

#### Backend existant
- ✅ **Service Heartbeat** (`run_heartbeat.py`) : Connexion WebSocket Binance multi-timeframes
- ✅ **Double diffusion** : Canaux "stream" (brut) + "heartbeat" (bougies fermées)
- ✅ **WebSocket Consumers** : HeartbeatConsumer + StreamConsumer fonctionnels
- ✅ **Modèle HeartbeatStatus** : Table de monitoring basique
- ✅ **Processing OHLCV** : Extraction données bougies complètes

#### Frontend existant
- ✅ **Vue HeartbeatView** : Affichage temps réel fonctionnel
- ✅ **Stream temps réel** : Liste des 20 derniers signaux
- ✅ **Grid timeframes** : 6 cases avec dernier prix + timestamp
- ✅ **Connexion WebSocket** : Client frontend opérationnel

### ❌ **Ce qui manque (À implémenter)**

#### Backend - Persistance
- ❌ **Table `candles_heartbeat`** : Stockage des signaux individuels
- ❌ **Sauvegarde automatique** : Enregistrement chaque bougie fermée
- ❌ **Tracking démarrage/arrêt** : Timestamps application start/stop
- ❌ **API REST** : Endpoints pour récupérer l'historique

#### Frontend - Interface avancée
- ❌ **Liste 60 éléments** : Actuellement limité à 20
- ❌ **Couleurs différentielles** : Orange (historique) vs Vert (nouveau)
- ❌ **Initialisation historique** : Chargement des 60 derniers au démarrage
- ❌ **Cases timeframes étendues** : Affichage 20 sur 60 stockés

---

## 📋 ÉTAPES D'IMPLÉMENTATION

### ÉTAPE 2.1 : Extension des modèles ✅➡️❌

#### Fichier : `backend/apps/core/models.py` (modifications)
```python
# Ajouter à la classe HeartbeatStatus existante
class HeartbeatStatus(models.Model):
    # ... champs existants ...
    
    # NOUVEAUX CHAMPS pour Module 2
    last_application_start = models.DateTimeField(null=True, blank=True)
    last_application_stop = models.DateTimeField(null=True, blank=True)
    
    # Mise à jour du Meta
    class Meta:
        db_table = 'heartbeat_status'
        verbose_name = 'État du Heartbeat'
        verbose_name_plural = 'États du Heartbeat'
    
    def record_start(self):
        """Enregistre le démarrage de l'application"""
        from django.utils import timezone
        self.last_application_start = timezone.now()
        self.is_connected = True
        self.save()
    
    def record_stop(self):
        """Enregistre l'arrêt de l'application"""
        from django.utils import timezone
        self.last_application_stop = timezone.now()
        self.is_connected = False
        self.save()


# NOUVEAU MODÈLE pour les signaux individuels
class CandleHeartbeat(models.Model):
    """Stockage individuel des signaux Heartbeat reçus"""
    heartbeat_status = models.ForeignKey(
        HeartbeatStatus,
        on_delete=models.CASCADE,
        related_name='candle_signals'
    )
    
    # Timestamps
    dhm_reception = models.DateTimeField()  # Quand le signal est reçu
    dhm_candle = models.DateTimeField()     # Timestamp de la bougie Binance
    
    # Type de signal
    signal_type = models.CharField(
        max_length=10,
        choices=[
            ('1m', '1 minute'),
            ('3m', '3 minutes'),
            ('5m', '5 minutes'),
            ('15m', '15 minutes'),
            ('1h', '1 heure'),
            ('4h', '4 heures'),
        ]
    )
    
    # Données OHLCV complètes
    symbol = models.CharField(max_length=20, default='BTCUSDT')
    open_price = models.DecimalField(max_digits=20, decimal_places=8)
    high_price = models.DecimalField(max_digits=20, decimal_places=8)
    low_price = models.DecimalField(max_digits=20, decimal_places=8)
    close_price = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'candles_heartbeat'
        ordering = ['-dhm_candle']
        indexes = [
            models.Index(fields=['signal_type', '-dhm_candle']),
            models.Index(fields=['symbol', 'signal_type']),
        ]
        verbose_name = 'Signal Heartbeat'
        verbose_name_plural = 'Signaux Heartbeat'
    
    def __str__(self):
        return f"{self.symbol} {self.signal_type} @ {self.close_price} ({self.dhm_candle})"
```

### ÉTAPE 2.2 : Service Heartbeat amélioré ✅➡️❌

#### Fichier : `backend/apps/core/management/commands/run_heartbeat.py` (modifications)
```python
import asyncio
import json
import websockets
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from apps.core.models import HeartbeatStatus, CandleHeartbeat
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run Binance WebSocket heartbeat service avec persistance'

    def __init__(self):
        super().__init__()
        self.heartbeat_status = None
        
    def handle(self, *args, **options):
        self.stdout.write('Starting Enhanced Heartbeat service...')
        
        # Initialiser ou récupérer le statut
        self.heartbeat_status, created = HeartbeatStatus.objects.get_or_create(
            id=1,  # Singleton
            defaults={
                'is_connected': False,
                'symbols_monitored': ['BTCUSDT']
            }
        )
        
        # Enregistrer le démarrage
        self.heartbeat_status.record_start()
        self.stdout.write(
            self.style.SUCCESS(f'✓ Heartbeat démarré à {self.heartbeat_status.last_application_start}')
        )
        
        try:
            asyncio.run(self.run_heartbeat())
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur critique: {e}'))
            self.shutdown()

    def shutdown(self):
        """Arrêt propre du service"""
        if self.heartbeat_status:
            self.heartbeat_status.record_stop()
            self.stdout.write(
                self.style.WARNING(f'⚠️ Heartbeat arrêté à {self.heartbeat_status.last_application_stop}')
            )

    async def run_heartbeat(self):
        """Boucle principale du Heartbeat avec persistance"""
        channel_layer = get_channel_layer()
        
        # URL WebSocket Binance multi-timeframes
        stream_url = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m/btcusdt@kline_3m/btcusdt@kline_5m/btcusdt@kline_15m/btcusdt@kline_1h/btcusdt@kline_4h"
        
        while True:
            try:
                async with websockets.connect(stream_url) as websocket:
                    self.stdout.write('✓ Connecté à Binance WebSocket')
                    self.heartbeat_status.is_connected = True
                    self.heartbeat_status.save()
                    
                    async for message in websocket:
                        await self.process_message(message, channel_layer)
                        
            except Exception as e:
                self.stdout.write(f'WebSocket error: {e}')
                self.heartbeat_status.is_connected = False
                self.heartbeat_status.last_error = str(e)
                self.heartbeat_status.save()
                await asyncio.sleep(5)

    async def process_message(self, message, channel_layer):
        """Traite un message WebSocket avec sauvegarde"""
        try:
            data = json.loads(message)
            
            # Diffuser le stream brut (existant)
            await channel_layer.group_send(
                "stream",
                {
                    "type": "stream_message",
                    "message": data
                }
            )
            
            # Traiter les bougies fermées
            if 'k' in data and data['k']['x']:  # Bougie fermée
                await self.process_closed_candle(data, channel_layer)
                
        except Exception as e:
            logger.error(f"Erreur traitement message: {e}")

    async def process_closed_candle(self, data, channel_layer):
        """Traite une bougie fermée avec sauvegarde DB"""
        k = data['k']
        dhm_reception = timezone.now()
        dhm_candle = timezone.datetime.fromtimestamp(k['T'] / 1000, tz=timezone.utc)
        
        # Préparer les données
        kline_data = {
            'symbol': k['s'],
            'timeframe': k['i'],
            'open_time': k['t'],
            'close_time': k['T'],
            'open_price': float(k['o']),
            'close_price': float(k['c']),
            'high_price': float(k['h']),
            'low_price': float(k['l']),
            'volume': float(k['v']),
            'is_closed': k['x'],
            'dhm_reception': dhm_reception.isoformat(),
            'dhm_candle': dhm_candle.isoformat()
        }
        
        # SAUVEGARDE EN BASE (NOUVEAU)
        try:
            candle_signal = CandleHeartbeat.objects.create(
                heartbeat_status=self.heartbeat_status,
                dhm_reception=dhm_reception,
                dhm_candle=dhm_candle,
                signal_type=k['i'],
                symbol=k['s'],
                open_price=kline_data['open_price'],
                high_price=kline_data['high_price'],
                low_price=kline_data['low_price'],
                close_price=kline_data['close_price'],
                volume=kline_data['volume']
            )
            
            logger.info(f"✓ Signal sauvé: {candle_signal}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde signal: {e}")
        
        # Diffuser le signal Heartbeat (existant + enrichi)
        await channel_layer.group_send(
            "heartbeat",
            {
                "type": "heartbeat_message",
                "message": kline_data
            }
        )
        
        self.stdout.write(
            f'💓 {kline_data["symbol"]} {kline_data["timeframe"]} @ {kline_data["close_price"]} '
            f'[Sauvé en DB]'
        )
```

### ÉTAPE 2.3 : APIs REST pour l'historique ❌

#### Fichier : `backend/apps/core/views.py` (nouveau)
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .models import HeartbeatStatus, CandleHeartbeat
from .serializers import HeartbeatStatusSerializer, CandleHeartbeatSerializer

class HeartbeatViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour consulter l'état du Heartbeat"""
    queryset = HeartbeatStatus.objects.all()
    serializer_class = HeartbeatStatusSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Retourne l'état actuel du Heartbeat"""
        try:
            heartbeat = HeartbeatStatus.objects.get(id=1)
            return Response({
                'is_connected': heartbeat.is_connected,
                'last_application_start': heartbeat.last_application_start,
                'last_application_stop': heartbeat.last_application_stop,
                'last_error': heartbeat.last_error,
                'symbols_monitored': heartbeat.symbols_monitored,
                'uptime_seconds': self.calculate_uptime(heartbeat)
            })
        except HeartbeatStatus.DoesNotExist:
            return Response(
                {'error': 'Heartbeat non initialisé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def signals_history(self, request):
        """Retourne l'historique des signaux par timeframe"""
        timeframe = request.query_params.get('timeframe', '1m')
        limit = min(int(request.query_params.get('limit', 60)), 100)  # Max 100
        
        signals = CandleHeartbeat.objects.filter(
            signal_type=timeframe
        ).order_by('-dhm_candle')[:limit]
        
        serializer = CandleHeartbeatSerializer(signals, many=True)
        return Response({
            'timeframe': timeframe,
            'signals': serializer.data,
            'count': len(serializer.data)
        })
    
    @action(detail=False, methods=['get'])
    def all_timeframes_latest(self, request):
        """Retourne les derniers signaux pour tous les timeframes"""
        timeframes = ['1m', '3m', '5m', '15m', '1h', '4h']
        result = {}
        
        for tf in timeframes:
            latest = CandleHeartbeat.objects.filter(
                signal_type=tf
            ).order_by('-dhm_candle').first()
            
            if latest:
                result[tf] = CandleHeartbeatSerializer(latest).data
            else:
                result[tf] = None
        
        return Response(result)
    
    def calculate_uptime(self, heartbeat):
        """Calcule l'uptime en secondes"""
        if heartbeat.last_application_start:
            if heartbeat.is_connected:
                return int((timezone.now() - heartbeat.last_application_start).total_seconds())
            elif heartbeat.last_application_stop:
                return int((heartbeat.last_application_stop - heartbeat.last_application_start).total_seconds())
        return 0
```

#### Fichier : `backend/apps/core/serializers.py` (nouveau)
```python
from rest_framework import serializers
from .models import HeartbeatStatus, CandleHeartbeat

class HeartbeatStatusSerializer(serializers.ModelSerializer):
    uptime_display = serializers.SerializerMethodField()
    
    class Meta:
        model = HeartbeatStatus
        fields = [
            'id', 'is_connected', 'last_application_start', 
            'last_application_stop', 'last_error', 'symbols_monitored',
            'created_at', 'updated_at', 'uptime_display'
        ]
    
    def get_uptime_display(self, obj):
        """Format d'affichage de l'uptime"""
        if obj.last_application_start:
            from django.utils import timezone
            if obj.is_connected:
                uptime = timezone.now() - obj.last_application_start
            elif obj.last_application_stop:
                uptime = obj.last_application_stop - obj.last_application_start
            else:
                return "Inconnu"
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days:
                return f"{days}j {hours}h {minutes}m"
            elif hours:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        return "Jamais démarré"

class CandleHeartbeatSerializer(serializers.ModelSerializer):
    age_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CandleHeartbeat
        fields = [
            'id', 'dhm_reception', 'dhm_candle', 'signal_type',
            'symbol', 'open_price', 'high_price', 'low_price', 
            'close_price', 'volume', 'created_at', 'age_display'
        ]
    
    def get_age_display(self, obj):
        """Âge du signal en format lisible"""
        from django.utils import timezone
        age = timezone.now() - obj.dhm_candle
        
        if age.days:
            return f"Il y a {age.days}j"
        elif age.seconds > 3600:
            hours = age.seconds // 3600
            return f"Il y a {hours}h"
        elif age.seconds > 60:
            minutes = age.seconds // 60
            return f"Il y a {minutes}min"
        else:
            return "Maintenant"
```

#### Fichier : `backend/apps/core/urls.py` (nouveau)
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HeartbeatViewSet

router = DefaultRouter()
router.register(r'heartbeat', HeartbeatViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

### ÉTAPE 2.4 : Frontend amélioré ❌

#### Fichier : `frontend/src/views/HeartbeatView.vue` (modifications majeures)
```vue
<template>
  <div class="heartbeat-view">
    <h1>Heartbeat</h1>
    
    <!-- Section statut -->
    <div class="status-section">
      <div class="status-card" :class="{ connected: heartbeatStatus?.is_connected }">
        <h3>État de connexion</h3>
        <div class="status-indicator">
          <span class="dot" :class="heartbeatStatus?.is_connected ? 'online' : 'offline'"></span>
          {{ heartbeatStatus?.is_connected ? 'Connecté' : 'Déconnecté' }}
        </div>
        <div v-if="heartbeatStatus?.uptime_display" class="uptime">
          Uptime: {{ heartbeatStatus.uptime_display }}
        </div>
        <div v-if="heartbeatStatus?.last_application_start" class="timestamps">
          <small>Démarré: {{ formatDateTime(heartbeatStatus.last_application_start) }}</small>
        </div>
      </div>
    </div>
    
    <div class="stream-container">
      <!-- Stream temps réel étendu à 60 lignes -->
      <div class="stream-section">
        <h2>Stream Temps Réel</h2>
        <div class="stream-counter">
          {{ streamData.length }}/60 signaux affichés
        </div>
        <div class="stream-list">
          <div 
            v-for="(item, index) in streamData" 
            :key="item.id"
            :class="['stream-item', item.type, { 'is-new': item.isNew }]"
          >
            <span class="timestamp">{{ formatTime(item.timestamp) }}</span>
            <span class="symbol">{{ item.symbol }}</span>
            <span class="timeframe">{{ item.timeframe }}</span>
            <span class="price">{{ item.price }}</span>
            <span class="age">{{ item.age }}</span>
          </div>
        </div>
      </div>
      
      <!-- Section signaux timeframes améliorée -->
      <div class="heartbeat-section">
        <h2>Signaux Heartbeat</h2>
        <div class="timeframe-grid">
          <div 
            v-for="tf in timeframes" 
            :key="tf"
            class="timeframe-card"
            @click="loadTimeframeHistory(tf)"
          >
            <div class="timeframe-label">{{ tf }}</div>
            <div class="signal-count">{{ getSignalCount(tf) }}/60</div>
            <div class="last-signal">
              {{ getLastSignal(tf) }}
            </div>
            
            <!-- Liste des signaux pour ce timeframe -->
            <div class="signals-mini-list">
              <div 
                v-for="(signal, idx) in getTimeframeSignals(tf)" 
                :key="signal.id"
                :class="['mini-signal', { 'is-historical': signal.isHistorical }]"
                :title="`${signal.close_price} @ ${formatTime(signal.dhm_candle)}`"
              >
                <span class="mini-price">{{ formatPrice(signal.close_price) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import api from '@/api'

const streamData = ref([])
const heartbeatSignals = ref({})
const heartbeatStatus = ref(null)
const timeframes = ['1m', '3m', '5m', '15m', '1h', '4h']

// Stockage des signaux par timeframe (jusqu'à 60 par TF)
const timeframeHistory = ref({
  '1m': [], '3m': [], '5m': [], '15m': [], '1h': [], '4h': []
})

let websocket = null

onMounted(async () => {
  await loadHeartbeatStatus()
  await loadHistoricalSignals()
  connectWebSocket()
})

onUnmounted(() => {
  if (websocket) {
    websocket.close()
  }
})

async function loadHeartbeatStatus() {
  try {
    const response = await api.get('/api/core/heartbeat/status/')
    heartbeatStatus.value = response.data
  } catch (error) {
    console.error('Erreur chargement statut Heartbeat:', error)
  }
}

async function loadHistoricalSignals() {
  // Charger les 60 derniers signaux pour chaque timeframe
  for (const tf of timeframes) {
    try {
      const response = await api.get('/api/core/heartbeat/signals_history/', {
        params: { timeframe: tf, limit: 60 }
      })
      
      // Marquer comme historique et ajouter à la liste
      const historicalSignals = response.data.signals.map(signal => ({
        ...signal,
        isHistorical: true,
        isNew: false,
        id: `historical-${signal.id}`,
        timestamp: new Date(signal.dhm_candle),
        age: calculateAge(signal.dhm_candle)
      }))
      
      timeframeHistory.value[tf] = historicalSignals
      
      // Ajouter au stream principal (en orange)
      historicalSignals.forEach((signal, index) => {
        if (streamData.value.length < 60) {
          streamData.value.push({
            id: `stream-historical-${signal.id}`,
            timestamp: signal.timestamp,
            symbol: signal.symbol,
            timeframe: signal.signal_type,
            price: signal.close_price,
            type: 'historical',
            isNew: false,
            age: signal.age
          })
        }
      })
      
    } catch (error) {
      console.error(`Erreur chargement historique ${tf}:`, error)
    }
  }
}

function connectWebSocket() {
  websocket = new WebSocket('ws://localhost:8000/ws/heartbeat/')
  
  websocket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    // Nouveau signal en temps réel (vert)
    const newSignal = {
      id: `live-${Date.now()}`,
      timestamp: new Date(data.dhm_candle),
      symbol: data.symbol,
      timeframe: data.timeframe,
      price: data.close_price,
      type: 'live',
      isNew: true,
      age: 'Maintenant'
    }
    
    // Ajouter au début du stream principal
    streamData.value.unshift(newSignal)
    
    // Limiter à 60 éléments
    if (streamData.value.length > 60) {
      streamData.value = streamData.value.slice(0, 60)
    }
    
    // Ajouter aux signaux du timeframe correspondant
    const tfSignals = timeframeHistory.value[data.timeframe] || []
    tfSignals.unshift({
      ...data,
      isHistorical: false,
      isNew: true,
      id: newSignal.id,
      timestamp: newSignal.timestamp,
      age: 'Maintenant'
    })
    
    // Limiter à 60 par timeframe
    if (tfSignals.length > 60) {
      tfSignals.splice(60)
    }
    
    timeframeHistory.value[data.timeframe] = tfSignals
    
    // Mettre à jour les signaux heartbeat
    heartbeatSignals.value[data.timeframe] = {
      timestamp: new Date(data.dhm_candle),
      price: data.close_price
    }
    
    // Marquer comme ancien après 5 secondes
    setTimeout(() => {
      const signal = streamData.value.find(s => s.id === newSignal.id)
      if (signal) {
        signal.isNew = false
      }
    }, 5000)
  }
}

async function loadTimeframeHistory(timeframe) {
  // Recharger l'historique pour un timeframe spécifique
  await loadHistoricalSignals()
}

function formatTime(timestamp) {
  return timestamp.toLocaleTimeString()
}

function formatDateTime(isoString) {
  return new Date(isoString).toLocaleString()
}

function formatPrice(price) {
  return parseFloat(price).toFixed(2)
}

function calculateAge(isoString) {
  const now = new Date()
  const then = new Date(isoString)
  const diffMs = now - then
  const diffMinutes = Math.floor(diffMs / 60000)
  
  if (diffMinutes < 1) return 'Maintenant'
  if (diffMinutes < 60) return `${diffMinutes}min`
  
  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h`
  
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}j`
}

function getLastSignal(timeframe) {
  const signal = heartbeatSignals.value[timeframe]
  return signal ? `${signal.price} (${formatTime(signal.timestamp)})` : 'Aucun'
}

function getSignalCount(timeframe) {
  return timeframeHistory.value[timeframe]?.length || 0
}

function getTimeframeSignals(timeframe) {
  return timeframeHistory.value[timeframe]?.slice(0, 20) || []
}
</script>

<style scoped>
.heartbeat-view {
  padding: 1rem;
}

.status-section {
  margin-bottom: 2rem;
}

.status-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1rem;
  transition: border-color 0.3s ease;
}

.status-card.connected {
  border-color: var(--color-success);
}

.status-indicator {
  display: flex;
  align-items: center;
  margin: 0.5rem 0;
  font-size: 1.1em;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 0.5rem;
  animation: pulse 2s infinite;
}

.dot.online {
  background-color: var(--color-success);
}

.dot.offline {
  background-color: var(--color-danger);
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.stream-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.stream-section, .heartbeat-section {
  background-color: var(--color-surface);
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
}

.stream-counter {
  font-size: 0.9em;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
}

.stream-list {
  max-height: 600px;  /* Plus haut pour 60 éléments */
  overflow-y: auto;
}

.stream-item {
  display: grid;
  grid-template-columns: 80px 80px 50px 80px 60px;
  gap: 0.5rem;
  padding: 0.3rem 0.5rem;
  border-bottom: 1px solid var(--color-border);
  font-family: monospace;
  font-size: 0.85em;
  transition: background-color 0.3s ease;
}

.stream-item.historical {
  background-color: rgba(255, 165, 0, 0.1);  /* Orange pour historique */
  color: #FFA500;
}

.stream-item.live {
  background-color: rgba(0, 255, 136, 0.1);  /* Vert pour live */
  color: var(--color-success);
}

.stream-item.is-new {
  animation: newSignal 0.5s ease-out;
}

@keyframes newSignal {
  0% { 
    background-color: rgba(0, 255, 136, 0.5);
    transform: translateX(-10px);
  }
  100% { 
    background-color: rgba(0, 255, 136, 0.1);
    transform: translateX(0);
  }
}

.timeframe-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.timeframe-card {
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  padding: 1rem;
  cursor: pointer;
  transition: border-color 0.3s ease;
}

.timeframe-card:hover {
  border-color: var(--color-primary);
}

.timeframe-label {
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: 0.5rem;
}

.signal-count {
  font-size: 0.8em;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
}

.signals-mini-list {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-top: 0.5rem;
  max-height: 60px;
  overflow: hidden;
}

.mini-signal {
  font-size: 0.7em;
  padding: 1px 3px;
  border-radius: 2px;
  background: var(--color-success);
  color: var(--color-background);
}

.mini-signal.is-historical {
  background: #FFA500;  /* Orange pour historique */
}

.uptime, .timestamps {
  font-size: 0.9em;
  color: var(--color-text-secondary);
  margin: 0.25rem 0;
}
</style>
```

### ÉTAPE 2.5 : Mise à jour des URLs et configuration ❌

#### Fichier : `backend/aristobot/urls.py` (modification)
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/', include('apps.brokers.urls')),
    path('api/core/', include('apps.core.urls')),  # NOUVEAU
    # ... autres URLs ...
]
```

### ÉTAPE 2.6 : Migrations et validation ❌

```bash
# Créer les migrations
cd backend
python manage.py makemigrations core

# Appliquer les migrations
python manage.py migrate

# Tester le service Heartbeat amélioré
python manage.py run_heartbeat

# Vérifier l'API REST
curl http://localhost:8000/api/core/heartbeat/status/
curl http://localhost:8000/api/core/heartbeat/signals_history/?timeframe=1m&limit=10
```

---

## ⚡ FONCTIONNALITÉS AJOUTÉES

### ✨ **Backend améliorations :**
1. **Persistance complète** : Chaque signal → sauvé en `candles_heartbeat`
2. **Monitoring avancé** : Tracking démarrage/arrêt dans `heartbeat_status`
3. **APIs REST** : 3 endpoints pour récupérer l'historique
4. **Gestion d'erreurs** : Arrêt propre + sauvegarde du statut

### ✨ **Frontend améliorations :**
1. **Historique 60 éléments** : Stream étendu vs 20 actuels
2. **Couleurs différentielles** : Orange (historique) vs Vert (nouveau)
3. **Statut détaillé** : Card de connexion + uptime
4. **Mini-listes timeframes** : 20 signaux visibles par TF

### ✨ **UX améliorée :**
1. **Initialisation intelligente** : Chargement historique au démarrage
2. **Animations** : Nouveaux signaux animés
3. **Compteurs** : Affichage X/60 pour chaque section
4. **Clics interactifs** : Recharger l'historique par TF

---

## 🎯 TESTS DE VALIDATION

**Le démarrage des serveurs est du ressort de l'utilisateur !**. L'agent IA demande de démarrer ou redémarrer, l'utilisateur s'exécute avec plaisir. L'agent IA ne démarre JAMAIS les serveurs

### Tests Backend
```bash
# 1. Vérifier que les signaux sont sauvés
python manage.py shell
>>> from apps.core.models import CandleHeartbeat
>>> CandleHeartbeat.objects.count()  # Doit augmenter

# 2. Tester l'API
curl http://localhost:8000/api/core/heartbeat/status/
curl http://localhost:8000/api/core/heartbeat/signals_history/?timeframe=1m

# 3. Vérifier les timestamps
>>> from apps.core.models import HeartbeatStatus
>>> h = HeartbeatStatus.objects.get(id=1)
>>> h.last_application_start  # Doit avoir une valeur
```

### Tests Frontend
1. **Démarrer l'app** : Vérifier que les 60 derniers signaux sont chargés en orange
2. **Attendre nouveaux signaux** : Doivent apparaître en vert avec animation
3. **Cliquer sur timeframes** : Doit recharger l'historique
4. **Vérifier compteurs** : X/60 doit être affiché partout

---

## 📊 MÉTRIQUES DE SUCCÈS

- ✅ **Persistance** : 100% des signaux sauvés en DB
- ✅ **Performance** : API < 200ms pour récupérer 60 signaux
- ✅ **UX** : Différenciation visuelle historique/nouveau
- ✅ **Monitoring** : Uptime et statut temps réel
- ✅ **Capacité** : Support 60 signaux par timeframe sans ralentissement

---

## 🚀 LIVRAISON MODULE 2

Une fois terminé, le Module 2 transforme Heartbeat de **simple temps réel** vers **système complet** avec :

1. **📈 Historique complet** : 60 signaux × 6 timeframes = 360 signaux stockés
2. **🎨 Interface riche** : Couleurs, animations, compteurs
3. **📊 APIs REST** : Endpoints pour autres modules
4. **🔍 Monitoring** : Statut détaillé + uptime
5. **💾 Persistance** : Base solide pour Modules 3-8

**Module 2 = Fondation data pour tout Aristobot3 !** 🏗️