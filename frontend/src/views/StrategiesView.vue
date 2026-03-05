<template>
  <div class="strategies-layout" ref="layoutEl">
    <!-- Zone 1 — Liste des stratégies (colonne gauche — largeur variable) -->
    <aside class="strategies-list">
      <div class="list-header">
        <h2 class="list-title">Strategies</h2>
        <button class="btn-primary" @click="newStrategy">+ Nouvelle</button>
      </div>

      <div v-if="loadingList" class="loading-text">Chargement...</div>
      <div v-else-if="strategies.length === 0" class="empty-text">
        Aucune strategie. Cliquez sur "+ Nouvelle".
      </div>
      <ul v-else class="strategy-items">
        <li
          v-for="s in strategies"
          :key="s.id"
          class="strategy-item"
          :class="{ active: selectedStrategy?.id === s.id }"
          @click="selectStrategy(s)"
        >
          <div class="strategy-item-name">{{ s.name }}</div>
          <div class="strategy-item-meta">
            <span class="badge-tf">{{ s.timeframe }}</span>
            <div class="strategy-item-actions" @click.stop>
              <button class="btn-icon" title="Editer" @click="editStrategy(s)">✎</button>
              <button class="btn-icon danger" title="Supprimer" @click="confirmDelete(s)">✕</button>
            </div>
          </div>
        </li>
      </ul>
    </aside>

    <!-- Strip gauche : entre liste et editeur -->
    <div
      class="col-strip col-strip--left"
      :class="{ 'col-strip--collapsed': !listOpen }"
      @mousedown.prevent="onStripMousedown('list', $event)"
      title="Cliquer pour reduire/agrandir - Glisser pour redimensionner"
    >
      <span class="strip-chevron">{{ listOpen ? '&#8249;' : '&#8250;' }}</span>
    </div>

    <!-- Zone 2 — Editeur de code (zone centrale — espace restant) -->
    <main class="editor-zone">
      <!-- Formulaire métadonnées -->
      <div class="editor-meta">
        <div class="meta-row">
          <div class="field-group">
            <label class="field-label">Nom de la strategie *</label>
            <input
              v-model="form.name"
              class="field-input"
              placeholder="Ex: EMA Cross 10/20"
              maxlength="100"
            />
          </div>
          <div class="field-group field-group--small">
            <label class="field-label">Timeframe *</label>
            <select v-model="form.timeframe" class="field-select">
              <option value="1m">1 minute</option>
              <option value="3m">3 minutes</option>
              <option value="5m">5 minutes</option>
              <option value="15m">15 minutes</option>
              <option value="1h">1 heure</option>
              <option value="4h">4 heures</option>
            </select>
          </div>
        </div>
        <div class="field-group">
          <label class="field-label">Description (optionnel)</label>
          <input
            v-model="form.description"
            class="field-input"
            placeholder="Breve description de la strategie..."
          />
        </div>
      </div>

      <!-- Éditeur CodeMirror -->
      <div class="editor-wrapper">
        <div class="editor-toolbar">
          <span class="editor-label">Code Python</span>
          <div class="editor-actions">
            <button class="btn-validate" :disabled="validating" @click="validateCode">
              {{ validating ? 'Validation...' : '&#10003; Tester syntaxe' }}
            </button>
            <button class="btn-extract" :disabled="extractLoading || !selectedStrategy" @click="extractParams">
              {{ extractLoading ? 'Analyse...' : '&#9881; Extraire les params' }}
            </button>
            <button class="btn-save" :disabled="saving" @click="saveStrategy">
              {{ saving ? 'Sauvegarde...' : 'Sauvegarder' }}
            </button>
          </div>
        </div>
        <div ref="editorContainer" class="codemirror-container"></div>
      </div>

      <!-- Résultat validation -->
      <div v-if="validationResult" class="validation-result" :class="validationResult.valid ? 'valid' : 'invalid'">
        <span v-if="validationResult.valid">✓ Code valide — la strategie est prete.</span>
        <span v-else>
          ✗ Code invalide :
          <ul class="error-list">
            <li v-for="err in validationResult.errors" :key="err">{{ err }}</li>
          </ul>
        </span>
      </div>

      <!-- Paramètres détectés (lecture seule — modifiables dans Backtest) -->
      <div v-if="validationResult?.valid && Object.keys(detectedParams).length > 0" class="params-detected">
        <div class="params-detected-header">
          <span class="params-detected-title">Parametres detectes (STRATEGY_PARAMS)</span>
          <span class="params-detected-hint">Modifiables dans l'ecran Backtest</span>
        </div>
        <div class="params-grid">
          <div v-for="(schema, key) in detectedParams" :key="key" class="param-row">
            <span class="param-label">
              <span class="param-key">{{ key }}</span>
              <span v-if="schema.label && schema.label !== key" class="param-label-sub">{{ schema.label }}</span>
            </span>
            <span class="param-meta">
              defaut: <strong>{{ schema.default }}</strong>
              <template v-if="schema.min !== undefined"> &nbsp;|&nbsp; min: {{ schema.min }}</template>
              <template v-if="schema.max !== undefined"> &nbsp;|&nbsp; max: {{ schema.max }}</template>
              <template v-if="schema.step !== undefined"> &nbsp;|&nbsp; step: {{ schema.step }}</template>
              &nbsp;|&nbsp; type: {{ schema.type ?? '?' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Message si code valide mais sans STRATEGY_PARAMS -->
      <div v-else-if="validationResult?.valid" class="params-detected params-detected--empty">
        <span class="params-detected-hint">
          Aucun STRATEGY_PARAMS defini. Ajoutez-en pour rendre les parametres configurables dans le Backtest.
        </span>
      </div>
    </main>

    <!-- Strip droit : entre editeur et panneau IA -->
    <div
      class="col-strip col-strip--right"
      :class="{ 'col-strip--collapsed': !aiOpen }"
      @mousedown.prevent="onStripMousedown('ai', $event)"
      title="Cliquer pour reduire/agrandir - Glisser pour redimensionner"
    >
      <span class="strip-chevron">{{ aiOpen ? '&#8250;' : '&#8249;' }}</span>
    </div>

    <!-- Zone 3 — Assistant IA (panneau lateral redimensionnable) -->
    <aside class="ia-panel">
      <div class="ia-content">
        <!-- Actions rapides Analyser / Decrire -->
        <div class="ia-quick-actions">
          <button class="btn-quick" :disabled="!code.trim() || iaLoading" @click="runAssist">Analyser</button>
          <button class="btn-quick" :disabled="!code.trim() || iaLoading" @click="runDescribe">Decrire</button>
          <button class="btn-reset-chat" @click="resetChat" title="Nouvelle conversation">↺</button>
        </div>

        <!-- Historique visuel du chat -->
        <div class="chat-history" ref="chatHistoryEl">
          <div v-if="chatMessages.length === 0 && !iaResult" class="chat-placeholder">
            Decris ta strategie en francais...<br>
            <small>Ex: RSI croisement 30/70 avec stop 2% et TP 4%</small>
          </div>
          <!-- Messages du chat iteratif -->
          <div v-for="(msg, i) in chatMessages" :key="i" :class="['chat-msg', 'chat-msg--' + msg.role]">
            <span class="chat-role">{{ msg.role === 'user' ? '👤' : '🤖' }}</span>
            <span class="chat-content">{{ msg.content }}</span>
          </div>
          <!-- Reponse rapide (Analyser / Decrire) -->
          <div v-if="iaResult && chatMessages.length === 0" class="ia-result">
            <div class="ia-result-header"><span>Reponse IA</span></div>
            <pre class="ia-result-text">{{ iaResult }}</pre>
          </div>
          <div v-if="chatLoading" class="chat-loading">⏳ Generation...</div>
          <div v-if="iaError" class="ia-error">{{ iaError }}</div>
        </div>

        <!-- Zone de saisie chat -->
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
    </aside>

    <!-- Modal confirmation suppression -->
    <div v-if="deleteConfirm" class="modal-overlay" @click.self="deleteConfirm = null">
      <div class="modal-box">
        <h3 class="modal-title">Supprimer la strategie ?</h3>
        <p class="modal-text">
          Cette action est irreversible. La strategie "<strong>{{ deleteConfirm.name }}</strong>" sera supprimee.
        </p>
        <div class="modal-actions">
          <button class="btn-cancel" @click="deleteConfirm = null">Annuler</button>
          <button class="btn-danger" @click="deleteStrategy">Supprimer</button>
        </div>
      </div>
    </div>

    <!-- Modal extraction des parametres -->
    <div v-if="showExtractModal" class="modal-overlay" @click.self="showExtractModal = false">
      <div
        class="extract-modal"
        :style="{ position: 'fixed', left: modalPos.x + 'px', top: modalPos.y + 'px', margin: 0 }"
      >
        <h3 class="modal-title modal-title--drag" @mousedown.prevent="startDrag">
          &#9881; Extraire les parametres
          <span class="drag-hint">&#8645;</span>
        </h3>

        <!-- Params existants — editables -->
        <div v-if="existingParams.length > 0" class="extract-section">
          <div class="extract-section-title">&#10003; Parametres existants (modifiables)</div>
          <div class="extract-table-header">
            <span>Contexte</span><span>Nom variable</span>
            <span>Def.</span><span>Min</span><span>Max</span>
            <span>Step</span><span>Type</span><span>Occur.</span>
          </div>
          <div v-for="(p, i) in existingParams" :key="'e'+i" class="extract-row extract-row--existing">
            <span class="extract-context extract-context--existing">existant</span>
            <input v-model="p.name" class="extract-input" />
            <input v-model.number="p.default" class="extract-input extract-input--num" />
            <input v-model.number="p.min"     class="extract-input extract-input--num" />
            <input v-model.number="p.max"     class="extract-input extract-input--num" />
            <input v-model.number="p.step"    class="extract-input extract-input--num" />
            <select v-model="p.type" class="extract-select">
              <option value="int">int</option>
              <option value="float">float</option>
            </select>
            <span class="extract-occ">—</span>
          </div>
        </div>

        <!-- Nouveaux litteraux detectes -->
        <div v-if="newLiterals.length > 0 || manualParams.length > 0" class="extract-section">
          <div v-if="existingParams.length > 0" class="extract-section-title extract-section-title--new">&#10024; Nouveaux litteraux detectes</div>
          <div class="extract-table-header">
            <span>Contexte</span><span>Nom variable</span>
            <span>Def.</span><span>Min</span><span>Max</span>
            <span>Step</span><span>Type</span><span>Occur.</span>
          </div>

          <!-- Lignes auto-detectees -->
          <div v-for="(p, i) in newLiterals" :key="i" class="extract-row">
            <span class="extract-context extract-context--tip" :data-tip="p.context_full || p.context">
              <span v-if="p.lineno" class="extract-lineno">L.{{ p.lineno }}</span>{{ p.context }}
            </span>
            <input v-model="p.name" class="extract-input" />
            <input v-model.number="p.default" class="extract-input extract-input--num" />
            <input v-model.number="p.min"     class="extract-input extract-input--num" />
            <input v-model.number="p.max"     class="extract-input extract-input--num" />
            <input v-model.number="p.step"    class="extract-input extract-input--num" />
            <select v-model="p.type" class="extract-select">
              <option value="int">int</option>
              <option value="float">float</option>
            </select>
            <span class="extract-occ">x{{ p.occurrences }}</span>
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
            <span class="extract-occ extract-occ--warn" title="Aucun litteral a remplacer — sera ajoute a STRATEGY_PARAMS uniquement">&#9888;</span>
          </div>
        </div>

        <!-- Aucun param du tout -->
        <div v-if="newLiterals.length === 0 && manualParams.length === 0 && existingParams.length === 0" class="no-new">
          Aucun litteral numerique detecte et aucun STRATEGY_PARAMS existant.
        </div>

        <!-- Aucun nouveau (mais existants presents) -->
        <div v-else-if="newLiterals.length === 0 && manualParams.length === 0 && existingParams.length > 0" class="no-new">
          Aucun nouveau litteral numerique detecte. Modifiez les parametres existants ci-dessus si necessaire.
        </div>

        <button class="btn-add-manual" @click="addManualParam">+ Ajouter manuellement</button>

        <div class="modal-actions">
          <button class="btn-cancel" @click="showExtractModal = false">Annuler</button>
          <button class="btn-primary" @click="applyParams"
                  :disabled="newLiterals.length === 0 && existingParams.length === 0 && manualParams.filter(p => p.name).length === 0">
            Appliquer au code
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import api from '../api/index.js'
import { useCodeMirror } from '../composables/useCodeMirror.js'
import { useAuthStore } from '../stores/auth.js'

const authStore = useAuthStore()

// ─── Constantes layout redimensionnable ──────────────────────────────────────
const LIST_MIN = 180
const LIST_MAX = 420
const LIST_DEFAULT = 260
const AI_MIN = 260
const AI_MAX = 500
const AI_DEFAULT = 340
const LS_KEY = 'strategies_layout'
const DRAG_THRESHOLD = 3

// ─── Refs layout ──────────────────────────────────────────────────────────────
const layoutEl = ref(null)
const listWidth = ref(LIST_DEFAULT)
const aiWidth = ref(AI_DEFAULT)
const listOpen = ref(true)
const aiOpen = ref(true)

// ─── Fonctions layout ─────────────────────────────────────────────────────────

let _rafPending = false

function notifyCodeMirror() {
  if (_rafPending) return
  _rafPending = true
  requestAnimationFrame(() => {
    _rafPending = false
    if (editorView.value) {
      editorView.value.requestMeasure()
    }
  })
}

function applyWidths() {
  if (!layoutEl.value) return
  const lw = listOpen.value ? listWidth.value : 0
  const aw = aiOpen.value ? aiWidth.value : 0
  layoutEl.value.style.setProperty('--list-width', lw + 'px')
  layoutEl.value.style.setProperty('--ai-width', aw + 'px')
  notifyCodeMirror()
}

function loadLayout() {
  try {
    const saved = localStorage.getItem(LS_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      listWidth.value = parsed.listWidth ?? LIST_DEFAULT
      aiWidth.value = parsed.aiWidth ?? AI_DEFAULT
      listOpen.value = parsed.listOpen ?? true
      aiOpen.value = parsed.aiOpen ?? true
    }
  } catch (e) {
    // Silencieux — utiliser les valeurs par defaut
  }
  applyWidths()
}

function saveLayout() {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify({
      listWidth: listWidth.value,
      aiWidth: aiWidth.value,
      listOpen: listOpen.value,
      aiOpen: aiOpen.value,
    }))
  } catch (e) {
    // Silencieux — espace insuffisant ou mode prive
  }
}

