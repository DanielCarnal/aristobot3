/**
 * Frontend Logger — Queue async avec fallback console.warn
 *
 * - Envoie les logs vers POST /api/frontend-log (backend)
 * - Queue locale: 3 tentatives avec 1s de delay entre chaque
 * - Fallback console.warn si backend injoignable apres les 3 tentatives
 * - Timestamps ISO8601 directement correlables avec le backend
 * - Zero impact performance UI (fire & forget)
 */
import api from '../api/index.js'

const QUEUE_MAX_RETRIES = 3
const QUEUE_RETRY_DELAY = 1000

class FrontendLogger {
  constructor () {
    this.queue = []
    this.processing = false
  }

  _enqueue (level, message, component, data = {}) {
    this.queue.push({
      level,
      message,
      component,
      timestamp: new Date().toISOString(),
      data
    })

    if (!this.processing) {
      this._processQueue()
    }
  }

  async _processQueue () {
    this.processing = true

    while (this.queue.length > 0) {
      const entry = this.queue.shift()
      let sent = false

      for (let attempt = 0; attempt < QUEUE_MAX_RETRIES; attempt++) {
        try {
          await api.post('/api/frontend-log', entry)
          sent = true
          break
        } catch (e) {
          if (attempt < QUEUE_MAX_RETRIES - 1) {
            await new Promise(r => setTimeout(r, QUEUE_RETRY_DELAY))
          }
        }
      }

      if (!sent) {
        console.warn(
          `[FrontendLogger] Fallback - [${entry.level.toUpperCase()}] [${entry.component}] ${entry.message}`,
          entry.data
        )
      }
    }

    this.processing = false
  }

  info (message, component = 'app', data = {}) {
    this._enqueue('info', message, component, data)
  }

  warn (message, component = 'app', data = {}) {
    this._enqueue('warn', message, component, data)
  }

  error (message, component = 'app', data = {}) {
    this._enqueue('error', message, component, data)
  }

  debug (message, component = 'app', data = {}) {
    this._enqueue('debug', message, component, data)
  }
}

const frontendLogger = new FrontendLogger()
export default frontendLogger
