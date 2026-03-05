# Tech Spec — Extract Params (M5 Patch v2)

```yaml
status: ready-for-dev
date: 2026-03-03
validated_by: Dac (Party Mode)
prerequisite: Patch M5 v1 (base.py STRATEGY_PARAMS + validate_code params_schema)
```

## Contexte

Complement du Patch M5 v1. Permet a l'utilisateur d'extraire automatiquement les
litteraux numeriques de son code strategy et de les convertir en STRATEGY_PARAMS.

**Workflow cible :**
```
IA genere code brut (valeurs hardcodees)
    ↓
[Tester syntaxe]          → validation normale, inchangee
    ↓
[⚙ Extraire les params]  → modale : nouveaux litteraux detectes, noms editables
    ↓
[Appliquer au code]       → code transforme dans l'editeur (self.params['...'])
    ↓
User ajoute condition : rsi > 25 and rsi < 48
    ↓
[⚙ Extraire les params]  → modale : existants en resume + 25 et 48 comme nouveaux
    ↓
[Appliquer]               → code mis a jour de nouveau
    ↓
BacktestView              → lit STRATEGY_PARAMS, expose avec sliders/grids
```

**Idempotent** : peut etre relance N fois, detecte uniquement les NOUVEAUX litteraux.

---

## Fichiers a modifier

| Fichier | Changement |
|---------|-----------|
| `backend/apps/strategies/views.py` | +2 actions : extract_params, apply_params |
| `frontend/src/views/StrategiesView.vue` | +bouton + modal + logic (~120 lignes) |

Pas de migration, pas de nouveau modele.

---

## Backend

### Action 1 : `extract_params`

```
POST /api/strategies/extract-params/
Auth: IsAuthenticated
detail: False
```

**Input :**
```json
{ "code": "..." }
```

**Output :**
```json
{
  "new_literals": [
    {
      "value": 14,
      "suggested_name": "rsi_fast",
      "suggested_label": "RSI rapide (periode)",
      "suggested_default": 14,
      "suggested_min": 2,
      "suggested_max": 50,
      "suggested_step": 1,
      "suggested_type": "int",
      "context": "ta.rsi(length=14)",
      "occurrences": 2
    }
  ],
  "already_parameterized": ["risk_reward", "atr_period"]
}
```

**Logique AST :**

```python
def _extract_params(code: str) -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {'new_literals': [], 'already_parameterized': []}

    # 1. Trouver la classe Strategy
    cls_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                name = base.id if isinstance(base, ast.Name) else ''
                if name == 'Strategy':
                    cls_node = node
                    break

    if not cls_node:
        return {'new_literals': [], 'already_parameterized': []}

    # 2. Extraire les defaults deja dans STRATEGY_PARAMS (valeurs deja parametrees)
    existing_defaults = set()
    existing_names = []
    for stmt in cls_node.body:
        if (isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == 'STRATEGY_PARAMS'):
            try:
                sp = ast.literal_eval(stmt.value)
                for k, v in sp.items():
                    existing_defaults.add(v.get('default'))
                    existing_names.append(k)
            except (ValueError, TypeError):
                pass
            break

    # 3. Parcourir les corps de methodes, collecter ast.Constant numeriques
    EXCLUDED_INDICES = {-1, 0, 1}
    found = {}  # value -> {context, occurrences, parent_info}

    for method in cls_node.body:
        if not isinstance(method, ast.FunctionDef):
            continue
        for node in ast.walk(method):
            if not isinstance(node, ast.Constant):
                continue
            if not isinstance(node.value, (int, float)):
                continue
            v = node.value
            if v in EXCLUDED_INDICES:
                continue
            if v in existing_defaults:
                continue
            # Inferer contexte depuis parent (appel de fonction + kwarg)
            context = _infer_context(node, method)
            if v not in found:
                found[v] = {'context': context, 'occurrences': 0}
            found[v]['occurrences'] += 1

    # 4. Construire new_literals avec nommage heuristique
    new_literals = []
    used_names = set(existing_names)
    for value, info in found.items():
        name = _infer_name(value, info['context'], used_names)
        used_names.add(name)
        vtype = 'int' if isinstance(value, int) else 'float'
        mn, mx, step = _infer_range(value, vtype)
        new_literals.append({
            'value': value,
            'suggested_name': name,
            'suggested_label': _infer_label(name),
            'suggested_default': value,
            'suggested_min': mn,
            'suggested_max': mx,
            'suggested_step': step,
            'suggested_type': vtype,
            'context': info['context'],
            'occurrences': info['occurrences'],
        })

    return {'new_literals': new_literals, 'already_parameterized': existing_names}
```

**Heuristiques de nommage :**

