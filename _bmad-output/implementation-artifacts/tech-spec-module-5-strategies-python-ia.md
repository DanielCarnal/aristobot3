---
title: 'Module 5 - Strategies Python + IA'
slug: 'module-5-strategies-python-ia'
created: '2026-03-02'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
validatedBy: 'Dac'
validatedAt: '2026-03-02'
tech_stack:
  - Django 4.2.15
  - Vue.js 3 Composition API
  - PostgreSQL (TextField pour code Python)
  - CodeMirror v6 (codemirror + @codemirror/lang-python + @codemirror/theme-one-dark)
  - OpenRouter API / Ollama API via aiohttp (deja dans requirements.txt)
  - ast builtin Python pour validation syntaxique
files_to_modify:
  - backend/apps/strategies/models.py        # vide -> modele Strategy
  - backend/apps/strategies/views.py         # vide -> ViewSet + ai-assist + validate_code
  - backend/apps/strategies/urls.py          # urlpatterns=[] -> router + endpoints
  - backend/apps/accounts/models.py          # ajouter champ ai_model CharField
  - backend/aristobot/urls.py               # ajouter path api/strategies/
  - frontend/src/views/StrategiesView.vue   # stub -> vue complete CodeMirror + IA
  - frontend/package.json                   # ajouter codemirror + @codemirror/lang-python + @codemirror/theme-one-dark
files_to_create:
  - backend/apps/strategies/base.py         # NOUVEAU - classe abstraite Strategy
  - backend/apps/strategies/serializers.py  # StrategySerializer + StrategyValidationSerializer
  - backend/apps/strategies/services.py     # AIAssistService (OpenRouter/Ollama) + SYSTEM_PROMPTS
  - frontend/src/composables/useCodeMirror.js  # NOUVEAU - composable Vue reutilisable
code_patterns:
  - Multi-tenant: Strategy.objects.filter(user=self.request.user) - pattern trading_manual/views.py
  - DRF ViewSet + Router + @action(detail=True/False) pour validate_code et ai_assist
  - CsrfExemptSessionAuthentication (settings.py) + permission_classes=[IsAuthenticated]
  - Vue 3 Composition API: ref(), computed(), onMounted() uniquement
  - Dark neon theme: fond #0a0a1a, bordure rgba(0,212,255,0.2), texte #00D4FF
  - aiohttp.ClientSession pour appels IA backend-side uniquement
  - '# -*- coding: utf-8 -*-' premiere ligne chaque fichier Python
  - UserRateThrottle DRF pour ai_assist (10 req/min)
test_patterns:
  - Test manuel: POST /api/strategies/{id}/validate_code/ code valide -> {valid: true}
  - Test manuel: POST avec syntaxe erreur -> {valid: false, errors: [...]}
  - Test manuel: POST sans classe Strategy -> erreur explicite
  - Test multi-tenant: user A ne voit pas strategies user B
  - Test IA OFF: ai_provider='none' -> HTTP 400 erreur claire
  - Test rate limit: 11e requete /ai-assist/ -> HTTP 429
---

# Tech-Spec: Module 5 - Strategies Python + IA

**Created:** 2026-03-02
**Party Mode Review:** 2026-03-02 (Winston, Barry, Murat, Sally, Amelia, John, Dr. Quinn)

---

## Overview

### Problem Statement

L'application `apps/strategies` est un placeholder completement vide (models.py, views.py, urls.py tous vides,
aucune route enregistree dans aristobot/urls.py). Le Trading Engine (Terminal 3) ecoute deja le signal
Heartbeat via Redis Pub/Sub, mais sa methode `listen_heartbeat()` est un stub sans strategie a executer.
Il est impossible pour l'utilisateur de creer, editer ou valider des strategies de trading Python.

### Solution

Construire l'app `strategies` complete avec :
1. Classe de base abstraite `apps/strategies/base.py` que toutes les strategies utilisateur doivent heriter
2. Modele `Strategy` Django (CRUD multi-tenant, champs anticipes pour Module 6 et 7)
3. API REST DRF (CRUD + validation syntaxique AST + assistant IA trimodal)
4. Frontend `StrategiesView.vue` avec editeur CodeMirror v6, template pre-rempli, assistant IA
5. Champ `ai_model` ajoute au modele `User` (migration + exposition dans AccountView)

