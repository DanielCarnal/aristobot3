# SESSION SAVE — Logging Infrastructure Debug Distribué
**Date :** 2026-01-31
**Statut :** PLAN VALIDÉ — Prêt à implémenter
**Décision Dac :** "On y va d'un coup" — pas de découpage V1/V1.1
**Workflow à invoquer pour reprendre :** `/bmad:bmm:workflows:quick-dev`

---

## TOUTES LES DÉCISIONS SONT VALIDÉES — NE PAS REDISCUTER

Les points suivants ont été débattus, challengés par l'équipe BMAD (Winston, Murat, Barry, Dr. Quinn), et validés par Dac. Aucune discussion préalable nécessaire à la reprise.

| Décision | Statut |
|---|---|
| Loguru sur les 7 terminaux | ✅ Validé |
| Rotation 2min, rétention 10min | ✅ Validé |
| Niveau INFO par défaut, DEBUG activable via env var | ✅ Validé |
| Frontend logging async + queue locale + fallback console.warn | ✅ Validé |
| Trace ID UUID propagé dans tous les messages Redis | ✅ Validé |
| Timeline causale avec calcul délais dans l'agrégateur | ✅ Validé |
| Alertes intégrées avec seuils par défaut (recalibrables) | ✅ Validé |
| Test sur Module 3 (trading_manual) — stable | ✅ Validé |
| Suppression immédiate scripts Redis obsolètes après validation | ✅ Validé |
| Redis stats serveur : skip en V1 | ✅ Validé |
| Même machine Win11 — pas de clock skew | ✅ Confirmé |
| Chrome envoie JSON structuré | ✅ Confirmé |
| Volume I/O : pas de risque saturation | ✅ Confirmé |
| Phase 0 (analyse critique) intégrée à Phase 1, pas séparée | ✅ Validé |

---

## PLAN D'IMPLÉMENTATION COMPLET

### Phase 0 — Analyse codebase (intégrée à Phase 1)
**Scope :** `apps/trading_manual` (Module 3, stable)
**Critères pour identifier les points critiques à logger :**
1. `try/except` sans logging
2. Appels API externes (Bitget, Redis) sans trace
3. Décisions métier (calcul ordre, risk check) sans log
4. Transitions d'état importantes (ordre créé → envoyé → confirmé)

**Output :** Liste de ~10-15 points critiques avec numéros de ligne
**Important :** Les logs sont ajoutés immédiatement lors de Phase 1, pas après.

---

### Phase 1 — Loguru setup (45min)
- `pip install loguru` sur les 7 terminaux
- Template config réutilisable par terminal :
  - Rotation : nouveau fichier toutes les 2 minutes
  - Rétention : 10 minutes (~5 fichiers par terminal)
  - Format : JSON avec timestamps ISO8601 précis à la milliseconde
- Niveau par défaut : `INFO`
- `DEBUG` : activable manuellement (env var ou argument CLI)
- Champs obligatoires dans chaque log : `timestamp`, `terminal_name`, `level`, `message`, `data` contextuelles
- Replace les `print()` existants + ajout des points critiques identifiés en Phase 0

---

### Phase 2 — Frontend logging (30min)
- Endpoint `POST /api/frontend-log` — async, non-bloquant
- Intercepteurs côté Vue.js :
  - `console.error`
  - Messages WebSocket reçus
  - Exceptions Vue.js
  - State updates
- Queue locale frontend :
  - 3 tentatives avec 1s de delay entre chaque
  - Fallback `console.warn()` si backend injoignable après les 3 tentatives
- Timestamps ISO8601 directement corrélables avec le backend
- Zéro impact performance UI

---

### Phase 3 — Trace ID propagation (45min)
- Génération `UUID` au point d'entrée :
  - `webhook_receiver` (Terminal 6) — pour les flows webhooks TradingView
  - `trading_manual` (Terminal 1) — pour les flows trading manuel
