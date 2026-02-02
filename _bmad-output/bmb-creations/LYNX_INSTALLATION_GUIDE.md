# 🔍 LYNX — Guide d'Installation et d'Utilisation

**Agent:** debug-loguru (Lynx)
**Type:** Expert stand-alone avec sidecar
**Status:** ✅ INSTALLÉ
**Date:** 2026-02-02

---

## ✅ Installation Effectuée

L'agent Lynx a été installé avec succès dans votre projet Aristobot3. Voici ce qui a été créé :

### 📁 Fichiers Créés

#### 1. Agent Compilé (Fichier Principal)
```
_bmad/stand-alone/agents/debug-loguru/debug-loguru.md
```
Fichier compilé complet avec activation XML, persona, menu et prompts.

#### 2. Claude Code Skill Wrapper
```
.claude/commands/bmad/stand-alone/agents/debug-loguru.md
```
Wrapper léger qui enregistre Lynx comme skill Claude Code.

#### 3. Sidecar (Mémoire Persistante)
```
_bmad/_memory/debug-loguru-sidecar/
├── memories.yaml         # Sessions de debug sauvegardées
└── instructions.md       # Protocoles opérationnels complets
```

#### 4. Registres BMAD
- `_bmad/_config/agent-manifest.csv` — Entrée ajoutée pour debug-loguru
- `_bmad/_config/files-manifest.csv` — 3 fichiers enregistrés

---

## 🚀 Comment Utiliser Lynx

### Activation

**Option 1 : Via Skill (Recommandé)**
```
/debug-loguru
```

**Option 2 : Via BMAD Master**
```
/bmad-master
→ [Agents] → Chercher "Lynx" ou "debug-loguru"
```

### Menu Principal

Une fois activé, Lynx affiche 7 commandes :

| Code | Commande | Description |
|------|----------|-------------|
| **DL** | debug-loguru | Entrée principale — auto-déduit les 4 modes |
| **DM** | debug-memory | Affiche les 5 dernières sessions mémorisées |
| **DB** | debug-bmad | Délégation forcée à BMAD (équivalent --bmad) |
| MH | menu/help | Réafficher le menu |
| CH | chat | Dialoguer avec Lynx |
| PM | party-mode | Lancer Party Mode |
| DA | exit | Quitter Lynx |

---

## 🎯 Les 4 Modes (Auto-Déduits)

Lynx analyse ton langage naturel et choisit automatiquement le mode :

### 1. INSTRUMENTE 🔧
**Mots-clés déclencheurs :** "ajoute du debug", "instrumente", "loguru dans..."

**Exemple :**
```
DL ajoute du debug dans backend/apps/webhooks/views.py
```

**Ce que Lynx fait :**
1. Scanne le fichier Python
2. Identifie les points stratégiques (entrée fonction, appels Redis, etc.)
3. **Propose un diff lisible AVANT modification**
4. Attend ta validation
5. Insère les points loguru uniquement si tu confirmes

### 2. RECHERCHE 🔎
**Mots-clés déclencheurs :** "cherche", "recherche", "depuis X minutes", "trace_id..."

**Exemple :**
```
DL cherche balance USDT depuis 10 minutes
```

**Ce que Lynx fait :**
1. Identifie les terminaux concernés (T2, T3, T5...)
2. Lance `tools/log_aggregator.py` avec les bons arguments
3. Lit le rapport généré
4. Présente les résultats filtrés

### 3. DIAGNOSTIQUE 🧠
**Mots-clés déclencheurs :** "pourquoi", "ne marche pas", "problème avec..."

**Exemple :**
```
DL pourquoi le trading manuel ne marche pas
```

**Ce que Lynx fait :**
1. Lit `Aristobot3_1.md` pour le flow architecturel
2. Identifie les terminaux impliqués
3. Cherche dans les logs (via mode RECHERCHE)
4. **Détecte la complexité** (3 signaux) :
   - Plus de 2 terminaux
   - Pas de trace_id
   - Pas d'erreur explicite
5. Si ≥2 signaux → propose délégation BMAD (Dr. Quinn, architect, etc.)
6. Si <2 signaux → suggère une solution

### 4. CONTRÔLE VIVANT ⚙️
**Mots-clés déclencheurs :** "baisse les logs", "configure la retention", "couverture debug..."

**Exemple :**
```
DL baisse les logs de Terminal 2
```

**Ce que Lynx fait :**
1. Ajuste les niveaux de log par terminal (DEBUG → INFO → WARNING)
2. Configure la rétention (sans toucher rotation 2min)
3. Query la couverture debug (zones instrumentées vs aveugles)

---

## 🧠 Mémoire Persistante

Lynx **mémorise chaque session** dans `memories.yaml` :

```yaml
- date: "2026-02-02"
  probleme: "Webhook TradingView reçu mais pas traité par T3"
  terminaux: [T6, T3]
  cause_racine: "Redis channel 'webhook_raw' non écouté par T3"
  solution: "Ajouté listener webhook_raw dans run_trading_engine.py"
  echecs: ["Tenté de redémarrer T6 — pas le vrai problème"]
  duree_resolution_min: 18
```

**Commande :** `DM` pour afficher les 5 dernières sessions.

---

## 🛡️ Périmètre Strict (Immuable)