### Scope

**In Scope:**
- Classe abstraite `Strategy` dans `apps/strategies/base.py`
- Modele `Strategy` : user, name, description, code (TextField), timeframe, created_at, updated_at
- Champ `ai_model` ajoute a `accounts.User` + migration
- Serializers DRF : `StrategySerializer` + `StrategyValidationSerializer`
- ViewSet DRF : list, create, retrieve, update, destroy + `validate_code` + `ai_assist`
- Validation enrichie : ast.parse() + ClassDef + 5 methodes + FORBIDDEN_IMPORTS (os, subprocess, sys, socket...)
- Service IA : `AIAssistService` avec `SYSTEM_PROMPTS` par mode (generate/assist/describe)
- Rate limiting IA : 10 req/min via DRF UserRateThrottle
- URL `/api/strategies/` dans `aristobot/urls.py`
- Composable Vue `useCodeMirror.js` (reutilisable Module 6)
- `StrategiesView.vue` complete : liste CRUD, modal creation/edition, editeur CodeMirror, bouton "Tester syntaxe", assistant IA trimodal

**Out of Scope:**
- Execution reelle des strategies en trading live (Module 7 - ActiveStrategy)
- Backtesting (Module 6 - BacktestResult)
- broker/symbol/risk_percent dans Strategy model (appartiennent a ActiveStrategy M7 et BacktestResult M6)
- Pre-prompts IA modifiables par l'utilisateur (future evolution)
- Sandbox securisee exec() (Module 7, avec __builtins__: {} dans safe_globals)
- Partage de strategies entre utilisateurs

---

## Implementation Plan

### Tasks

- [ ] Task 1: Creer `apps/strategies/base.py` — classe abstraite Strategy
  - File: `backend/apps/strategies/base.py`
  - Action: Creer la classe abstraite avec les 5 methodes abstraites
  - Notes: `# -*- coding: utf-8 -*-` en premiere ligne. Pas d'import externe.
  ```python
  from abc import ABC, abstractmethod

  class Strategy(ABC):
      def __init__(self, candles, balance, position=None):
          self.candles = candles
          self.balance = balance
          self.position = position

      @abstractmethod
      def should_long(self) -> bool: pass

      @abstractmethod
      def should_short(self) -> bool: pass

      @abstractmethod
      def calculate_position_size(self) -> float: pass

      @abstractmethod
      def calculate_stop_loss(self) -> float: pass

      @abstractmethod
      def calculate_take_profit(self) -> float: pass
  ```

- [ ] Task 2: Creer le modele `Strategy` dans `apps/strategies/models.py`
  - File: `backend/apps/strategies/models.py`
  - Action: Creer le modele Strategy multi-tenant
  - Notes: TextField pour code (PostgreSQL TEXT illimite). Index sur (user, timeframe) pour M7.
  - Champs: user (FK), name, description (blank), code (TextField), timeframe (choices), created_at, updated_at
  - Timeframe choices: 1m, 3m, 5m, 15m, 1h, 4h
  - Meta: db_table='strategies', ordering=['-updated_at'], index sur ['user','timeframe']