- Propagation dans tous les messages Redis : champ `trace_id` ajouté au payload JSON
- Loguru context : `logger.bind(trace_id=xxx).info(...)` — le trace_id est porté automatiquement sur tous les logs du flow
- Permet de filtrer un flow complet dans l'agrégateur avec `--trace ABC123`

---

### Phase 4 — Script agrégateur (1h)
**Fichier :** `tools/log_aggregator.py`

**Deux modes d'exécution :**
- Sans arguments : GUI console interactive (sélection composants via menu checkbox)
- Avec arguments : mode script automatisé (pour intégration Claude Code)

**Paramètres CLI :**
```
--components webhook,trading,redis,chrome    # Sélection ciblée
--all                                         # Tous les composants
--last N                                      # N fichiers = N×2 minutes de logs
--level ERROR|INFO|DEBUG                      # Filtrer par niveau
--trace ABC123                                # Filtrer un flow spécifique par trace_id
```

**Output :** Fichier markdown horodaté pour analyse par Claude Code

**Timeline causale par trace_id :**
```
[TRACE abc-123] Webhook received          →    0ms
[TRACE abc-123] Trading decision          →   +45ms
[TRACE abc-123] Bitget API call           →  +120ms
[TRACE abc-123] Bitget response           →  +890ms  ⚠️ SLOW
[TRACE abc-123] Frontend notified         →  +910ms
[TRACE abc-123] UI updated                →  +925ms
```

**Alertes intégrées — seuils par défaut :**
| Opération | WARNING | CRITIQUE |
|---|---|---|
| API Exchange (Bitget, Binance) | >500ms | >2s |
| Redis pub/sub | >200ms | >1s |
| DB write | >1s | >3s |

Les seuils sont recalibrables après observation des premières données réelles.

---

### Phase 5 — Validation & nettoyage
1. Test complet sur Module 3 (`apps/trading_manual`)
2. Vérifier la timeline causale bout en bout sur un flow réel
3. Suppression des scripts obsolètes après validation :
   - `listen_redis_webhooks.py`
   - `debug_redis_communication.py`
4. Git est le safety net — pas de période de transition nécessaire

---

### Exclusions confirmées
- ❌ Redis stats serveur (skip — ajout ultérieur si besoin, via timer dans Terminal 5)
- ❌ Dashboard web (markdown suffit pour Claude Code)
- ❌ Métriques/alerting externe
- ❌ Découpage V1/V1.1 — tout d'un coup

---

## TÂCHES NOTÉES POUR PLUS TARD (hors scope logging)

Ces tâches ont été identifiées lors de l'analyse du code. Elles sont **séparées** du projet logging et ne doivent être traitées qu'après.

### Task #1 — Fix signal Heartbeat vers Terminal 3
**Priorité :** Bloque Task #3
**Problème :** Terminal 2 publie via `channel_layer.group_send("heartbeat")` (Django Channels). Terminal 3 écoute via `redis.pubsub().subscribe('heartbeat')` (Redis Pub/Sub natif). Mécanismes incompatibles — Terminal 3 ne reçoit aucun signal Heartbeat.
**Fix :** Ajouter un `redis.publish('heartbeat', json.dumps(kline_data))` dans `process_closed_candle()` de `run_heartbeat.py`, en parallèle du `group_send` existant.
**Fichier :** `backend/apps/core/management/commands/run_heartbeat.py:141`
**Scope :** 3-5 lignes de code + import redis
**Workflow :** `/bmad:bmm:workflows:quick-dev`

### Task #2 — Compléter Module 4 (update_sl_tp + WebhookState)
**Priorité :** Indépendante
**Problème :** Deux blocs inactifs dans `run_trading_engine.py` :
1. `update_sl_tp()` (L370-393) est un squelette avec TODO. Doit : annuler les anciens ordres SL/TP via ExchangeClient, puis créer les nouveaux.
2. Le modèle `WebhookState` existe complet dans `webhooks/models.py` (suivi position, P&L, SL/TP order IDs) mais n'est **jamais instancié** dans `process_webhook()`. La position en cours n'est pas suivie.
**Fichiers :**
- `backend/apps/core/management/commands/run_trading_engine.py:370-393`
- `backend/apps/webhooks/models.py` (modèle de référence, ne pas modifier)
**Workflow :** `/bmad:bmm:workflows:create-story` puis `/bmad:bmm:workflows:dev-story`