function toggleColumn(column) {
  // Activer la transition CSS pour l'animation de collapse
  if (layoutEl.value) layoutEl.value.classList.add('is-transitioning')

  if (column === 'list') {
    listOpen.value = !listOpen.value
    if (listOpen.value && listWidth.value < LIST_MIN) listWidth.value = LIST_DEFAULT
  } else {
    aiOpen.value = !aiOpen.value
    if (aiOpen.value && aiWidth.value < AI_MIN) aiWidth.value = AI_DEFAULT
  }
  applyWidths()
  notifyCodeMirror()
  saveLayout()

  // Retirer la transition apres son execution (250ms + 30ms de marge)
  setTimeout(() => {
    if (layoutEl.value) layoutEl.value.classList.remove('is-transitioning')
  }, 280)
}

function onStripMousedown(column, event) {
  const startX = event.clientX
  const startWidth = column === 'list' ? listWidth.value : aiWidth.value
  let didDrag = false

  function onMousemove(e) {
    const dx = e.clientX - startX

    if (Math.abs(dx) >= DRAG_THRESHOLD) {
      didDrag = true
    }

    if (didDrag) {
      let newWidth
      if (column === 'list') {
        // Strip gauche : glisser a droite elargit la liste
        newWidth = Math.max(LIST_MIN, Math.min(LIST_MAX, startWidth + dx))
        listWidth.value = newWidth
        if (newWidth > 0 && !listOpen.value) {
          listOpen.value = true
        }
      } else {
        // Strip droit : glisser a gauche elargit le panneau IA
        newWidth = Math.max(AI_MIN, Math.min(AI_MAX, startWidth - dx))
        aiWidth.value = newWidth
        if (newWidth > 0 && !aiOpen.value) {
          aiOpen.value = true
        }
      }
      applyWidths()
      notifyCodeMirror()
    }
  }

  function onMouseup() {
    document.removeEventListener('mousemove', onMousemove)
    document.removeEventListener('mouseup', onMouseup)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''

    if (!didDrag) {
      // C'est un clic — toggler le collapse
      toggleColumn(column)
    } else {
      // Fin de drag — sauvegarder
      saveLayout()
    }
  }

  document.addEventListener('mousemove', onMousemove)
  document.addEventListener('mouseup', onMouseup)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

// ─── Template de base ────────────────────────────────────────────────────────
const BASE_TEMPLATE = `import pandas_ta as ta

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
`

// ─── Refs état ────────────────────────────────────────────────────────────────
const strategies = ref([])
const selectedStrategy = ref(null)
const loadingList = ref(false)
const saving = ref(false)
const validating = ref(false)
const validationResult = ref(null)
const detectedParams = ref({})
const deleteConfirm = ref(null)

// ─── Extract Params (Patch M5 v2) ─────────────────────────────────────────────
const showExtractModal = ref(false)
const extractLoading = ref(false)

// ─── Drag modale ──────────────────────────────────────────────────────────────
const modalPos = ref({ x: 0, y: 0 })
const _dragOffset = { x: 0, y: 0 }
let _dragActive = false

function _initModalPos() {
  const w = Math.min(900, window.innerWidth * 0.95)
  modalPos.value = {
    x: Math.round((window.innerWidth - w) / 2),
    y: Math.round(window.innerHeight * 0.08),
  }
}

function startDrag(e) {
  _dragActive = true
  _dragOffset.x = e.clientX - modalPos.value.x
  _dragOffset.y = e.clientY - modalPos.value.y
  document.addEventListener('mousemove', _onDrag)
  document.addEventListener('mouseup', _stopDrag)
}

function _onDrag(e) {
  if (!_dragActive) return
  modalPos.value = {
    x: Math.max(0, Math.min(window.innerWidth - 120, e.clientX - _dragOffset.x)),
    y: Math.max(0, Math.min(window.innerHeight - 60, e.clientY - _dragOffset.y)),
  }
}

function _stopDrag() {
  _dragActive = false
  document.removeEventListener('mousemove', _onDrag)
  document.removeEventListener('mouseup', _stopDrag)
}
const newLiterals = ref([])
const alreadyParameterized = ref([])
const existingParams = ref([])
const manualParams = ref([])

const form = ref({ name: '', timeframe: '15m', description: '' })

// ─── CodeMirror ──────────────────────────────────────────────────────────────
const editorContainer = ref(null)
const { code, setCode, mount, editorView } = useCodeMirror(editorContainer, BASE_TEMPLATE)

// ─── IA ──────────────────────────────────────────────────────────────────────
const iaResult = ref('')
const iaError = ref('')
const iaLoading = ref(false)

// Chat iteratif
const chatMessages = ref([])  // [{role: 'user'|'assistant', content: string}]
const chatInput = ref('')
const chatLoading = ref(false)
const chatHistoryEl = ref(null)

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  loadLayout()          // 1. Charger et appliquer le layout persiste
  await loadStrategies() // 2. Charger les donnees
  await nextTick()
  mount()               // 3. Monter CodeMirror apres que le DOM est stable
})

