# MODULE 4 - API REFERENCE

## 📋 Endpoints REST Webhooks

### Base URL
```
http://localhost:8000/api/
```

---

## 🔌 Webhooks Endpoints

### 1. Liste des webhooks
```http
GET /api/webhooks/
```

**Description** : Récupère l'historique complet des webhooks reçus.

**Query Parameters** :
- `symbol` (string, optional) : Filtrer par symbole (ex: "BTCUSDT")
- `action` (string, optional) : Filtrer par action ("PING", "BuyMarket", etc.)
- `status` (string, optional) : Filtrer par status ("received", "processed", "error")
- `broker` (int, optional) : Filtrer par broker_id
- `ordering` (string, optional) : Tri (ex: "-received_at" pour plus récent en premier)

**Response** :
```json
{
  "count": 42,
  "results": [
    {
      "id": 123,
      "user": 1,
      "user_username": "dev",
      "broker": 13,
      "broker_name": "Bitget Dev",
      "exchange_name": "bitget",
      "symbol": "BTCUSDT",
      "exchange": "BITGET",
      "interval": "15m",
      "action": "BuyLimit",
      "prix": 43000.00,
      "prix_sl": 42000.00,
      "prix_tp": 45000.00,
      "pour_cent": 50.00,
      "status": "processed",
      "order_id": "1234567890",
      "error_message": "",
      "raw_payload": {...},
      "received_at": "2026-01-29T14:32:15.000Z",
      "processed_at": "2026-01-29T14:32:16.500Z"
    }
  ]
}
```

---

### 2. Détail d'un webhook
```http
GET /api/webhooks/{id}/
```

**Description** : Récupère les détails complets d'un webhook spécifique.

**Response** : Objet webhook complet (même structure que liste).

---

### 3. Statistiques webhooks
```http
GET /api/webhooks/stats/
```

**Description** : Statistiques globales sur les webhooks.

**Query Parameters** :
- `period` (string, optional) : Période d'analyse ("24h", "7d", "30d", default: "24h")
- `broker_id` (int, optional) : Filtrer par broker

**Response** :
```json
{
  "total_webhooks": 156,
  "received": 5,
  "processing": 2,
  "processed": 145,
  "errors": 4,
  "missed": 0,
  "actions_breakdown": {
    "PING": 50,
    "BuyMarket": 30,
    "SellMarket": 25,
    "BuyLimit": 20,
    "SellLimit": 18,
    "MAJ": 13
  },
  "success_rate": 92.95,
  "last_webhook_time": "2026-01-29T15:45:30.000Z",
  "period_start": "2026-01-28T15:45:30.000Z",
  "period_end": "2026-01-29T15:45:30.000Z"
}
```

---

### 4. Webhooks récents
```http
GET /api/webhooks/recent/
```

**Description** : 20 derniers webhooks reçus (pour affichage temps réel).

**Response** : Tableau de 20 webhooks (même structure que liste).

---

## 📊 Positions Webhooks Endpoints

### 5. Liste des positions
```http
GET /api/webhook-states/
```

**Description** : Liste complète des positions ouvertes via webhooks.

**Query Parameters** :
- `symbol` (string, optional) : Filtrer par symbole
- `status` (string, optional) : Filtrer par status ("open", "closed")
- `broker` (int, optional) : Filtrer par broker_id
- `ordering` (string, optional) : Tri (ex: "-opened_at")

**Response** :
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "user": 1,
      "user_username": "dev",
      "broker": 13,
      "broker_name": "Bitget Dev",
      "exchange_name": "bitget",
      "symbol": "BTCUSDT",
      "side": "buy",
      "quantity": 0.01,
      "entry_price": 43000.00,
      "current_price": 43500.00,
      "stop_loss_price": 42000.00,
      "stop_loss_order_id": "SL_1234567890",
      "take_profit_price": 45000.00,
      "take_profit_order_id": "TP_0987654321",
      "unrealized_pnl": 5.00,
      "status": "open",
      "opened_at": "2026-01-29T14:30:00.000Z",
      "updated_at": "2026-01-29T15:45:30.000Z"
    }
  ]
}
```

---

### 6. Résumé positions
```http
GET /api/webhook-states/summary/
```

**Description** : Résumé global des positions ouvertes.

**Response** :
```json
{
  "open_positions_count": 3,
  "total_unrealized_pnl": 127.50,
  "active_symbols": [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT"
  ]
}
```

---

### 7. Positions ouvertes uniquement
```http
GET /api/webhook-states/open/
```

**Description** : Filtre uniquement les positions avec status="open".

**Response** : Tableau de positions ouvertes (même structure que liste).

---

## 🔐 Authentification

Tous les endpoints requièrent une **authentification Django Session**.

### Exemple avec axios (frontend)
```javascript
import axios from 'axios'

// Configuration avec credentials
const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true,  // Important pour sessions Django
  headers: {
    'Content-Type': 'application/json'
  }
})

// Utilisation
const response = await api.get('/api/webhooks/stats/', {
  params: { period: '7d' }
})
```

---

## 📝 Exemples d'Utilisation

### Afficher statistiques 7 derniers jours
```javascript
const stats = await api.get('/api/webhooks/stats/', {
  params: { period: '7d' }
})

console.log(`Taux de succes: ${stats.data.success_rate}%`)
console.log(`Total webhooks: ${stats.data.total_webhooks}`)
```

### Afficher positions ouvertes avec P&L
```javascript
const summary = await api.get('/api/webhook-states/summary/')

console.log(`Positions ouvertes: ${summary.data.open_positions_count}`)
console.log(`P&L non realise: ${summary.data.total_unrealized_pnl} USDT`)
```

### Surveiller webhooks en temps réel
```javascript
// Polling toutes les 5 secondes
setInterval(async () => {
  const recent = await api.get('/api/webhooks/recent/')
  console.log('Derniers webhooks:', recent.data)
}, 5000)
```

---

## ⚠️ Notes Importantes

### Multi-tenant
Tous les endpoints filtrent automatiquement par `user_id` de l'utilisateur connecté. Impossible d'accéder aux données d'un autre utilisateur.

### Sécurité
- ✅ Authentification requise sur tous les endpoints
- ✅ Filtrage multi-tenant automatique
- ✅ Permissions Django REST Framework

### Performance
- Les endpoints utilisent `select_related()` pour optimiser les requêtes SQL
- Pagination automatique DRF (20 items par page)
- Index DB sur champs fréquemment filtrés

---

## 🧪 Tests

### Test avec curl
```bash
# Stats webhooks
curl -X GET http://localhost:8000/api/webhooks/stats/?period=24h \
  -H "Cookie: sessionid=YOUR_SESSION_ID"

# Positions ouvertes
curl -X GET http://localhost:8000/api/webhook-states/open/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

### Test avec navigateur
1. Connecte-toi à l'interface Django : http://localhost:8000/admin
2. Ouvre un nouvel onglet : http://localhost:8000/api/webhooks/
3. L'API REST DRF browsable s'affiche

---

**✅ Task #4 Terminée** : APIs REST complètes pour Module 4 Webhooks
