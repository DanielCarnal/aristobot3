# PLAN D'IMPLÉMENTATION ARISTOBOT3

## 📊 ÉTAT GLOBAL DU PROJET

### ✅ MODULE 1 - USER ACCOUNT & BROKERS (85% TERMINÉ)
- **Authentification** : Système multi-tenant sécurisé ✅
- **Mode DEBUG** : Gestion via table DebugMode ✅  
- **Brokers CCXT** : CRUD complet avec test connexion ✅
- **Frontend AccountView** : Interface complète avec modale ✅
- **Services** : SymbolUpdaterService + endpoints API ✅
- **Sécurité** : Chiffrement clés API + permissions ✅

### 🔄 EN COURS - Finalisation Module 1
- ⚠️ Command init_aristobot (user dev normal)
- ⚠️ Frontend debug toggle dans LoginView  
- ⚠️ Tests complets mode DEBUG_ARISTOBOT=False

### 📋 PROCHAINS MODULES
- **MODULE 2** : Heartbeat amélioré + bougies DB
- **MODULE 3** : Trading manuel  
- **MODULE 4** : Webhooks TradingView
- **MODULE 5** : Stratégies Python + IA
- **MODULE 6** : Backtest
- **MODULE 7** : Trading BOT
- **MODULE 8** : Statistiques

## 🎯 DÉCISIONS TECHNIQUES VALIDÉES

### Base de données
- **PostgreSQL uniquement** (pas de MongoDB)
- **Multi-tenant strict** : Filtrage par `user_id` obligatoire
- **Decimal Python** pour tous les montants/prix
- **UTC en DB**, affichage selon préférence utilisateur

### Architecture
- **CCXT** pour multi-exchange (version gratuite, REST API)
- **Singleton pattern** pour instances CCXT (une par exchange/user)
- **asyncio** pour parallélisme (pas de Celery)
- **Django Channels** pour WebSocket
- **Heartbeat** : WebSocket natif Binance (indépendant de CCXT)

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
2. Gérer les brokers (exchanges) avec CCXT
3. Implémenter le mode DEBUG avec user "dev"
4. Créer la table partagée des symboles
5. Frontend de gestion des comptes et brokers

**📋 Détails techniques complets :** Voir `MODULE1_IMPLEMENTATION.md`

**✅ Statut :** 85% terminé - Fonctionnalités core implémentées

---

## 📦 MODULE 2 : HEARTBEAT AMÉLIORÉ

### Objectifs
1. Améliorer le service Heartbeat existant
2. Sauvegarder les bougies en PostgreSQL
3. Créer une interface de monitoring temps réel
4. Gérer la cohérence des données

### Structure générale
- Modèle `Candle` pour stocker les bougies
- Service amélioré avec sauvegarde DB
- API REST pour récupérer l'historique
- WebSocket pour le temps réel
- Frontend avec affichage 20 lignes / scroll 60

---

## 📦 MODULE 3 : TRADING MANUEL

### Objectifs
1. Interface de trading manuel complète
2. Passage d'ordres via CCXT
3. Visualisation du portfolio
4. Historique des trades

### Structure générale
- Modèle `Trade` multi-tenant
- API pour passer des ordres (buy/sell, market/limit)
- Service de calcul position/balance
- Frontend avec calculateur quantité/montant
- Sélection des paires depuis `ExchangeSymbol`

---

## 📦 MODULE 4 : WEBHOOKS

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

## 📦 MODULE 5 : STRATÉGIES

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

## 📦 MODULE 6 : BACKTEST

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

## 📦 MODULE 7 : TRADING BOT

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
   - ccxt_service.py
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
- CCXT avec enableRateLimit: true

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

### Module 1
- [ ] Migrations créées et appliquées (accounts, brokers, core)
- [ ] Script init_aristobot fonctionne
- [ ] Table HeartbeatStatus initialisée
- [ ] Mode DEBUG : connexion auto avec user "dev"
- [ ] CRUD Brokers fonctionnel
- [ ] Test connexion CCXT réussi
- [ ] Service SymbolUpdater fonctionnel
- [ ] Mise à jour symboles en arrière-plan
- [ ] Trading Engine démarre sans erreur (mode test)
- [ ] Frontend AccountView complet
- [ ] Chiffrement des API keys vérifié
- [ ] Table Position créée pour suivi des trades ouverts

### Points d'attention
- Toujours utiliser `request.user` pour le multi-tenant
- Vérifier les permissions sur chaque endpoint
- Tester en mode DEBUG_ARISTOBOT=True et DEBUG_ARISTOBOT=False
- Valider le chiffrement/déchiffrement des clés

---

## 📝 NOTES IMPORTANTES

1. **CCXT Rate Limiting** : Toujours activer `enableRateLimit: true`
2. **Multi-tenant** : Ne jamais oublier de filtrer par `user_id`
3. **Mode Dev** : L'user "dev" a accès à TOUTES les données
4. **Testnet** : À implémenter progressivement
5. **Symboles** : Table partagée mise à jour en async
6. **Instances CCXT** : Singleton pattern obligatoire

Ce plan est votre guide de référence. Suivez-le étape par étape avec Claude Code.

Bonne implémentation ! 🚀
