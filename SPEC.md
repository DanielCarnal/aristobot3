# Tech Spec M5 Patch v4 — Prompt Modal + Thinking Display + Diff Vue + Scrollbars

```yaml
status: ready-for-dev
date: 2026-03-07
validated_by: Dac (Party Mode 2026-03-06)
prerequisite: Patch M5 v3 (Chat IA + mode continue)
```

---

## Decisions validees (Party Mode 2026-03-06)

| # | Decision |
|---|----------|
| 1 | Prompt Modal : bouton [👁 Prompt] dans panel IA, drawer fixe non bloquant (ne couvre pas editeur) |
| 2 | `prompt_sent` toujours inclus dans la reponse API REST |
| 3 | Thinking : vrais `<think>` tags ou champ `reasoning` UNIQUEMENT — ZERO simulation si modele non thinking |
| 4 | `thinking_chunk` event WS emis UNIQUEMENT si `has_thinking=True` cote backend |
| 5 | Diff : `difflib.unified_diff` cote backend (stdlib Python, 0 dependances npm) |
| 6 | Diff visible uniquement en mode `continue` (pas `generate`) |
| 7 | `diff_summary: {adds: N, removes: N}` retourne dans reponse pour label accordeon |
| 8 | Scrollbar pattern Sally : gradient #00D4FF, 8px, border-radius 4px, hover glow — sur toutes zones scrollables |
| 9 | WS streaming : events `connecting`, `thinking_chunk`, `code_chunk`, `done`, `error` |
| 10 | Normalisation multi-provider : Ollama extrait balises think ; OpenRouter lit `reasoning`/`reasoning_content` |

---

## Contrat de reponse normalise

`call_ai()` retourne toujours ce dict :

```python
{
    'result': str,           # Code Python ou reponse texte
    'thinking': str,         # Contenu reflexion (vide si non supporte)
    'has_thinking': bool,    # True seulement si thinking reel detecte
    'prompt_sent': str,      # Prompt complet envoye au modele
    'tokens': int | None,    # Tokens utilises
    'diff': list[str] | None,       # Lignes unified diff (None si mode generate)
    'diff_summary': dict | None,    # {'adds': N, 'removes': N}
}
```

---

## Fichiers a modifier

| Fichier | Changement |
|---------|-----------|
| `backend/apps/strategies/services.py` | Normalisation `call_ai()` + extraction thinking + calcul diff |
| `backend/apps/strategies/consumers.py` | NOUVEAU — `AIStreamConsumer` WebSocket |
| `backend/aristobot/routing.py` | Ajouter route `ws/ai-stream/` |
| `backend/apps/strategies/views.py` | Passer `current_code`, retourner dict complet |
| `frontend/src/views/StrategiesView.vue` | Tous les changements frontend |

**Services a redemarrer :** Terminal 1 (Daphne) apres taches 1-4.

---

## Tache 1 — strategies/services.py

### 1.1 Extraction thinking Ollama

```python
import re as _re

def _extract_thinking_ollama(raw_text: str) -> tuple:
    """Extrait <think>...</think> du texte Ollama. Retourne (thinking, has_thinking, result)."""
    match = _re.search(r'<think>(.*?)</think>', raw_text, _re.DOTALL)
    if match:
        thinking = match.group(1).strip()
        result = _re.sub(r'<think>.*?</think>', '', raw_text, flags=_re.DOTALL).strip()
        return thinking, True, result
    return '', False, raw_text
```

### 1.2 Extraction thinking OpenRouter

```python
def _extract_thinking_openrouter(response_data: dict) -> tuple:
    """Champs possibles : reasoning, reasoning_content selon modele."""
    choices = response_data.get('choices', [{}])
    if not choices:
        return '', False
    message = choices[0].get('message', {})
    thinking = message.get('reasoning') or message.get('reasoning_content') or ''
    if thinking:
        return thinking.strip(), True
    return '', False
```

### 1.3 Calcul diff

```python
import difflib as _difflib

def _compute_diff(old_code: str, new_code: str) -> tuple:
    """Retourne (lines, summary) ou (None, None) si identiques ou old vide."""
    if not old_code or not old_code.strip():
        return None, None
    old_lines = old_code.splitlines(keepends=True)
    new_lines = new_code.splitlines(keepends=True)
    diff_lines = list(_difflib.unified_diff(
        old_lines, new_lines,
        fromfile='avant', tofile='apres', n=3
    ))
    if not diff_lines:
        return None, None
    adds = sum(1 for l in diff_lines if l.startswith('+') and not l.startswith('+++'))
    removes = sum(1 for l in diff_lines if l.startswith('-') and not l.startswith('---'))
    return [l.rstrip('\n') for l in diff_lines], {'adds': adds, 'removes': removes}
```

