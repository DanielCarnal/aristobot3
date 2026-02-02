# MODULE 4 - Architecture MAJ + Terminal 7 Position Guardian

**Date:** 2026-02-02
**Décisions validées par:** Dac + Équipe BMAD (Winston, Dr. Quinn, Barry, John, Murat, Lynx)
**Contexte:** Party Mode - Implémentation action MAJ webhooks avec validation Terminal 7

---

## 🎯 Décisions Architecturales Validées

### **1. Terminal 6 - Webhook Receiver (Modifié)**

**Responsabilité étendue:**
- ✅ Recevoir webhook TradingView (existant)
- ✅ Valider token (existant)
- ✅ **NOUVEAU:** Enregistrer TOUS les webhooks en DB immédiatement (y compris PING)
- ✅ Publier sur Redis 'webhook_raw' (existant)
- ✅ Réponse rapide < 100ms (existant)

**Changement clé:** Terminal 6 fait maintenant la sauvegarde DB (avant c'était Terminal 3)

---

### **2. Terminal 3 - Trading Engine (Action MAJ)**

**Fonction:** `update_sl_tp()` - Exécution "fire and forget"

**Logique simplifiée:**
1. Vérifier position existe (WebhookState status='open')
   - Si absente → marquer webhook 'processed' avec message, STOP
2. Annuler anciens SL/TP via Terminal 5 (ExchangeClient)
   - Si échec → warning log, continuer
3. Créer nouveaux SL/TP via Terminal 5
   - Quantité = 100% position.quantity (PourCent ignoré pour MAJ)
   - Side calculé automatiquement (LONG → sell, SHORT → buy)
4. Mettre à jour WebhookState (current_sl, current_tp, sl_order_id, tp_order_id)
5. Si échec création → **Logger erreur, Terminal 7 réparera automatiquement**

**Décision critique:** Si création SL/TP échoue, Terminal 3 ne fait PAS de rollback. Terminal 7 détectera et réparera dans max 10 secondes.

---

### **3. Terminal 7 - Order Monitor + Position Guardian (Étendu)**

**Responsabilités:**

**A) Order Monitor (Existant - 11,130 lignes déjà implémenté):**
- Détection automatique ordres fill
- Calcul P&L (Price Averaging + FIFO)
- Sauvegarde Trade (source='order_monitor')

**B) Position Guardian (NOUVEAU):**
- Validation cohérence SL/TP toutes les 10s
- Pour chaque position WebhookState (status='open'):
  1. Vérifier SL actif en DB (Trade table, type='stop_loss', status='open')
  2. Vérifier TP actif en DB (Trade table, type='take_profit', status='open')
  3. Si SL manquant et position.current_sl existe:
     - Créer ordre SL via Terminal 5 (ExchangeClient)
     - Prix = position.current_sl (depuis DB)
     - Quantité = position.quantity
  4. Si TP manquant et position.current_tp existe:
     - Créer ordre TP via Terminal 5
     - Prix = position.current_tp
     - Quantité = position.quantity

**Timing:** Boucle indépendante 10s (pas besoin de PING webhook)

**Clarification importante:**
- Terminal 7 **LIT** DB pour **VÉRIFIER** quels ordres sont actifs
- Terminal 7 **PASSE** nouveaux ordres **VIA TERMINAL 5** (ExchangeClient)
- Terminal 7 **NE COMMUNIQUE JAMAIS** directement avec l'exchange

---

## 🔄 Flow Complet Webhook MAJ

### **Scénario Normal (Succès)**

```
1. TradingView → Terminal 6 (POST :8888/webhook)
   Action: MAJ, PrixSL: 42000, PrixTP: 45000

2. Terminal 6 (0.05s):
   - Enregistre Webhook en DB (status='received')
   - Publie Redis 'webhook_raw'
   - Return 200 OK

3. Terminal 3 (1-3s):
   - Lit webhook DB
   - Charge position WebhookState
   - Annule anciens SL/TP via Terminal 5
   - Crée nouveaux SL/TP via Terminal 5
   - Met à jour WebhookState
   - Marque webhook 'processed'

4. Terminal 7 (10s après):
   - Lit WebhookState
   - Vérifie SL actif en DB → ✅ OK
   - Vérifie TP actif en DB → ✅ OK
   - Aucune action nécessaire
```

