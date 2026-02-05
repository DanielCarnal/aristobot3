# RÈGLES DE DÉVELOPPEMENT ARISTOBOT3

**Date de création:** 2026-02-02
**Validé par:** Dac
**Statut:** Règles architecturales strictes - NON NÉGOCIABLES

---

## 🔴 RÈGLE CRITIQUE #1 - WEBSOCKETS OBLIGATOIRES

### Principe Fondamental

**TOUS les affichages liés à des données LIVE (pouvant changer, s'ajouter de manière spontanée, inattendue) DOIVENT OBLIGATOIREMENT utiliser des WebSockets.**

### ✅ CAS D'USAGE WEBSOCKETS (OBLIGATOIRE)

Utiliser WebSockets pour:

1. **Données temps réel**
   - Heartbeat / Signaux de marché
   - Webhooks TradingView reçus
   - Ordres exécutés (Terminal 7 Order Monitor)
   - Prix de marché temps réel
   - P&L positions ouvertes

2. **Événements spontanés**
   - Notifications système
   - Alertes de trading
   - Messages de statut des services
   - Mises à jour de positions

3. **Flux continus**
   - Streams de données
   - Logs en temps réel
   - Monitoring des services

### ❌ EXCEPTIONS - Polling REST API Autorisé

Polling API REST acceptable UNIQUEMENT pour:

1. **Listes CRUD classiques**
   - Liste des brokers configurés
   - Liste des stratégies sauvegardées
   - Liste des utilisateurs (admin)
   - Paramètres de configuration

2. **Listes simplistes statiques**
   - Sélecteurs de symboles (marchés)
   - Listes de référence (exchanges disponibles)
   - Données historiques archivées

3. **Données froides**
   - Statistiques agrégées passées
   - Rapports mensuels/annuels
   - Données de backtest terminés

---

## 🎯 ARCHITECTURE WEBSOCKET STANDARD

### Pattern Obligatoire

```javascript
// ✅ BON - WebSocket pour données live
onMounted(() => {
  connectWebSocket()              // WebSocket temps réel
  loadHistoricalData()            // Chargement initial une fois
  // PAS de setInterval pour recharger!
})

function connectWebSocket() {
  ws = new WebSocket('ws://localhost:8000/ws/channel_name/')

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)

    // Ajouter au début de la liste (unshift)
    items.value.unshift(data)

    // Limiter la taille
    if (items.value.length > MAX_ITEMS) {
      items.value = items.value.slice(0, MAX_ITEMS)
    }
  }
}
```

```javascript
// ❌ MAUVAIS - Polling pour données live
onMounted(() => {
  loadData()
  setInterval(loadData, 5000)  // ❌ FLASH garanti!
})
```

### Backend Consumer Pattern

Chaque canal WebSocket doit avoir un Consumer Django Channels:

```python
# backend/apps/MODULE/consumers.py
class DataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("group_name", self.channel_name)
        await self.accept()

    async def data_message(self, event):
        await self.send(text_data=json.dumps(event['message']))
```

---

## 📋 CHECKLIST IMPLÉMENTATION DONNÉES LIVE

Avant d'implémenter un affichage de données live, vérifier:

- [ ] ✅ Consumer WebSocket créé dans `apps/MODULE/consumers.py`
- [ ] ✅ Routing WebSocket ajouté dans `backend/aristobot/routing.py`
- [ ] ✅ Publication depuis le service source (Terminal X)
- [ ] ✅ Frontend connecte WebSocket dans `onMounted()`
- [ ] ✅ Données ajoutées avec `unshift()` (pas de remplacement total)
- [ ] ✅ Limite de taille de liste implémentée
- [ ] ✅ Gestion déconnexion/reconnexion WebSocket
- [ ] ✅ Chargement historique séparé (une seule fois)
- [ ] ❌ AUCUN `setInterval()` qui recharge les données via API

---

## 🚫 ANTI-PATTERNS À ÉVITER

### ❌ Pattern Polling avec setInterval
```javascript
// INTERDIT pour données live!
setInterval(() => {
  api.get('/api/live-data/').then(data => {
    items.value = data  // Flash garanti
  })
}, 5000)
```

**Problèmes:**
- Flash visuel à chaque refresh
- Charge serveur inutile
- Latence 0-5 secondes
- Pas scalable
- Mauvaise UX

### ❌ Remplacement Total de Liste
```javascript
// INTERDIT - Remplace tout
ws.onmessage = (event) => {
  items.value = [event.data, ...items.value]  // Recréation array
}
```

**Correct:**
```javascript
// ✅ BON - Ajout incrémental
ws.onmessage = (event) => {
  items.value.unshift(event.data)  // Modif in-place
}
```

---

## 📚 RÉFÉRENCES

### Exemples de Référence dans le Code

1. **HeartbeatView.vue** (✅ MODÈLE PARFAIT)
   - WebSocket temps réel
   - Chargement historique une fois
   - Ajout incrémental avec `unshift()`
   - Animation nouveaux éléments
   - Limite 60 éléments par timeframe

2. **HeartbeatConsumer** (backend/apps/core/consumers.py)
   - Pattern consumer standard
   - Groupes Django Channels
   - Publication depuis Terminal 2

### À Implémenter Selon Ce Pattern

- [ ] WebhooksView.vue → WebSocket pour webhooks reçus
- [ ] OrderMonitorView.vue → WebSocket pour ordres exécutés
- [ ] TradingManualView.vue → WebSocket pour notifications trades

---

## ⚠️ CONSÉQUENCES NON-RESPECT

Le non-respect de cette règle entraîne:

1. **Flash visuel** constant (mauvaise UX)
2. **Charge serveur** excessive (polling inutile)
3. **Latence** dans l'affichage des données
4. **Code technique** rejeté en code review
5. **Refactoring obligatoire** avant merge

---

## 📝 NOTES ADDITIONNELLES

### Performance WebSockets

- **Latence:** < 50ms (vs 0-5000ms polling)
- **Bande passante:** Push seulement nouvelles données (vs tout recharger)
- **Charge serveur:** Connexion persistante (vs requêtes répétées)
- **UX:** Fluide, sans flash (vs clignotement constant)

### Gestion Déconnexions

```javascript
ws.onclose = () => {
  console.log('WebSocket fermé - Reconnexion dans 5s')
  setTimeout(connectWebSocket, 5000)
}

ws.onerror = (error) => {
  console.error('Erreur WebSocket:', error)
}
```

---

## 🔴 RÈGLE CRITIQUE #2 - STACK TECHNIQUE NON NÉGOCIABLE

### Principe Fondamental

**L'architecture technique est NON NÉGOCIABLE.** Toutes les technologies et patterns listés ci-dessous DOIVENT être respectés sans exception.

### Backend Obligatoire

#### Framework et Serveur
- **Django 4.2.15** + **Django Channels** (OBLIGATOIRE)
- **Serveur ASGI:** Daphne (pas Gunicorn/uWSGI)
- **Python:** 3.11 dans environnement Conda

#### Base de Données
- **PostgreSQL** est la source de vérité unique
- **MongoDB est FORMELLEMENT EXCLU**
- Multi-tenant strict avec isolation par `user_id`

#### Communication Temps Réel
- **Redis** pour Django Channels (Pub/Sub inter-processus)
- **WebSockets** pour données live (voir RÈGLE #1)

##### ⚠️ Deux Systèmes Pub/Sub — Règle de Décision (OBLIGATOIRE)

Aristobot3 utilise **deux systèmes de communication** entre les terminaux backend. Ils sont **INCOMPATIBLES** : un message publié dans l'un n'arrive jamais dans l'autre. Erreur silencieuse — aucun log, aucune exception.

| Système | Utilisé par | Vers quoi | Comment identifier |
|---------|-------------|-----------|-------------------|
| **Django Channels** (`channel_layer.group_send`) | Terminal 1, Terminal 2 | Le **frontend** via WebSocket consumers | Le destinataire est un `Consumer` dans `consumers.py` |
| **Redis natif** (`redis.asyncio publish/subscribe`) | Terminal 3, Terminal 6 | Un autre **processus backend** | Le destinataire fait un `subscribe()` dans un management command ou un serveur standalone |

**Règle de décision :**
- Le message doit atteindre le **navigateur** → Django Channels
- Le message part d'un processus **hors Django** (ex: Terminal 6 aiohttp) → Redis natif
- Le message va **backend Django → backend Django**, sans besoin du frontend → préférez Redis natif pour éviter le couplage avec Daphne

**Piège classique à éviter :**
Publier via `redis.asyncio` et attendre la réception dans un Django Channels consumer, ou vice versa. Le message disparaît en silence.

**Pourquoi deux systèmes ?**
Terminal 6 (Webhook Receiver) est un serveur `aiohttp` standalone — il ne tourne pas dans Django, il ne peut pas accéder à `channel_layer`. Cette contrainte est volontaire : Terminal 6 doit recevoir les webhooks TradingView depuis Internet avec une latence minimale. Le deuxième système existe pour permettre à ce processus léger de communiquer avec le reste du système.

#### Librairies Python
- **Analyse Technique:** Pandas TA Classic uniquement
  - Repository: https://github.com/xgboosted/pandas-ta-classic
- **Accès Marchés:** APIs Natives des Exchanges
  - Bitget, Binance, KuCoin, Kraken 
  - **AUCUNE** autre librairie trading (pas CCXT pour connexions réelles)

#### Parallélisme et Asynchrone
- **asyncio OBLIGATOIRE** pour calculs concurrents
- **Celery est EXCLU** (garder architecture simple)
- **Tous appels API Exchange via `await`** (non bloquant)
- Préserver performances boucle `asyncio`

#### Architecture Service Centralisé
- **Exchange Gateway (Terminal 5):** Hub unique connexions exchanges
- Une instance par type d'exchange (injection credentials dynamique)
- Communication via Redis (`exchange_requests`/`exchange_responses`)
- Respect strict des rate limits

### Frontend Obligatoire

#### Framework
- **Vue.js 3** avec **Composition API uniquement**
- **Options API est INTERDITE**
- **Pinia** pour gestion état global
- **Vite** comme build tool

#### Séparation des Responsabilités
- **Backend fait TOUS les calculs** (pas le frontend)
- **Frontend = Affichage uniquement** (présentation des données)
- Communication temps réel via **WebSockets** (voir RÈGLE #1)

### Sécurité et Validation

#### Chiffrement
- **Clés API DOIVENT être chiffrées**
- Utiliser `SECRET_KEY` de Django comme clé de chiffrement
- Stockage sécurisé en base de données

#### Validation Bidirectionnelle
- **Côté client:** Meilleure UX (feedback immédiat)
- **Côté serveur:** Sécurité et intégrité (serializers DRF)
- **Les deux sont OBLIGATOIRES**

#### Multi-tenant
- Filtrage systématique par `user_id`
- Isolation stricte des données utilisateur
- Vérification permissions sur chaque endpoint

### Messages d'Erreur

#### Format Obligatoire
- **Techniques et en français**
- Exemple: `"Erreur de connexion à Binance : Invalid API Key"`
- Faciliter le débogage (pas de messages génériques)

---

## 🔴 RÈGLE CRITIQUE #3 - DESIGN SYSTEM OBLIGATOIRE

### Principe Fondamental

**Le design system est NON NÉGOCIABLE.** L'identité visuelle crypto doit être cohérente sur toute l'application.

### Thème Obligatoire

#### Style Général
- **Thème sombre crypto** (inspiré Binance/TradingView)
- Utilisation de **cards** avec:
  - Fond sombre
  - Subtile bordure luminescente

#### Couleurs Néon (NON NÉGOCIABLES)
- **Primaire:** `#00D4FF` (Bleu Électrique)
- **Succès:** `#00FF88` (Vert Néon)
- **Danger:** `#FF0055` (Rouge Trading)

**INTERDIT:**
- Modifier ces couleurs
- Utiliser d'autres couleurs primaires
- Ajouter thème clair par défaut

### Responsive

#### Approche
- **"Desktop first"** OBLIGATOIRE
- UI optimisée pour grands écrans
- Adaptation mobile secondaire

---

## 🔴 RÈGLE CRITIQUE #4 - APIS NATIVES COMPLÈTES

### Principe Fondamental

**Les API natives des exchanges DOIVENT être développées dans leur ENTIÈRETÉ.**

### Directive Stricte pour Développeurs/IA

#### Obligations
- Implémenter **TOUTES les fonctionnalités** de l'API
- Inclure **TOUS les paramètres** disponibles
- **NE PAS** se contenter de la partie utile du moment

#### Objectif
- Réutilisabilité pour autres applications Aristobot3
- Éviter refactoring futur pour fonctionnalités manquantes
- Cohérence avec documentation officielle exchange

#### Exemple
**❌ INTERDIT:**
```python
# Implémentation partielle
def place_order(symbol, side, quantity):
    # Seulement les paramètres de base
    pass
```

**✅ OBLIGATOIRE:**
```python
# Implémentation complète
def place_order(
    symbol, side, quantity, order_type='market',
    price=None, stop_price=None, time_in_force='GTC',
    reduce_only=False, position_side='LONG',
    client_order_id=None, **advanced_params
):
    # TOUS les paramètres de l'API native
    pass
```

---

## 📝 RÈGLE CRITIQUE #5 - CONTRAINTES TECHNIQUES OPÉRATIONNELLES

### Principe Fondamental

**Ces contraintes techniques DOIVENT être respectées pour garantir le bon fonctionnement du système.**

### Encodage et Caractères

#### Encodage Windows
- **`# -*- coding: utf-8 -*-`** OBLIGATOIRE en première ligne de chaque fichier Python
- **Caractères ASCII uniquement** dans le code :
  - `é` → `e`
  - `è` → `e`
  - `à` → `a`
- **INTERDIT :** Émojis et accents dans le code source
- **Autorisé :** Accents dans strings/commentaires uniquement

### Frontend Vite/Vue

#### Structure Fichiers
- **`index.html`** DOIT être à la racine `frontend/` (PAS dans `public/`)
- **`vite.config.js`** DOIT inclure :
  - Vue runtime complet
  - Feature flags appropriés

#### CORS Configuration
- **Frontend :** `withCredentials: true`
- **Backend :** `CORS_ALLOW_CREDENTIALS = True`
- **Obligatoire** pour authentification session

### Django Auth et Migrations

#### Ordre Migrations
- **App `accounts` TOUJOURS en premier** dans `INSTALLED_APPS`
- **Raison :** Dépendances modèle User custom

#### Backend Authentication
- **Spécifier `backend=`** explicitement dans appels `login()`
- **Éviter :** Authentification implicite

#### Reset Migrations (en cas de conflit)
```bash
# Procédure complète
DROP DATABASE aristobot3;
CREATE DATABASE aristobot3;
rm -rf backend/apps/*/migrations/0*.py
python manage.py makemigrations
python manage.py migrate
```

### Multi-tenant et Sécurité

#### Filtrage Obligatoire
- **TOUJOURS filtrer par `user_id`** dans ViewSets
- **JAMAIS** de requêtes sans filtrage utilisateur
- **Vérifier permissions** sur chaque endpoint

#### Chiffrement API Keys
- **Fernet + `SECRET_KEY`** Django
- **Stockage sécurisé** en base de données
- **Déchiffrement** uniquement au moment de l'utilisation

#### CCXT (si utilisé pour métadonnées)
- **`enableRateLimit: true`** OBLIGATOIRE
- **Éviter bans** des exchanges

### Variables d'Environnement

#### Fichier .env
- **Localisation :** Racine du projet
- **Variables obligatoires :**
  - `DEBUG='True'` (développement)
  - `SECRET_KEY` (unique et sécurisé)
  - `REDIS_HOST` (pour Django Channels)
  - `WEBHOOK_TOKEN` (pour Terminal 6)

### API REST et Permissions

#### Authentification
- **`SessionAuthentication`** par défaut (DRF)
- **Filtrage `request.user` OBLIGATOIRE** dans ViewSets
- **`@permission_classes([AllowAny])`** UNIQUEMENT pour endpoints auth

### Commandes de Base

#### Initialisation
```bash
python manage.py init_aristobot  # Crée users "dev" et "dac"
```

#### Ports Standards
- **Django/Daphne :** 8000
- **Vue.js/Vite :** 5173
- **Webhook Receiver :** 8888

#### Tests
- **Tester après chaque migration**
- **Tester après reset DB**

### Directives Claude Code

#### NE PAS Démarrer Services
- **L'utilisateur démarre les services manuellement**
- **Raison :** Voir les logs en temps réel
- **Daphne ne supporte PAS les restarts automatiques**
- **Action Claude Code :** Indiquer quels services redémarrer après modifications

#### Scripts de Tests
- **Claude Code PEUT exécuter** scripts tests/initialisations
- **MAIS doit demander confirmation utilisateur** avant exécution

---

## 📝 RÈGLE CRITIQUE #6 - MAINTENANCE DOCUMENTATION

### Principe Fondamental

**La documentation technique DOIT rester synchronisée avec le code.**

### Cartographer - Carte du Codebase

#### Fichier Concerné
- **`docs/CODEBASE_MAP.md`** (auto-généré par Cartographer)
- **⚠️ NE JAMAIS éditer manuellement**

#### Régénération Obligatoire

**Quand régénérer :**
- ✅ Avant chaque commit majeur (nouvelles fonctionnalités)
- ✅ Après modifications architecturales significatives
- ✅ Ajout/suppression de modules Django (apps)
- ✅ Création de nouveaux services (Terminaux)
- ✅ Refactoring de structure de fichiers
- ✅ Modifications importantes dans `backend/apps/` ou `frontend/src/`

**Comment régénérer :**
```bash
# Dans Claude Code
/cartographer
```

**Process recommandé :**
1. Modifier le code
2. Tester les modifications
3. Régénérer CODEBASE_MAP.md (si architecture modifiée)
4. Commit avec message descriptif

#### Exemples Déclencheurs

**✅ Régénération REQUISE :**
- Création `apps/new_module/`
- Ajout Terminal 8
- Refactoring `apps/core/services/`
- Nouvelle vue Vue.js dans `frontend/src/views/`

**❌ Régénération NON REQUISE :**
- Modifications mineures dans fonctions existantes
- Corrections de bugs sans changement structure
- Mise à jour dépendances (requirements.txt, package.json)
- Modifications dans fichiers de config uniquement

### Autres Documentations

#### Mises à Jour Manuelles Requises

**IMPLEMENTATION_PLAN.md**
- **Quand :** Après chaque module complété
- **Contenu :** Statut modules, checklist 
- **Responsable :** BMAD, /bmad:bmm:agents:tech-writer, tech-writer agent (project)

**Aristobot3_1.md**
- **Quand :** Seulement si design architectural change
- **Contenu :** Architecture fonctionnelle, workflows
- **Responsable :** DAC, le PO, Product Owner, avec l'aide de l'agent tech-writer. Comparaison de la réalité du code (CODEBASE_MAP.md) avec ce qui a été décris dans Aristobot3_1.md en tenant compte de ce qui est réalisé (IMPLEMENTATION_PLAN.md)

**DEVELOPMENT_RULES.md**
- **Quand :** Seulement si nouvelles contraintes techniques
- **Contenu :** Règles critiques non négociables
- **Responsable :** DAC, le PO, Product Owner, avec l'aide de l'agent tech-writer.

#### Auto-générées (NE JAMAIS Éditer)

**docs/CODEBASE_MAP.md**
- **Généré par :** Cartographer
- **Mise à jour :** Via `/cartographer` uniquement

---

## 📋 CHECKLIST DE CONFORMITÉ GLOBALE

Avant chaque commit, vérifier:

### RÈGLE #1 - WebSockets
- [ ] Données live utilisent WebSockets (pas polling)
- [ ] Pattern `unshift()` pour ajout incrémental
- [ ] Consumer Django Channels créé
- [ ] Gestion reconnexion implémentée

### RÈGLE #2 - Stack Technique
- [ ] Django 4.2.15 + Channels utilisé
- [ ] Vue.js 3 Composition API (pas Options API)
- [ ] PostgreSQL seule DB (pas MongoDB)
- [ ] asyncio utilisé (pas Celery)
- [ ] APIs Exchange natives asynchrones (`await`)
- [ ] Validation bidirectionnelle implémentée
- [ ] Clés API chiffrées
- [ ] Messages d'erreur en français

### RÈGLE #3 - Design System
- [ ] Thème sombre appliqué
- [ ] Couleurs néon respectées (#00D4FF, #00FF88, #FF0055)
- [ ] Cards avec bordure luminescente
- [ ] Desktop first respecté

### RÈGLE #4 - APIs Natives
- [ ] API implémentée complètement
- [ ] Tous paramètres inclus
- [ ] Documentation API officielle consultée
- [ ] Pas de fonctionnalités tronquées

### RÈGLE #5 - Contraintes Techniques
- [ ] `# -*- coding: utf-8 -*-` en première ligne Python
- [ ] Caractères ASCII uniquement dans code
- [ ] App `accounts` en premier dans INSTALLED_APPS
- [ ] Filtrage `user_id` dans tous les ViewSets
- [ ] Variables .env configurées correctement
- [ ] Directives Claude Code respectées (pas de démarrage services)

### RÈGLE #6 - Maintenance Documentation
- [ ] Tests passent
- [ ] Documentation synchronisée avec code :
  - [ ] **CODEBASE_MAP.md régénéré** (si architecture modifiée avec `/cartographer`)
  - [ ] **IMPLEMENTATION_PLAN.md** mis à jour (si module complété)
  - [ ] **Aristobot3_1.md** mis à jour (si design architectural change)
  - [ ] **DEVELOPMENT_RULES.md** mis à jour (si nouvelles contraintes)

---

**Dernière mise à jour:** 2026-02-02
**Validé par:** Dac
**Statut:** OBLIGATOIRE - Règles architecturales non négociables