```python
NAMING_PATTERNS = {
    # (func_name, kwarg_name) -> template
    ('rsi',    'length'): 'rsi_period',
    ('ema',    'length'): 'ema_period',
    ('sma',    'length'): 'sma_period',
    ('hma',    'length'): 'hma_period',
    ('wma',    'length'): 'wma_period',
    ('atr',    'length'): 'atr_period',
    ('bbands', 'length'): 'bb_period',
    ('macd',   'fast'):   'macd_fast',
    ('macd',   'slow'):   'macd_slow',
    ('macd',   'signal'): 'macd_signal',
    ('stoch',  'k'):      'stoch_k',
    ('stoch',  'd'):      'stoch_d',
}

def _infer_name(value, context, used_names):
    # Chercher dans NAMING_PATTERNS via le contexte
    # Ex: "ta.rsi(length=14)" → ('rsi','length') → 'rsi_period'
    for (func, kwarg), template in NAMING_PATTERNS.items():
        if func in context and kwarg in context:
            name = template
            # Deduplication si nom deja utilise
            if name in used_names:
                name = f"{template}_2"
            return name
    # Assignation simple : "rr = 1.5" → nom de la variable
    if '=' in context and not '==' in context:
        varname = context.split('=')[0].strip()
        if varname.isidentifier():
            return varname
    # Fallback
    i = 1
    while f"param_{i}" in used_names:
        i += 1
    return f"param_{i}"

def _infer_range(value, vtype):
    if vtype == 'int':
        v = int(value)
        mn = max(1, v // 4)
        mx = v * 4
        return mn, mx, 1
    else:
        v = float(value)
        mn = round(v * 0.1, 4)
        mx = round(v * 10, 4)
        step = round(v * 0.1, 4)
        return mn, mx, step
```

---

### Action 2 : `apply_params`

```
POST /api/strategies/apply-params/
Auth: IsAuthenticated
detail: False
```

**Input :**
```json
{
  "code": "...",
  "params": [
    {
      "name": "rsi_fast",
      "label": "RSI rapide",
      "default": 14,
      "min": 2,
      "max": 50,
      "step": 1,
      "type": "int",
      "replace_value": 14
    },
    {
      "name": "volume_filter",
      "label": "Filtre volume",
      "default": 1000,
      "min": 100,
      "max": 10000,
      "step": 100,
      "type": "int",
      "replace_value": null
    }
  ]
}
```

`replace_value: null` = ajout manuel (pas de valeur a remplacer dans le code) → ajout
a STRATEGY_PARAMS uniquement.

**Output :**
```json
{ "code": "..." }
```

**Logique de transformation :**

```python
def _apply_params(code: str, params: list) -> str:
    # Separer params avec valeur a remplacer vs ajout manuel
    to_replace = [p for p in params if p['replace_value'] is not None]
    manual_only = [p for p in params if p['replace_value'] is None]

    # 1. Remplacement textuel (toutes occurrences — Option 1 validee par Dac)
    #    Utiliser ast pour localiser, puis remplacement par token
    for p in to_replace:
        code = _replace_literal_in_methods(code, p['replace_value'], f"self.params['{p['name']}']")

    # 2. Mettre a jour STRATEGY_PARAMS dans le code
    code = _upsert_strategy_params(code, params)

    # 3. S'assurer que __init__ a params=None + super().__init__(..., params)
    code = _ensure_init_params(code)

    return code
```

**Remplacement de litteraux :**

Strategie : remplacement textuel base sur `ast.get_source_segment` pour localiser,
puis substitution string ciblant les corps de methodes uniquement (pas STRATEGY_PARAMS).
Toutes les occurrences de la valeur dans les methodes sont remplacees (Option 1).

---

## Frontend

### Nouveaux refs

```javascript
const showExtractModal = ref(false)
const extractLoading = ref(false)
const newLiterals = ref([])          // rows editables dans la modale
const alreadyParameterized = ref([]) // noms deja parametres (summary)
const manualParams = ref([])         // lignes ajoutees manuellement
```

### Nouveau bouton dans `editor-toolbar`

```html
<button class="btn-extract" :disabled="extractLoading || !selectedStrategy"
        @click="extractParams">
  {{ extractLoading ? 'Analyse...' : '⚙ Extraire les params' }}
</button>
```

### Fonctions

```javascript
async function extractParams() {
  extractLoading.value = true
  try {
    const resp = await api.post('/api/strategies/extract-params/', { code: code.value })
    newLiterals.value = resp.data.new_literals.map(p => ({
      replace_value: p.value,
      name: p.suggested_name,
      label: p.suggested_label,
      default: p.suggested_default,
      min: p.suggested_min,
      max: p.suggested_max,
      step: p.suggested_step,
      type: p.suggested_type,
      context: p.context,
      occurrences: p.occurrences,
    }))
    alreadyParameterized.value = resp.data.already_parameterized
    manualParams.value = []
    showExtractModal.value = true
  } finally {
    extractLoading.value = false
  }
}

function addManualParam() {
  manualParams.value.push({
    replace_value: null,
    name: '',
    label: '',
    default: 0,
    min: 0,
    max: 100,
    step: 1,
    type: 'int',
    context: 'manuel',
    noValueWarning: true,
  })
}

async function applyParams() {
  const allParams = [
    ...newLiterals.value,
    ...manualParams.value.filter(p => p.name.trim()),
  ]
  try {
    const resp = await api.post('/api/strategies/apply-params/', {
      code: code.value,
      params: allParams,
    })
    setCode(resp.data.code)
    showExtractModal.value = false
    validationResult.value = null
    detectedParams.value = {}
  } catch (e) {
    console.error('Erreur apply-params:', e)
  }
}
```