// Reset validation et params detectes quand le code change
watch(code, () => { validationResult.value = null; detectedParams.value = {} })

// Reset chat quand on change de strategie
watch(selectedStrategy, () => { resetChat() })

// ─── Actions liste ────────────────────────────────────────────────────────────
async function loadStrategies() {
  loadingList.value = true
  try {
    const resp = await api.get('/api/strategies/')
    strategies.value = resp.data.results ?? resp.data
  } catch (e) {
    console.error('Erreur chargement strategies:', e)
  } finally {
    loadingList.value = false
  }
}

function newStrategy() {
  selectedStrategy.value = null
  form.value = { name: '', timeframe: '15m', description: '' }
  setCode(BASE_TEMPLATE)
  validationResult.value = null
  detectedParams.value = {}
  resetChat()
}

function selectStrategy(s) {
  selectedStrategy.value = s
  form.value = { name: s.name, timeframe: s.timeframe, description: s.description || '' }
  setCode(s.code)
  validationResult.value = null
  detectedParams.value = {}
  // resetChat() est appele par watch(selectedStrategy)
}

function editStrategy(s) {
  selectStrategy(s)
}

function confirmDelete(s) {
  deleteConfirm.value = s
}

async function deleteStrategy() {
  if (!deleteConfirm.value) return
  try {
    await api.delete(`/api/strategies/${deleteConfirm.value.id}/`)
    if (selectedStrategy.value?.id === deleteConfirm.value.id) {
      newStrategy()
    }
    deleteConfirm.value = null
    await loadStrategies()
  } catch (e) {
    console.error('Erreur suppression:', e)
  }
}

