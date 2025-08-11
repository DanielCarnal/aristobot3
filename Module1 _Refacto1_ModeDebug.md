# Refactorisation du système d'authentification - Aristobot3

## Mission
Refactoriser le système d'authentification en gardant le design actuel mais en corrigeant les problèmes de sécurité et d'architecture. L'utilisateur "dev" ne doit plus avoir de privilèges spéciaux.

## ÉTAPE 1 : ANALYSE ET NETTOYAGE

### Rechercher et documenter :
1. Trouve TOUTES les références où l'utilisateur "dev" a des privilèges spéciaux
   - Cherche dans tout le backend : `grep -r "dev" --include="*.py"`
   - Cherche les conditions du type : `if user.username == "dev"` ou `if request.user.username == "dev"`
   - Liste tous les endroits où "dev" peut accéder aux données d'autres utilisateurs

2. Localise le code d'authentification actuel dans `apps/accounts`
   - Identifie ce qui doit être déplacé vers la nouvelle app `auth`
   - Note le design/style des composants existants à conserver

### Nettoyer :
- Supprime TOUTES les conditions spéciales pour l'utilisateur "dev"
- Remplace par des filtres normaux : `filter(user=request.user)` partout
- Ne supprime PAS le design/style existant des pages

## ÉTAPE 2 : CRÉATION DE LA NOUVELLE APP AUTH

### Backend - Créer `apps/auth/` :

```python
# apps/auth/models.py
from django.db import models

class DebugMode(models.Model):
    """Singleton pour l'état du mode debug"""
    is_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'debug_mode'
    
    @classmethod
    def get_state(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj.is_active
    
    @classmethod
    def set_state(cls, active):
        obj, created = cls.objects.get_or_create(id=1)
        obj.is_active = active
        obj.save()
        return obj.is_active
````

### Endpoints à créer dans `apps/auth/views.py` :

* `/api/auth/login/` - Login standard (garde la logique existante)
* `/api/auth/logout/` - Logout standard
* `/api/auth/register/` - Création compte (garde le modal existant)
* `/api/auth/status/` - Info user connecté + mode debug
* `/api/auth/debug-config/` - Retourne {enabled: bool, active: bool}
* `/api/auth/toggle-debug/` - Active/désactive mode debug
* `/api/auth/debug-login/` - Auto-login avec "dev" si mode actif

## ÉTAPE 3 : MIGRATION DU FRONTEND

### Garde le design existant mais réorganise :

1. **SI une LoginView existe déjà** : La modifier, pas la recréer

2. **Ajouter le DebugToggle** au formulaire de login existant :

     ```vue
   <!-- Ajouter après les champs password, GARDER LE STYLE EXISTANT -->
   <div v-if="debugEnabled" class="debug-toggle-container">
     <button 
       @click="toggleDebug"
       :class="['debug-btn', debugActive ? 'active' : 'inactive']"
       class="[UTILISER LES CLASSES CSS EXISTANTES]"
     >
       Mode développement: {{ debugActive ? 'ON' : 'OFF' }}
     </button>
   </div>
   ```

3. **Modifier la StatusBar existante** pour ajouter l'indicateur debug :

 ```vue
   <!-- Ajouter dans la barre de status existante -->
   <span v-if="isDebugSession" class="status-debug">
     Debug actif
   </span>
   ```

## ÉTAPE 4 : CORRECTION DES PERMISSIONS

### Pour CHAQUE endpoint/vue qui accède aux données :

**AVANT (à supprimer) :**

python

```python
# NE PAS FAIRE ÇA
if request.user.username == "dev":
    strategies = Strategy.objects.all()  # ABERRATION!
else:
    strategies = Strategy.objects.filter(user=request.user)
```

**APRÈS (corriger partout) :**

```python
# TOUJOURS filtrer par user, même pour "dev"
strategies = Strategy.objects.filter(user=request.user)
```

### Vérifier et corriger dans :

* `apps/strategies/views.py`
* `apps/trading_engine/views.py`
* `apps/brokers/views.py`
* `apps/trading_manual/views.py`
* `apps/backtest/views.py`
* Tous les serializers et viewsets

## ÉTAPE 5 : CONFIGURATION

### Dans `settings.py` :



```python
# Ajouter
DEBUG_ARISTOBOT = env.bool('DEBUG_ARISTOBOT', default=False)

INSTALLED_APPS = [
    ...
    'apps.auth',  # Nouvelle app
    'apps.accounts',  # Garder pour les autres fonctions user
    ...
]
```

### Dans `.env.example` :

```
# Mode debug pour tests avec agents IA
DEBUG_ARISTOBOT=False
```

## ÉTAPE 6 : COMMANDE D'INITIALISATION

### Mettre à jour `management/commands/init_aristobot.py` :

```python
# Créer l'utilisateur dev SANS privilèges spéciaux
User.objects.create_user(
    username='dev',
    password='dev123',
    email='dev@aristobot.local'
)

# Créer son broker par défaut comme pour tout utilisateur
broker = Broker.objects.create(
    user=dev_user,
    name="Binance Testnet",
    exchange="binance",
    is_testnet=True,
    is_default=True
)

# Initialiser la table DebugMode
DebugMode.objects.get_or_create(id=1, defaults={'is_active': False})
```

## VÉRIFICATIONS FINALES

1. **Tester que "dev" ne peut PAS :**

   * Voir les stratégies des autres users
   * Voir les trades des autres users
   * Voir les brokers des autres users
   * Accéder à AUCUNE donnée d'un autre user

2. **Tester que le mode debug :**

   * N'apparaît QUE si DEBUG\_ARISTOBOT=True
   * Persiste son état après redémarrage
   * Permet l'auto-login avec "dev"
   * Affiche "Debug actif" dans la status bar

3. **Vérifier que le design n'a pas changé :**

   * Même thème sombre
   * Mêmes couleurs néon (`#00D4FF`, `#00FF88`, `#FF0055`)
   * Même disposition des éléments

## IMPORTANT

* Ne PAS recréer les composants UI qui existent déjà
* GARDER le style et le design actuels
* SEULEMENT nettoyer le code backend des privilèges "dev"
* L'utilisateur "dev" est un utilisateur NORMAL après cette refacto

Commence par l'ÉTAPE 1 pour me montrer tous les endroits problématiques, puis implémente les corrections.
