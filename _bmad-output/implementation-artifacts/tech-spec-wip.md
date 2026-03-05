---
title: 'Module 6 - Backtest + Patch M5 STRATEGY_PARAMS'
slug: 'module-6-backtest-patch-m5'
created: '2026-03-03'
status: 'review'
stepsCompleted: [1, 2, 3]
tech_stack:
  - Django 4.2.15 + DRF
  - Vue.js 3 Composition API
  - PostgreSQL (DecimalField pour montants financiers)
  - lightweight-charts (TradingView open source, npm)
  - asyncio + concurrent.futures.ThreadPoolExecutor
  - Django Channels (BacktestConsumer groupe "backtest" deja en place)
  - Redis channel_layer.group_send pour progression WebSocket
  - ExchangeClient (apps/core/services/exchange_client.py) pour get_candles
  - ast builtin Python pour detection STRATEGY_PARAMS
  - itertools.product pour combinaisons grid search
  - threading.Event pour interruption propre du worker
  - useCodeMirror.js composable (deja cree en M5, reutilisable)
files_to_modify:
  - backend/apps/strategies/base.py            # Patch M5 : STRATEGY_PARAMS + params= dans __init__
  - backend/apps/strategies/views.py           # Patch M5 : _validate_strategy_code retourne params_schema
  - frontend/src/views/StrategiesView.vue      # Patch M5 : panneau params lecture seule
  - backend/apps/backtest/models.py            # Candle + BacktestResult (actuellement vide)
  - backend/apps/backtest/views.py             # BacktestViewSet (actuellement vide)
  - backend/apps/backtest/urls.py              # urlpatterns=[] -> router
  - backend/aristobot/urls.py                 # ajouter path api/backtest/
  - frontend/src/views/BacktestView.vue        # stub 3 lignes -> vue complete
  - frontend/package.json                      # ajouter lightweight-charts
files_to_create:
  - backend/apps/backtest/serializers.py       # BacktestRunSerializer + BacktestResultSerializer
  - backend/apps/backtest/services.py          # BacktestService
  - backend/apps/backtest/migrations/0001_initial.py  # via makemigrations backtest
code_patterns:
  - '# -*- coding: utf-8 -*-' premiere ligne chaque fichier Python
  - Multi-tenant: filter(user=request.user) obligatoire (pattern strategies/views.py)
  - DRF DefaultRouter + @action pour endpoints custom (pattern strategies/urls.py)
  - CsrfExemptSessionAuthentication (settings.py) + IsAuthenticated
  - Vue 3 Composition API: ref(), computed(), onMounted(), onUnmounted()
  - Dark neon theme: fond #0a0a1a, bordure rgba(0,212,255,0.2), neon #00D4FF/#00FF88/#FF0055
  - WebSocket: connecter ws://hostname:8000/ws/backtest/ depuis BacktestView.vue
  - DecimalField(max_digits=20, decimal_places=8) pour tous montants financiers
  - useCodeMirror(containerRef, initialCode) depuis frontend/src/composables/useCodeMirror.js
  - ExchangeClient(user_id=...).get_candles(broker_id, symbol, timeframe, limit)
test_patterns:
  - Test STRATEGY_PARAMS: POST validate_code code avec STRATEGY_PARAMS -> params_schema retourne
  - Test backtest run: POST /api/backtest/run/ -> WebSocket progression -> GET /api/backtest/ liste
  - Test cancel: POST /api/backtest/cancel/ pendant run -> status cancelled
  - Test multi-tenant: user A ne voit pas resultats user B
  - Test iteratif: params_ranges valid -> N backtests en sequence, tableau comparatif
  - Test coherence: bougies manquantes -> rechargement avant calcul
  - Test 1 backtest/user: 2e run pendant 1er -> HTTP 409 Conflict
---

# Tech-Spec: Module 6 - Backtest + Patch M5 STRATEGY_PARAMS

**Created:** 2026-03-03
**Party Mode Review:** 2026-03-03 (Winston, John, Barry, Mary, Sally)

## Overview

### Problem Statement

1. **Table candles mal concue** : La doc prevoit `broker_id` (FK privee) alors que les bougies sont des donnees de marche partagees. Deux users Bitget chargeraient les memes donnees deux fois.
2. **M5 sans variables configurables** : `Strategy.base.py` n'expose pas de `STRATEGY_PARAMS`. Impossible de faire varier les parametres pour un backtest. Oubli confirme par Dac le 2026-03-03.
3. **Module 6 absent** : `apps/backtest/models.py` et `views.py` sont vides (1 ligne chacun), `BacktestView.vue` est un stub 3 lignes. `urlpatterns = []` dans `apps/backtest/urls.py`.

