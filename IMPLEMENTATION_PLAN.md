# PLAN D'IMPLÉMENTATION ARISTOBOT3

## 📊 ÉTAT GLOBAL DU PROJET

### ✅ MODULE 1 - USER ACCOUNT & BROKERS (✅ COMPLÉTÉ)
- **Authentification** : Système multi-tenant sécurisé ✅
- **Mode DEBUG** : Gestion via table DebugMode ✅  
- **Brokers** : CRUD complet avec test connexion ✅
- **Frontend AccountView** : Interface complète avec modale ✅
- **Services** : SymbolUpdaterService + endpoints API ✅
- **Sécurité** : Chiffrement clés API + permissions ✅

### ✅ MODULE 2 - HEARTBEAT AMÉLIORÉ (✅ COMPLÉTÉ)
- **Persistance PostgreSQL** : Modèle CandleHeartbeat avec OHLCV ✅
- **Service heartbeat étendu** : Sauvegarde auto + WebSocket dual-channel ✅
- **APIs REST** : 3 endpoints pour historique et statut ✅
- **Frontend amélioré** : Historique orange + temps réel vert ✅
- **Interface épurée** : Suppression barre statut + titre explicatif ✅
- **Monitoring complet** : 240 signaux historiques + surveillance temps réel ✅

### 🚀 MODULES SUIVANTS - PRIORITÉ RECOMMANDÉE

#### ✅ **MODULE 3 - TRADING MANUEL** (✅ COMPLÉTÉ)
**Réalisé :** Base nécessaire pour tous les autres modules
- Interface trading manuelle complète ✅
- Passage d'ordres via APIs natives (buy/sell, market/limit) ✅  
- Calcul automatique quantité/montant ✅
- Historique des trades avec persistance ✅

#### 🔔 **MODULE 4 - WEBHOOKS TRADINGVIEW** (Priorité 1 - Automatisation Simple)
**Pourquoi maintenant :** Logique simple, réutilise Module 3 terminé
- Réception signaux TradingView
- Exécution automatique des ordres
- Monitoring et logs complets

#### 🧠 **MODULE 5 - STRATÉGIES PYTHON + IA** (Priorité 2 - Intelligence)
**Pourquoi après Module 4 :** Fondation pour automation intelligente
- Éditeur de stratégies Python
- Assistant IA pour génération de code
- Validation et tests de stratégies

#### 🤖 **MODULE 7 - TRADING BOT** (Priorité 3 - Automatisation Complète)
**Pourquoi après Module 5 :** Utilise stratégies + Heartbeat fonctionnel
- Activation des stratégies automatisées
- Écoute signaux Heartbeat
- Exécution trades automatiques

#### 📊 **MODULE 6 - BACKTEST** (Priorité 4 - Validation)
**Pourquoi après Module 7 :** Nécessite stratégies validées en production
- Test stratégies sur données historiques
- Validation performance avant production

#### 📈 **MODULE 8 - STATISTIQUES** (Priorité 5 - Analyse)
**Final :** Analyse complète avec historique complet

## 🎯 DÉCISIONS TECHNIQUES VALIDÉES

### Base de données
- **PostgreSQL uniquement** (pas de MongoDB)
- **Multi-tenant strict** : Filtrage par `user_id` obligatoire
- **Decimal Python** pour tous les montants/prix
- **UTC en DB**, affichage selon préférence utilisateur

### Architecture
- **APIs natives** pour trading (Bitget, Binance, Kraken) + **CCXT métadonnées** (liste exchanges, validation)
- **Singleton pattern** pour instances Exchange (une par exchange/user)
- **asyncio** pour parallélisme (pas de Celery)
- **Django Channels** pour WebSocket
- **Heartbeat** : WebSocket natif Binance

### Développement
- **Mode DEBUG** : `DEBUG_ARISTOBOT=True` -> Table DebugMode + user "dev" normal
- **Mode TESTNET** : Global avec status bar inversée
- **Historique complet** : Toutes les tentatives de trades
- **Chiffrement** : Django SECRET_KEY pour API keys

### Frontend
- **Vue 3 Composition API** uniquement
- **Pinia** pour l'état global
- **LocalStorage** pour préférences UI
- **Dark mode** obligatoire avec couleurs néon

---

## 📦 MODULE 1 : USER ACCOUNT & BROKERS

