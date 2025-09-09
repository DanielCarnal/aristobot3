# HEARTBEAT MODULE2 - GUIDE DE DEMARRAGE

## Statut
✅ **MODULE2 COMPLET ET FONCTIONNEL**

## Architecture implémentée

### Backend Django
- ✅ Modèles étendus : `CandleHeartbeat` + `HeartbeatStatus`
- ✅ Service persistance : `run_heartbeat.py` avec sauvegarde DB
- ✅ APIs REST complètes : status, recent, timeframes, signals
- ✅ URLs routing : `/api/heartbeat/*`
- ✅ Migrations appliquées
- ✅ Authentification requise

### Frontend Vue.js  
- ✅ Interface 60 éléments (40 historiques + 20 temps réel)
- ✅ Différenciation couleur : 🟠 Orange (historique) + 🟢 Vert (temps réel)
- ✅ Barre de statut avec monitoring
- ✅ Statistiques par timeframe
- ✅ Actualisation automatique

## Démarrage rapide

### 1. Test des APIs (recommandé)
```bash
# Terminal 1 - Démarrer Django
cd backend/
python manage.py runserver

# Terminal 2 - Tester MODULE2
cd ..
python test_heartbeat_quick.py
```

### 2. Interface complète
```bash
# Terminal 1 - Backend Django
cd backend/
python manage.py runserver

# Terminal 2 - Service Heartbeat (données temps réel)  
cd backend/
python manage.py run_heartbeat

# Terminal 3 - Frontend Vue.js
cd frontend/
npm run dev

# Ouvrir : http://localhost:5173/heartbeat
```

## APIs MODULE2 disponibles

| Endpoint | Description | Exemple |
|----------|-------------|---------|
| `GET /api/heartbeat/status/` | Statut service Heartbeat | `{"is_connected": true, ...}` |
| `GET /api/heartbeat/recent/?limit=60` | 60 derniers signaux | `{"signals": [...], "count": 42}` |
| `GET /api/heartbeat/timeframes/?hours_back=1` | Stats par timeframe | `{"timeframe_counts": [...]}` |
| `GET /api/heartbeat/signals/?signal_type=1m` | Historique filtré | `{"results": [...]}` |

## Fonctionnalités MODULE2

### Interface Heartbeat
- **60 éléments maximum** (configurable via `limit`)
- **Couleurs différentielles** :
  - 🟠 **Orange** : Signaux historiques (chargés depuis la DB)
  - 🟢 **Vert** : Signaux temps réel (WebSocket direct)
- **Barre de statut** : Connexion, total signaux, dernière màj
- **Statistiques timeframes** : Compteurs 1h par période (1m, 3m, 5m, 15m, 1h, 4h)

### Persistance données
- **Tous les signaux sauvés** dans `CandleHeartbeat`
- **Cycle de vie trackê** : start/stop dans `HeartbeatStatus`  
- **Données OHLCV complètes** : Open, High, Low, Close, Volume
- **Timestamps précis** : réception + timestamp Binance

## Diagnostic

### Si status "Déconnecté"
```bash
# Vérifier si le service Heartbeat tourne
cd backend/
python heartbeat_diagnostic.py

# Si arrêté, démarrer :
python manage.py run_heartbeat
```

### Si APIs retournent 404
```bash  
# Vérifier que Django est démarré
curl http://localhost:8000/api/heartbeat/status/

# Si erreur, démarrer :
cd backend/
python manage.py runserver
```

### Si frontend ne charge pas les données
1. Vérifier authentification : Login dans l'interface
2. Vérifier APIs backend : `python test_heartbeat_quick.py`
3. Vérifier console browser : F12 → Network/Console

## Fichiers clés

```
backend/
├── apps/core/models.py           # CandleHeartbeat + HeartbeatStatus  
├── apps/core/views.py            # HeartbeatViewSet (APIs)
├── apps/core/serializers.py     # Sérialiseurs DRF
├── apps/core/urls.py             # Routes APIs
├── apps/core/management/commands/run_heartbeat.py  # Service persistance
└── aristobot/urls.py             # Configuration principale

frontend/
└── src/views/HeartbeatView.vue   # Interface MODULE2

racine/
├── test_heartbeat_quick.py       # Test APIs Python
├── test_heartbeat_module2.sh     # Test complet Bash  
├── test_heartbeat_module2.ps1    # Test complet PowerShell
└── heartbeat_diagnostic.py       # Diagnostic backend
```

## Prochaines étapes possibles

- **MODULE3** : Stratégies de trading
- **MODULE4** : Engine de trading automatisé  
- **MODULE5** : Backtesting avancé

---

🎯 **MODULE2 HEARTBEAT COMPLET !**
Interface 60 éléments avec persistance et différenciation couleurs opérationnelle.