### Solution

**Livrable 1 — Patch M5 (3 taches)** : `STRATEGY_PARAMS = {}` dict de classe dans `Strategy`, `params=None` dans `__init__`, extraction AST dans `_validate_strategy_code`, affichage lecture seule dans `StrategiesView.vue`.

**Livrable 2 — Table Candle (incluse dans Livrable 3)** : Modele `Candle` avec `(exchange, symbol, timeframe, open_time)` unique_together — partagee entre tous les users, sans `broker_id` ni `user_id`.

**Livrable 3 — Module 6 complet** : `BacktestService` non-bloquant (`run_in_executor` + `threading.Event` pour cancel), Phase 0 coherence bougies, simulation avec fees taker/maker, graphique `lightweight-charts`, historique, grid search iteratif.

### Scope

**In Scope:**
- Patch M5 : STRATEGY_PARAMS dans base.py, detection AST, panneau UI lecture seule dans StrategiesView.vue
- Modele `Candle` (exchange, symbol, timeframe, open_time, OHLCV) unique_together, partage
- Modele `BacktestResult` (user, strategy, broker, symbol, tf, dates, fees, params_used, metrics, trades_detail JSON, iteration_group)
- `BacktestService` : run_in_executor + ThreadPoolExecutor, 1 backtest/user, cancel via threading.Event, progression WebSocket 2 phases
- Phase 0 : verification coherence bougies + rechargement manquants via ExchangeClient.get_candles
- Simulation : calcul P&L, fees taker/maker, SL/TP appliques
- Frontend `BacktestView.vue` : selection strategie+params editables, graphique lightweight-charts (bougies + indicateurs + markers), historique cliquable, grid search UI
- Grid search iteratif : ranges par parametre, combinaisons via itertools.product, warning > 500, tableau comparatif
- Endpoints REST : run, cancel, list, detail

**Out of Scope:**
- Creation/suppression strategies (M5)
- Export CSV des resultats
- Optimisation ML / gradient descent
- Backtest sur donnees live
- Backtests paralleles multi-users simultanes

---

## Context for Development

### Codebase Patterns

**Etat confirme par investigation directe des fichiers :**

- `apps/backtest/models.py` — 1 ligne vide → clean slate total
- `apps/backtest/views.py` — 1 ligne vide → clean slate total
- `apps/backtest/urls.py` — `urlpatterns = []` → a remplacer
- `apps/backtest/` NON enregistre dans `aristobot/urls.py` → a ajouter
- `apps/backtest/` NON dans migrations → `makemigrations backtest` requis
- `frontend/src/views/BacktestView.vue` — stub 3 lignes → remplacer entierement
- `ws/backtest/` → `BacktestConsumer(AsyncWebsocketConsumer)` dans `core/consumers.py` DEJA declare dans `routing.py` (groupe: "backtest", handler: `backtest_progress`)

**Pattern a reproduire pour ViewSet (strategies/views.py + strategies/urls.py) :**
```python
# urls.py
router = DefaultRouter()
router.register(r'', BacktestViewSet, basename='backtest')
urlpatterns = [path('', include(router.urls))]

# views.py
class BacktestViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return BacktestResult.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='run')
    def run(self, request): ...

    @action(detail=False, methods=['post'], url_path='cancel')
    def cancel(self, request): ...
```

**Pattern WebSocket progression :**
```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)("backtest", {
    "type": "backtest_progress",
    "message": {"phase": "coherence", "pct": 45, "current": 450, "total": 1000}
})
```

**Pattern ExchangeClient :**
```python
from apps.core.services.exchange_client import ExchangeClient
client = ExchangeClient(user_id=user_id)
candles = await client.get_candles(broker_id=broker_id, symbol=symbol, timeframe=timeframe, limit=1000)
```

**STRATEGY_PARAMS convention (a implementer) :**
```python
class MaStrategie(Strategy):
    STRATEGY_PARAMS = {
        'ma_length': {'default': 20, 'min': 1, 'max': 200, 'step': 1,    'type': 'int',   'label': 'Longueur MA'},
        'rsi_period': {'default': 14, 'min': 2, 'max': 100, 'step': 1,   'type': 'int',   'label': 'Periode RSI'},
        'risk_pct':   {'default': 0.02, 'min': 0.001, 'max': 0.1, 'step': 0.001, 'type': 'float', 'label': 'Risque %'},
    }
    def __init__(self, candles, balance, position=None, params=None):
        p = {k: v['default'] for k, v in self.STRATEGY_PARAMS.items()}
        if params:
            p.update(params)
        self.ma_length = p['ma_length']
        # ...
```

