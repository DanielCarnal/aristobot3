# FIX ERREUR 404 WEBHOOKS

## 🔍 Problème Détecté

Les endpoints webhooks retournent 404 :
- `/api/webhooks/stats/`
- `/api/webhooks/recent/`
- `/api/webhook-states/open/`

## ✅ Cause

**Daphne (Terminal 1) n'a pas été redémarré** après l'ajout des nouvelles routes webhooks dans `aristobot/urls.py`.

Django charge les URLs au démarrage du serveur. Toute modification des fichiers `urls.py` nécessite un redémarrage pour être prise en compte.

## 🔧 Solution

### Étape 1 : Arrêter Terminal 1 (Daphne)

Dans le terminal où Daphne tourne, appuyer sur **Ctrl+C**.

### Étape 2 : Redémarrer Terminal 1

```bash
cd backend
daphne aristobot.asgi:application
```

### Étape 3 : Vérifier

Une fois Daphne redémarré, rafraîchir le navigateur :
```
http://localhost:5173/webhooks
```

Les erreurs 404 devraient disparaître et les statistiques s'afficher.

---

## 🧪 Test Manuel des Endpoints

Après redémarrage, tester avec curl :

```bash
# Test stats (devrait retourner JSON)
curl http://localhost:8000/api/webhooks/stats/?period=24h

# Test recent (devrait retourner tableau vide au début)
curl http://localhost:8000/api/webhooks/recent/

# Test positions (devrait retourner tableau vide au début)
curl http://localhost:8000/api/webhook-states/open/
```

---

## 📋 Rappel : Quand Redémarrer les Terminaux

### Terminal 1 (Daphne) - À redémarrer si :
- ✅ Modification de `urls.py` (n'importe où)
- ✅ Modification de `settings.py`
- ✅ Ajout/modification de models.py
- ✅ Ajout/modification de serializers.py, views.py
- ⚠️ **Daphne ne supporte PAS l'auto-reload** (contrairement à `runserver`)

### Terminal 2 (Heartbeat) - À redémarrer si :
- Modification du code de `run_heartbeat.py`
- Changement de symbole surveillé

### Terminal 3 (Trading Engine) - À redémarrer si :
- Modification du code de `run_trading_engine.py`
- Ajout/suppression du flag `--test`

### Terminal 5 (Exchange Gateway) - À redémarrer si :
- Modification du code de `run_native_exchange_service.py`
- Modification des clients natifs

### Terminal 6 (Webhook Receiver) - À redémarrer si :
- Modification du code de `run_webhook_receiver.py`
- Changement de port ou token

---

## 🎯 Prochaines Étapes Après Fix

Une fois Daphne redémarré et les endpoints accessibles :

1. **Vérifier interface** : http://localhost:5173/webhooks
   - Les 4 cartes statistiques devraient afficher "0"
   - Les tableaux devraient afficher "Aucun webhook reçu" / "Aucune position ouverte"

2. **Tester réception webhook** :
   ```bash
   python test_webhook.py
   ```
   Résultat attendu : Webhook affiché dans l'interface après refresh

3. **Tester flux complet** :
   ```bash
   python test_webhook_complete.py
   ```
   Résultat attendu : Statistiques mises à jour en temps réel

---

**Note** : Daphne **ne recharge pas automatiquement** le code Python modifié. C'est différent de `python manage.py runserver` qui a l'auto-reload. Il faut toujours redémarrer Daphne manuellement après toute modification de code.