// ─── Validation & Sauvegarde ──────────────────────────────────────────────────
async function validateCode() {
  if (!selectedStrategy.value) {
    validationResult.value = { valid: false, errors: ['Sauvegardez la strategie avant de la valider.'] }
    return
  }
  validating.value = true
  validationResult.value = null
  detectedParams.value = {}
  try {
    const resp = await api.post(`/api/strategies/${selectedStrategy.value.id}/validate_code/`, {
      code: code.value,
    })
    validationResult.value = resp.data
    detectedParams.value = resp.data.params_schema ?? {}
  } catch (e) {
    validationResult.value = { valid: false, errors: ['Erreur de communication avec le serveur.'] }
  } finally {
    validating.value = false
  }
}

async function saveStrategy() {
  if (!form.value.name.trim()) {
    alert('Le nom de la strategie est obligatoire.')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      timeframe: form.value.timeframe,
      description: form.value.description,
      code: code.value,
    }
    if (selectedStrategy.value) {
      const resp = await api.patch(`/api/strategies/${selectedStrategy.value.id}/`, payload)
      selectedStrategy.value = resp.data
    } else {
      const resp = await api.post('/api/strategies/', payload)
      selectedStrategy.value = resp.data
    }
    await loadStrategies()
  } catch (e) {
    console.error('Erreur sauvegarde:', e)
    alert('Erreur lors de la sauvegarde. Verifiez les champs obligatoires.')
  } finally {
    saving.value = false
  }
}