**Detection AST de STRATEGY_PARAMS (a ajouter dans _validate_strategy_code) :**
```python
# Chercher STRATEGY_PARAMS = {...} dans le body de la ClassDef
params_schema = {}
for stmt in cls_node.body:
    if isinstance(stmt, ast.Assign):
        for target in stmt.targets:
            if isinstance(target, ast.Name) and target.id == 'STRATEGY_PARAMS':
                if isinstance(stmt.value, ast.Dict):
                    for key, val in zip(stmt.value.keys, stmt.value.values):
                        if isinstance(key, ast.Constant) and isinstance(val, ast.Dict):
                            param_def = {}
                            for pk, pv in zip(val.keys, val.values):
                                if isinstance(pk, ast.Constant) and isinstance(pv, ast.Constant):
                                    param_def[pk.value] = pv.value
                            params_schema[key.value] = param_def
# Retourner {'valid': True, 'errors': [], 'params_schema': params_schema}
```

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `backend/apps/strategies/base.py` | Classe abstraite Strategy — a patcher (STRATEGY_PARAMS + params=) |
| `backend/apps/strategies/views.py` | _validate_strategy_code + ViewSet — a patcher pour retourner params_schema |
| `backend/apps/strategies/serializers.py` | Pattern StrategySerializer a suivre pour BacktestResultSerializer |
| `backend/apps/strategies/urls.py` | Pattern DefaultRouter a reproduire pour backtest/urls.py |
| `backend/apps/strategies/models.py` | FK source pour BacktestResult.strategy |
| `backend/apps/core/consumers.py` | BacktestConsumer deja en place — groupe "backtest", type "backtest_progress" |
| `backend/apps/core/services/exchange_client.py` | get_candles() — a appeler depuis BacktestService |
| `backend/aristobot/routing.py` | ws/backtest/ deja declare, rien a modifier |
| `backend/aristobot/urls.py` | Ajouter path('api/backtest/', include('apps.backtest.urls')) |
| `backend/aristobot/settings.py` | CsrfExemptSessionAuthentication reference |
| `frontend/src/composables/useCodeMirror.js` | Composable reutilisable — ne pas modifier, importer dans BacktestView si editeur code |
| `frontend/src/views/StrategiesView.vue` | Ajouter panneau params apres bloc editeur (lignes ~70-80) |
| `frontend/src/views/BacktestView.vue` | Remplacer stub entierement |
| `frontend/package.json` | Ajouter lightweight-charts |

### Technical Decisions

1. **Candle partage par exchange** : Champ `exchange` CharField, pas de `broker_id` ni `user_id`. Convention identique a `ExchangeSymbol`. Contrainte `unique_together = [('exchange', 'symbol', 'timeframe', 'open_time')]` garantit l'absence de doublons.

2. **Lien broker → candles** : Au moment du backtest, on resout `broker.exchange` depuis le Broker de l'utilisateur. Le `broker_id` sert uniquement a obtenir les credentials pour fetcher les manquants via Terminal 5.

3. **Calcul non-bloquant** : `loop.run_in_executor(ThreadPoolExecutor(max_workers=2), worker_sync, ...)`. Le worker est synchrone (CPU-bound) et communique vers Django via `async_to_sync(channel_layer.group_send)`.

4. **1 backtest par user** : Dict module-level `_active_backtests: dict[int, concurrent.futures.Future]` + `_cancel_events: dict[int, threading.Event]`. Check a l'entree du run : si user_id deja present → HTTP 409. Nettoyage en `finally`.

5. **Cancel** : `_cancel_events[user_id].set()`. Le worker verifie `cancel_event.is_set()` au debut de chaque bougie traitee.

6. **Progression 2 phases** :
   - Phase "coherence" : `{"phase": "coherence", "pct": N, "action": "verification"|"chargement", "count": N}`
   - Phase "simulation" : `{"phase": "simulation", "pct": N, "current_candle": timestamp, "trades": N}`

7. **Fees** : `taker_fee` et `maker_fee` passes en parametres du run, stockes dans BacktestResult. Defaults selon exchange via constante `EXCHANGE_FEES = {'bitget': {'taker': 0.001, 'maker': 0.001}, 'binance': {'taker': 0.001, 'maker': 0.001}, 'kraken': {'taker': 0.0026, 'maker': 0.0016}}`.

8. **Graphique** : `lightweight-charts` v4+. CandlestickSeries pour OHLCV, LineSeries pour indicateurs (tracees depuis les donnees de `trades_detail`), Markers (type 'arrowUp'/'arrowDown') pour les ordres.