---

### **Scénario Échec (Broker Down)**

```
1-2. [Identique]

3. Terminal 3 (1-3s):
   - Lit webhook DB
   - Charge position WebhookState
   - Annule anciens SL/TP via Terminal 5 → ✅ OK
   - Crée nouveau SL → ❌ ÉCHEC (broker down)
   - Logger erreur
   - Marque webhook 'error'

4. Terminal 7 (10s après):
   - Lit WebhookState
   - Vérifie SL actif en DB → ❌ ABSENT
   - position.current_sl existe (42000)
   - 🔥 RÉPARATION: Crée SL via Terminal 5
   - Met à jour position.sl_order_id
   - Logger "SL réparé avec succès"

5. Terminal 7 (20s après - cycle suivant):
   - Vérifie SL actif → ✅ OK
   - Vérifie TP actif → ✅ OK
   - Position protégée
```

---

## 📊 Tables DB Impliquées

### **Webhook (apps/webhooks/models.py)**
- Enregistré par: Terminal 6 (NOUVEAU)
- Mis à jour par: Terminal 3 (status='processed'/'error')
- Champs clés:
  - `status`: 'received' → 'processed'/'error'
  - `action`: 'PING', 'BuyMarket', 'MAJ', etc.
  - `prix_sl`, `prix_tp`: Prix demandés
  - `raw_payload`: JSON complet TradingView

### **WebhookState (apps/webhooks/models.py)**
- Créé par: Terminal 3 (BuyMarket/SellMarket)
- Mis à jour par: Terminal 3 (MAJ), Terminal 7 (réparation)
- Champs clés:
  - `status`: 'open'/'closed'
  - `current_sl`, `current_tp`: Derniers prix SL/TP connus
  - `sl_order_id`, `tp_order_id`: IDs ordres actifs
  - `quantity`: Quantité position (pour réparation)

### **Trade (apps/trading_manual/models.py)**
- Créé par: Terminal 5 (pour tous ordres)
- Utilisé par: Terminal 7 (validation)
- Champs clés:
  - `source`: 'webhook', 'order_monitor', 'trading_manual', 'strategy'
  - `type`: 'market', 'limit', 'stop_loss', 'take_profit'
  - `status`: 'open', 'closed', 'cancelled'
  - `exchange_order_id`: ID exchange natif

---

## 🔍 Points d'Instrumentation Loguru

**Voir fichier séparé:** `MODULE4_INSTRUMENTATION_LOGURU.md`

**Résumé:** 14 points stratégiques
- Terminal 6: 3 points (réception, DB, Redis)
- Terminal 3: 7 points (recherche position, annulations, créations)
- Terminal 7: 4 points (validation, réparations)

**Propagation trace_id:** T6 (génération) → Redis → T3 → T5 → Logs distribués

---

## ✅ Avantages Architecture

1. **🛡️ Résilience:** Position jamais sans protection > 10s
2. **🔄 Auto-réparation:** Terminal 7 répare automatiquement échecs Terminal 3
3. **⚡ Performance:** Pas de surcharge - validation toutes les 10s déjà en place
4. **📊 Observabilité:** trace_id permet reconstruction causale complète
5. **🎯 Simplicité:** Terminal 3 "fire and forget" - pas de rollback complexe

---

## 🚀 Prochaines Étapes

1. ✅ Sauvegarder architecture (ce fichier)
2. ✅ Sauvegarder points instrumentation (fichier séparé)
3. 🔄 Modifier Terminal 6 (sauvegarde DB)
4. 🔄 Compléter Terminal 3 (fonction update_sl_tp)
5. 🔄 Étendre Terminal 7 (Position Guardian)
6. 🔄 Instrumenter avec Loguru (14 points)
7. ✅ Tests validation complète

---

**Validé par:** Dac
**Implémentation:** Barry (Dev) + Lynx (Instrumentation)
**Architecture:** Winston + Dr. Quinn
**Tests:** Murat
