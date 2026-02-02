# PROPOSITION INFRASTRUCTURE LOGGING DISTRIBUÉ - ARISTOBOT3

**Date :** 30 janvier 2026
**Auteur :** Dac
**Statut :** En attente de revue équipe (Party Mode)

---

## 📋 RÉSUMÉ EXÉCUTIF

Infrastructure de logging structurée pour faciliter le debug de l'architecture distribuée Aristobot3 (7 terminaux + Redis + Frontend).

**Objectif :** Traçabilité end-to-end complète avec corrélation temporelle précise entre tous les composants.

---

## 🎯 PROBLÈME ACTUEL

### Symptômes
1. **Debug = perte de temps** importante
2. **Traçage impossible** : Impossible de suivre un événement de bout en bout
3. **Copier/coller manuel** : 7 consoles différentes à surveiller
4. **Scripts monitoring séparés** : `listen_redis_webhooks.py`, `debug_redis_communication.py`
5. **Aucune corrélation temporelle** entre composants

### Impact
- Module 4 (Webhooks) bloqué pour debug
- Ralentissement développement Modules 5-8
- Risque d'erreurs silencieuses non détectées
- Difficulté identification bottlenecks/race conditions

---

## 💡 SOLUTION PROPOSÉE

### Architecture Complète

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPOSANTS LOGGÉS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Terminal 1 (Daphne)        →  Loguru JSON                 │
│  Terminal 2 (Heartbeat)     →  Loguru JSON                 │
│  Terminal 3 (Trading Engine)→  Loguru JSON                 │
│  Terminal 4 (Frontend)      →  Loguru JSON                 │
│  Terminal 5 (Exchange)      →  Loguru JSON                 │
│  Terminal 6 (Webhook)       →  Loguru JSON                 │
│  Terminal 7 (Order Monitor) →  Loguru JSON                 │
│                                                             │
│  Redis Client Operations    →  Interception automatique    │
│  Chrome/Vue.js Frontend     →  Endpoint /api/frontend-log  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              ROTATION & RÉTENTION AUTOMATIQUE                │
├─────────────────────────────────────────────────────────────┤
│  • Rotation : Nouveau fichier toutes les 2 minutes          │
│  • Rétention : Conservation 10 minutes (≈5 fichiers)        │
│  • Format : {terminal_name}_{timestamp}.log                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           SCRIPT AGRÉGATEUR INTELLIGENT                     │
├─────────────────────────────────────────────────────────────┤
│  tools/log_aggregator.py                                    │
│                                                             │
│  Modes :                                                    │
│  • GUI interactive (sélection composants)                   │
│  • Script automatisé (pour Claude Code)                     │
│                                                             │
│  Paramètres :                                               │
│  --components webhook,trading,redis,chrome                  │
│  --all (tous les composants)                                │
│  --level ERROR|INFO|DEBUG                                   │
│  --files 1-5 (nombre fichiers à agréger)                    │
│  --mode timeline|terminal                                   │
│                                                             │
│  Output : Markdown horodaté ISO8601                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    ANALYSE CLAUDE CODE                       │
├─────────────────────────────────────────────────────────────┤
│  • Timeline unifiée avec corrélation temporelle             │
│  • Identification race conditions                           │
│  • Détection bottlenecks                                    │
│  • Traçage événements perdus                                │
│  • Analyse patterns d'erreurs                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 DÉTAILS TECHNIQUES

### 1. Logging Structuré (Loguru)

**Remplacement :**
- ❌ `print()` statements
- ❌ `logging` standard Python
- ✅ `loguru` avec format JSON unifié

**Format JSON :**
```json
{
  "timestamp": "2026-01-30T14:32:15.123Z",
  "terminal": "webhook_receiver",
  "level": "INFO",
  "message": "Webhook reçu",
  "data": {
    "symbol": "BTCUSDT",
    "action": "BuyLimit",
    "prix": 43000.0,
    "user_id": 1,
    "broker_id": 5
  }
}
```