9. **Grid search** : `itertools.product(*[range_values for each param])`. Warning si `total_combinations > 500` : retourner HTTP 400 avec message et le nombre calcule. Chaque run iteratif partage le meme `iteration_group` UUID. Table comparaison triee par `sharpe_ratio` desc.

10. **Simulation logique** : Parcourir les bougies en ordre chronologique. A chaque bougie close :
    - Instancier la strategie : `exec(strategy.code, local_vars)` → trouver la classe → `instance = StratClass(candles_window, balance, position, params)`
    - Appeler `should_long()` / `should_short()`, `calculate_position_size()`, `calculate_stop_loss()`, `calculate_take_profit()`
    - Simuler l'ordre avec fees
    - Verifier SL/TP si position ouverte
    - Enregistrer trade dans `trades_detail`
    - Verifier `cancel_event.is_set()` → break si True

11. **Fenetre de bougies** : Passer les N dernieres bougies a chaque iteration (N = 200 par defaut, configurable). Utiliser un deque ou slice de la liste complete.

---

## Implementation Plan

### Tasks

**LIVRABLE 1 — Patch M5 (prerequis)**

- [ ] **Tache 1 : Patch base.py — STRATEGY_PARAMS + params=None**
  - Fichier : `backend/apps/strategies/base.py`
  - Action : Ajouter `STRATEGY_PARAMS = {}` comme attribut de classe dans `Strategy`. Modifier `__init__` pour accepter `params=None` et fusionner avec les defaults. Mettre a jour la docstring et le template affiche.
  - Notes : `params` est un dict optionnel `{nom_param: valeur}`. La fusion : `p = {k: v['default'] for k, v in self.STRATEGY_PARAMS.items()}; if params: p.update(params)`. Ne pas rendre `__init__` abstrait, juste modifier la signature.

- [ ] **Tache 2 : Patch views.py — _validate_strategy_code retourne params_schema**
  - Fichier : `backend/apps/strategies/views.py`
  - Action : Dans `_validate_strategy_code()`, apres la validation des 5 methodes, ajouter la detection AST de `STRATEGY_PARAMS` dans le body de la ClassDef. Retourner `{'valid': True, 'errors': [], 'params_schema': params_schema}` au lieu de `{'valid': True, 'errors': []}`.
  - Notes : Si `STRATEGY_PARAMS` absent ou mal forme, retourner `params_schema: {}` (pas une erreur). Voir le snippet AST dans "Context for Development" ci-dessus.

- [ ] **Tache 3 : Patch StrategiesView.vue — panneau params lecture seule**
  - Fichier : `frontend/src/views/StrategiesView.vue`
  - Action : Apres le bloc editeur CodeMirror, ajouter une section "Parametres detectes" visible uniquement si `validationResult.params_schema` est non vide. Afficher chaque parametre : label, type, default, min, max, step. Ce panneau est en lecture seule (informatif pour M5, editable en M6).
  - Notes : Declencher la detection en appelant `validate_code` apres chargement d'une strategie. Stocker `params_schema` dans une ref `detectedParams`. Style neon dark theme.

**LIVRABLE 2 — Backend Module 6**