### 1.4 Modifier call_ai() — nouvelle signature et retour

```python
async def call_ai(self, user, mode: str, prompt: str, current_code: str = '') -> dict:
    if mode == 'generate':
        system_prompt = user.ai_generate_prompt.strip() or SYSTEM_PROMPTS['generate']
    elif mode in SYSTEM_PROMPTS:
        system_prompt = SYSTEM_PROMPTS[mode]
    else:
        raise ValueError(f'Mode IA invalide: {mode}')

    if user.ai_provider == 'ollama':
        raw_response, usage = await self._call_ollama_raw(user, system_prompt, prompt)
        thinking, has_thinking, result = _extract_thinking_ollama(raw_response)
    elif user.ai_provider == 'openrouter':
        response_data, usage = await self._call_openrouter_raw(user, system_prompt, prompt)
        choices = response_data.get('choices', [{}])
        result = choices[0].get('message', {}).get('content', '') if choices else ''
        thinking, has_thinking = _extract_thinking_openrouter(response_data)
    else:
        raise ValueError('Fournisseur IA non configure')

    diff_lines, diff_summary = None, None
    if mode == 'continue' and current_code.strip():
        diff_lines, diff_summary = _compute_diff(current_code, result)

    return {
        'result': result,
        'thinking': thinking,
        'has_thinking': has_thinking,
        'prompt_sent': f'[SYSTEM]\n{system_prompt}\n\n[USER]\n{prompt}',
        'tokens': usage.get('total_tokens') if usage else None,
        'diff': diff_lines,
        'diff_summary': diff_summary,
    }
```

### 1.5 Renommer methodes internes

- `_call_ollama` → `_call_ollama_raw` (retourne `(raw_text: str, usage: dict)`)
- `_call_openrouter` → `_call_openrouter_raw` (retourne `(response_data: dict, usage: dict)`)

---

## Tache 2 — strategies/consumers.py (NOUVEAU)

```python
# -*- coding: utf-8 -*-
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)


class AIStreamConsumer(AsyncWebsocketConsumer):
    """Consumer WS. Events : connecting, thinking_chunk (si has_thinking), code_chunk, done, error"""

    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error('JSON invalide')
            return
        description = data.get('description', '')
        code = data.get('code', '')
        is_first_turn = data.get('is_first_turn', False)
        if not description.strip():
            await self._send_error('Message obligatoire')
            return
        await self._stream_response(description, code, is_first_turn)

    async def _stream_response(self, description, code, is_first_turn):
        from apps.strategies.services import AIAssistService
        await self.send(text_data=json.dumps({'type': 'connecting'}))
        try:
            service = AIAssistService()
            if is_first_turn:
                actual_mode = 'generate'
                prompt = f'{description}\n\n## Code actuel :\n{code}' if code.strip() else description
            else:
                actual_mode = 'continue'
                prompt = f'## Code actuel :\n{code}\n\n## Modification demandee :\n{description}'
            response = await sync_to_async(
                lambda: asyncio.run(service.call_ai(self.user, actual_mode, prompt, current_code=code))
            )()
            # ZERO simulation : thinking_chunk emis UNIQUEMENT si has_thinking=True
            if response['has_thinking'] and response['thinking']:
                await self.send(text_data=json.dumps({
                    'type': 'thinking_chunk',
                    'content': response['thinking']
                }))
            await self.send(text_data=json.dumps({'type': 'code_chunk', 'content': response['result']}))
            await self.send(text_data=json.dumps({
                'type': 'done',
                'result': response['result'],
                'thinking': response['thinking'],
                'has_thinking': response['has_thinking'],
                'prompt_sent': response['prompt_sent'],
                'tokens': response['tokens'],
                'diff': response['diff'],
                'diff_summary': response['diff_summary'],
            }))
        except Exception as e:
            logger.error(f'Erreur AIStreamConsumer: {e}')
            await self._send_error(str(e))

    async def _send_error(self, message: str):
        await self.send(text_data=json.dumps({'type': 'error', 'message': message}))
```

---

## Tache 3 — aristobot/routing.py