**Implémentation par terminal :**
```python
from loguru import logger
import sys

# Configuration Loguru
logger.remove()  # Supprimer handler par défaut
logger.add(
    f"logs/{terminal_name}_{{time:YYYYMMDD_HHmmss}}.log",
    rotation="2 minutes",
    retention="10 minutes",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
    serialize=True,  # JSON output
    level="INFO"
)
logger.add(sys.stderr, level="INFO")  # Console aussi

# Usage
logger.info("Webhook reçu", symbol="BTCUSDT", action="BuyLimit")
```

---

### 2. Rotation et Rétention

**Paramètres :**
- **Rotation** : `2 minutes` (nouveau fichier)
- **Rétention** : `10 minutes` (conservation)
- **Résultat** : ~5 fichiers par terminal à tout moment

**Nommage fichiers :**
```
logs/
├── webhook_20260130_143000.log    # -10min
├── webhook_20260130_143200.log    # -8min
├── webhook_20260130_143400.log    # -6min
├── webhook_20260130_143600.log    # -4min
├── webhook_20260130_143800.log    # -2min
└── webhook_20260130_144000.log    # Actuel
```

**Avantages :**
- Fichiers petits (< 1MB chacun)
- Recherche rapide par timestamp
- Pas de fichiers géants
- Auto-nettoyage (pas de disque plein)

---

### 3. Logging Composants Distribués

#### A. Redis (Interactions Client)

**Approche :**
- Interception automatique opérations Redis dans chaque terminal
- Format JSON unifié avec timestamps ISO8601
- **PAS de logs serveur Redis** (complexité WSL)

**Implémentation :**
```python
# Wrapper Redis avec logging automatique
class LoggedRedisClient:
    def __init__(self, redis_client):
        self.client = redis_client

    async def rpush(self, key, value):
        logger.info(
            "Redis RPUSH",
            key=key,
            value_preview=value[:100],
            operation="rpush"
        )
        return await self.client.rpush(key, value)

    async def get(self, key):
        result = await self.client.get(key)
        logger.info(
            "Redis GET",
            key=key,
            found=result is not None,
            operation="get"
        )
        return result
```

**Sélection agrégateur :**
```bash
# Filtrer seulement interactions Redis
python tools/log_aggregator.py --components redis --level INFO
```

**Scripts obsolètes :**
- ❌ `listen_redis_webhooks.py` (info déjà dans logs terminaux)
- ❌ `debug_redis_communication.py` (remplacé par agrégateur)

---

#### B. Frontend (Chrome/Vue.js)

**Endpoint Backend :**
```python
# backend/apps/core/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def frontend_log(request):
    """Endpoint logging frontend"""
    log_data = request.data

    logger.info(
        "Frontend Log",
        terminal="chrome_frontend",
        level=log_data.get('level', 'INFO'),
        message=log_data.get('message'),
        component=log_data.get('component'),
        data=log_data.get('data', {})
    )

    return Response({'status': 'logged'})
```

**Frontend Capture :**
```javascript
// frontend/src/utils/logger.js
export const frontendLogger = {
  error(message, data = {}) {
    console.error(message, data);

    // Envoyer au backend
    fetch('http://localhost:8000/api/frontend-log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        level: 'ERROR',
        message,
        component: 'vue-app',
        data,
        timestamp: new Date().toISOString()
      })
    });
  },

  websocket(event, data) {
    this.info(`WebSocket: ${event}`, data);
  }
};

// Vue.js global error handler
app.config.errorHandler = (err, instance, info) => {
  frontendLogger.error('Vue Error', {
    error: err.toString(),
    component: instance?.$options?.name,
    info
  });
};
```

---

### 4. Script Agrégateur Intelligent

**Fichier :** `tools/log_aggregator.py`