- [ ] **Tache 4 : Modeles Candle + BacktestResult**
  - Fichier : `backend/apps/backtest/models.py`
  - Action : Creer deux modeles :

  ```python
  # -*- coding: utf-8 -*-
  from django.db import models
  from django.conf import settings

  EXCHANGE_CHOICES = [
      ('bitget', 'Bitget'), ('binance', 'Binance'), ('kraken', 'Kraken'),
  ]

  class Candle(models.Model):
      """Bougie OHLCV — partagee entre tous les utilisateurs du meme exchange."""
      exchange  = models.CharField(max_length=20, choices=EXCHANGE_CHOICES)
      symbol    = models.CharField(max_length=20)
      timeframe = models.CharField(max_length=5)
      open_time  = models.DateTimeField()
      close_time = models.DateTimeField()
      open_price  = models.DecimalField(max_digits=20, decimal_places=8)
      high_price  = models.DecimalField(max_digits=20, decimal_places=8)
      low_price   = models.DecimalField(max_digits=20, decimal_places=8)
      close_price = models.DecimalField(max_digits=20, decimal_places=8)
      volume      = models.DecimalField(max_digits=20, decimal_places=8)
      class Meta:
          db_table = 'candles'
          unique_together = [('exchange', 'symbol', 'timeframe', 'open_time')]
          indexes = [models.Index(fields=['exchange', 'symbol', 'timeframe', 'open_time'])]

  class BacktestResult(models.Model):
      STATUS_CHOICES = [('running','En cours'),('completed','Termine'),('cancelled','Annule'),('error','Erreur')]
      user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='backtest_results')
      strategy  = models.ForeignKey('strategies.Strategy', on_delete=models.SET_NULL, null=True)
      broker    = models.ForeignKey('brokers.Broker', on_delete=models.SET_NULL, null=True)
      symbol    = models.CharField(max_length=20)
      timeframe = models.CharField(max_length=5)
      start_date = models.DateField()
      end_date   = models.DateField()
      params_used    = models.JSONField(default=dict)
      initial_amount = models.DecimalField(max_digits=20, decimal_places=8)
      final_amount   = models.DecimalField(max_digits=20, decimal_places=8, null=True)
      total_trades   = models.IntegerField(default=0)
      winning_trades = models.IntegerField(default=0)
      losing_trades  = models.IntegerField(default=0)
      max_drawdown   = models.DecimalField(max_digits=10, decimal_places=4, null=True)
      sharpe_ratio   = models.DecimalField(max_digits=10, decimal_places=4, null=True)
      taker_fee      = models.DecimalField(max_digits=8, decimal_places=6, default='0.001')
      maker_fee      = models.DecimalField(max_digits=8, decimal_places=6, default='0.001')
      trades_detail  = models.JSONField(default=list)
      status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
      is_iterative   = models.BooleanField(default=False)
      iteration_group = models.CharField(max_length=36, blank=True, default='')
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)
      class Meta:
          db_table = 'backtest_results'
          ordering = ['-created_at']
          indexes = [models.Index(fields=['user', 'status']), models.Index(fields=['iteration_group'])]
  ```

- [ ] **Tache 5 : Migration**
  - Action : `python manage.py makemigrations backtest` puis `python manage.py migrate`
  - Notes : Verifier que les FK vers `strategies.Strategy` et `brokers.Broker` se resolvent sans erreur.

- [ ] **Tache 6 : Serializers**
  - Fichier : `backend/apps/backtest/serializers.py` (a creer)
  - Action : Creer deux serializers :
    - `BacktestResultSerializer(ModelSerializer)` : tous les champs sauf `trades_detail` (trop lourd pour la liste). Ajouter `strategy_name` et `broker_name` en `SerializerMethodField`.
    - `BacktestResultDetailSerializer(BacktestResultSerializer)` : inclut `trades_detail`.
    - `BacktestRunSerializer(Serializer)` : valide les parametres d'entree du run (`strategy_id`, `broker_id`, `symbol`, `timeframe`, `start_date`, `end_date`, `initial_amount`, `taker_fee`, `maker_fee`, `params`, `params_ranges` optionnel).

- [ ] **Tache 7 : BacktestService**
  - Fichier : `backend/apps/backtest/services.py` (a creer)
  - Action : Implementer `BacktestService` avec :
    - `_active_backtests: dict[int, Future]` et `_cancel_events: dict[int, threading.Event]` au niveau module
    - `EXCHANGE_FEES` constante dict par exchange
    - `run(user_id, broker_id, strategy_id, symbol, timeframe, start_date, end_date, initial_amount, taker_fee, maker_fee, params, params_ranges)` async : verifie 1 backtest/user → envoie vers executor → retourne `backtest_result_id`
    - `cancel(user_id)` : `_cancel_events[user_id].set()`
    - `_worker_sync(...)` synchrone : Phase 0 coherence → Phase 1 simulation (ou grid search)
    - `_run_single_simulation(candles, strategy_code, params, initial_amount, taker_fee, maker_fee, cancel_event, progress_cb)` → retourne dict metriques + trades_detail
    - `_check_and_fill_gaps(exchange, symbol, timeframe, start_date, end_date, broker_id, user_id, cancel_event, progress_cb)` : requete DB, detecte trous, fetch manquants via ExchangeClient, sauvegarde Candle
    - `_generate_combinations(params_ranges)` : itertools.product → liste de dicts params
    - `_publish_progress(phase, pct, extra)` : `async_to_sync(channel_layer.group_send)("backtest", {"type": "backtest_progress", "message": {...}})`
  - Notes : Utiliser `concurrent.futures.ThreadPoolExecutor(max_workers=2)` cree une fois au niveau module. Le `cancel_event` est verifie apres chaque bougie simulee. La strategie est executee via `exec(code, {'__builtins__': {}}, local_vars)` dans un espace isole.

