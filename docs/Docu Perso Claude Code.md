Pour clarifier : les imports `@` sont une fonctionnalité de **Claude Code**, donc ils vont dans `CLAUDE.md`, pas dans `Aristobot3.md`.

`Aristobot3.md` reste votre fichier Markdown normal - c'est Claude Code qui lit `CLAUDE.md` et traite les imports.

## 🔍 **Autres imports utiles pour CLAUDE.md**

Voici d'autres imports que vous pourriez ajouter selon vos besoins :

### **Configuration et environnement**

markdown

```markdown
@requirements.txt                    # Dépendances Python
@frontend/package.json              # Dépendances Node.js  
@backend/aristobot/urls.py          # Routes principales
@backend/aristobot/routing.py       # WebSocket routing
```

### **Modèles et données**

markdown

```markdown
@backend/apps/accounts/models.py    # Modèles utilisateur
@backend/apps/brokers/models.py     # Modèles brokers
@backend/apps/core/models.py        # Modèles système (déjà présent)
```

### **Services et logique métier**

markdown

```markdown
@backend/apps/core/services/ccxt_client.py     # Client CCXT
@backend/apps/core/consumers.py                # WebSocket consumers
@backend/apps/core/management/commands/run_heartbeat.py  # Service Heartbeat
```

### **Frontend**

markdown

```markdown
@frontend/src/websocket/client.js   # Client WebSocket
@frontend/vite.config.js           # Config Vite
@frontend/src/design-system/tokens.js  # Design system
```

### **Documentation technique**

markdown

```markdown
@MODULE2-Refacto-CCXT_MicroServ.md  # Instructions spécifiques
@README.md                          # Overview du projet
```

## 🎯 **Stratégie d'imports recommandée**

### **Imports permanents** (dans CLAUDE.md actuellement)

markdown

```markdown
@.claude-instructions      # Règles de développement
@.env.example             # Variables d'environnement
@backend/apps/core/models.py  # Structure DB principale
@backend/aristobot/settings.py  # Config Django
@Aristobot3.md            # Documentation complète
```

### **Imports contextuels** (ajoutés selon le travail)

Si vous travaillez sur :

**Frontend** → Ajoutez temporairement :
```markdown
@frontend/package.json
@frontend/vite.config.js
@frontend/src/websocket/client.js
```

**Services backend** → Ajoutez temporairement :
```markdown
@backend/apps/core/services/ccxt_client.py
@backend/apps/core/consumers.py
```

**Modèles spécifiques** → Ajoutez temporairement :
```markdown
@backend/apps/accounts/models.py
@backend/apps/brokers/models.py
```

## ⚡ **Comment optimiser selon vos besoins**

### **Option 1 : CLAUDE.md enrichi** (plus de contexte permanent)

F

edit\_file

Requête

``{ `path`: `C:\\Users\\dac\\Documents\\Python\\Django\\Aristobot3\\CLAUDE.md`, `edits`: [ { `newText`: `## Imports de contexte @.claude-instructions @.env.example @backend/apps/core/models.py @backend/aristobot/settings.py @backend/requirements.txt @frontend/package.json @Aristobot3.md`, `oldText`: `## Imports de contexte @.claude-instructions @.env.example @backend/apps/core/models.py @backend/aristobot/settings.py @Aristobot3.md` } ] }``

Réponse

` ```diff Index: C:\Users\dac\Documents\Python\Django\Aristobot3\CLAUDE.md =================================================================== --- C:\Users\dac\Documents\Python\Django\Aristobot3\CLAUDE.md original +++ C:\Users\dac\Documents\Python\Django\Aristobot3\CLAUDE.md modified @@ -4,8 +4,10 @@ @.claude-instructions @.env.example @backend/apps/core/models.py @backend/aristobot/settings.py +@backend/requirements.txt +@frontend/package.json @Aristobot3.md --- ``` `

Processus de réflexion

J'ai ajouté requirements.txt et frontend/package.json qui sont des fichiers utiles pour comprendre les dépendances du projet. Cela donne à Claude Code une vision complète de l'environnement technique sans surcharger avec trop d'imports.

Laissez-moi expliquer les limites et recommandations pour l'utilisation des imports.

### **Option 2 : CLAUDE.md modulaire** (imports à la demande)

Vous gardez les imports de base et ajoutez/retirez selon le contexte de travail.

## ⚠️ **Limitations importantes**

### **Limite de tokens**

Claude Code a une limite de contexte. Trop d'imports = dépassement :

markdown

```markdown
@backend/apps/*/models.py           ❌ (trop de fichiers)
@backend/apps/core/models.py        ✅ (fichier ciblé)
```

### **Pertinence du contexte**

markdown

```markdown
@frontend/package.json              ✅ (si travail frontend)
@frontend/src/components/Button.vue ❌ (trop spécifique, rarement utile)
```

### **Fichiers sensibles**

markdown

```markdown
@.env.example    ✅ (variables d'exemple)
@.env           ❌ (secrets réels)
```

## 🎯 **Ma recommandation**

J'ai ajouté `requirements.txt` et `package.json` à votre `CLAUDE.md` - ils donnent une vision complète des dépendances sans surcharger.

**Configuration actuelle optimale** :

* ✅ Règles de développement (`.claude-instructions`)
* ✅ Configuration environnement (`.env.example`)
* ✅ Modèles principaux (`core/models.py`)
* ✅ Config Django (`settings.py`)
* ✅ Dépendances (`requirements.txt`, `package.json`)
* ✅ Documentation complète (`Aristobot3.md`)

**Pour des besoins spécifiques**, vous pouvez temporairement ajouter/retirer des imports dans `CLAUDE.md` selon le contexte de développement.

Cette approche vous donne le **maximum de contexte utile** sans risquer la surcharge ! 🚀
