# Plan M5 Patch v3 — Chat IA + Pre-prompt modifiable + Template fix

```yaml
status: ready-for-dev
date: 2026-03-04
validated_by: Dac (Party Mode)
prerequisite: Patch M5 v2 (extract_params + apply_params)
```

---

## Decisions validees (Party Mode 2026-03-04)

| # | Decision |
|---|----------|
| 1 | BASE_TEMPLATE : STRATEGY_PARAMS = {} commente + return 0.0 sur SL/TP |
| 2 | Pre-prompt modifiable uniquement par user username='dev' via AccountView |
| 3 | Chat iteratif : [system_prompt + code_actuel + message_user] — AUCUN historique envoye au backend |
| 4 | Deux system prompts : GENERATE (1er tour) + CONTINUE (tours suivants) |
| 5 | Code envoye = code.value lu en temps reel depuis CodeMirror au moment de l'envoi |
| 6 | SYSTEM_PROMPT_GENERATE inclut "genere toujours un STRATEGY_PARAMS complet" |
| 7 | Migration : User.ai_generate_prompt TextField(blank=True) |

---

## Fichiers a modifier

| Fichier | Changement |
|---------|-----------|
| `backend/apps/accounts/models.py` | + champ `ai_generate_prompt` |
| `backend/apps/accounts/migrations/0004_user_ai_generate_prompt.py` | nouvelle migration |
| `backend/apps/accounts/views.py` | exposer `ai_generate_prompt` dans le profil user |
| `backend/apps/strategies/services.py` | 2 system prompts (GENERATE + CONTINUE) + utiliser user.ai_generate_prompt |
| `backend/apps/strategies/views.py` | mode `chat` dans ai_assist + parametre `is_first_turn` |
| `frontend/src/views/StrategiesView.vue` | fix template + refactor panel IA en chat |
| `frontend/src/views/AccountView.vue` | textarea pre-prompt conditionnelle (user dev seulement) |

---

## Tache 1 — accounts/models.py : champ ai_generate_prompt

Ajouter apres `ai_endpoint_url` :
```python
ai_generate_prompt = models.TextField(
    blank=True,
    default='',
    help_text="Pre-prompt personnalise pour le mode Generer (admin uniquement)"
)
```

---

## Tache 2 — Migration

```
python manage.py makemigrations accounts --name user_ai_generate_prompt
```
Fichier genere : `accounts/migrations/0004_user_ai_generate_prompt.py`

---

## Tache 3 — accounts/views.py : exposer ai_generate_prompt

Dans le serializer ou la vue profil utilisateur (endpoint GET/PATCH profil),
ajouter `ai_generate_prompt` dans les champs exposes.
Verifier que l'endpoint `/api/accounts/profile/` (ou equivalent) supporte PATCH de ce champ.

---

## Tache 4 — strategies/services.py : 2 system prompts + logique user

### Remplacer SYSTEM_PROMPTS['generate'] par :