- [ ] **Tache 8 : BacktestViewSet**
  - Fichier : `backend/apps/backtest/views.py`
  - Action : Implementer `BacktestViewSet(viewsets.ReadOnlyModelViewSet)` avec :
    - `get_queryset()` : `BacktestResult.objects.filter(user=self.request.user)`
    - Serializer `BacktestResultSerializer` par defaut, `BacktestResultDetailSerializer` pour `retrieve()`
    - `@action POST run` : valider `BacktestRunSerializer` → si `len(combinations) > 500` retourner HTTP 400 avec count → appeler `BacktestService.run(...)` → retourner `backtest_result_id`
    - `@action POST cancel` : appeler `BacktestService.cancel(user_id)` → retourner 200
    - `@action GET group/{iteration_group}` : retourner tous les BacktestResult du groupe, tries par sharpe_ratio desc

- [ ] **Tache 9 : URLs backtest**
  - Fichier : `backend/apps/backtest/urls.py`
  - Action : Remplacer `urlpatterns = []` par `DefaultRouter` avec `BacktestViewSet` enregistre sur `r''`.

- [ ] **Tache 10 : Enregistrer dans aristobot/urls.py**
  - Fichier : `backend/aristobot/urls.py`
  - Action : Ajouter `path('api/backtest/', include('apps.backtest.urls'))` apres la ligne strategies.

**LIVRABLE 3 — Frontend Module 6**

- [ ] **Tache 11 : Ajouter lightweight-charts**
  - Fichier : `frontend/package.json`
  - Action : Ajouter `"lightweight-charts": "^4.2.0"` dans `dependencies`. Puis `npm install` (a executer par Dac).

- [ ] **Tache 12 : BacktestView.vue — vue complete**
  - Fichier : `frontend/src/views/BacktestView.vue`
  - Action : Remplacer le stub entierement. Implémenter la vue avec :

  **Layout 2 colonnes + zone resultats :**
  ```
  ┌──────────────────────────────────────────────────────────────────┐
  │  PANNEAU GAUCHE (30%)      │  GRAPHIQUE (70%)                    │
  │  ─ Selecteur strategie     │  ┌──────────────────────────────┐   │
  │  ─ Parametres editables    │  │  CandlestickSeries + markers │   │
  │  ─ Broker / Symbol         │  │  (lightweight-charts)        │   │
  │  ─ Timeframe               │  └──────────────────────────────┘   │
  │  ─ Date debut / fin        │  ┌──────────────────────────────┐   │
  │  ─ Montant initial         │  │  LineSeries indicateurs      │   │
  │  ─ Fees taker/maker        │  └──────────────────────────────┘   │
  │  ─ [Grid search toggle]    │                                     │
  │    Ranges par parametre    │                                     │
  │    Nb combinaisons: N      │                                     │
  │  ─ [LANCER] [ANNULER]      │                                     │
  │  ─ Progression:            │                                     │
  │    Phase / ████░ 67%       │                                     │
  ├────────────────────────────┴─────────────────────────────────────┤
  │  ZONE RESULTATS (pleine largeur)                                 │
  │  [Statistiques] [Trades] [Historique] [Comparaison iterative]    │
  └──────────────────────────────────────────────────────────────────┘
  ```

  **Fonctionnalites Vue :**
  - `onMounted()` : charger liste des strategies (GET `/api/strategies/`) et des brokers, connecter WebSocket `ws://hostname:8000/ws/backtest/`
  - `onUnmounted()` : fermer WebSocket
  - `selectStrategy(s)` : appeler `POST /api/strategies/{id}/validate_code/` pour obtenir `params_schema`, afficher les parametres editables (inputs numeriques avec min/max/step)
  - `toggleGridSearch()` : basculer entre mode simple et mode iteratif. En mode iteratif, afficher pour chaque param : min, max, step, et calculer dynamiquement `nb_combinaisons = product des lengths de ranges`. Afficher warning rouge si > 500.
  - `launchBacktest()` : POST `/api/backtest/run/` avec tous les parametres. Si HTTP 409 → toast "Un backtest est deja en cours".
  - `cancelBacktest()` : POST `/api/backtest/cancel/`
  - WebSocket `onmessage` : mettre a jour `progressPhase`, `progressPct`, `progressDetail`
  - Apres run : GET `/api/backtest/{id}/` pour resultats, mettre a jour le graphique et les stats
  - `loadHistory()` : GET `/api/backtest/` pour historique, afficher dans tableau. Clic sur une ligne → charger les resultats et reafficher graphique.
  - `loadGroupComparison(iteration_group)` : GET `/api/backtest/group/{id}/` → tableau comparatif trie par sharpe_ratio

  **Graphique lightweight-charts :**
  ```javascript
  import { createChart } from 'lightweight-charts'
  // Dans onMounted(), apres div#chart est monte
  const chart = createChart(chartContainer.value, {
    layout: { background: { color: '#0a0a1a' }, textColor: '#00D4FF' },
    grid: { vertLines: { color: 'rgba(0,212,255,0.05)' }, horzLines: { color: 'rgba(0,212,255,0.05)' } },
  })
  const candleSeries = chart.addCandlestickSeries({ ... })
  // Apres backtest: setData(candles), setMarkers(trades.map(...))
  // Pour indicateurs: chart.addLineSeries({color: '#00FF88'}).setData(indicator_points)
  ```

  **Markers pour ordres :**
  ```javascript
  markers = trades.map(t => ({
    time: t.timestamp,
    position: t.side === 'buy' ? 'belowBar' : 'aboveBar',
    color: t.side === 'buy' ? '#00FF88' : '#FF0055',
    shape: t.side === 'buy' ? 'arrowUp' : 'arrowDown',
    text: `${t.side.toUpperCase()} ${t.quantity}`,
  }))
  ```

  **Onglets resultats :**
  - **Statistiques** : Tableau recap (montant initial/final, total trades, win rate, max drawdown, sharpe ratio, total fees)
  - **Trades** : Liste de tous les trades simules (date, side, qty, price, fee, P&L, balance)
  - **Historique** : 20 derniers BacktestResult (strategy, symbol, tf, dates, win rate, sharpe, params_used resume). Clic = rechargement graphique.
  - **Comparaison** : Visible seulement si dernier run iteratif. Tableau des N combinaisons triees par sharpe_ratio. Colonnes = parametres + metriques.