// ─── Assistant IA — Chat iteratif ─────────────────────────────────────────────
async function sendChatMessage() {
  const message = chatInput.value.trim()
  if (!message || chatLoading.value) return

  const isFirstTurn = chatMessages.value.length === 0
  const currentCode = code.value

  chatMessages.value.push({ role: 'user', content: message })
  chatInput.value = ''
  chatLoading.value = true
  iaError.value = ''
  iaResult.value = ''

  await nextTick()
  scrollChatToBottom()

  try {
    const resp = await api.post('/api/strategies/ai-assist/', {
      mode: 'chat',
      description: message,
      code: currentCode,
      is_first_turn: isFirstTurn,
    })

    const result = resp.data.result
    chatMessages.value.push({ role: 'assistant', content: result })

    // Si la reponse contient du code Python → l'injecter dans l'editeur
    const codeMatch = result.match(/```python\n?([\s\S]*?)```/)
    if (codeMatch) {
      setCode(codeMatch[1].trim())
    } else if (result.includes('class ') && result.includes('Strategy')) {
      setCode(result.trim())
    }

    validationResult.value = null
    detectedParams.value = {}

  } catch (e) {
    const msg = e.response?.data?.error || 'Erreur lors de l\'appel IA.'
    chatMessages.value.push({ role: 'assistant', content: 'Erreur : ' + msg })
  } finally {
    chatLoading.value = false
    await nextTick()
    scrollChatToBottom()
  }
}

function resetChat() {
  chatMessages.value = []
  chatInput.value = ''
  iaResult.value = ''
  iaError.value = ''
}

function scrollChatToBottom() {
  if (chatHistoryEl.value) {
    chatHistoryEl.value.scrollTop = chatHistoryEl.value.scrollHeight
  }
}

// Boutons rapides Analyser / Decrire (non-chat, reponse dans iaResult)
async function runAssist() {
  iaError.value = ''
  iaResult.value = ''
  iaLoading.value = true
  try {
    const resp = await api.post('/api/strategies/ai-assist/', { mode: 'assist', code: code.value })
    iaResult.value = resp.data.result
    chatMessages.value = []  // vider le chat pour afficher la reponse rapide
  } catch (e) {
    iaError.value = e.response?.data?.error || 'Erreur lors de l\'analyse.'
  } finally {
    iaLoading.value = false
  }
}

async function runDescribe() {
  iaError.value = ''
  iaResult.value = ''
  iaLoading.value = true
  try {
    const resp = await api.post('/api/strategies/ai-assist/', { mode: 'describe', code: code.value })
    iaResult.value = resp.data.result
    chatMessages.value = []  // vider le chat pour afficher la reponse rapide
  } catch (e) {
    iaError.value = e.response?.data?.error || 'Erreur lors de la description.'
  } finally {
    iaLoading.value = false
  }
}

// ─── Extract Params (Patch M5 v2) ─────────────────────────────────────────────
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
      context_full: p.context_full,
      lineno: p.lineno,
      occurrences: p.occurrences,
    }))
    alreadyParameterized.value = resp.data.already_parameterized
    existingParams.value = (resp.data.existing_params || []).map(p => ({
      ...p,
      original_name: p.name,  // tracker le nom original pour detecter les renommages
    }))
    manualParams.value = []
    _initModalPos()
    showExtractModal.value = true
  } catch (e) {
    console.error('Erreur extract-params:', e)
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
    ...existingParams.value,
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
</script>

<style scoped>
/* ─── Layout principal — CSS Grid 5 colonnes ───────────────────────────────── */
.strategies-layout {
  --list-width: 260px;
  --ai-width: 340px;

  display: grid;
  grid-template-columns:
    var(--list-width)
    8px
    1fr
    8px
    var(--ai-width);
  grid-template-rows: 100%;
  height: 100%;
  background: #0a0a1a;
  color: #c0c0d0;
  overflow: hidden;
}

/* Transition activee seulement lors du toggle collapse (pas pendant le drag) */
.strategies-layout.is-transitioning {
  transition: grid-template-columns 0.25s ease;
}

/* ─── Colonne liste ─────────────────────────────────────────────────────────── */
.strategies-list {
  grid-column: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  border-right: none;
}

/* ─── Strips de controle ───────────────────────────────────────────────────── */
.col-strip {
  height: 100%;
  width: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: col-resize;
  background: rgba(0, 212, 255, 0.04);
  border-left: 1px solid rgba(0, 212, 255, 0.08);
  border-right: 1px solid rgba(0, 212, 255, 0.08);
  transition: background 0.15s, box-shadow 0.15s;
  user-select: none;
  position: relative;
  z-index: 10;
  flex-shrink: 0;
}

.col-strip--left  { grid-column: 2; }
.col-strip--right { grid-column: 4; }

.col-strip:hover {
  background: rgba(0, 212, 255, 0.1);
  box-shadow: 0 0 6px #00D4FF;
}

.col-strip--collapsed {
  background: rgba(0, 212, 255, 0.07);
}

.col-strip--collapsed:hover {
  background: rgba(0, 212, 255, 0.15);
  box-shadow: 0 0 6px #00D4FF;
}

.strip-chevron {
  font-size: 10px;
  color: rgba(0, 212, 255, 0.5);
  line-height: 1;
  pointer-events: none;
  transition: color 0.15s;
}

.col-strip:hover .strip-chevron {
  color: #00D4FF;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
}

.list-title {
  font-size: 1rem;
  font-weight: 600;
  color: #00D4FF;
  margin: 0;
}

.strategy-items {
  list-style: none;
  margin: 0;
  padding: 0.5rem;
  overflow-y: auto;
  flex: 1;
}

.strategy-item {
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 0.25rem;
  border: 1px solid transparent;
  transition: background 0.15s, border-color 0.15s;
}

.strategy-item:hover {
  background: rgba(0, 212, 255, 0.05);
  border-color: rgba(0, 212, 255, 0.15);
}

.strategy-item.active {
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.35);
}

