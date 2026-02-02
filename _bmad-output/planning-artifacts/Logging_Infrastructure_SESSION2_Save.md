# SESSION SAVE — Logging Infrastructure (Session 2)
**Date :** 2026-01-31
**Statut :** IMPLÉMENTATION COMPLÈTE — Validation en cours
**Reprendre avec :** session vierge, pas de workflow nécessaire

---

## CE QUI EST FAIT — 100%

### Phase 1-5 : Toutes les phases du plan sont implémentées et compilent

**Fichiers créés :**
- `backend/apps/core/services/loguru_config.py` — config partagée loguru (rotation 2min, rétention 10min, JSON serialize)
- `frontend/src/services/logger.js` — logger frontend async avec queue + retry + fallback
- `tools/log_aggregator.py` — agrégateur dual-mode (interactif + CLI) avec timeline causale + alertes

**Fichiers modifiés :**
- `requirements.txt` — ajout `loguru`
- `backend/apps/core/management/commands/run_heartbeat.py` — loguru Terminal 2
- `backend/apps/core/management/commands/run_trading_engine.py` — loguru Terminal 3 + trace_id
- `backend/apps/core/management/commands/run_webhook_receiver.py` — loguru Terminal 6 + trace_id UUID
- `backend/apps/core/management/commands/run_native_exchange_service.py` — loguru Terminal 5
- `backend/apps/core/services/native_exchange_manager.py` — suppression de ~39 print() + traceback.print_exc()
- `backend/apps/core/views.py` — endpoint `frontend_log_view`
- `backend/apps/core/urls.py` — route `frontend-log`
- `frontend/src/main.js` — suppression 8 console.log DEBUG, import frontendLogger, intercepteur console.error + window.error
- `backend/aristobot/settings.py` — intercepteur Terminal 1 avec 3 fixes (voir ci-dessous)

**Supprimés :**
- `listen_redis_webhooks.py`
- `backend/debug_redis_communication.py`

**Installé :**
- `loguru==0.7.3` (+ colorama, win32_setctime)

---

## BUGS FIXES APPLIQUÉS (session 2)

### Bug 1 — AppRegistryNotReady
**Cause :** `from apps.core.services.loguru_config import ...` dans settings.py exécute `__init__.py` qui importe `native_exchange_manager` qui importe `apps.brokers.models.Broker` avant que Django ait initialisé les apps.
**Fix :** Charger loguru_config par chemin de fichier via `importlib.util.spec_from_file_location()` — court-circuit le `__init__.py`.
**Fichier :** `backend/aristobot/settings.py` ligne ~236

### Bug 2 — PermissionError sur terminal1.log (Windows file locking)
**Cause :** Tous les management commands chargent settings.py qui appelait `setup_loguru("terminal1")`. Daphne ET Terminal 5 écrivaient dans le même fichier. La rotation loguru essayait de renommer un fichier verrouillé par un autre processus.
**Fix :** Guard `setup_loguru("terminal1")` avec `_is_daphne = 'daphne' in sys.argv[0].lower()`. Seul Daphne ouvre terminal1.log.
**Fichier :** `backend/aristobot/settings.py` ligne ~244

### Bug 3 — Intercepteur terminal_name hardcodé
**Cause :** Le `_LoguruInterceptHandler` bindait toujours `terminal_name="terminal1"`, même dans les management commands. Logs interceptés via Python logging apparaissaient avec le mauvais tag.
**Fix :** Conditionnel dans `emit()` — bind `terminal_name="terminal1"` seulement si `_is_daphne`, sinon laisser loguru utiliser le contexte posé par le `setup_loguru("terminalX")` du management command.
**Fichier :** `backend/aristobot/settings.py` ligne ~255

### Bug 4 — Blocs brisés après suppression print()
**Cause :** `sed -i '/^\s*print(/d'` a laissé 3 blocs vides dans native_exchange_manager.py : un `except` sans corps, un `if` sans corps, un `try/except` Claude-debug autour d'un logger.info.
**Fix :** Corrigé manuellement : `except` → `logger.error(...)`, `if` superflu supprimé (`pass`), `try/except` autour du logger.info supprimé (était un artifact de debug).
**Fichier :** `backend/apps/core/services/native_exchange_manager.py`

---

## ÉTAT ACTUEL DES TERMINAUX

| Terminal | Commande | Statut | Action nécessaire |
|---|---|---|---|
| T1 Daphne | `daphne aristobot.asgi:application` | ✅ Running | Rien |
| T2 Heartbeat | `python manage.py run_heartbeat` | ❓ Non redémarré | Redémarrer pour activer loguru |
| T3 Trading Engine | `python manage.py run_trading_engine` | ❓ Non redémarré | Redémarrer pour activer loguru |
| T4 Frontend | `npm run dev` | ❓ Non redémarré | Redémarrer pour charger main.js modifié |
| T5 Exchange | `python manage.py run_native_exchange_service` | ✅ Running | Rien — logs vérifié dans terminal5.log |
| T6 Webhook | `python manage.py run_webhook_receiver` | ❓ Non redémarré | Redémarrer pour activer loguru + trace_id |

---

## LOGS VÉRIFIÉS

**terminal5.log** — vérifié, contenu correct :
- Format JSON structuré ✓
- `terminal_name: "terminal5"` partout ✓ (y compris les logs interceptés via Python logging)
- `trace_id: null` — normal, sera peuplé via flow webhook
- Rotation fonctionne ✓ (fichiers datés visibles)
- Aucune erreur ✓

**terminal1.log** — existe, non vérifié encore

---

## À FAIRE DANS LA PROCHAINE SESSION

### Priorité 1 — Finaliser validation
1. Redémarrer T2, T3, T4, T6
2. Vérifier les logs de chaque terminal (`logs/terminal2.log`, `terminal3.log`, `terminal6.log`, `terminal1.log`)
3. Test end-to-end : envoyer un webhook test → vérifier la timeline causale dans les logs (trace_id dans T6 → T3 → T5)
4. Tester l'agrégateur : `python tools/log_aggregator.py --all --last 3`

### Priorité 2 — Tâches hors scope logging (identifiées mais NON traitées)

**Task A — Fix signal Heartbeat vers Terminal 3**
- Problème : T2 publie via `channel_layer.group_send("heartbeat")` (Django Channels). T3 écoute via `redis.pubsub().subscribe('heartbeat')` (Redis Pub/Sub natif). Mécanismes incompatibles.
- Fix : Ajouter `redis.publish('heartbeat', json.dumps(kline_data))` dans `process_closed_candle()` de `run_heartbeat.py`, en parallèle du `group_send` existant.
- Fichier : `backend/apps/core/management/commands/run_heartbeat.py`
- Scope : 3-5 lignes + import redis

**Task B — Compléter Module 4 (update_sl_tp + WebhookState)**
- `update_sl_tp()` dans run_trading_engine.py est un squelette TODO
- Le modèle `WebhookState` existe dans webhooks/models.py mais n'est jamais instancié
- Fichiers : `run_trading_engine.py`, `webhooks/models.py` (référence)

**Task C — Module 7 (Stratégies Python + listen_heartbeat)**
- `listen_heartbeat()` dans run_trading_engine.py est un placeholder `pass`
- Dépend de Task A (le signal doit arriver d'abord)