```python
SYSTEM_PROMPTS = {
    'generate': (
        "Tu es un expert en trading algorithmique Python. "
        "L'utilisateur va te decrire en langage naturel une strategie de trading. "
        "Tu dois generer le code Python COMPLET d'une classe qui herite de Strategy. "
        "OBLIGATOIRE : inclure STRATEGY_PARAMS avec TOUTES les valeurs numeriques utilisees. "
        "Format STRATEGY_PARAMS : "
        "{'nom': {'default': val, 'min': mn, 'max': mx, 'step': st, 'type': 'int'|'float', 'label': '...'}}. "
        "La classe Strategy de base a ces 5 methodes abstraites : "
        "should_long() -> bool, should_short() -> bool, "
        "calculate_position_size() -> float, calculate_stop_loss() -> float, "
        "calculate_take_profit() -> float. "
        "Importe pandas_ta as ta si tu utilises des indicateurs techniques. "
        "self.candles est un DataFrame Pandas avec colonnes : open, high, low, close, volume. "
        "Utilise self.params['nom'] pour toutes les valeurs numeriques. "
        "Reponds UNIQUEMENT avec le code Python, sans explication ni markdown."
    ),
    'continue': (
        "Tu es un expert en trading algorithmique Python. "
        "Voici une classe Strategy existante. L'utilisateur souhaite la modifier. "
        "REGLES STRICTES : "
        "1) Applique UNIQUEMENT la modification demandee. "
        "2) Ne change rien a ce qui n'est pas mentionne. "
        "3) Conserve STRATEGY_PARAMS intact sauf si la modification concerne les params. "
        "4) Conserve les 5 methodes obligatoires. "
        "Reponds UNIQUEMENT avec le code Python COMPLET modifie, sans explication ni markdown."
    ),
    'assist': (
        "Tu es un expert en trading algorithmique Python. "
        "L'utilisateur va te montrer le code d'une strategie de trading. "
        "Analyse ce code et propose des ameliorations concretes en francais : "
        "logique de signal, gestion du risque, indicateurs techniques complementaires, etc. "
        "Sois concis et pratique. Reponds en francais."
    ),
    'describe': (
        "Tu es un expert en trading algorithmique Python. "
        "L'utilisateur va te montrer le code d'une strategie de trading. "
        "Decris en 2-3 phrases simples et en francais ce que fait cette strategie : "
        "quand elle achete, quand elle vend, et sa gestion du risque. "
        "Sois clair et accessible, sans jargon technique Python."
    ),
}
```

### Modifier call_ai() pour supporter 'continue' et le pre-prompt custom :

```python
async def call_ai(self, user, mode: str, prompt: str) -> str:
    if mode == 'generate':
        # Utiliser le pre-prompt personnalise si defini pour user dev
        system_prompt = user.ai_generate_prompt.strip() or SYSTEM_PROMPTS['generate']
    elif mode in SYSTEM_PROMPTS:
        system_prompt = SYSTEM_PROMPTS[mode]
    else:
        raise ValueError(f"Mode IA invalide: {mode}")
    ...
```

Ajouter 'continue' dans la validation des modes acceptes.

---

## Tache 5 — strategies/views.py : endpoint ai_assist supporte mode 'chat'

Modifier l'action `ai_assist` pour accepter :
- `mode` = 'chat' (nouveau) en plus de 'generate', 'assist', 'describe'
- Nouveau parametre `is_first_turn` (bool, defaut False)
- Nouveau parametre `code` (toujours present en mode chat)

Logique :
```python
if mode == 'chat':
    if not description.strip():
        return 400 "message obligatoire en mode chat"
    if is_first_turn:
        actual_mode = 'generate'
        # En mode generate avec code vide, prompt = description seule
        # En mode generate avec code existant, on inclut le code dans le prompt
        if code.strip():
            prompt = f"{description}\n\n## Code actuel :\n```python\n{code}\n```"
        else:
            prompt = description
    else:
        actual_mode = 'continue'
        prompt = f"## Code actuel :\n```python\n{code}\n```\n\n## Modification demandee :\n{description}"

    result = asyncio.run(service.call_ai(request.user, actual_mode, prompt))
    return Response({'result': result})
```

Mettre a jour la validation des modes pour accepter 'chat'.

---

## Tache 6 — StrategiesView.vue : fix template

### BASE_TEMPLATE : remplacer par

```python
import pandas_ta as ta

class MaNouvelleStrategie(Strategy):
    # Parametres configurables — definir apres avoir ecrit la logique
    # ou utiliser "Extraire les params" pour les detecter automatiquement
    STRATEGY_PARAMS = {
        # Exemple : 'rsi_period': {'default': 14, 'min': 2, 'max': 50, 'step': 1, 'type': 'int', 'label': 'Periode RSI'},
    }

    def __init__(self, candles, balance, position=None, params=None):
        super().__init__(candles, balance, position, params)

    def should_long(self) -> bool:
        # Exemple : return self.params.get('rsi_period', 14) > 30
        return False

    def should_short(self) -> bool:
        return False

    def calculate_position_size(self) -> float:
        return 0.0

    def calculate_stop_loss(self) -> float:
        return 0.0

    def calculate_take_profit(self) -> float:
        return 0.0
```