```python
from apps.strategies.consumers import AIStreamConsumer

# Dans websocket_urlpatterns ajouter :
path('ws/ai-stream/', AIStreamConsumer.as_asgi()),
```

---

## Tache 4 — strategies/views.py

Dans action `ai_assist`, passer `current_code` a `call_ai()` et retourner dict complet :

```python
code = request.data.get('code', '')

# Appel avec current_code
response = asyncio.run(service.call_ai(request.user, actual_mode, prompt, current_code=code))

return Response({
    'result': response['result'],
    'thinking': response['thinking'],
    'has_thinking': response['has_thinking'],
    'prompt_sent': response['prompt_sent'],
    'tokens': response['tokens'],
    'diff': response['diff'],
    'diff_summary': response['diff_summary'],
})
```

---

## Tache 5 — StrategiesView.vue

### 5.1 Nouveaux refs

```javascript
const wsState = ref('idle')          // idle | connecting | done
const showPromptModal = ref(false)
const lastPromptSent = ref('')
const lastDiff = ref(null)           // array lignes unified diff
const lastDiffSummary = ref(null)    // {adds: N, removes: N}
const showDiff = ref(false)
const pendingCode = ref('')          // code en attente avant application diff
```

### 5.2 sendChatMessage — gestion reponse enrichie

```javascript
async function sendChatMessage() {
  const message = chatInput.value.trim()
  if (!message || chatLoading.value) return
  const isFirstTurn = chatMessages.value.length === 0
  const currentCode = code.value

  chatMessages.value.push({ role: 'user', content: message })
  chatInput.value = ''
  chatLoading.value = true
  wsState.value = 'connecting'
  lastDiff.value = null
  lastDiffSummary.value = null
  showDiff.value = false

  try {
    const resp = await api.post('/api/strategies/ai-assist/', {
      mode: 'chat',
      description: message,
      code: currentCode,
      is_first_turn: isFirstTurn,
    })
    const data = resp.data
    wsState.value = 'done'
    lastPromptSent.value = data.prompt_sent || ''

    chatMessages.value.push({
      role: 'assistant',
      content: data.result,
      thinking: data.has_thinking ? data.thinking : null,
      has_thinking: data.has_thinking,
      prompt_sent: data.prompt_sent,
      tokens: data.tokens,
      diff: data.diff,
      diff_summary: data.diff_summary,
    })

    if (data.diff && data.diff_summary) {
      lastDiff.value = data.diff
      lastDiffSummary.value = data.diff_summary
      pendingCode.value = data.result
      showDiff.value = true
    } else {
      const codeMatch = data.result.match(/```python\n?([\s\S]*?)```/)
      if (codeMatch) {
        setCode(codeMatch[1].trim())
      } else if (data.result.includes('class ') && data.result.includes('Strategy')) {
        setCode(data.result.trim())
      }
      validationResult.value = null
      detectedParams.value = {}
    }
  } catch (e) {
    wsState.value = 'idle'
    chatMessages.value.push({
      role: 'assistant',
      content: 'Erreur : ' + (e.response?.data?.error || e.message)
    })
  } finally {
    chatLoading.value = false
    if (wsState.value !== 'done') wsState.value = 'idle'
  }
}
```

### 5.3 Fonctions diff et prompt

```javascript
function applyDiff() {
  setCode(pendingCode.value)
  showDiff.value = false
  lastDiff.value = null
  lastDiffSummary.value = null
  pendingCode.value = ''
  validationResult.value = null
  detectedParams.value = {}
}

function ignoreDiff() {
  showDiff.value = false
  lastDiff.value = null
  lastDiffSummary.value = null
  pendingCode.value = ''
}

function getDiffLineClass(line) {
  if (line.startsWith('+++') || line.startsWith('---')) return 'diff-meta-file'
  if (line.startsWith('@@')) return 'diff-meta-hunk'
  if (line.startsWith('+')) return 'diff-add'
  if (line.startsWith('-')) return 'diff-remove'
  return 'diff-context'
}

function openPromptModal(promptText) {
  lastPromptSent.value = promptText || ''
  showPromptModal.value = true
}
```

### 5.4 Template additions dans le panel IA

