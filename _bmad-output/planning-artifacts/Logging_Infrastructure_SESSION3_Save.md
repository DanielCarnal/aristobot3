# SESSION SAVE — Logging Infrastructure (Session 3)
**Date :** 2026-02-01
**Statut :** Logging 100% validé | Frontend fixé | T7 attend redemarrage
**Reprendre avec :** session vierge, pas de workflow nécessaire

---

## CE QUI EST FAIT CETTE SESSION

### 1. Validation logs tous les terminaux ✅
- terminal2.log ✅ — `terminal_name: "terminal2"`, structured binds (symbol, timeframe, close_price)
- terminal3.log ✅ — `terminal_name: "terminal3"`, binds (mode, host, port), écoute heartbeat + webhook_raw
- terminal5.log ✅ — vérifié session 2, confirmé session 3
- terminal6.log ✅ — `terminal_name: "terminal6"`, binds (host, port)
- terminal7.log ✅ — voir section T7 ci-dessous

### 2. Fix Terminal 7 — deux corrections
**Correction A (session 3, début) :** `setup_loguru("terminal7")` manquait dans `handle()`.
- Fichier : `backend/apps/core/management/commands/run_order_monitor.py`
- Ajouté import `from apps.core.services.loguru_config import setup_loguru` + appel `setup_loguru("terminal7")` au début de `handle()`

**Correction B (session 3, après analyse TEA) :** Asymétrie logging complète.
- Diagnostic TEA : T7 utilisait `self.stdout.write()` pour TOUS ses messages opérationnels + `logging.getLogger(__name__)` au lieu de loguru. Les logs apparaissaient dans terminal7.log via l'intercepteur settings.py avec `file: settings.py` au lieu de `file: run_order_monitor.py`.
- Fix appliqué :
  - `import logging` / `logger = logging.getLogger(__name__)` → `from loguru import logger`
  - Tous les messages opérationnels récurrents → `logger.info()` avec structured binds (`cycle`, `broker_id`, `symbol`, `side`)
  - Les doubles `stdout.write` + `logger.error` sur les erreurs → `logger.error` uniquement
  - `traceback.print_exc()` → `exc_info=True` dans logger
  - Bloc verbose logging (`logging.getLogger().setLevel`) supprimé
- **Ce qui reste stdout-only (correct)** : bannière ASCII, prerequis checks, `[TIP]`, `_display_service_stats()`, `_display_final_stats()`, signal handler, messages [TEST]

### 3. Fix Frontend — page blanche ✅
Trois bugs dans le frontend, tous corrigés :

**Bug 1 — Fatal : import named vs default**
- `main.js:5` : `import { frontendLogger }` mais `logger.js` fait `export default`
- Fix : `import frontendLogger from './services/logger.js'` (accolades enlevées)

**Bug 2 — Critical : boucle infinie console.error**
- L'intercepteur `console.error` appelait `frontendLogger.error()` → `api.post()` → si POST échoue → axios intercepteur → `console.error` → loop
- Fix : guard `_loggingError` boolean pour casser la récursion

**Bug 3 — Minor : DEBUG console.log dans App.vue**
- 6 `console.log('DEBUG: ...')` + 1 `console.error('DEBUG: ...')` supprimés/nettoyés

---

## ÉTAT ACTUEL DES TERMINAUX

| Terminal | Commande | Statut | Action nécessaire |
|---|---|---|---|
| T1 Daphne | `daphne aristobot.asgi:application` | ✅ Running | Rien |
| T2 Heartbeat | `python manage.py run_heartbeat` | ✅ Running | Rien |
| T3 Trading Engine | `python manage.py run_trading_engine` | ✅ Running | Rien |
| T4 Frontend | `npm run dev` | ✅ Running | Vérifier que la page blanche est résolue après refresh |
| T5 Exchange | `python manage.py run_native_exchange_service` | ✅ Running | Rien |
| T6 Webhook | `python manage.py run_webhook_receiver` | ✅ Running | Rien |
| T7 Order Monitor | `python manage.py run_order_monitor` | 🔄 Redemarrage requis | Redemarrer pour appliquer la correction B (loguru) |

