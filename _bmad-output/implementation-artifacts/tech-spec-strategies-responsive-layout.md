# Tech-Spec : Responsive Layout StrategiesView — Colonnes redimensionnables avec strips de contrôle

**Auteure** : Sally, UX Designer senior
**Date** : 2026-03-04
**Statut** : `ready-for-dev`
**Fichier cible** : `frontend/src/views/StrategiesView.vue`
**Services à redémarrer** : Terminal 4 (Vite — `npm run dev`) uniquement

---

## 1. Vue d'ensemble et objectif

### Problème actuel

`StrategiesView.vue` utilise un layout `display: flex` avec des largeurs fixes (`.strategies-list` à `280px`, `.ia-panel` à `320px`). Les colonnes ne sont pas redimensionnables, le panneau IA n'a qu'un mécanisme de collapse rudimentaire basé sur un `width: 44px` résiduel avec bouton `ia-toggle` intégré à la colonne elle-même.

Ce design crée deux frustrations :
1. L'utilisateur ne peut pas agrandir l'éditeur quand il travaille sur du code long.
2. Le panneau IA collapsed reste visuellement intrusif (44px de largeur avec texte vertical).

### Objectif

Remplacer le layout `flex` par un **CSS Grid 5 colonnes** avec :
- Deux **strips de contrôle** (8px chacun) positionnés entre les colonnes, toujours visibles.
- **Clic sur un strip** (sans mouvement, `|dx| < 3px`) → toggle collapse de la colonne adjacente avec transition.
- **Clic-glisser sur un strip** (déplacement `dx >= 3px`) → resize live de la colonne adjacente.
- **Persistance** des largeurs et états d'ouverture dans `localStorage`.
- **Notification à CodeMirror** après tout changement de layout pour qu'il recalcule ses dimensions.

---

## 2. Layout CSS Grid — Structure et variables CSS

### 2.1 Template columns

Le conteneur `.strategies-layout` adopte un CSS Grid à 5 colonnes :

```
[list-col]   [strip-L 8px]   [editor-col 1fr]   [strip-R 8px]   [ai-col]
```