.strategy-item-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #e0e0f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.strategy-item-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.25rem;
}

.badge-tf {
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  background: rgba(0, 212, 255, 0.1);
  color: #00D4FF;
  border-radius: 4px;
  font-family: monospace;
}

.strategy-item-actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.15s;
}

.strategy-item:hover .strategy-item-actions {
  opacity: 1;
}

.loading-text, .empty-text {
  padding: 1.5rem 1rem;
  color: rgba(192, 192, 208, 0.5);
  font-size: 0.85rem;
  text-align: center;
}

/* ─── Colonne editeur (centre — prend tout l'espace restant) ─────────────── */
.editor-zone {
  grid-column: 3;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.editor-meta {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.meta-row {
  display: flex;
  gap: 1rem;
}

.field-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.field-group--small {
  flex: 0 0 140px;
}

.field-label {
  font-size: 0.72rem;
  color: rgba(192, 192, 208, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.field-input, .field-select {
  background: rgba(0, 0, 30, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  color: #e0e0f0;
  padding: 0.35rem 0.6rem;
  font-size: 0.85rem;
  outline: none;
}

.field-input:focus, .field-select:focus {
  border-color: rgba(0, 212, 255, 0.5);
}

.field-select {
  cursor: pointer;
}

/* ─── CodeMirror ───────────────────────────────────────────────────────────── */
.editor-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  background: rgba(0, 0, 30, 0.4);
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
}

.editor-label {
  font-size: 0.75rem;
  color: rgba(192, 192, 208, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.editor-actions {
  display: flex;
  gap: 0.5rem;
}

.codemirror-container {
  flex: 1;
  overflow: hidden;
}

.codemirror-container :deep(.cm-editor) {
  height: 100%;
}

/* ─── Validation ───────────────────────────────────────────────────────────── */
.validation-result {
  padding: 0.6rem 1rem;
  font-size: 0.82rem;
  border-top: 1px solid rgba(0, 212, 255, 0.1);
}

.validation-result.valid {
  color: #00FF88;
  background: rgba(0, 255, 136, 0.05);
}

.validation-result.invalid {
  color: #FF0055;
  background: rgba(255, 0, 85, 0.05);
}

.error-list {
  margin: 0.25rem 0 0 1rem;
  padding: 0;
}

/* ─── Colonne IA (droite — largeur variable) ────────────────────────────── */
.ia-panel {
  grid-column: 5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  border-left: none;
}

.ia-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

/* ─── Actions rapides Analyser / Decrire ─────────────────────────────────── */
.ia-quick-actions {
  display: flex;
  gap: 0.35rem;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
  align-items: center;
}

.btn-quick {
  flex: 1;
  padding: 0.3rem 0.4rem;
  font-size: 0.72rem;
  background: transparent;
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 4px;
  color: rgba(192, 192, 208, 0.7);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.btn-quick:hover:not(:disabled) {
  border-color: rgba(0, 212, 255, 0.5);
  color: #00D4FF;
  background: rgba(0, 212, 255, 0.06);
}

.btn-quick:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-reset-chat {
  background: transparent;
  border: 1px solid rgba(192, 192, 208, 0.2);
  border-radius: 4px;
  color: rgba(192, 192, 208, 0.5);
  cursor: pointer;
  padding: 0.3rem 0.45rem;
  font-size: 0.85rem;
  transition: color 0.15s, border-color 0.15s;
}

.btn-reset-chat:hover {
  color: #00D4FF;
  border-color: rgba(0, 212, 255, 0.4);
}

/* ─── Historique chat ─────────────────────────────────────────────────────── */
.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 0.6rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.chat-placeholder {
  color: rgba(192, 192, 208, 0.35);
  font-size: 0.8rem;
  text-align: center;
  padding: 1.5rem 0.5rem;
  line-height: 1.6;
}

.chat-placeholder small {
  font-size: 0.72rem;
  color: rgba(192, 192, 208, 0.25);
}

.chat-msg {
  display: flex;
  gap: 0.4rem;
  font-size: 0.78rem;
  line-height: 1.5;
  align-items: flex-start;
}

.chat-msg--user {
  flex-direction: row-reverse;
}

.chat-role {
  flex-shrink: 0;
  font-size: 0.85rem;
}

.chat-content {
  padding: 0.35rem 0.55rem;
  border-radius: 6px;
  max-width: 90%;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-msg--user .chat-content {
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  color: #c8e8ff;
}

.chat-msg--assistant .chat-content {
  background: rgba(0, 0, 30, 0.5);
  border: 1px solid rgba(192, 192, 208, 0.1);
  color: #c0c0d0;
  font-family: "Fira Code", "Consolas", monospace;
  font-size: 0.73rem;
}

.chat-loading {
  color: rgba(0, 212, 255, 0.5);
  font-size: 0.78rem;
  text-align: center;
  padding: 0.4rem 0;
}

/* ─── Zone saisie chat ────────────────────────────────────────────────────── */
.chat-input-area {
  border-top: 1px solid rgba(0, 212, 255, 0.1);
  padding: 0.5rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.chat-textarea {
  background: rgba(0, 0, 30, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  color: #e0e0f0;
  padding: 0.5rem;
  font-size: 0.8rem;
  resize: none;
  outline: none;
  font-family: inherit;
  width: 100%;
  box-sizing: border-box;
}

.chat-textarea:focus {
  border-color: rgba(0, 212, 255, 0.5);
}

.chat-textarea:disabled {
  opacity: 0.5;
}

.btn-send {
  background: rgba(0, 212, 255, 0.12);
  border: 1px solid rgba(0, 212, 255, 0.35);
  color: #00D4FF;
  padding: 0.35rem 0.7rem;
  border-radius: 4px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: background 0.15s;
  align-self: flex-end;
}

.btn-send:hover:not(:disabled) {
  background: rgba(0, 212, 255, 0.22);
}

.btn-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.chat-hint {
  font-size: 0.65rem;
  color: rgba(192, 192, 208, 0.25);
}

/* ─── Reponse rapide (Analyser / Decrire) ────────────────────────────────── */
.ia-result {
  background: rgba(0, 0, 30, 0.5);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 6px;
  overflow: hidden;
}

.ia-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 0.6rem;
  background: rgba(0, 212, 255, 0.05);
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
  font-size: 0.72rem;
  color: rgba(192, 192, 208, 0.6);
}

.ia-result-text {
  margin: 0;
  padding: 0.6rem;
  font-size: 0.78rem;
  font-family: "Fira Code", "Consolas", monospace;
  white-space: pre-wrap;
  color: #c0c0d0;
  max-height: 350px;
  overflow-y: auto;
}

.ia-error {
  padding: 0.5rem;
  background: rgba(255, 0, 85, 0.08);
  border: 1px solid rgba(255, 0, 85, 0.3);
  border-radius: 4px;
  color: #FF0055;
  font-size: 0.82rem;
}

/* ─── Boutons ──────────────────────────────────────────────────────────────── */
.btn-primary {
  background: rgba(0, 212, 255, 0.15);
  border: 1px solid rgba(0, 212, 255, 0.4);
  color: #00D4FF;
  padding: 0.3rem 0.7rem;
  border-radius: 4px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-primary:hover {
  background: rgba(0, 212, 255, 0.25);
}

.btn-icon {
  background: transparent;
  border: none;
  color: rgba(192, 192, 208, 0.5);
  cursor: pointer;
  padding: 0.1rem 0.3rem;
  font-size: 0.85rem;
  border-radius: 3px;
  transition: color 0.15s, background 0.15s;
}

.btn-icon:hover {
  color: #00D4FF;
  background: rgba(0, 212, 255, 0.1);
}

.btn-icon.danger:hover {
  color: #FF0055;
  background: rgba(255, 0, 85, 0.1);
}

.btn-validate {
  background: transparent;
  border: 1px solid rgba(0, 255, 136, 0.3);
  color: #00FF88;
  padding: 0.3rem 0.7rem;
  border-radius: 4px;
  font-size: 0.78rem;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-validate:hover:not(:disabled) {
  background: rgba(0, 255, 136, 0.1);
}

.btn-validate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-save {
  background: rgba(0, 212, 255, 0.15);
  border: 1px solid rgba(0, 212, 255, 0.4);
  color: #00D4FF;
  padding: 0.3rem 0.7rem;
  border-radius: 4px;
  font-size: 0.78rem;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-save:hover:not(:disabled) {
  background: rgba(0, 212, 255, 0.25);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-ia {
  background: rgba(0, 212, 255, 0.12);
  border: 1px solid rgba(0, 212, 255, 0.35);
  color: #00D4FF;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: background 0.15s;
  width: 100%;
}

.btn-ia:hover:not(:disabled) {
  background: rgba(0, 212, 255, 0.22);
}

.btn-ia:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-insert {
  background: transparent;
  border: 1px solid rgba(0, 255, 136, 0.3);
  color: #00FF88;
  padding: 0.15rem 0.5rem;
  border-radius: 3px;
  font-size: 0.72rem;
  cursor: pointer;
}

.btn-insert:hover {
  background: rgba(0, 255, 136, 0.08);
}

/* ─── Modal ────────────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-box {
  background: #0d0d2a;
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 8px;
  padding: 1.5rem;
  max-width: 400px;
  width: 90%;
}

.modal-title {
  color: #00D4FF;
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
}

.modal-text {
  font-size: 0.85rem;
  color: rgba(192, 192, 208, 0.8);
  margin: 0 0 1rem 0;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.btn-cancel {
  background: transparent;
  border: 1px solid rgba(192, 192, 208, 0.3);
  color: rgba(192, 192, 208, 0.7);
  padding: 0.4rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-danger {
  background: rgba(255, 0, 85, 0.15);
  border: 1px solid rgba(255, 0, 85, 0.4);
  color: #FF0055;
  padding: 0.4rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-danger:hover {
  background: rgba(255, 0, 85, 0.25);
}

.btn-cancel:hover {
  border-color: rgba(192, 192, 208, 0.5);
}

/* ─── Panneau Parametres detectes (Patch M5) ─────────────────────────────── */
.params-detected {
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(0, 212, 255, 0.04);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 6px;
}

.params-detected--empty {
  background: rgba(192, 192, 208, 0.03);
  border-color: rgba(192, 192, 208, 0.12);
}

.params-detected-header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 0.6rem;
}

.params-detected-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #00D4FF;
  font-family: monospace;
}

.params-detected-hint {
  font-size: 0.72rem;
  color: rgba(192, 192, 208, 0.5);
  font-style: italic;
}

.params-grid {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.param-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.78rem;
}

.param-label {
  min-width: 140px;
  display: flex;
  flex-direction: column;
}

.param-meta {
  color: rgba(192, 192, 208, 0.65);
  font-family: monospace;
}

.param-meta strong {
  color: #00FF88;
}

/* ─── Bouton Extraire les params ────────────────────────────────────────────── */
.btn-extract {
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid #00d4ff;
  color: #00d4ff;
  padding: 0.3rem 0.7rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.78rem;
  transition: background 0.2s;
}

.btn-extract:hover:not(:disabled) {
  background: rgba(0, 212, 255, 0.2);
}

.btn-extract:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ─── Modal extraction ──────────────────────────────────────────────────────── */
.extract-modal {
  background: #1a1a2e;
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 8px;
  padding: 24px;
  max-width: 900px;
  width: 95vw;
  max-height: 80vh;
  overflow-y: auto;
  /* Le positionnement fixed est appliqué inline via :style */
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
}

.modal-title--drag {
  cursor: grab;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.modal-title--drag:active {
  cursor: grabbing;
}

.drag-hint {
  font-size: 1.1rem;
  opacity: 0.4;
  font-style: normal;
  margin-left: auto;
}

/* ─── Deja parametres ───────────────────────────────────────────────────────── */
.already-params {
  background: rgba(0, 255, 136, 0.08);
  border: 1px solid rgba(0, 255, 136, 0.2);
  border-radius: 4px;
  padding: 8px 12px;
  margin-bottom: 16px;
  font-size: 12px;
  color: #00ff88;
}

.already-label {
  font-weight: 600;
}

.already-names {
  color: rgba(255, 255, 255, 0.7);
  margin-left: 8px;
}

/* ─── Sections de la modale extraction ─────────────────────────────────────── */
.extract-section {
  margin-bottom: 16px;
}

.extract-section-title {
  font-size: 12px;
  font-weight: 600;
  color: #00FF88;
  margin-bottom: 8px;
  padding: 4px 6px;
  border-left: 2px solid rgba(0, 255, 136, 0.4);
}

.extract-section-title--new {
  color: #00D4FF;
  border-left-color: rgba(0, 212, 255, 0.4);
}

/* ─── Lignes existantes ──────────────────────────────────────────────────────── */
.extract-row--existing {
  background: rgba(0, 255, 136, 0.04);
}

.extract-row--existing:hover {
  background: rgba(0, 255, 136, 0.08);
}

.extract-context--existing {
  color: rgba(0, 255, 136, 0.7);
  font-style: italic;
  font-family: inherit;
}

/* ─── Cle de parametre dans le panneau detectes ─────────────────────────────── */
.param-key {
  font-family: "Fira Code", "Consolas", monospace;
  color: #e0e0f0;
  font-weight: 600;
}

.param-label-sub {
  display: block;
  font-size: 0.68rem;
  color: rgba(192, 192, 208, 0.45);
  font-style: italic;
  font-weight: 400;
  font-family: inherit;
  margin-top: 1px;
}

/* ─── Aucun nouveau ─────────────────────────────────────────────────────────── */
.no-new {
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  padding: 24px;
  font-size: 0.85rem;
}

/* ─── En-tete du tableau ────────────────────────────────────────────────────── */
.extract-table-header {
  display: grid;
  grid-template-columns: 2fr 1.5fr 0.5fr 0.5fr 0.5fr 0.5fr 0.6fr 0.4fr;
  gap: 6px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
  text-transform: uppercase;
  padding: 4px 6px;
  margin-bottom: 4px;
}

/* ─── Lignes ────────────────────────────────────────────────────────────────── */
.extract-row {
  display: grid;
  grid-template-columns: 2fr 1.5fr 0.5fr 0.5fr 0.5fr 0.5fr 0.6fr 0.4fr;
  gap: 6px;
  align-items: center;
  padding: 4px 6px;
  border-radius: 4px;
  margin-bottom: 3px;
}

.extract-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.extract-row--manual {
  background: rgba(255, 165, 0, 0.05);
}

/* ─── Inputs de la grille ───────────────────────────────────────────────────── */
.extract-input {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 3px;
  color: #fff;
  padding: 3px 6px;
  font-size: 12px;
  width: 100%;
  outline: none;
}

.extract-input:focus {
  border-color: rgba(0, 212, 255, 0.5);
}

.extract-input--num {
  text-align: right;
}

.extract-select {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 3px;
  color: #fff;
  padding: 3px 4px;
  font-size: 12px;
  width: 100%;
  outline: none;
  cursor: pointer;
}

/* ─── Colonne contexte ──────────────────────────────────────────────────────── */
.extract-context {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: "Fira Code", "Consolas", monospace;
}

.extract-context--manual {
  color: rgba(255, 165, 0, 0.7);
  font-style: italic;
  font-family: inherit;
}

/* ─── Numéro de ligne ───────────────────────────────────────────────────────── */
.extract-lineno {
  color: #ffaa00;
  font-size: 10px;
  font-weight: bold;
  margin-right: 0.35rem;
  flex-shrink: 0;
}

/* ─── Tooltip custom (remplace title HTML) ──────────────────────────────────── */
.extract-context--tip {
  position: relative;
  cursor: help;
  display: flex;
  align-items: center;
}

.extract-context--tip::after {
  content: attr(data-tip);
  position: absolute;
  left: 0;
  bottom: calc(100% + 6px);
  background: #0d1f2d;
  border: 1px solid rgba(0, 212, 255, 0.35);
  color: #d0e8ff;
  font-size: 11px;
  font-family: "Fira Code", "Consolas", monospace;
  padding: 0.45rem 0.65rem;
  border-radius: 5px;
  white-space: pre-wrap;
  word-break: break-all;
  min-width: 220px;
  max-width: 420px;
  z-index: 9999;
  display: none;
  box-shadow: 0 4px 16px rgba(0,0,0,0.5);
  line-height: 1.5;
}

.extract-context--tip:hover::after {
  display: block;
}

/* ─── Colonne occurrences ───────────────────────────────────────────────────── */
.extract-occ {
  color: rgba(255, 255, 255, 0.4);
  font-size: 11px;
  text-align: center;
}

.extract-occ--warn {
  color: #ff8800;
  font-size: 14px;
  cursor: help;
}

/* ─── Bouton ajout manuel ───────────────────────────────────────────────────── */
.btn-add-manual {
  background: transparent;
  border: 1px dashed rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.5);
  padding: 6px 14px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-top: 10px;
  width: 100%;
  transition: border-color 0.2s, color 0.2s;
}

.btn-add-manual:hover {
  border-color: #00d4ff;
  color: #00d4ff;
}
</style>