#### Mode 1 : GUI Interactive
```bash
python tools/log_aggregator.py
```

**Interface :**
```
╔════════════════════════════════════════════════════════╗
║     ARISTOBOT3 - LOG AGGREGATOR                       ║
╚════════════════════════════════════════════════════════╝

Sélectionnez les composants à inclure :
  [x] 1. Terminal 1 (Daphne)
  [x] 2. Terminal 3 (Trading Engine)
  [x] 3. Terminal 5 (Exchange Gateway)
  [x] 4. Terminal 6 (Webhook Receiver)
  [ ] 5. Redis (interactions client)
  [ ] 6. Chrome Frontend
  [ ] 7. Tous les terminaux

Période : [1] 2min  [2] 4min  [3] 6min  [4] 8min  [5] 10min
Niveau  : [1] ERROR  [2] INFO  [3] DEBUG
Format  : [1] Timeline  [2] Par Terminal

Choix : _
```

#### Mode 2 : Script Automatisé
```bash
# Exemple 1 : Debug webhook spécifique
python tools/log_aggregator.py \
  --components webhook,trading,exchange \
  --level INFO \
  --files 2 \
  --mode timeline \
  --output debug_webhook_2026-01-30.md

# Exemple 2 : Tous les composants avec Redis
python tools/log_aggregator.py \
  --all \
  --level ERROR \
  --files 5 \
  --output full_debug.md

# Exemple 3 : Frontend uniquement
python tools/log_aggregator.py \
  --components chrome \
  --level DEBUG \
  --output frontend_issues.md
```

#### Output Markdown
```markdown
# Debug Log Aggregation - 2026-01-30 14:32:15

**Période :** 4 minutes (2 fichiers par composant)
**Composants :** webhook_receiver, trading_engine, exchange_gateway
**Niveau :** INFO

---

## Timeline Unifiée

**14:30:12.123** [webhook] INFO - Webhook reçu
  - Symbol: BTCUSDT
  - Action: BuyLimit
  - Prix: 43000.0

**14:30:12.156** [webhook] INFO - Redis RPUSH webhook_raw
  - Queue length: 1

**14:30:12.234** [trading] INFO - Webhook consommé depuis Redis
  - Request ID: abc-123
  - Broker: bitget

**14:30:12.567** [trading] INFO - Validation broker
  - Type trading: Webhooks ✅
  - Balance: 1000 USDT ✅

**14:30:13.123** [trading] INFO - Préparation ordre
  - Symbol: BTCUSDT
  - Side: buy
  - Type: limit
  - Amount: 0.01
  - Price: 43000.0

**14:30:13.234** [trading] INFO - Envoi ordre à Exchange Gateway
  - Request ID: xyz-789

**14:30:13.456** [exchange] INFO - Ordre reçu Exchange Gateway
  - Broker ID: 5
  - Client: BitgetNativeClient

**14:30:14.123** [exchange] INFO - Ordre passé sur Bitget
  - Order ID: 1234567890
  - Status: NEW

**14:30:14.234** [exchange] INFO - Réponse envoyée via Redis
  - Response key: exchange_response_xyz-789

**14:30:14.345** [trading] INFO - Confirmation reçue
  - Order ID: 1234567890
  - Sauvegarde DB en cours

**14:30:14.456** [trading] INFO - Trade sauvegardé
  - Trade ID: 456
  - Status: processed

---

## Statistiques

**Total events :** 11
**Durée totale :** 2.333 secondes
**Composants actifs :** 3

**Latences :**
- Webhook → Redis : 33ms
- Redis → Trading Engine : 78ms
- Trading validation : 333ms
- Trading → Exchange : 111ms
- Exchange → Bitget API : 667ms
- Bitget → Réponse : 111ms
- Réponse → DB : 111ms

**Total pipeline :** 1.444 secondes

---
```

---

## 📊 BÉNÉFICES ATTENDUS