---

### Acceptance Criteria

- [ ] **AC 1** : Etant donne une strategie avec `STRATEGY_PARAMS` declare, quand `POST /api/strategies/{id}/validate_code/` est appele, alors la reponse contient `params_schema` avec les clefs/valeurs detectees, en plus de `valid: true`.

- [ ] **AC 2** : Etant donne que `STRATEGY_PARAMS` est absent du code, quand `validate_code` est appele, alors `params_schema` est un dict vide `{}` et `valid` reste `true` (pas d'erreur).

- [ ] **AC 3** : Etant donne une strategie chargee dans StrategiesView avec `STRATEGY_PARAMS`, quand la validation est effectuee, alors le panneau "Parametres detectes" affiche les params avec leurs contraintes (min/max/step/default/type).

- [ ] **AC 4** : Etant donne deux utilisateurs avec un broker Bitget, quand tous les deux backtestent BTC/USDT 1h sur la meme periode, alors la table `candles` ne contient qu'une seule serie de donnees pour `(exchange='bitget', symbol='BTCUSDT', timeframe='1h')`.

- [ ] **AC 5** : Etant donne un user avec un broker Binance et un autre avec Bitget, quand ils backtestent le meme symbole/periode, alors la table `candles` contient deux series distinctes (une par exchange).

- [ ] **AC 6** : Etant donne un backtest en cours pour user A, quand user A tente de lancer un second backtest, alors l'API retourne HTTP 409 avec message "Un backtest est deja en cours".

- [ ] **AC 7** : Etant donne un backtest en cours, quand `POST /api/backtest/cancel/` est appele, alors le calcul s'arrete proprement (au plus a la bougie suivante), le BacktestResult est mis en `status='cancelled'`, et le WebSocket publie un message de fin.

- [ ] **AC 8** : Etant donne une plage de dates avec des trous dans la table `candles`, quand un backtest est lance, alors la Phase 0 detecte les manquants, les fetche via Terminal 5, les sauvegarde en DB, et le calcul commence avec des donnees completes.

- [ ] **AC 9** : Etant donne un backtest termine, quand les resultats sont affiches, alors le P&L tient compte des fees taker/maker saisis (chaque ordre est debite des fees).

- [ ] **AC 10** : Etant donne un backtest termine, quand les resultats sont affiches dans BacktestView, alors le graphique lightweight-charts montre les bougies OHLCV avec des fleches vertes (achats) et rouges (ventes) aux timestamps corrects.

- [ ] **AC 11** : Etant donne le mode grid search avec 3 valeurs pour parametre A et 4 valeurs pour parametre B, quand l'utilisateur entre les ranges, alors l'UI affiche "12 combinaisons". Si > 500, un warning rouge s'affiche et le bouton Lancer est desactive.

- [ ] **AC 12** : Etant donne un grid search lance, quand tous les backtests iteratifs sont termines, alors l'onglet "Comparaison" affiche un tableau avec une ligne par combinaison, triees par sharpe_ratio decroissant.

- [ ] **AC 13** : Etant donne l'historique des backtests, quand l'utilisateur clique sur une ligne de l'historique, alors le graphique se recharge avec les bougies et trades de ce backtest precedent.

- [ ] **AC 14** : Etant donne user A et user B, quand user A appelle `GET /api/backtest/`, alors la liste ne contient que les BacktestResult de user A (multi-tenant strict).

- [ ] **AC 15** : Etant donne un backtest en cours, quand le WebSocket est connecte, alors les messages de progression arrivent avec `phase` ("coherence" ou "simulation") et `pct` (0-100) en temps reel.

---

## Additional Context

### Dependencies

**Nouvelles dependances npm :**
- `lightweight-charts: ^4.2.0` — graphique bougies TradingView open source. `npm install lightweight-charts` a executer par Dac apres modification de package.json.

**Pas de nouveau package Python :**
- `asyncio`, `concurrent.futures`, `threading`, `itertools`, `ast` sont tous stdlib Python 3.11.

**Infrastructure existante reutilisee :**
- `BacktestConsumer` + route `ws/backtest/` : deja en place, aucune modification
- `useCodeMirror.js` : aucune modification, importable si besoin
- `ExchangeClient.get_candles()` : deja implementee

**Services a redemarrer apres implementation :**
- Terminal 1 (Daphne) : apres toute modification backend
- Terminal 4 (Vite/npm) : apres `npm install lightweight-charts`

**Ordre d'execution des migrations :**
```bash
python manage.py makemigrations backtest
python manage.py migrate
```

### Testing Strategy

**Tests manuels prioritaires (dans l'ordre) :**

1. **Patch M5** : Charger une strategie avec `STRATEGY_PARAMS` dans StrategiesView → cliquer "Tester syntaxe" → verifier que le panneau "Parametres detectes" apparait.

2. **Table Candle** : Apres migration, verifier `python manage.py dbshell` → `\d candles` → confirmer `unique_together`.

3. **Run simple** : Lancer un backtest via BacktestView (broker Bitget, BTC/USDT, 1h, 7 jours, montant 1000 USDT). Verifier WebSocket progression dans la console. Verifier BacktestResult cree en DB.

4. **Cancel** : Lancer backtest longue periode, cliquer Annuler → verifier status='cancelled'.

5. **Grid search 9 combinaisons** : 3 valeurs MA × 3 valeurs RSI → verifier 9 BacktestResult avec meme iteration_group → verifier tableau comparatif.

6. **Warning >500** : Entrer ranges generant 501 combinaisons → verifier warning rouge et bouton desactive.

7. **Multi-tenant** : User A lance backtest → GET /api/backtest/ avec user B → verifier liste vide.

8. **Coherence bougies** : Backtest sur periode sans bougies en DB → verifier Phase 0 effectue le chargement.

9. **Graphique** : Verifier bougies OHLCV visibles, markers achat/vente places aux bons timestamps.

10. **Historique** : Cliquer sur run precedent dans l'historique → verifier rechargement du graphique.

### Notes

**Points d'attention pour l'implementeur :**

- `BacktestConsumer` diffuse a TOUS les clients connectes au groupe "backtest". Cela est acceptable car 1 seul backtest par user a la fois. Si plusieurs users backtestent simultanement (un par user), leurs progressions se melangent dans le meme canal. Pour M6, ajouter `user_id` dans les messages de progression afin que le frontend filtre les siens.

- `get_candles` de ExchangeClient retourne des donnees brutes de Terminal 5. Verifier le format exact (list de dicts avec cles `open`, `high`, `low`, `close`, `volume`, `timestamp`) avant d'implementer la sauvegarde `Candle.objects.bulk_create`.

- La detection AST de `STRATEGY_PARAMS` est best-effort. Si l'utilisateur declare le dict de facon non-litterale (ex: `STRATEGY_PARAMS = build_params()`), la detection retourne `{}` sans erreur. Documenter cette limite dans l'UI.

- `exec()` dans `_worker_sync` doit utiliser un namespace isole : `local_vars = {}; exec(code, {'__builtins__': {}, 'pandas_ta': pandas_ta_module}, local_vars)`. Importer pandas_ta au debut de services.py pour le rendre disponible.

- Le `BacktestResult` est cree en DB avec `status='running'` AVANT le debut du calcul, pour que l'ID soit disponible a retourner immediatement a l'API. Le worker le met a jour en `completed` ou `cancelled` ou `error` en fin de traitement.

- TradingView `lightweight-charts` v4 : l'API a change entre v3 et v4. S'assurer d'utiliser `createChart` de la v4 (import `{ createChart, ColorType }` de `'lightweight-charts'`).
