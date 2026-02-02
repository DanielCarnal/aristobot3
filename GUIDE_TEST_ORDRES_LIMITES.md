# 🎯 GUIDE TEST - ORDRES LIMITES SÉCURISÉS

## 📋 STRATÉGIE DE TEST

**Objectif** : Tester le passage d'ordres réels SANS risque d'exécution

**Méthode** :
- ✅ **BUY Limit à 50%** du prix actuel → Trop bas, jamais exécuté
- ✅ **SELL Limit à 200%** du prix actuel → Trop haut, jamais exécuté
- ✅ **Ordres visibles** sur l'exchange → Preuve que ça fonctionne
- ✅ **Suppression manuelle** → Contrôle total

**Exemple avec BTC @ $90,000** :
- BUY Limit : $45,000 (50%) → Jamais fill
- SELL Limit : $180,000 (200%) → Jamais fill

---

## 🔧 OPTION 1 : TESTNET (Recommandé - Zéro Risque)

### Prérequis
1. Créer compte TESTNET Bitget : https://testnet.bitget.com
2. Obtenir API keys testnet
3. Configurer broker avec ces clés

### Configuration

```bash
# Configurer broker en testnet
python configure_broker_testnet.py
```

### Avantages
- ✅ Monnaie fictive (aucun risque)
- ✅ Test complet du flux
- ✅ Ordres réels sur testnet

---

## 💰 OPTION 2 : PRODUCTION avec Petits Montants

### Configuration

```bash
# Configurer broker pour webhooks (production)
python configure_test_broker.py
```

### Sécurité
- ⚠️ Montants limités à **5% de la balance**
- ⚠️ Prix garantis non-fill (50% / 200%)
- ⚠️ Vérifier balance avant test

---

## 🚀 PROCÉDURE COMPLÈTE DE TEST

### ÉTAPE 1 : Préparation (Terminal 1-3)

**Terminal 1 - Terminal 5 (Exchange Gateway)** :
```bash
cd backend
python manage.py run_native_exchange_service
```

**Terminal 2 - Terminal 6 (Webhook Receiver)** :
```bash
cd backend
python manage.py run_webhook_receiver
```

**Terminal 3 - Terminal 3 (Trading Engine) SANS --test** :
```bash
cd backend
python manage.py run_trading_engine --verbose
```

⚠️ **IMPORTANT** : **SANS** le flag `--test` cette fois ! Les ordres seront réels.

---

### ÉTAPE 2 : Configuration Broker

**Option A - Testnet (recommandé)** :
```bash
python configure_broker_testnet.py
```

**Option B - Production** :
```bash
python configure_test_broker.py
```

---

### ÉTAPE 3 : Lancer Tests Ordres Limites

**Terminal 4 - Script de test** :
```bash
python test_webhook_limit_orders.py
```

**Le script va** :
1. Récupérer le prix actuel de BTC depuis Binance
2. Calculer prix sécurisés (50% / 200%)
3. Afficher un résumé et demander confirmation
4. Envoyer webhooks BuyLimit et SellLimit
5. Afficher les Order IDs créés

---

### ÉTAPE 4 : Vérification sur Exchange

**Connecte-toi à l'interface de ton exchange** :

1. **Bitget** : https://www.bitget.com (ou testnet)
2. Va dans **"Ordres" → "Ordres ouverts"**
3. Cherche les 2 ordres créés :
   - Un BUY à ~50% du prix actuel
   - Un SELL à ~200% du prix actuel
4. **Vérifie les Order IDs** correspondent à ceux affichés

**Tu devrais voir** :
```
Ordre #1 : BUY BTCUSDT @ $45,000 (Limit)
Ordre #2 : SELL BTCUSDT @ $180,000 (Limit)
Status : Open (En attente)
```

---

### ÉTAPE 5 : Suppression Manuelle

**Sur l'interface exchange** :
1. Sélectionne chaque ordre
2. Clique "Annuler" ou "Cancel"
3. Confirme la suppression

**Ou via Trading Manuel Aristobot** :
1. Va dans l'interface Trading Manuel
2. Onglet "Ordres ouverts"
3. Clique "Supprimer" sur chaque ligne

---

### ÉTAPE 6 : Nettoyage

```bash
# Remettre broker en mode OFF
python configure_test_broker.py reset
```

---

## 🔍 RÉSULTATS ATTENDUS

### Terminal 3 (Trading Engine)

```
📥 Webhook: BTCUSDT BuyLimit @ 45000.0 (5%) - User 1 Broker 13
🔥 Execution ordre: buy limit BTCUSDT @ 45000.0 (5%)
💰 Balance USDT: 1000.0
📊 Ordre calcule: 50.0 USDT @ BTC/USDT
✅ Ordre execute: 1234567890

📥 Webhook: BTCUSDT SellLimit @ 180000.0 (5%) - User 1 Broker 13
🔥 Execution ordre: sell limit BTCUSDT @ 180000.0 (5%)
💰 Balance BTC: 0.001
📊 Ordre calcule: 0.00005 BTC @ BTC/USDT
✅ Ordre execute: 1234567891

📊 Stats: Webhooks 2 processed, 0 errors, 2 orders executed
```

### Base de Données

```python
# Django shell
from apps.webhooks.models import Webhook

webhooks = Webhook.objects.filter(action__in=['BuyLimit', 'SellLimit']).order_by('-id')[:2]

for w in webhooks:
    print(f"{w.action}: Prix={w.prix}, OrderID={w.order_id}, Status={w.status}")

# Résultat attendu :
# SellLimit: Prix=180000.00, OrderID=1234567891, Status=processed
# BuyLimit: Prix=45000.00, OrderID=1234567890, Status=processed
```

---

## ✅ VALIDATION RÉUSSIE SI

| Critère | Statut |
|---------|--------|
| Webhooks reçus par Terminal 6 | ✅ |
| Webhooks traités par Terminal 3 | ✅ |
| Ordres sauvegardés en DB avec Order ID | ✅ |
| Ordres visibles sur exchange | ✅ |
| Ordres **NON exécutés** (Open) | ✅ |
| Suppression manuelle possible | ✅ |

---

## 🚨 DÉPANNAGE

### Erreur "Balance insuffisante"

**Cause** : Pas assez d'USDT pour BUY ou pas assez de BTC pour SELL

**Solution** :
- **Testnet** : Déposer des fonds testnet
- **Production** : Réduire `PourCent` dans le script (ligne 223/239)

---

### Ordre exécuté immédiatement

**Cause** : Prix mal calculé (trop proche du marché)

**Solution** : Vérifier calcul dans `calculate_safe_prices()` :
- BUY doit être < prix actuel
- SELL doit être > prix actuel

---

### Order ID = None en DB

**Cause** : Ordre rejeté par exchange ou Terminal 3 en mode --test

**Solution** :
1. Vérifier Terminal 3 lancé **SANS** --test
2. Vérifier logs Terminal 5 pour erreur exchange
3. Vérifier API keys valides

---

## 🎯 PROCHAINES ÉTAPES APRÈS VALIDATION

Une fois les tests réussis :

1. ✅ **Module 4 validé** : Flux webhook → ordre réel fonctionne
2. 🔄 **Tâche #4** : Créer APIs REST pour frontend
3. 🔄 **Tâche #5** : Interface Vue.js WebhooksView
4. 🔄 **Module 5** : Stratégies Python avec IA

---

**Questions ? Problèmes ? Note tout pour débriefing ! 📝**
