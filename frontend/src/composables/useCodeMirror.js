// Composable Vue 3 pour CodeMirror v6 — reutilisable M5 (Strategies) et M6 (Backtest)
import { ref, onUnmounted } from 'vue'
import { EditorView, basicSetup } from 'codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'

/**
 * useCodeMirror — encapsule un editeur CodeMirror v6 dans un composable Vue 3.
 *
 * @param {Ref<HTMLElement|null>} containerRef - ref vers l'element DOM conteneur
 * @param {string} initialCode - code initial a afficher dans l'editeur
 * @returns {{ code: Ref<string>, setCode: Function, mount: Function, editorView: Ref<EditorView|null> }}
 */
export function useCodeMirror(containerRef, initialCode = '') {
  const code = ref(initialCode)
  // editorView expose l'instance EditorView pour permettre requestMeasure() apres resize
  const editorView = ref(null)

  function mount() {
    if (!containerRef.value || editorView.value) return

    editorView.value = new EditorView({
      doc: code.value,
      extensions: [
        basicSetup,
        python(),
        oneDark,
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            code.value = update.state.doc.toString()
          }
        }),
        // Style de base pour integration dans le theme Aristobot
        EditorView.theme({
          '&': { height: '100%', fontSize: '13px' },
          '.cm-scroller': { overflow: 'auto', fontFamily: '"Fira Code", "Consolas", monospace' },
        }),
      ],
      parent: containerRef.value,
    })
  }

  /**
   * Remplace le contenu de l'editeur par un nouveau code.
   * @param {string} newCode
   */
  function setCode(newCode) {
    code.value = newCode
    if (editorView.value) {
      editorView.value.dispatch({
        changes: {
          from: 0,
          to: editorView.value.state.doc.length,
          insert: newCode,
        },
      })
    }
  }

  onUnmounted(() => {
    if (editorView.value) {
      editorView.value.destroy()
      editorView.value = null
    }
  })

  return { code, setCode, mount, editorView }
}