### 1. Traçabilité End-to-End
- ✅ Suivre un webhook depuis TradingView jusqu'à l'UI
- ✅ Identifier où un événement se perd
- ✅ Détecter delays anormaux dans la chaîne
- ✅ Corrélation temporelle précise (millisecondes)

### 2. Productivité Debug
- ✅ Zéro copier/coller manuel
- ✅ Timeline unifiée lisible
- ✅ Filtrage par composant/niveau
- ✅ Analyse automatique patterns

### 3. Qualité & Robustesse
- ✅ Détection race conditions
- ✅ Identification bottlenecks
- ✅ Alertes déconnexions silencieuses
- ✅ Analyse performances par phase

### 4. Intégration Claude Code
- ✅ Format markdown optimisé
- ✅ Contexte préservé entre sessions
- ✅ Analyse IA facilitée
- ✅ Suggestions basées sur patterns

---

## 💰 COÛT D'IMPLÉMENTATION

### Temps Estimé
- **Loguru 7 terminaux** : 4h (30min/terminal)
- **Redis logging wrapper** : 2h
- **Frontend endpoint + capture** : 2h
- **Script agrégateur** : 4h
- **Tests & validation** : 2h
- **Documentation** : 1h

**Total :** ~15h soit **2 jours ouvrés**

### Dépendances
- **loguru** : 1 package Python (zero dépendances transitives)
- **Librairies standard** : json, argparse, pathlib, datetime

### Maintenance
- **Initiale** : Configurer rotation/rétention
- **Ongoing** : Quasi-nulle (auto-rotation/cleanup)
- **Évolution** : Ajout niveaux logs si nécessaire

---

## ⚖️ TRADE-OFFS

### Avantages
- ✅ Debug 10x plus rapide
- ✅ Traçabilité complète
- ✅ Détection proactive problèmes
- ✅ Rétention courte = pas de disque plein
- ✅ Format unifié tous composants

### Inconvénients
- ⚠️ 2 jours développement
- ⚠️ Module 4 toujours bloqué pendant implémentation
- ⚠️ Modules 5-8 retardés
- ⚠️ Complexité additionnelle (nouvelle dépendance)
- ⚠️ Possible over-engineering pour 5 users

---

## 🔄 ALTERNATIVES

### Option A : Minimal (1-2h)
```python
# Logging standard Python avec format unifié
import logging
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d | %(name)s | %(message)s',
    level=logging.INFO
)
```
**+ Script bash simple agrégation**

### Option B : Infrastructure Complète (2-3j)
**Proposition actuelle**

### Option C : Hybride
- Minimal maintenant (débloquer Module 4)
- Complet après Module 6-7 (besoin mesuré)

---

## ❓ QUESTIONS OUVERTES

1. **ROI justifié ?** 2 jours infra pour projet 5 users ?
2. **Besoin réel mesuré ?** Combien de fois/semaine debug multi-terminal ?
3. **Loguru indispensable ?** Logging standard insuffisant pourquoi ?
4. **Frontend logging prioritaire ?** Combien bugs UI vs backend ?
5. **Redis logging valeur ajoutée ?** Scripts actuels suffisent ?
6. **Impact timeline ?** Modules 5-8 bloqués combien de temps ?

---

## 🎯 DÉCISION ATTENDUE

**Via Party Mode :**
1. ✅ Valider infrastructure complète OU
2. 🔧 Modifier proposition OU
3. 🚀 Approche progressive (minimal + évolution)

**Plan d'implémentation :**
- Étapes concrètes
- Ordre d'exécution
- Effort réel
- Timeline ajustée Modules 5-8

**Risques identifiés :**
- Points d'attention
- Mitigations
- Dépendances critiques

---

**STATUS : EN ATTENTE REVUE PARTY MODE** 🎉

---

*Document préparé pour discussion équipe BMAD*
*Fichier sauvegardé : 2026-01-30*