✅ **Ce que Lynx FAIT :**
- Instrumenter le code avec loguru (insertion de points d'observation)
- Agréger les logs via `tools/log_aggregator.py`
- Lancer le linter silencieux (détection divergences doc)

❌ **Ce que Lynx NE FAIT JAMAIS :**
- Toucher la logique du code
- Modifier la documentation du projet
- Diagnostiquer les bugs (il délègue à BMAD)

---

## 🤝 Délégation BMAD

Si Lynx détecte un problème complexe (≥2 signaux), il propose :

| Cas | Délégation | Justification |
|-----|-----------|---------------|
| Diagnostic multi-terminaux | Dr. Quinn (problem-solving) | ≥2 signaux complexité |
| Modification code hors loguru | Barry (quick-dev) | Au-delà du périmètre |
| Question architecturale | Winston (architect) | Compréhension flow |
| Divergence doc | Paige (tech-writer) | Linter silencieux confirme |

**Flag manuel :** Ajoute `--bmad` à ta commande pour forcer la délégation immédiate.

```
DL pourquoi le webhook ne fonctionne pas --bmad
```

---

## 📊 Conventions Aristobot3

Lynx connaît parfaitement ton architecture :

### Terminaux
| Terminal | Commande | Rôle |
|----------|----------|------|
| T1 | daphne | Serveur web + WebSocket |
| T2 | run_heartbeat | Service Heartbeat Binance |
| T3 | run_trading_engine | Cerveau (stratégies + webhooks) |
| T4 | npm run dev | Frontend Vue.js |
| T5 | run_native_exchange_service | Exchange Gateway centralisé |
| T6 | run_webhook_receiver | Réception webhooks TradingView |
| T7 | run_order_monitor | Monitoring ordres |

### Propagation trace_id
```
T6 → Redis 'webhook_raw' → T3 → Redis 'exchange_requests' → T5
```

### Conventions Loguru
- `setup_loguru("terminalX")` obligatoire
- `serialize=True`, `enqueue=True`
- trace_id via `contextvars.ContextVar` uniquement
- Logs JSON dans `logs/terminalX.log`
- Rotation 2min, rétention 10min (configurable)

---

## 🎨 Style de Communication

Lynx est **nocturne et silencieux** :
- Court, factuel, visuel
- Présente les faits comme un diff lisible (fichier, ligne, changement, pourquoi)
- Pose **une seule question précise** si incertain (jamais trois)
- Ton neutre, jamais d'exclamation
- Communication en français

---

## 🧪 Exemples d'Utilisation

### Exemple 1 : Instrumentation
```
User: DL ajoute du debug dans backend/apps/trading_manual/services.py
Lynx:
Fichier: backend/apps/trading_manual/services.py
Points strategiques identifies:
  - Ligne 45: entree fonction place_order()
  - Ligne 78: appel Redis exchange_requests
  - Ligne 102: retour API avec status

Diff propose:
  [Ligne 45] logger.info("place_order called", user_id=user_id, symbol=symbol)
  [Ligne 78] logger.debug("Redis publish", channel="exchange_requests", request_id=req_id)
  [Ligne 102] logger.info("Order response", status=response.status, order_id=response.id)

Valider? (oui/non)
```

### Exemple 2 : Recherche
```
User: DL cherche trace_id abc123 depuis 5 minutes
Lynx:
Terminaux concernes: T6, T3, T5
Lancement log_aggregator: --trace abc123 --components T6,T3,T5 --since 5min

Rapport:
  [T6 14:32:15] Webhook recu, trace_id=abc123
  [T3 14:32:16] Signal webhook traite, trace_id=abc123
  [T5 14:32:17] Ordre execute, trace_id=abc123, status=FILLED
```

### Exemple 3 : Diagnostic Complexe
```
User: DL pourquoi le trading manuel ne fonctionne pas
Lynx:
Flow architecturel (Aristobot3_1.md):
  Frontend → T1 (Daphne) → T5 (Exchange Gateway) → Binance API

Terminaux impliques: T1, T5 (2 terminaux)
trace_id: non disponible (signal 2/3)
Erreur explicite: non trouvee (signal 3/3)

⚠️ Complexite detectee (3/3 signaux)
→ Delegation recommandee: Dr. Quinn (problem-solving)

Justification: Absence trace_id + multi-terminaux + pas d'erreur claire
= probleme architectural potentiel

Deleguer maintenant? (oui/non)
```

---

## 🔧 Dépannage

### Lynx ne s'active pas
1. Vérifier que Claude Code a rechargé les skills :
   ```
   Ctrl+Shift+P → "Reload Window"
   ```

2. Vérifier l'installation :
   ```
   ls .claude/commands/bmad/stand-alone/agents/
   → debug-loguru.md doit exister
   ```

### Sidecar non trouvé
Vérifier le chemin :
```
ls _bmad/_memory/debug-loguru-sidecar/
→ memories.yaml et instructions.md doivent exister
```

### Mémoire vide
Normal au premier lancement. Les sessions seront sauvegardées après chaque opération avec `DL`.

---

## 📚 Fichiers de Référence

- **Plan complet** : `_bmad-output/analysis/brainstorming-session-20260201.md`
- **Validation** : `_bmad-output/bmb-creations/validation-report-debug-loguru.md`
- **Completion** : `_bmad-output/bmb-creations/agent-completion-debug-loguru.md`
- **Source YAML** : `_bmad-output/bmb-creations/debug-loguru/debug-loguru.agent.yaml`

---

## 🎉 Prêt à l'Emploi

Lynx est maintenant **opérationnel** dans ton projet Aristobot3. Lance simplement :

```
/debug-loguru
```

Et laisse Lynx instrumenter, rechercher, diagnostiquer ou contrôler tes logs multi-terminaux avec expertise. 🔍

---

**Créé par :** BMAD BMB Workflow (Agent Builder)
**Validation :** 5/5 PASS (Metadata, Persona, Menu, Structure, Sidecar)
**Installation :** Manuelle — 2026-02-02