```html
<!-- Indicateur generation -->
<div v-if="wsState === 'connecting'" class="connecting-indicator">
  <span class="connecting-dot"></span> Generation en cours...
</div>

<!-- Dans chaque message assistant : thinking accordion + bouton prompt -->
<details v-if="msg.role === 'assistant' && msg.has_thinking" class="thinking-details">
  <summary class="thinking-summary">🧠 Reflexion du modele</summary>
  <pre class="thinking-content">{{ msg.thinking }}</pre>
</details>
<button v-if="msg.role === 'assistant' && msg.prompt_sent"
        class="btn-prompt-peek"
        @click="openPromptModal(msg.prompt_sent)">
  👁 Prompt
</button>

<!-- Zone diff (apres historique, avant input) -->
<div v-if="showDiff && lastDiff" class="diff-container">
  <details class="diff-accordion">
    <summary class="diff-summary-btn">
      📊 Modifications IA —
      <span class="diff-adds">+{{ lastDiffSummary?.adds }}</span>
      <span class="diff-removes">-{{ lastDiffSummary?.removes }}</span>
    </summary>
    <div class="diff-viewer">
      <div v-for="(line, i) in lastDiff" :key="i"
           :class="['diff-line', getDiffLineClass(line)]">
        <code>{{ line }}</code>
      </div>
    </div>
  </details>
  <div class="diff-actions">
    <button class="btn-apply-diff" @click="applyDiff">✅ Appliquer</button>
    <button class="btn-ignore-diff" @click="ignoreDiff">❌ Ignorer</button>
  </div>
</div>

<!-- Prompt Drawer (position: fixed, non bloquant) -->
<div v-if="showPromptModal" class="prompt-drawer">
  <div class="prompt-drawer-header">
    <span>👁 Prompt envoye</span>
    <button class="btn-close-drawer" @click="showPromptModal = false">✕</button>
  </div>
  <pre class="prompt-drawer-content">{{ lastPromptSent }}</pre>
</div>
```

### 5.5 CSS a ajouter

```css
/* === SCROLLBARS (pattern Sally) === */
.chat-history, .diff-viewer, .thinking-content, .prompt-drawer-content {
  scrollbar-width: thin;
  scrollbar-color: #00D4FF var(--color-surface, #1a1a2e);
}
.chat-history::-webkit-scrollbar,
.diff-viewer::-webkit-scrollbar,
.thinking-content::-webkit-scrollbar,
.prompt-drawer-content::-webkit-scrollbar { width: 8px; }
.chat-history::-webkit-scrollbar-track,
.diff-viewer::-webkit-scrollbar-track,
.thinking-content::-webkit-scrollbar-track,
.prompt-drawer-content::-webkit-scrollbar-track {
  background: var(--color-surface, #1a1a2e); border-radius: 4px;
}
.chat-history::-webkit-scrollbar-thumb,
.diff-viewer::-webkit-scrollbar-thumb,
.thinking-content::-webkit-scrollbar-thumb,
.prompt-drawer-content::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #00D4FF, rgba(0,212,255,0.5));
  border-radius: 4px;
}
.chat-history::-webkit-scrollbar-thumb:hover,
.diff-viewer::-webkit-scrollbar-thumb:hover,
.thinking-content::-webkit-scrollbar-thumb:hover,
.prompt-drawer-content::-webkit-scrollbar-thumb:hover {
  box-shadow: 0 0 6px rgba(0,212,255,0.5);
}

/* === CONNECTING INDICATOR === */
.connecting-indicator {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 12px; font-size: 12px; color: #888;
}
.connecting-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #00D4FF;
  animation: pulse-dot 1s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.7); }
}

/* === THINKING === */
.thinking-details {
  margin-top: 6px;
  border: 1px solid rgba(155,89,182,0.3); border-radius: 4px; overflow: hidden;
}
.thinking-summary {
  cursor: pointer; padding: 6px 10px; font-size: 12px;
  color: #9b59b6; background: rgba(155,89,182,0.1); user-select: none;
}
.thinking-content {
  max-height: 200px; overflow-y: auto; padding: 10px;
  font-size: 11px; color: #aaa; background: rgba(0,0,0,0.2);
  white-space: pre-wrap; margin: 0;
}

/* === DIFF === */
.diff-container {
  border: 1px solid rgba(0,212,255,0.2); border-radius: 6px;
  margin: 8px 0; overflow: hidden;
}
.diff-accordion > summary.diff-summary-btn {
  cursor: pointer; padding: 8px 12px; font-size: 12px;
  background: rgba(0,212,255,0.05); user-select: none;
  display: flex; align-items: center; gap: 8px;
}
.diff-adds { color: #00FF88; font-weight: bold; }
.diff-removes { color: #FF0055; font-weight: bold; }
.diff-viewer {
  max-height: 250px; overflow-y: auto;
  font-family: monospace; font-size: 11px;
}
.diff-line { padding: 1px 10px; white-space: pre; }
.diff-add { background: rgba(0,255,136,0.1); color: #00FF88; }
.diff-remove { background: rgba(255,0,85,0.1); color: #FF0055; }
.diff-meta-hunk { color: #00D4FF; background: rgba(0,212,255,0.05); }
.diff-meta-file { color: #888; }
.diff-context { color: #ccc; }
.diff-actions {
  display: flex; gap: 8px; padding: 8px 12px;
  border-top: 1px solid rgba(0,212,255,0.1);
}
.btn-apply-diff {
  background: rgba(0,255,136,0.15); color: #00FF88;
  border: 1px solid #00FF88; border-radius: 4px;
  padding: 4px 12px; cursor: pointer; font-size: 12px;
}
.btn-ignore-diff {
  background: rgba(255,0,85,0.1); color: #FF0055;
  border: 1px solid #FF0055; border-radius: 4px;
  padding: 4px 12px; cursor: pointer; font-size: 12px;
}

/* === PROMPT BUTTON === */
.btn-prompt-peek {
  margin-top: 4px; background: transparent; color: #888;
  border: 1px solid #333; border-radius: 3px;
  padding: 2px 8px; font-size: 11px; cursor: pointer;
}
.btn-prompt-peek:hover { color: #00D4FF; border-color: #00D4FF; }

/* === PROMPT DRAWER === */
.prompt-drawer {
  position: fixed; top: 60px; right: 0;
  width: 380px; height: calc(100vh - 60px);
  background: var(--color-surface, #1a1a2e);
  border-left: 1px solid rgba(0,212,255,0.3);
  z-index: 1000; display: flex; flex-direction: column;
  box-shadow: -4px 0 20px rgba(0,0,0,0.5);
}
.prompt-drawer-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-bottom: 1px solid rgba(0,212,255,0.2);
  font-size: 13px; color: #00D4FF;
}
.btn-close-drawer {
  background: transparent; border: none; color: #888;
  cursor: pointer; font-size: 16px; padding: 0 4px;
}
.btn-close-drawer:hover { color: #FF0055; }
.prompt-drawer-content {
  flex: 1; overflow-y: auto; padding: 16px;
  font-size: 11px; color: #aaa; white-space: pre-wrap;
  font-family: monospace; line-height: 1.5; margin: 0;
}
```