| Slot grid | Contenu | Taille |
|-----------|---------|--------|
| `list-col` | `<aside class="strategies-list">` | Variable (`--list-width`) |
| `strip-L` | `<div class="col-strip col-strip--left">` | 8px fixe |
| `editor-col` | `<main class="editor-zone">` | `1fr` (prend tout l'espace restant) |
| `strip-R` | `<div class="col-strip col-strip--right">` | 8px fixe |
| `ai-col` | `<aside class="ia-panel">` | Variable (`--ai-width`) |

### 2.2 Variables CSS et règle grid

```css
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
```

**Important** : les variables CSS `--list-width` et `--ai-width` sont mises à jour en JavaScript via `element.style.setProperty('--list-width', width + 'px')`. Cette approche évite de reconstruire l'intégralité de la règle `grid-template-columns` depuis JS et reste réactive via le moteur CSS natif.

### 2.3 Affectation des colonnes aux enfants directs

```css
.strategies-list { grid-column: 1; overflow: hidden; min-width: 0; }
.col-strip--left  { grid-column: 2; }
.editor-zone      { grid-column: 3; overflow: hidden; min-width: 0; }
.col-strip--right { grid-column: 4; }
.ia-panel         { grid-column: 5; overflow: hidden; min-width: 0; }
```

`min-width: 0` est obligatoire sur les colonnes `1fr` et variables dans un Grid pour empêcher le débordement implicite.

### 2.4 Contraintes de largeur

| Colonne | Valeur min | Valeur max | Défaut | État collapsed |
|---------|-----------|-----------|--------|----------------|
| Liste stratégies | 180px | 420px | 260px | 0px |
| Éditeur (centre) | Pas de contrainte — prend le reste | — | 1fr | Jamais collapsed |
| Assistant IA | 260px | 500px | 340px | 0px |

Les contraintes min/max sont appliquées dans le code JavaScript lors du resize, pas via CSS, pour éviter les conflits avec la variable CSS.

---

## 3. Composant Strip de contrôle

### 3.1 HTML — Structure des strips

Deux strips sont ajoutés comme enfants directs du `.strategies-layout`, positionnés entre les colonnes :

```html
<!-- Strip gauche : entre liste et éditeur -->
<div
  class="col-strip col-strip--left"
  :class="{ 'col-strip--collapsed': !listOpen }"
  @mousedown.prevent="onStripMousedown('list', $event)"
  title="Cliquer pour réduire/agrandir · Glisser pour redimensionner"
>
  <span class="strip-chevron">{{ listOpen ? '‹' : '›' }}</span>
</div>

<!-- Strip droit : entre éditeur et IA -->
<div
  class="col-strip col-strip--right"
  :class="{ 'col-strip--collapsed': !aiOpen }"
  @mousedown.prevent="onStripMousedown('ai', $event)"
  title="Cliquer pour réduire/agrandir · Glisser pour redimensionner"
>
  <span class="strip-chevron">{{ aiOpen ? '›' : '‹' }}</span>
</div>
```

### 3.2 CSS — Style des strips

```css
/* ─── Strip de contrôle ────────────────────────────────────────────────────── */
.col-strip {
  width: 8px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: col-resize;
  background: rgba(0, 212, 255, 0.04);
  border-left: 1px solid rgba(0, 212, 255, 0.08);
  border-right: 1px solid rgba(0, 212, 255, 0.08);
  transition: background 0.15s, box-shadow 0.15s;
  user-select: none;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

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

/* Chevron centré dans le strip */
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
```

### 3.3 Logique mousedown / click / drag — Détail complet

La distinction entre un **clic** (toggle collapse) et un **glisser** (resize) est déterminée par le déplacement horizontal total depuis le `mousedown`. Le seuil est `|dx| < 3px` pour un clic, `dx >= 3px` pour un drag.

#### Algorithme

```javascript
// Seuil de distinction clic/drag (pixels)
const DRAG_THRESHOLD = 3

// Refs de travail pour le drag en cours (non réactives — pas besoin de Vue)
let _dragState = null  // null quand aucun drag actif

function onStripMousedown(column, event) {
  // column : 'list' | 'ai'
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
        // Strip gauche : glisser à droite → liste plus large
        newWidth = Math.max(LIST_MIN, Math.min(LIST_MAX, startWidth + dx))
        // Si on glisse suffisamment à gauche et que la liste était ouverte,
        // ne pas forcer le collapse ici — le collapse reste sur clic uniquement.
        listWidth.value = newWidth
        if (newWidth > 0 && !listOpen.value) {
          listOpen.value = true
        }
      } else {
        // Strip droit : glisser à gauche → panneau IA plus large
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

  function onMouseup(e) {
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
```

**Points critiques** :
- `document.body.style.cursor = 'col-resize'` pendant le drag empêche le curseur de "sauter" quand la souris quitte le strip.
- `document.body.style.userSelect = 'none'` empêche la sélection de texte accidentelle pendant le drag.
- Les listeners `mousemove` et `mouseup` sont ajoutés sur `document` (pas sur le strip) pour capter les mouvements hors du strip.
- Les listeners sont toujours nettoyés dans `onMouseup`, y compris si `!didDrag`.

---

## 4. Gestion des états Vue

### 4.1 Constantes

```javascript
// Contraintes de largeur (pixels)
const LIST_MIN = 180
const LIST_MAX = 420
const LIST_DEFAULT = 260
const AI_MIN = 260
const AI_MAX = 500
const AI_DEFAULT = 340

// Clé localStorage
const LS_KEY = 'strategies_layout'
```

### 4.2 Refs réactifs

```javascript
const listWidth = ref(LIST_DEFAULT)
const aiWidth   = ref(AI_DEFAULT)
const listOpen  = ref(true)
const aiOpen    = ref(true)
```

### 4.3 Initialisation depuis localStorage

À appeler dans `onMounted()`, **avant** `mount()` (CodeMirror) :

```javascript
function loadLayout() {
  try {
    const saved = localStorage.getItem(LS_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      listWidth.value = parsed.listWidth ?? LIST_DEFAULT
      aiWidth.value   = parsed.aiWidth   ?? AI_DEFAULT
      listOpen.value  = parsed.listOpen  ?? true
      aiOpen.value    = parsed.aiOpen    ?? true
    }
  } catch (e) {
    // Silencieux — utiliser les valeurs par défaut
  }
  applyWidths()
}
```

### 4.4 Sauvegarde dans localStorage

```javascript
function saveLayout() {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify({
      listWidth: listWidth.value,
      aiWidth:   aiWidth.value,
      listOpen:  listOpen.value,
      aiOpen:    aiOpen.value,
    }))
  } catch (e) {
    // Silencieux — espace insuffisant ou mode privé
  }
}
```

### 4.5 Application des variables CSS

```javascript
// Ref sur l'élément racine du layout
const layoutEl = ref(null)

function applyWidths() {
  if (!layoutEl.value) return
  const lw = listOpen.value ? listWidth.value : 0
  const aw = aiOpen.value  ? aiWidth.value   : 0
  layoutEl.value.style.setProperty('--list-width', lw + 'px')
  layoutEl.value.style.setProperty('--ai-width',   aw + 'px')
}
```

**Important** : quand une colonne est collapsed (`Open = false`), on passe `0px` à la variable CSS. La colonne disparaît complètement du flux grid. Le strip lui-même reste dans la colonne fixe de 8px et reste toujours visible.

### 4.6 Toggle collapse

```javascript
function toggleColumn(column) {
  if (column === 'list') {
    listOpen.value = !listOpen.value
    // Si on rouvre, s'assurer que la largeur est dans les bornes
    if (listOpen.value && listWidth.value < LIST_MIN) {
      listWidth.value = LIST_DEFAULT
    }
  } else {
    aiOpen.value = !aiOpen.value
    if (aiOpen.value && aiWidth.value < AI_MIN) {
      aiWidth.value = AI_DEFAULT
    }
  }
  applyWidths()
  notifyCodeMirror()
  saveLayout()
}
```

### 4.7 Intégration dans onMounted

```javascript
onMounted(async () => {
  loadLayout()          // 1. Charger et appliquer le layout persisté
  await loadStrategies() // 2. Charger les données
  await nextTick()
  mount()               // 3. Monter CodeMirror (après que le DOM est stable)
})
```

---

## 5. Intégration CodeMirror — requestMeasure()

### 5.1 Problème

CodeMirror v6 mesure ses dimensions au montage. Quand la colonne contenant l'éditeur change de taille (resize ou toggle), CodeMirror ignore le changement CSS car il ne reçoit pas d'événement `resize` sur son conteneur direct.

### 5.2 Solution

Appeler `editorView.requestMeasure()` après tout changement de layout, dans un `requestAnimationFrame()` pour laisser le navigateur appliquer les nouvelles dimensions CSS **avant** la mesure.

### 5.3 Implémentation

Le composable `useCodeMirror` expose déjà `mount` et les refs `code`, `setCode`. Il faut également exposer `editorView` (l'instance `EditorView` de CodeMirror).

```javascript
// Dans useCodeMirror.js — s'assurer que editorView est exporté
// return { code, setCode, mount, editorView }

// Dans StrategiesView.vue — importer editorView
const { code, setCode, mount, editorView } = useCodeMirror(editorContainer, BASE_TEMPLATE)

// Fonction de notification à appeler après tout changement de layout
function notifyCodeMirror() {
  requestAnimationFrame(() => {
    if (editorView.value) {
      editorView.value.requestMeasure()
    }
  })
}
```

`notifyCodeMirror()` est appelé dans :
- `applyWidths()` à la fin de chaque mise à jour de variable CSS (optionnel — couvrir systématiquement).
- `onMousemove` pendant le drag (à chaque déplacement).
- `toggleColumn()` après le toggle.

Pour ne pas surcharger le thread principal pendant un drag rapide, on peut optionnellement throttler avec un flag `_rafPending` :

```javascript
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
```

---

## 6. Transitions CSS pour collapse

La transition `width` de la colonne est gérée par la variable CSS sur le conteneur grid. Pour obtenir une animation fluide au toggle (pas pendant le drag — le drag doit être instantané), une classe CSS `is-transitioning` est ajoutée temporairement.

### 6.1 CSS

```css
/* Transition activée uniquement au toggle (pas au drag) */
.strategies-layout.is-transitioning {
  transition: grid-template-columns 0.25s ease;
}
```

### 6.2 JavaScript dans toggleColumn

```javascript
function toggleColumn(column) {
  // Activer la transition
  if (layoutEl.value) layoutEl.value.classList.add('is-transitioning')

  // Appliquer le changement
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

  // Retirer la transition après son exécution
  setTimeout(() => {
    if (layoutEl.value) layoutEl.value.classList.remove('is-transitioning')
  }, 280) // 25ms de marge après la transition de 250ms
}
```

**Pourquoi ne pas laisser la transition permanente** : si la transition est toujours active, le resize par drag devient visuellement "élastique" (lag de 250ms entre la souris et la colonne), ce qui est inconfortable. La classe temporaire garantit que seul le toggle est animé.

---

## 7. Suppression du mécanisme IA collapse existant

Le mécanisme actuel utilise :
- `iaCollapsed` ref et classe `.ia-panel.collapsed` avec `width: 44px`
- Bouton `.ia-toggle` dans le panneau `<aside class="ia-panel">`

Ces éléments sont **supprimés** et remplacés par le strip droit. Le panneau IA ne contient plus de bouton de toggle — le toggle se fait exclusivement via le strip.

### Changements HTML

- Supprimer `<button class="ia-toggle" ...>` et ses conditions `v-if="!iaCollapsed"`.
- Remplacer `:class="{ collapsed: iaCollapsed }"` sur `.ia-panel` par une simple affectation de largeur via la variable CSS.
- Supprimer `const iaCollapsed = ref(false)` du `<script setup>`.
- Le contenu de `.ia-content` est toujours rendu — CSS le cache quand `--ai-width: 0px` (via `overflow: hidden` déjà présent).

### Ajout de la ref sur le layout

```html
<div class="strategies-layout" ref="layoutEl">
```

---

## 8. Récapitulatif des changements dans StrategiesView.vue

### 8.1 Template

| Élément | Action |
|---------|--------|
| `<div class="strategies-layout">` | Ajouter `ref="layoutEl"` |
| `<aside class="strategies-list">` | Inchangé — retirer `width`/`min-width` du CSS (géré par grid) |
| Nouveau `<div class="col-strip col-strip--left">` | Insérer après `</aside>` (liste) |
| `<main class="editor-zone">` | Inchangé |
| Nouveau `<div class="col-strip col-strip--right">` | Insérer avant `<aside class="ia-panel">` |
| `<aside class="ia-panel" :class="{ collapsed: iaCollapsed }">` | Retirer `:class`, retirer le `<button class="ia-toggle">`, retirer `v-if="!iaCollapsed"` sur `.ia-content` |

### 8.2 Script

| Élément | Action |
|---------|--------|
| `iaCollapsed` ref | Supprimer |
| Nouvelles refs | `listWidth`, `aiWidth`, `listOpen`, `aiOpen`, `layoutEl` |
| Nouvelles constantes | `LIST_MIN/MAX/DEFAULT`, `AI_MIN/MAX/DEFAULT`, `LS_KEY`, `DRAG_THRESHOLD` |
| Nouvelles fonctions | `loadLayout()`, `saveLayout()`, `applyWidths()`, `toggleColumn()`, `onStripMousedown()`, `notifyCodeMirror()` |
| Import `useCodeMirror` | Ajouter `editorView` à la déstructuration |
| `onMounted` | Ajouter `loadLayout()` en premier |

### 8.3 Style

| Règle CSS | Action |
|-----------|--------|
| `.strategies-layout` | Remplacer `display: flex` → `display: grid` + `grid-template-columns` avec variables |
| `.strategies-list` | Retirer `width`, `min-width` fixes → `grid-column: 1` |
| `.editor-zone` | Retirer `flex: 1` → `grid-column: 3` |
| `.ia-panel` | Retirer `width`, `min-width`, `transition: width`, `&.collapsed` → `grid-column: 5` |
| `.ia-toggle`, `.ia-panel.collapsed` | Supprimer |
| Nouvelles règles | `.col-strip`, `.col-strip--left`, `.col-strip--right`, `.col-strip--collapsed`, `.strip-chevron`, `.strategies-layout.is-transitioning` |

---

## 9. Extrait CSS complet — règles nouvelles et modifiées

```css
/* ─── Layout principal ─────────────────────────────────────────────────────── */
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

/* Transition activée seulement lors du toggle (pas pendant le drag) */
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
  border-right: none; /* remplacé par le strip */
}

/* ─── Colonne éditeur ───────────────────────────────────────────────────────── */
.editor-zone {
  grid-column: 3;
  flex: unset; /* retirer flex: 1 de l'ancienne règle */
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* ─── Colonne IA ────────────────────────────────────────────────────────────── */
.ia-panel {
  grid-column: 5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  border-left: none; /* remplacé par le strip */
  /* Retirer : width, min-width, transition: width, &.collapsed */
}

/* ─── Strips de contrôle ───────────────────────────────────────────────────── */
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
```

---

## 10. Critères d'acceptation

**CA-01** — Le layout s'affiche avec trois colonnes visibles au chargement : liste stratégies (260px), éditeur (espace restant), panneau IA (340px). Les deux strips de 8px sont visibles entre les colonnes.

**CA-02** — Un clic sans mouvement (`|dx| < 3px`) sur le strip gauche ferme la colonne liste (largeur à 0) avec une transition de 250ms. Un second clic la rouvre à sa largeur précédente.

**CA-03** — Un clic sans mouvement sur le strip droit ferme la colonne IA (largeur à 0) avec une transition de 250ms. Un second clic la rouvre à sa largeur précédente.

**CA-04** — Pendant un collapse ou expand, le curseur du chevron du strip bascule correctement : `‹` quand la colonne est ouverte (indique qu'on peut la fermer vers la gauche), `›` quand elle est fermée (indique qu'on peut l'ouvrir).

**CA-05** — Glisser le strip gauche horizontalement redimensionne la liste en temps réel, sans transition (instantané). La largeur reste contrainte entre 180px et 420px.

**CA-06** — Glisser le strip droit horizontalement redimensionne le panneau IA en temps réel, sans transition. La largeur reste contrainte entre 260px et 500px.

**CA-07** — Les strips restent toujours visibles (8px), y compris quand les colonnes adjacentes sont à 0px. Il n'est pas possible de "perdre" un strip derrière une colonne collapsée.

**CA-08** — Après un resize ou un toggle, l'éditeur CodeMirror recalcule ses dimensions correctement (pas de décalage de numérotation de lignes, pas de contenu tronqué, pas de scrollbar intempestive).

**CA-09** — Les largeurs et états d'ouverture sont persistés dans `localStorage` sous la clé `strategies_layout`. Après un rafraîchissement de page, le layout est restauré à l'état exact de la session précédente.

**CA-10** — Pendant un drag, le curseur `col-resize` est appliqué au `body` entier, empêchant le curseur de reprendre sa forme par défaut quand la souris sort momentanément du strip. La sélection de texte est désactivée pendant le drag.

---

## 11. Fichiers modifiés

| Fichier | Type de modification |
|---------|---------------------|
| `frontend/src/views/StrategiesView.vue` | Unique fichier modifié — template, script setup, styles |

Si `useCodeMirror.js` n'exporte pas encore `editorView`, une modification minimale de `frontend/src/composables/useCodeMirror.js` est requise pour ajouter `editorView` au return.

---

## 12. Services à redémarrer

**Terminal 4 uniquement** : `npm run dev` (Vite hot-reload suffit, mais un redémarrage complet est recommandé si le hot-reload ne prend pas en compte les changements de script setup).

Aucun redémarrage de Terminal 1 (Daphne), Terminal 2, Terminal 3 ou Terminal 5 n'est nécessaire — cette modification est 100% frontend.