### Objectifs
1. Créer le système d'authentification multi-tenant
2. Gérer les brokers (exchanges) avec APIs natives
3. Implémenter le mode DEBUG avec user "dev"
4. Créer la table partagée des symboles
5. Frontend de gestion des comptes et brokers

**📋 Détails techniques complets :** Voir `MODULE1_IMPLEMENTATION.md`

**✅ Statut :** 85% terminé - Fonctionnalités core implémentées

---

## 📦 MODULE 2 : HEARTBEAT AMÉLIORÉ ✅ **TERMINÉ**

### ✅ Objectifs réalisés
1. ✅ Service Heartbeat amélioré avec persistance PostgreSQL
2. ✅ Modèle `CandleHeartbeat` pour bougies OHLCV complètes
3. ✅ Interface monitoring temps réel avec différenciation couleurs
4. ✅ APIs REST robustes pour historique et statut

### ✅ Réalisations techniques
- **Modèle CandleHeartbeat** : Stockage OHLCV + timestamps
- **Service dual-channel** : WebSocket brut + processed
- **3 APIs REST** : /status/, /heartbeat-history/, /signals/
- **Frontend épuré** : 240 signaux historiques (orange) + temps réel (vert)
- **Interface intuitive** : Titre "Heartbeat" + explication contextuelle

**📊 Détails complets :** Voir `MODULE2_IMPLEMENTATION.md`

## 📦 MODULE 2 : Service Exchange Centralisé (Terminal 5) ✅ **TERMINÉ**

⚠️ **DOCUMENTATION COMPLÈTE** : Voir `_bmad-output/planning-artifacts/Terminal5_Exchange_Gateway.md` pour architecture détaillée avec décisions Party Mode (2026-01-21)

**Le Service Exchange Centralisé** (Terminal 5) est le hub unique pour toutes les interactions avec les exchanges via APIs natives. Il garantit une utilisation optimale des connexions et le respect strict des rate limits.

**Principe de fonctionnement :**
* **Service dédié** : Processus indépendant qui maintient toutes les connexions natives (Bitget, Binance, Kraken)
* **Option B : 1 instance par type d'exchange** : Dictionnaire `{'bitget': BitgetClient, 'binance': BinanceClient}` avec injection dynamique credentials
* **Communication Redis** : Tous les autres services communiquent via channels `exchange_requests` et `exchange_responses`
* **Architecture native** : Clients natifs haute performance pour toutes les opérations de trading

**Optimisations implémentées** :
  1. Architecture optimisée: Un seul exchange par type (bitget, binance, etc.) au lieu d'une instance par (user_id, broker_id)
  2. Injection de credentials: Les credentials sont injectés dynamiquement avant chaque appel API
  3. Affichage optimisé:
    - Premier broker: bitget/1 → Loading → OK (35s)
    - Deuxième broker: bitget/Aristobot2-v1 → SHARED (0s instantané)
  4. Gain d'efficacité:
    - Avant: 2 instances séparées = 2x temps de chargement
    - Maintenant: 1 exchange partagé + configurations instantanées

  Résultat: Au lieu de charger bitget deux fois (60-70 secondes total), on le charge une seule fois (35s) et le deuxième broker est configuré
  instantanément.

## 🎯 RECOMMANDATION : PROCHAINE ÉTAPE MODULE 4

### Pourquoi le Module 4 (Webhooks) maintenant ?

1. **🚀 Logique simple** : Réception JSON + exécution ordres (réutilise Module 3)
2. **⚡ Automatisation rapide** : Premier niveau d'automation sans complexité
3. **🔗 Intégration TradingView** : Permet signaux externes immédiats
4. **📊 Données pour Stats** : Génère plus d'historique de trades

### Ce que le Module 4 apportera
- Réception automatique de signaux TradingView
- Exécution ordres basée sur Module 3
- Monitoring complet des webhooks
- Base pour l'automation avancée (Module 5-7)

---

## 📦 MODULE 3 : TRADING MANUEL ✅ **TERMINÉ**

### ✅ Objectifs réalisés
1. ✅ Interface de trading manuel complète
2. ✅ Passage d'ordres via Service Exchange centralisé
3. ✅ Visualisation du portfolio temps réel
4. ✅ Historique des trades avec persistance