---

## Ordre d'execution

1. `strategies/services.py` — normalisation + extraction thinking + diff
2. `strategies/consumers.py` — NOUVEAU AIStreamConsumer
3. `aristobot/routing.py` — ajouter route `ws/ai-stream/`
4. `strategies/views.py` — passer `current_code` + retourner dict complet
5. `StrategiesView.vue` — tous les changements frontend
6. **Redemarrer Terminal 1 (Daphne)**

---

## Criteres d'acceptance

| # | Critere |
|---|---------|
| AC1 | `call_ai()` retourne toujours le dict normalise avec tous les champs |
| AC2 | Modele avec `<think>` (deepseek-r1, qwen3) : accordion Reflexion du modele visible |
| AC3 | Modele sans thinking : AUCUN accordion, AUCUN texte de remplacement |
| AC4 | `has_thinking=False` cote backend => `thinking_chunk` jamais emis |
| AC5 | Bouton [Prompt] sur chaque message assistant => ouvre drawer droit |
| AC6 | Drawer prompt non bloquant : editeur CodeMirror reste accessible |
| AC7 | Mode `continue` avec code existant : zone diff affichee si code modifie |
| AC8 | Mode `generate` (1er tour, code vide) : zone diff NON affichee |
| AC9 | Bouton Appliquer => code mis dans editeur, zone diff disparait |
| AC10 | Bouton Ignorer => code inchange dans editeur, zone diff disparait |
| AC11 | Label accordeon diff affiche +N / -N avant ouverture |
| AC12 | Lignes diff colorees : vert #00FF88 (add), rouge #FF0055 (remove), bleu #00D4FF (@@) |
| AC13 | Scrollbars 8px gradient #00D4FF sur chat-history, diff-viewer, thinking-content, prompt-drawer |
| AC14 | `prompt_sent` accessible via `msg.prompt_sent` dans historique visuel |
| AC15 | OpenRouter : champ `reasoning` ou `reasoning_content` lu selon modele |
| AC16 | Indicateur pulsant visible pendant la generation |