---

## Tache 7 — StrategiesView.vue : refactor panel IA en chat

### Nouveaux refs

```javascript
const chatMessages = ref([])       // [{role: 'user'|'assistant', content: string}]
const chatInput = ref('')
const chatLoading = ref(false)
```

### Logique chat

```javascript
async function sendChatMessage() {
  const message = chatInput.value.trim()
  if (!message || chatLoading.value) return

  const isFirstTurn = chatMessages.value.length === 0
  const currentCode = code.value  // toujours relu depuis CodeMirror

  // Ajouter message user dans l'historique visuel
  chatMessages.value.push({ role: 'user', content: message })
  chatInput.value = ''
  chatLoading.value = true

  try {
    const resp = await api.post('/api/strategies/ai-assist/', {
      mode: 'chat',
      description: message,
      code: currentCode,          // code lu en temps reel
      is_first_turn: isFirstTurn,
    })

    const result = resp.data.result

    // Ajouter reponse IA dans l'historique visuel
    chatMessages.value.push({ role: 'assistant', content: result })

    // Si la reponse contient du code Python, le mettre dans l'editeur
    const codeMatch = result.match(/```python\n?([\s\S]*?)```/)
    if (codeMatch) {
      setCode(codeMatch[1].trim())
    } else if (result.includes('class ') && result.includes('Strategy')) {
      // Reponse directe sans fences markdown
      setCode(result.trim())
    }

    validationResult.value = null
    detectedParams.value = {}

  } catch (e) {
    chatMessages.value.push({ role: 'assistant', content: 'Erreur : ' + (e.response?.data?.error || e.message) })
  } finally {
    chatLoading.value = false
  }
}

function resetChat() {
  chatMessages.value = []
  chatInput.value = ''
}

// Watcher : reset chat si nouvelle strategie selectionnee
watch(selectedStrategy, () => { resetChat() })
```

### Remplacement du panel IA (cote droit)

Le panel actuel a : boutons Generer/Analyser/Decrire + textarea description + bouton "Generer le code".

Nouveau panel :
```html
<div class="ai-panel">
  <div class="ai-panel-header">
    <span>✨ Assistant IA</span>
    <div class="ai-quick-actions">
      <!-- Garder Analyser et Decrire comme boutons rapides -->
      <button @click="runAssist" :disabled="!code.trim() || aiLoading" class="btn-quick">Analyser</button>
      <button @click="runDescribe" :disabled="!code.trim() || aiLoading" class="btn-quick">Decrire</button>
      <button @click="resetChat" class="btn-reset-chat" title="Nouvelle conversation">↺</button>
    </div>
  </div>

  <!-- Historique visuel (affichage seulement, non envoye) -->
  <div class="chat-history" ref="chatHistoryEl">
    <div v-if="chatMessages.length === 0" class="chat-placeholder">
      Decris ta strategie en francais...<br>
      <small>Ex: RSI croisement 30/70 avec stop 2% et TP 4%</small>
    </div>
    <div v-for="(msg, i) in chatMessages" :key="i"
         :class="['chat-msg', 'chat-msg--' + msg.role]">
      <span class="chat-role">{{ msg.role === 'user' ? '👤' : '🤖' }}</span>
      <span class="chat-content">{{ msg.content }}</span>
    </div>
    <div v-if="chatLoading" class="chat-loading">⏳ Generation...</div>
  </div>

  <!-- Input -->
  <div class="chat-input-area">
    <textarea
      v-model="chatInput"
      class="chat-textarea"
      rows="3"
      placeholder="Decris une strategie ou demande une modification..."
      @keydown.ctrl.enter.prevent="sendChatMessage"
      :disabled="chatLoading || !selectedStrategy"
    ></textarea>
    <button class="btn-send" @click="sendChatMessage"
            :disabled="!chatInput.trim() || chatLoading || !selectedStrategy">
      {{ chatLoading ? '...' : 'Envoyer' }}
    </button>
    <small class="chat-hint">Ctrl+Entree pour envoyer</small>
  </div>
</div>
```