### ✅ Structure implémentée
- ✅ Modèle `Trade` multi-tenant fonctionnel
- ✅ APIs complètes (portfolio, ordres, symboles, validation)
- ✅ Services TradingService + PortfolioService optimisés
- ✅ Frontend TradingManualView.vue avec interface 3 colonnes
- ✅ Calculateur bidirectionnel quantité/montant
- ✅ Filtrage symboles USDT/USDC + recherche

**📊 Détails complets :** Voir `MODULE3_IMPLEMENTATION.md`

---

## 📦 MODULE 4 : WEBHOOKS (Priorité 1)

### Objectifs
1. Recevoir des signaux TradingView
2. Passer automatiquement les ordres
3. Logger toutes les tentatives

### Structure générale
- Modèle `Webhook` pour l'historique
- Endpoint POST pour réception
- Service de traitement asynchrone
- Frontend de monitoring

---

## 📦 MODULE 5 : STRATÉGIES (Priorité 2)

### Objectifs
1. Éditeur de stratégies Python
2. Assistant IA pour coder
3. Validation syntaxique
4. Template de base `Strategy`

### Structure générale
- Modèle `Strategy` avec code Python
- Classe de base `apps.strategies.base.Strategy`
- API de validation Python (ast.parse)
- Intégration IA (OpenRouter/Ollama)
- Frontend avec éditeur de code

---

## 📦 MODULE 7 : TRADING BOT (Priorité 3)

### Objectifs
1. Activation des stratégies
2. Écoute du Heartbeat
3. Exécution automatique
4. Monitoring en temps réel

### Structure générale
- Modèle `ActiveStrategy`
- Service Trading Engine amélioré
- Connexion au Heartbeat
- Frontend de contrôle

---

## 📦 MODULE 6 : BACKTEST (Priorité 4)

### Objectifs
1. Test sur données historiques
2. Progression en temps réel
3. Calcul des métriques
4. Interruption possible

### Structure générale
- Modèle `BacktestResult`
- Service de calcul asynchrone
- WebSocket pour progression
- Frontend avec graphiques

---

## 📦 MODULE 8 : STATISTIQUES

### Objectifs
1. Calcul des performances
2. Graphiques d'évolution
3. Analyse par stratégie

### Structure générale
- Services de calcul statistique
- API d'agrégation
- Frontend avec charts

---

## 🔧 PROMPTS OPTIMISÉS POUR CLAUDE CODE

### Pour le Module 1 (à copier-coller dans Claude Code)

```
Contexte : Je développe Aristobot3, un bot de trading crypto en Django/Vue.js.

Fichiers de référence :
- ARISTOBOT3.md : Description complète du projet
- IMPLEMENTATION_PLAN.md : Plan détaillé avec TOUT le code du Module 1 (c'est là que tu trouveras le code à copier)

Chemin du projet : C:\Users\dac\Documents\Python\Django\Aristobot3

Objectif : Implémenter EXACTEMENT le Module 1 (User Account & Brokers) en suivant le code fourni dans IMPLEMENTATION_PLAN.md

Actions à réaliser dans l'ordre :
1. Créer les modèles dans :
   - backend/apps/core/models.py (HeartbeatStatus, Position)
   - backend/apps/accounts/models.py (User étendu)
   - backend/apps/brokers/models.py (Broker, ExchangeSymbol)
2. Créer backend/apps/accounts/backends.py (DevModeBackend)
3. Créer les services dans backend/apps/core/services/ :
   - __init__.py
   - exchange_service.py
   - symbol_updater.py
4. Créer les management commands :
   - backend/apps/accounts/management/commands/init_aristobot.py
   - backend/apps/core/management/commands/run_trading_engine.py
5. Créer les serializers et viewsets :
   - backend/apps/brokers/serializers.py
   - backend/apps/brokers/views.py
6. Créer les views pour accounts :
   - backend/apps/accounts/views.py
7. Configurer les URLs :
   - backend/apps/accounts/urls.py
   - backend/apps/brokers/urls.py
   - Modifier backend/aristobot/urls.py
8. Modifier backend/aristobot/settings.py
9. Créer/modifier le frontend Vue :
   - frontend/src/stores/auth.js
   - frontend/src/views/AccountView.vue

Prérequis à vérifier :
- PostgreSQL est installé et configuré
- Redis est installé et lancé
- Un fichier .env existe avec DEBUG_ARISTOBOT=True
- Le projet Django de base existe déjà
- Le projet Vue.js de base existe avec Pinia installé

Dépendances à installer si besoin :
pip install ccxt cryptography django-cors-headers channels channels-redis djangorestframework python-dotenv

Contraintes importantes :
- PostgreSQL uniquement (pas de MongoDB)
- Multi-tenant strict (toujours filtrer par user_id)
- Chiffrement avec Django SECRET_KEY
- Mode DEBUG = connexion auto avec user "dev"
- APIs avec rate limiting activé

Tests après chaque étape :
1. Vérifier que le serveur démarre : python manage.py runserver
2. Après tous les modèles, faire les migrations :
   python manage.py makemigrations accounts brokers core
   python manage.py migrate
3. Après tout, lancer : python manage.py init_aristobot
4. Tester le Trading Engine : python manage.py run_trading_engine --test

IMPORTANT : Le code détaillé pour chaque fichier est dans IMPLEMENTATION_PLAN.md, section "MODULE 1". 
Utilise CE code exact, ne réinvente pas. Le code commence à "ÉTAPE 1.1" et va jusqu'à "ÉTAPE 1.7".
```