---

## À FAIRE — PRIORITÉS POUR LA PROCHAINE SESSION

### Priorité 1 — Redemarrer T7 + vérifier terminal7.log
- Redemarrer T7
- Vérifier que terminal7.log montre maintenant `file: run_order_monitor.py` (pas settings.py)
- Vérifier les structured binds : `cycle`, `broker_id`, `symbol`, `side`

### Priorité 2 — Vérifier frontend
- Rafraîchir http://localhost:5173/ — la page blanche devrait être résolue
- Si ça marche, passer à la priorité 3

### Priorité 3 — Test end-to-end webhook (trace_id)
- Envoyer un webhook test vers T6 (port 8888)
- Vérifier la timeline causale : trace_id dans terminal6.log → terminal3.log → terminal5.log
- Scripts disponibles dans le repo : `test_webhook.py`, `test_webhook_5dollars.py`, `test_webhook_complete.py`
- Le WEBHOOK_TOKEN est dans `.env`

### Priorité 4 — Task A : Fix signal Heartbeat vers Terminal 3
- **Problème :** T2 publie via `channel_layer.group_send("heartbeat")` (Django Channels). T3 écoute via `redis.pubsub().subscribe('heartbeat')` (Redis Pub/Sub natif). Mécanismes **incompatibles** — les signaux heartbeat n'arrivent jamais en T3.
- **Fix :** Ajouter dans `run_heartbeat.py`, fonction `process_closed_candle()`, en parallèle du `group_send` existant :
  ```python
  import redis
  # Dans process_closed_candle(), après le group_send :
  redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
  redis_client.publish('heartbeat', json.dumps(kline_data))
  ```
- **Scope :** 3-5 lignes + import redis
- **Fichier :** `backend/apps/core/management/commands/run_heartbeat.py`
- **Dépendance :** Task C (listen_heartbeat dans Trading Engine) dépend de ce fix

### Priorité 5 — Task B : Compléter Module 4 (update_sl_tp + WebhookState)
- `update_sl_tp()` dans `run_trading_engine.py` est un squelette TODO
- Le modèle `WebhookState` existe dans `webhooks/models.py` mais n'est jamais instancié
- Fichiers : `run_trading_engine.py`, `webhooks/models.py`

### Priorité 6 — Task C : listen_heartbeat dans Trading Engine
- `listen_heartbeat()` dans `run_trading_engine.py` est un placeholder `pass`
- Dépend de Task A (le signal doit arriver d'abord via Redis Pub/Sub)

---

## FICHIERS MODIFIÉS CETTE SESSION

| Fichier | Modification |
|---|---|
| `backend/apps/core/management/commands/run_order_monitor.py` | setup_loguru + conversion complète logging → loguru |
| `frontend/src/main.js` | Fix import default + guard anti-recursion console.error |
| `frontend/src/App.vue` | Suppression 6 console.log DEBUG + nettoyage console.error |

---

## ARCHITECTURE RAPPEL

```
T1 Daphne (8000)     — Serveur web + WebSocket
T2 Heartbeat         — WebSocket Binance → signaux → Redis heartbeat (À FIXER: publie Channels pas Redis)
T3 Trading Engine    — Écoute Redis heartbeat + webhook_raw (heartbeat ne marche pas encore)
T4 Frontend (5173)   — Vue.js 3
T5 Exchange Gateway  — Hub centralisé APIs natives exchanges
T6 Webhook Receiver  — HTTP 8888, reçoit TradingView → Redis webhook_raw
T7 Order Monitor     — Scan ordres toutes les 10s via T5, calcul P&L
```

Communication Redis : heartbeat | webhook_raw | exchange_requests | exchange_responses | websockets