- [ ] Task 3: Ajouter `ai_model` dans `accounts.User`
  - File: `backend/apps/accounts/models.py`
  - Action: Ajouter `ai_model = CharField(max_length=100, blank=True, default='')`
  - Notes: Exemples: 'gpt-4o-mini', 'llama3:8b'. Pas de chiffrement (ce n'est pas une cle API).
  - Placer apres le champ `ai_api_key` existant

- [ ] Task 4: Creer les migrations
  - Files: `backend/`
  - Action: `python manage.py makemigrations strategies` puis `python manage.py makemigrations accounts`
  - Notes: Verifier que les deux migrations se creent sans conflit. Appliquer avec `python manage.py migrate`.

- [ ] Task 5: Creer `apps/strategies/serializers.py`
  - File: `backend/apps/strategies/serializers.py`
  - Action: Creer StrategySerializer (CRUD) + StrategyValidationSerializer (validation code)
  - Notes:
    - `StrategySerializer`: fields = ['id', 'name', 'description', 'code', 'timeframe', 'created_at', 'updated_at']. user non expose (injecte via perform_create).
    - `StrategyValidationSerializer`: fields = ['code']. Pour action validate_code.
    - `read_only_fields = ['created_at', 'updated_at']`

- [ ] Task 6: Creer `apps/strategies/services.py` — AIAssistService
  - File: `backend/apps/strategies/services.py`
  - Action: Creer la classe AIAssistService avec SYSTEM_PROMPTS et methode call_ai()
  - Notes:
    - `SYSTEM_PROMPTS` dict avec cles 'generate', 'assist', 'describe'
    - Mode 'generate': description naturelle -> code Python complet avec template Strategy
    - Mode 'assist': code existant -> suggestions d'amelioration en francais
    - Mode 'describe': code existant -> description francaise en 2-3 phrases
    - Verifier `user.ai_provider` ('openrouter'/'ollama'/'none') avant appel
    - Si 'none': raise ValueError("Aucun fournisseur IA configure")
    - OpenRouter: POST https://openrouter.ai/api/v1/chat/completions avec Bearer token
    - Ollama: POST {user.ai_endpoint_url}/api/chat avec model=user.ai_model
    - Utiliser `aiohttp.ClientSession` (deja dans requirements.txt)
    - Timeout 30s sur les appels IA

- [ ] Task 7: Creer `apps/strategies/views.py` — StrategyViewSet complet
  - File: `backend/apps/strategies/views.py`
  - Action: Creer le ViewSet avec CRUD + 2 actions custom
  - Notes:
    - `get_queryset`: filter(user=self.request.user) OBLIGATOIRE (multi-tenant)
    - `perform_create`: injecter user depuis request
    - `@action(detail=True, methods=['post'], url_path='validate_code')`: validation AST enrichie
      - ast.parse() + ClassDef + 5 methodes + FORBIDDEN_IMPORTS
      - Retourner `{'valid': bool, 'errors': list}`
    - `@action(detail=False, methods=['post'], url_path='ai-assist')`:
      - Valider mode ('generate'/'assist'/'describe')
      - Mode 'generate' requis field 'description'
      - Mode 'assist'/'describe' requis field 'code'
      - Appeler AIAssistService (sync wrapper avec asyncio.run ou async view)
      - throttle_classes = [AIAssistThrottle] (10/min)
    - Classe AIAssistThrottle: herite UserRateThrottle, rate = '10/min'

- [ ] Task 8: Configurer `apps/strategies/urls.py`
  - File: `backend/apps/strategies/urls.py`
  - Action: Configurer DefaultRouter + enregistrer StrategyViewSet
  - Notes: `router.register(r'', StrategyViewSet, basename='strategy')`. Inclure urls ai-assist et validate_code.

- [ ] Task 9: Enregistrer strategies dans `aristobot/urls.py`
  - File: `backend/aristobot/urls.py`
  - Action: Ajouter `path('api/strategies/', include('apps.strategies.urls'))`
  - Notes: Ajouter apres la ligne trading-manual. Pattern coherent avec les autres apps.

- [ ] Task 10: Installer CodeMirror dans le frontend
  - File: `frontend/package.json`
  - Action: `npm install codemirror @codemirror/lang-python @codemirror/theme-one-dark`
  - Notes: Versions: codemirror@6.x. Verifier compatibilite avec vue@3.4 et vite@5.

- [ ] Task 11: Creer `frontend/src/composables/useCodeMirror.js`
  - File: `frontend/src/composables/useCodeMirror.js`
  - Action: Composable Vue 3 encapsulant CodeMirror v6
  - Notes:
    - Accepte (containerRef, initialCode) en parametres
    - Extensions: basicSetup + python() + oneDark
    - EditorView.updateListener pour sync ref code
    - onUnmounted: editor.destroy() pour cleanup
    - Retourner `{ code, setCode }` (setCode permet de reinitialiser le contenu)
    - Reutilisable dans BacktestView (Module 6)

- [ ] Task 12: Implementer `frontend/src/views/StrategiesView.vue` — vue complete
  - File: `frontend/src/views/StrategiesView.vue`
  - Action: Remplacer le stub par la vue complete avec 3 zones
  - Notes:
    - **Zone 1 — Liste strategies** (colonne gauche, 30%):
      - Liste des strategies de l'utilisateur (GET /api/strategies/)
      - Bouton "Nouvelle strategie" -> ouvre modal
      - Chaque ligne: nom, timeframe, boutons Editer/Supprimer
    - **Zone 2 — Editeur de code** (zone centrale, 70%):
      - Editeur CodeMirror v6 via useCodeMirror composable
      - Theme oneDark, syntaxe Python
      - Formulaire: name (input), timeframe (select), description (textarea optionnel)
      - Bouton "Tester syntaxe" -> POST /api/strategies/{id}/validate_code/
      - Affichage resultat validation (vert = OK, rouge = erreurs)
      - Bouton "Sauvegarder" -> PATCH /api/strategies/{id}/
      - Bouton "Nouvelle" -> reinitialiser avec template de base
    - **Zone 3 — Assistant IA** (panneau lateral collapsible):
      - Selecteur de mode: [✨ Generer] / [🔍 Analyser] / [📖 Decrire]
      - Mode 'generate': textarea description -> POST /api/strategies/ai-assist/ {mode:'generate', description:...}
      - Mode 'assist'/'describe': utilise code actuel de l'editeur
      - Affichage reponse IA avec bouton "Inserer dans l'editeur" (mode generate)
      - Spinner pendant appel IA
      - Message si ai_provider='none': "Configurez un fournisseur IA dans Mon Compte"
    - Template de base (quand nouvelle strategie):
      ```python
      import pandas_ta as ta

      class MaNouvelleStrategie(Strategy):
          def __init__(self, candles, balance, position=None):
              self.candles = candles
              self.balance = balance
              self.position = position

          def should_long(self) -> bool:
              return False

          def should_short(self) -> bool:
              return False

          def calculate_position_size(self) -> float:
              return self.balance * 0.1

          def calculate_stop_loss(self) -> float:
              return 0.02

          def calculate_take_profit(self) -> float:
              return 0.04
      ```
    - Design: dark neon, fond #0a0a1a, bordures rgba(0,212,255,0.2), desktop-first

---

## Acceptance Criteria

- [ ] AC 1: Etant donne un utilisateur authentifie, quand il cree une strategie via POST /api/strategies/, alors la strategie est sauvegardee en DB avec user=request.user et retournee avec HTTP 201.

- [ ] AC 2: Etant donne deux utilisateurs A et B, quand A fait GET /api/strategies/, alors seules les strategies de A sont retournees (isolation multi-tenant stricte).

- [ ] AC 3: Etant donne du code Python syntaxiquement valide avec une classe heritant de Strategy et les 5 methodes, quand POST /api/strategies/{id}/validate_code/, alors la reponse est `{valid: true, errors: []}`.

- [ ] AC 4: Etant donne du code avec une erreur de syntaxe Python, quand POST validate_code, alors `{valid: false, errors: ["Syntaxe: ...message..."]}`.

- [ ] AC 5: Etant donne du code syntaxiquement valide mais sans classe heritant de Strategy, quand POST validate_code, alors `{valid: false, errors: ["Aucune classe heritant de Strategy trouvee"]}`.

- [ ] AC 6: Etant donne du code avec une methode manquante (ex: sans should_long), quand POST validate_code, alors `{valid: false, errors: ["Methodes manquantes: should_long"]}`.

- [ ] AC 7: Etant donne du code avec `import os`, quand POST validate_code, alors `{valid: false, errors: ["Import interdit: 'os'"]}`.

- [ ] AC 8: Etant donne un utilisateur avec ai_provider='openrouter' et une cle valide, quand POST /api/strategies/ai-assist/ avec mode='generate' et une description, alors la reponse contient du code Python avec une classe Strategy.

- [ ] AC 9: Etant donne un utilisateur avec ai_provider='none', quand POST /api/strategies/ai-assist/, alors HTTP 400 avec message "Aucun fournisseur IA configure".

- [ ] AC 10: Etant donne un utilisateur qui envoie plus de 10 requetes/min sur /ai-assist/, alors la 11e requete retourne HTTP 429 (Too Many Requests).

- [ ] AC 11: Etant donne l'editeur frontend, quand l'utilisateur clique "Nouvelle strategie", alors l'editeur CodeMirror est pre-rempli avec le template de base (classe MaNouvelleStrategie heritant de Strategy).

- [ ] AC 12: Etant donne l'editeur CodeMirror ouvert, quand l'utilisateur tape du code Python, alors la coloration syntaxique Python est active (mots-cles en couleur, indentation guidee).

- [ ] AC 13: Etant donne le panneau IA en mode 'Analyser' ou 'Decrire', quand l'utilisateur clique le bouton, alors le code actuel de l'editeur est envoye au backend (pas de textarea supplementaire requis).

---

## Additional Context

### Dependencies

- `codemirror` + `@codemirror/lang-python` + `@codemirror/theme-one-dark` — npm install dans frontend/
- `aiohttp==3.9.1` — deja dans requirements.txt
- `ast` — builtin Python, aucune installation
- Modules 6 et 7 pourront reutiliser `useCodeMirror.js` et la classe `Strategy` de base.py

### Testing Strategy

- **Tests manuels backend** (apres demarrage de Daphne):
  1. POST /api/strategies/ avec code valide — verifier HTTP 201 et persistance DB
  2. POST /api/strategies/{id}/validate_code/ avec code valide — verifier `{valid: true}`
  3. Meme endpoint avec erreur syntaxe — verifier `{valid: false, errors: [...]}`
  4. Meme endpoint avec `import os` — verifier detection import interdit
  5. Connecter user B, GET /api/strategies/ — verifier isolation (zero resultat si user A a des strategies)
  6. POST /ai-assist/ avec ai_provider='none' — verifier HTTP 400
- **Tests manuels frontend**:
  1. Ouvrir StrategiesView — verifier editeur CodeMirror avec coloration syntaxique
  2. Bouton "Nouvelle" — verifier template pre-rempli
  3. Modifier code, "Tester syntaxe" — verifier affichage succes/erreur
  4. Sauvegarder — verifier persistance et rafraichissement liste
  5. Assistant IA mode 'generate' — verifier retour code Python

### Notes

- **Migration ordre**: `makemigrations strategies` d'abord (nouvelle app), puis `makemigrations accounts` (ai_model field). Appliquer avec `migrate`.
- **apps/strategies est dans INSTALLED_APPS** (settings.py ligne existante) mais PAS dans aristobot/urls.py — a ajouter en Task 9.
- **CodeMirror v6 API** tres differente de v5: pas de `CodeMirror(element, options)`. Utiliser `new EditorView({...})` avec extensions array.
- **Anticipation Module 7**: le champ `timeframe` dans Strategy est utilise par Terminal 3 pour filtrer `Strategy.objects.filter(user=..., timeframe=signal_timeframe)` — ne pas le rendre optionnel.
- **Anticipation Module 6**: le composable `useCodeMirror.js` sera reutilise dans BacktestView pour afficher/editer le code de la strategie selectionnee.
- **exec() securise Module 7**: a implementer en M7 avec `safe_globals = {'__builtins__': {}, 'pandas_ta': pandas_ta}`. Hors scope M5.
- **Pre-prompts IA modifiables**: evolution future possible en ajoutant champs ai_prompt_* dans User model. Hors scope M5.
- **Services a redemarrer apres implementation**: Terminal 1 (Daphne) uniquement — les strategies sont CRUD dans Django, pas de nouveau terminal.