### Pour débugger si nécessaire

```
J'ai une erreur : [coller l'erreur]

Contexte : Module 1 de Aristobot3
Fichier concerné : [nom du fichier]

Aide-moi à corriger sans casser le reste du code.
```

---

## ✅ CHECKLIST DE VALIDATION

### Module 1 ✅ **COMPLÉTÉ**
- [✅] Migrations créées et appliquées (accounts, brokers, core)
- [✅] Script init_aristobot fonctionne
- [✅] Table HeartbeatStatus initialisée
- [✅] Mode DEBUG : connexion auto avec user "dev"
- [✅] CRUD Brokers fonctionnel
- [✅] Test connexion API réussi
- [✅] Service SymbolUpdater fonctionnel
- [✅] Mise à jour symboles en arrière-plan
- [✅] Trading Engine démarre sans erreur (mode test)
- [✅] Frontend AccountView complet
- [✅] Chiffrement des API keys vérifié
- [✅] Table Position créée pour suivi des trades ouverts

### Module 2 ✅ **COMPLÉTÉ**
- [✅] Modèle CandleHeartbeat avec OHLCV
- [✅] Service heartbeat avec sauvegarde auto
- [✅] WebSocket dual-channel (brut + processed)
- [✅] 3 APIs REST fonctionnelles
- [✅] Frontend avec historique + temps réel
- [✅] Couleurs différentielles (orange/vert)
- [✅] Interface épurée et intuitive
- [✅] 240 signaux historiques au démarrage

### Module 3 ✅ **COMPLÉTÉ**
- [✅] Modèle Trade créé avec migrations appliquées
- [✅] Services TradingService + PortfolioService implémentés
- [✅] APIs REST complètes (10+ endpoints)
- [✅] Frontend TradingManualView.vue fonctionnel
- [✅] Interface 3 colonnes avec calculateur bidirectionnel
- [✅] Portfolio temps réel avec optimisation batch pricing
- [✅] Passage d'ordres buy/sell market/limit opérationnel
- [✅] Filtrage symboles USDT/USDC + recherche
- [✅] WebSocket notifications temps réel
- [✅] Intégration Service Exchange centralisé validée

### Points d'attention
- Toujours utiliser `request.user` pour le multi-tenant
- Vérifier les permissions sur chaque endpoint
- Tester en mode DEBUG_ARISTOBOT=True et DEBUG_ARISTOBOT=False
- Valider le chiffrement/déchiffrement des clés

---

## 📝 NOTES IMPORTANTES

1. **Rate Limiting API** : Les clients natifs gèrent le rate limiting automatiquement
2. **Multi-tenant** : Ne jamais oublier de filtrer par `user_id`
3. **Mode Dev** : L'user "dev" a accès à TOUTES les données
4. **Testnet** : À implémenter progressivement
5. **Symboles** : Table partagée mise à jour en async (via CCXT métadonnées)
6. **Instances Exchange** : Singleton pattern obligatoire

Ce plan est votre guide de référence. Suivez-le étape par étape avec Claude Code.

Bonne implémentation ! 🚀