### Modal template (structure)

```html
<div v-if="showExtractModal" class="modal-overlay" @click.self="showExtractModal = false">
  <div class="extract-modal">
    <h3 class="modal-title">⚙ Extraire les parametres</h3>

    <!-- Deja parametres — resume collapsed -->
    <div v-if="alreadyParameterized.length > 0" class="already-params">
      <span class="already-label">✓ Deja parametres ({{ alreadyParameterized.length }})</span>
      <span class="already-names">{{ alreadyParameterized.join(', ') }}</span>
    </div>

    <!-- Nouveaux detectes -->
    <div v-if="newLiterals.length === 0 && manualParams.length === 0" class="no-new">
      Aucun nouveau litteral numerique detecte.
    </div>

    <div v-else>
      <div class="extract-table-header">
        <span>Contexte</span><span>Nom variable</span>
        <span>Def.</span><span>Min</span><span>Max</span>
        <span>Step</span><span>Type</span><span>Occur.</span>
      </div>

      <!-- Lignes auto-detectees -->
      <div v-for="(p, i) in newLiterals" :key="i" class="extract-row">
        <span class="extract-context" :title="p.context">{{ p.context }}</span>
        <input v-model="p.name" class="extract-input" />
        <input v-model.number="p.default" class="extract-input extract-input--num" />
        <input v-model.number="p.min"     class="extract-input extract-input--num" />
        <input v-model.number="p.max"     class="extract-input extract-input--num" />
        <input v-model.number="p.step"    class="extract-input extract-input--num" />
        <select v-model="p.type" class="extract-select">
          <option value="int">int</option>
          <option value="float">float</option>
        </select>
        <span class="extract-occ">×{{ p.occurrences }}</span>
      </div>

      <!-- Lignes manuelles -->
      <div v-for="(p, i) in manualParams" :key="'m'+i" class="extract-row extract-row--manual">
        <span class="extract-context extract-context--manual">manuel</span>
        <input v-model="p.name" class="extract-input" placeholder="nom_param" />
        <input v-model.number="p.default" class="extract-input extract-input--num" />
        <input v-model.number="p.min"     class="extract-input extract-input--num" />
        <input v-model.number="p.max"     class="extract-input extract-input--num" />
        <input v-model.number="p.step"    class="extract-input extract-input--num" />
        <select v-model="p.type" class="extract-select">
          <option value="int">int</option>
          <option value="float">float</option>
        </select>
        <span class="extract-occ extract-occ--warn" title="Aucun litteral a remplacer — sera ajoute a STRATEGY_PARAMS uniquement">⚠</span>
      </div>
    </div>

    <button class="btn-add-manual" @click="addManualParam">+ Ajouter manuellement</button>

    <div class="modal-actions">
      <button class="btn-cancel" @click="showExtractModal = false">Annuler</button>
      <button class="btn-primary" @click="applyParams"
              :disabled="newLiterals.length === 0 && manualParams.filter(p=>p.name).length === 0">
        Appliquer au code
      </button>
    </div>
  </div>
</div>
```

---

## Criteres d'acceptance

| # | Critere |
|---|---------|
| AC1 | Code avec 4 litteraux → modale affiche 4 lignes detectees |
| AC2 | Apres application → STRATEGY_PARAMS mis a jour dans l'editeur |
| AC3 | Apres application → toutes occurrences de la valeur remplacees par `self.params['nom']` |
| AC4 | Re-lancer apres ajout manuel `rsi > 25` → 25 detecto comme nouveau, existants en resume |
| AC5 | Param ajoute manuellement sans valeur → icone ⚠, ajout STRATEGY_PARAMS seulement |
| AC6 | Indices `-1`, `0`, `1` dans slices exclus de la detection |
| AC7 | SyntaxError dans le code → detection vide silencieuse (pas d'erreur frontend) |
| AC8 | Tous champs editables inline dans la modale (nom, min, max, step, type) |
| AC9 | `__init__` mis a jour avec `params=None` + `super().__init__(..., params)` si absent |

---

## Taches d'implementation (ordre)

1. `views.py` — helper `_extract_params()` avec logique AST
2. `views.py` — helper `_infer_name()` + `_infer_range()` + `_infer_label()`
3. `views.py` — action `extract_params` (appelle `_extract_params`)
4. `views.py` — helper `_apply_params()` : remplacement litteraux + upsert STRATEGY_PARAMS
5. `views.py` — helper `_ensure_init_params()` : patch `__init__`
6. `views.py` — action `apply_params` (appelle `_apply_params`)
7. `StrategiesView.vue` — refs + `extractParams()` + `applyParams()` + `addManualParam()`
8. `StrategiesView.vue` — bouton "⚙ Extraire les params" dans toolbar
9. `StrategiesView.vue` — modal template complet
10. `StrategiesView.vue` — CSS modal (`.extract-modal`, `.extract-row`, `.extract-input`)

**Service a redemarrer** : Terminal 1 (Daphne) uniquement.
Pas de migration.
