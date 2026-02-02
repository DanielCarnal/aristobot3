import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import frontendLogger from './services/logger.js'

// Import views
import HeartbeatView from './views/HeartbeatView.vue'
import TradingManualView from './views/TradingManualView.vue'
import TradingBotView from './views/TradingBotView.vue'
import StrategiesView from './views/StrategiesView.vue'
import BacktestView from './views/BacktestView.vue'
import WebhooksView from './views/WebhooksView.vue'
import StatsView from './views/StatsView.vue'
import AccountView from './views/AccountView.vue'
import LoginView from './views/LoginView.vue'

const routes = [
  { path: '/login', component: LoginView },
  { path: '/', redirect: '/heartbeat' },
  { path: '/heartbeat', component: HeartbeatView },
  { path: '/trading-manual', component: TradingManualView },
  { path: '/trading-bot', component: TradingBotView },
  { path: '/strategies', component: StrategiesView },
  { path: '/backtest', component: BacktestView },
  { path: '/webhooks', component: WebhooksView },
  { path: '/stats', component: StatsView },
  { path: '/account', component: AccountView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const pinia = createPinia()

const app = createApp(App)
app.use(pinia)
app.use(router)

// Intercepteur console.error -> log structure backend (guard anti-recursion)
let _loggingError = false
const originalError = console.error
console.error = function (...args) {
  originalError.apply(console, args)
  if (_loggingError) return
  _loggingError = true
  const message = args.map(a => (typeof a === 'object' ? JSON.stringify(a) : String(a))).join(' ')
  frontendLogger.error(message, { component: 'global' })
  _loggingError = false
}

// Exceptions non catchees
window.addEventListener('error', (event) => {
  frontendLogger.error(event.message, {
    component: 'window',
    stack: event.stack,
    filename: event.filename,
    lineno: event.lineno
  })
})

app.mount('#app')

frontendLogger.info('App montee avec succes', { component: 'main' })