### Task #3 — Module 7 (Analyse bougies + Stratégies Python)
**Priorité :** Après Task #1 (dépend du fix signal Heartbeat)
**Problème :** `listen_heartbeat()` dans `run_trading_engine.py:133-151` est un placeholder avec `pass`. À implémenter :
- Charger les stratégies actives depuis DB (`active_strategies`)
- Récupérer les bougies depuis DB (`CandleHeartbeat`)
- Charge dynamique du code Python via `exec()` dans un namespace isolé
- Identification de la classe via `issubclass(cls, Strategy)`
- Instanciation avec `candles`, `balance`, `position`
- Appel `should_long()` / `should_short()`
- Calcul indicateurs via `pandas_ta`
- Décision trading → ordre vers Terminal 5 via ExchangeClient
**Fichier :** `backend/apps/core/management/commands/run_trading_engine.py:133-151`
**Workflow :** `/bmad:bmm:workflows:create-story` puis `/bmad:bmm:workflows:dev-story`

---

## FINDINGS CODE — Résumé pour ne pas re-lire

### run_heartbeat.py (Terminal 2)
- Rôle : Réception WebSocket Binance → persistance DB → publication signal. **Aucune analyse de bougies.**
- Timeframes actifs : `1m, 3m, 5m, 15m, 1h, 4h` (6 sur 8 dans la spec — manque `10m` et `2h`)
- Symbole : `BTCUSDT` uniquement, hardcoded
- Publication : `channel_layer.group_send("heartbeat")` → va vers le Frontend via Django Channels
- Import mort : `async_to_sync` importé L6, jamais utilisé
- Risque doublon DB si reconnexion WebSocket (pas de `update_or_create`)
- Si sauvegarde DB échoue, le signal est quand même publié (log erreur + continue)

### run_trading_engine.py (Terminal 3)
- Deux tâches parallèles : `listen_heartbeat()` + `listen_webhooks()`
- `listen_heartbeat()` : placeholder `pass` — ne fait rien
- `listen_webhooks()` : **opérationnel** — traitement complet des webhooks
- `execute_order()` : **opérationnel** — balance, calcul quantité via PourCent, ExchangeClient
- `update_sl_tp()` : squelette avec TODO — ne fait aucune action
- `WebhookState` : modèle complet en DB, jamais utilisé dans le code

### run_webhook_receiver.py (Terminal 6)
- Serveur aiohttp sur port 8888
- Endpoint `POST /webhook` + `GET /health`
- Validation token via header `X-Webhook-Token`
- Publication : `redis.publish('webhook_raw', ...)` — Redis Pub/Sub natif
- Réponse rapide, aucune logique métier
- **Opérationnel**

### Webhook model (webhooks/models.py)
- `Webhook` : stockage dual (colonnes typées + `raw_payload` JSONB), statuts complets, indices optimisés
- `WebhookState` : suivi position (entry_price, quantity, SL/TP order IDs, P&L), unique_together sur (user, broker, symbol, status)
- Deux modèles complets et bien structurés

---

## COMMENT REPRENDRE

1. Invoquer `/bmad:bmm:workflows:quick-dev`
2. Indiquer : "Implémentation du plan de logging structuré — voir `_bmad-output/planning-artifacts/Logging_Infrastructure_Session_Save.md`"
3. Le plan est complet, les décisions sont validées, pas de discussion préalable nécessaire
4. Barry (Quick Flow Solo Dev) est le bon agent pour l'implémentation
5. Estimation totale : ~3h30