### CSS a ajouter

Styles pour `.chat-history`, `.chat-msg`, `.chat-msg--user`, `.chat-msg--assistant`,
`.chat-input-area`, `.chat-textarea`, `.btn-send`, `.chat-placeholder`, `.chat-hint`,
`.btn-reset-chat`, `.btn-quick`, `.ai-quick-actions`.

Hauteur fixe pour `.chat-history` avec `overflow-y: auto` et auto-scroll vers le bas
apres chaque message.

---

## Tache 8 — AccountView.vue : textarea pre-prompt pour user dev

Dans la section "Configuration IA", ajouter conditionnellement :

```html
<div v-if="authStore.user?.username === 'dev'" class="admin-section">
  <div class="section-title">Pre-prompt Generer (admin uniquement)</div>
  <textarea
    v-model="aiGeneratePrompt"
    class="prompt-textarea"
    rows="6"
    placeholder="Laisser vide pour utiliser le pre-prompt par defaut..."
  ></textarea>
  <div class="prompt-actions">
    <button @click="resetGeneratePrompt" class="btn-reset">Reinitialiser</button>
    <button @click="saveGeneratePrompt" class="btn-save">Sauvegarder</button>
  </div>
  <details class="prompt-default">
    <summary>Voir le pre-prompt par defaut</summary>
    <pre>{{ defaultGeneratePrompt }}</pre>
  </details>
</div>
```

Logique :
- Charger `ai_generate_prompt` depuis le profil user au montage
- PATCH `/api/accounts/profile/` avec `{ai_generate_prompt: value}` a la sauvegarde
- "Reinitialiser" = mettre la valeur a '' (vide = utilise le defaut)
- Afficher le prompt par defaut (hardcode cote frontend pour reference)

---

## Ordre d'execution

1. `accounts/models.py` — ajouter champ
2. Migration — `makemigrations + migrate`
3. `accounts/views.py` — exposer champ dans profil API
4. `strategies/services.py` — 2 system prompts + logique user.ai_generate_prompt
5. `strategies/views.py` — mode 'chat' dans ai_assist
6. `StrategiesView.vue` — fix template + refactor chat
7. `AccountView.vue` — textarea pre-prompt admin

**Services a redemarrer :** Terminal 1 (Daphne) apres taches 1-5.
Terminal 4 (Vite) se recharge automatiquement.

---

## Criteres d'acceptance

| # | Critere |
|---|---------|
| AC1 | Nouvelle strategie → template avec STRATEGY_PARAMS vide commente, return 0.0 |
| AC2 | Chat : 1er message → GENERATE, messages suivants → CONTINUE |
| AC3 | Chat : le code envoye est toujours code.value au moment de l'envoi |
| AC4 | Chat : reponse IA contenant du code → code mis dans l'editeur automatiquement |
| AC5 | Analyser et Decrire restent fonctionnels comme boutons rapides |
| AC6 | User 'dev' voit la textarea pre-prompt dans AccountView, autres users ne la voient pas |
| AC7 | User 'dev' sauvegarde un prompt custom → utilisé pour GENERATE a la place du defaut |
| AC8 | User 'dev' reinitialise → prompt vide = retour au defaut cote backend |
| AC9 | Ctrl+Entree envoie le message |
| AC10 | Changement de strategie reset le chat |
