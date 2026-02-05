/**
 * Frontend Logger — console uniquement
 *
 * Interface uniforme info/warn/error/debug utilisée par main.js
 * (intercepteur console.error + handler window.error).
 * Logs structurés vers la console du navigateur avec timestamp ISO8601.
 *
 * NOTE: POST vers /api/frontend-log supprimé — endpoint n'existe pas.
 * Ajouter l'endpoint backend (ou un WebSocket) avant de réactiver.
 */

const LEVEL_MAP = {
  debug: 'log',
  info: 'info',
  warn: 'warn',
  error: 'error'
}

class FrontendLogger {
  _log (level, message, component, data) {
    const method = LEVEL_MAP[level] || 'log'
    const prefix = `[${level.toUpperCase()}] [${component}]`
    const hasData = data && Object.keys(data).length > 0
    hasData
      ? console[method](prefix, message, data)
      : console[method](prefix, message)
  }

  info (message, component = 'app', data = {}) {
    this._log('info', message, component, data)
  }

  warn (message, component = 'app', data = {}) {
    this._log('warn', message, component, data)
  }

  error (message, component = 'app', data = {}) {
    this._log('error', message, component, data)
  }

  debug (message, component = 'app', data = {}) {
    this._log('debug', message, component, data)
  }
}

const frontendLogger = new FrontendLogger()
export default frontendLogger
