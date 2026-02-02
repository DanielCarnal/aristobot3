# 🚀 COMMANDES RAPIDES - MODULE 4 WEBHOOKS

## 📋 CHOIX DE STRATÉGIE DE TEST

| Stratégie | Risque | Commande |
|-----------|--------|----------|
| **1. MODE TEST (Simulation)** | ❌ **Aucun** | `python test_webhook_complete.py` |
| **2. TESTNET (Ordres réels monnaie fictive)** | ⚠️ **Zéro** | `python test_webhook_limit_orders.py` |
| **3. PRODUCTION Ordres limites sécurisés** | 🟡 **Faible** | `python test_webhook_limit_orders.py` |

---

## 🎯 STRATÉGIE 1 : MODE TEST (Recommandé pour débuter)

**Avantages** :
- ✅ Aucun ordre réel passé
- ✅ Teste le flux complet (sauf échange)
- ✅ 100% sécurisé

### Configuration
```bash
python configure_test_broker.py
```

### Démarrage Terminaux
```bash
# Terminal 1
cd backend && python manage.py run_native_exchange_service

# Terminal 2
cd backend && python manage.py run_webhook_receiver

# Terminal 3 (avec --test)
cd backend && python manage.py run_trading_engine --test --verbose

# Terminal 4
python test_webhook_complete.py
```

### Nettoyage
```bash
python configure_test_broker.py reset
```

---

## 🎯 STRATÉGIE 2 : TESTNET (Ordres réels, monnaie fictive)

**Avantages** :
- ✅ Test complet avec exchange réel
- ✅ Monnaie fictive (aucun risque financier)
- ✅ Ordres visibles sur testnet

**Prérequis** :
1. Compte testnet Bitget : https://testnet.bitget.com
2. Déposer fonds testnet (fictifs)
3. Créer API keys testnet

### Configuration
```bash
python configure_broker_testnet.py
# Suivre instructions pour créer broker testnet
```

### Démarrage Terminaux
```bash
# Terminal 1
cd backend && python manage.py run_native_exchange_service

# Terminal 2
cd backend && python manage.py run_webhook_receiver

# Terminal 3 (SANS --test cette fois)
cd backend && python manage.py run_trading_engine --verbose

# Terminal 4
python test_webhook_limit_orders.py
```

### Vérification
1. Connecte-toi sur https://testnet.bitget.com
2. Va dans "Ordres" → "Ordres ouverts"
3. Vérifie les 2 ordres (BUY 50%, SELL 200%)
4. Supprime-les manuellement

### Nettoyage
```bash
python configure_broker_testnet.py reset
```

---

## 🎯 STRATÉGIE 3 : PRODUCTION Ordres Limites Sécurisés

**⚠️ ATTENTION** : Ordres réels avec argent réel (mais prix garantis non-fill)

**Avantages** :
- ✅ Test avec exchange production
- ✅ Ordres garantis non-fill (50% / 200% du prix)
- ⚠️ Utilise petits montants (5% balance)

**Prérequis** :
1. Broker production avec vraies API keys
2. Balance minimum (ex: 50 USDT)
3. ⚠️ Accepter utilisation argent réel

### Configuration
```bash
python configure_test_broker.py
# Configure broker ID 13 (Bitget dev)
```

### Démarrage Terminaux
```bash
# Terminal 1
cd backend && python manage.py run_native_exchange_service

# Terminal 2
cd backend && python manage.py run_webhook_receiver

# Terminal 3 (SANS --test)
cd backend && python manage.py run_trading_engine --verbose

# Terminal 4
python test_webhook_limit_orders.py
```

### Vérification
1. Connecte-toi sur https://www.bitget.com
2. Va dans "Ordres" → "Ordres ouverts"
3. **IMPORTANT** : Vérifie que les ordres ne sont PAS exécutés
4. Supprime-les manuellement rapidement

### Nettoyage
```bash
python configure_test_broker.py reset
```

---

## 📊 COMPARAISON DES STRATÉGIES

| Critère | Mode TEST | Testnet | Production |
|---------|-----------|---------|------------|
| Ordres passés | ❌ Non | ✅ Oui | ✅ Oui |
| Exchange contacté | ❌ Non | ✅ Oui | ✅ Oui |
| Argent réel | ❌ Non | ❌ Non | ⚠️ Oui |
| Ordres visibles exchange | ❌ Non | ✅ Oui | ✅ Oui |
| Risque financier | ✅ Aucun | ✅ Aucun | 🟡 Faible |
| Validation complète | 🟡 Partielle | ✅ Complète | ✅ Complète |

---

## 🔍 VÉRIFICATION LOGS

### Terminal 6 (Webhook Receiver)
```
📥 Webhook recu: BTCUSDT BuyLimit (15ms)
📥 Webhook recu: BTCUSDT SellLimit (12ms)
```

### Terminal 3 (Trading Engine)

**Mode --test** :
```
📥 Webhook: BTCUSDT BuyLimit @ 45000.0
🧪 MODE TEST - Ordre non execute
✅ Ordre execute: TEST_ORDER_123
```

**Sans --test** :
```
📥 Webhook: BTCUSDT BuyLimit @ 45000.0
🔥 Execution ordre: buy limit BTCUSDT @ 45000.0
💰 Balance USDT: 100.0
📊 Ordre calcule: 5.0 USDT @ BTC/USDT
✅ Ordre execute: 1234567890
```

---

## 📝 CHECKLIST APRÈS TESTS

- [ ] Tous les webhooks traités sans erreur
- [ ] Order IDs présents en DB
- [ ] (Testnet/Prod) Ordres visibles sur exchange
- [ ] (Testnet/Prod) Ordres NON exécutés (status Open)
- [ ] (Testnet/Prod) Ordres supprimés manuellement
- [ ] Broker remis en mode OFF (`reset`)

---

## 🆘 AIDE RAPIDE

### Terminal 3 ne traite pas les webhooks
```bash
# Vérifier Redis fonctionne
redis-cli ping
# Résultat attendu : PONG

# Vérifier Terminal 3 écoute bien
# Logs devraient montrer :
# 📥 Ecoute canal 'webhook_raw'
```

### Order ID = None en DB
```bash
# Cause probable : Terminal 3 en mode --test
# Solution : Relancer SANS --test
cd backend && python manage.py run_trading_engine
```

### Balance insuffisante
```bash
# Modifier PourCent dans script
# Ligne 223/239 : PourCent: 1  (au lieu de 5)
```

---

## 🎯 RECOMMENDATION

**Pour premier test** : Utilise **STRATÉGIE 1 (MODE TEST)**

**Pour validation complète** : Utilise **STRATÉGIE 2 (TESTNET)**

**Pour test final avant prod** : Utilise **STRATÉGIE 3** avec montants très faibles

---

**Bon test ! 🚀**
