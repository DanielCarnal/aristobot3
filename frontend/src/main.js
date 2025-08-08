console.log('DEBUG: main.js - Debut du chargement')

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

console.log('DEBUG: main.js - Imports Vue charges')

// Import views
import HeartbeatView from './views/HeartbeatView.vue'
import TradingManualView from './views/TradingManualView.vue'
import TradingBotView from './views/TradingBotView.vue'
import StrategiesView from './views/StrategiesView.vue'
import BacktestView from './views/BacktestView.vue'
import WebhooksView from './views/WebhooksView.vue'
import StatsView from './views/StatsView.vue'
import AccountView from './views/AccountView.vue'

console.log('DEBUG: main.js - Toutes les vues importees')

const routes = [
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

console.log('DEBUG: main.js - Creation de l\'app Vue')

const app = createApp(App)
console.log('DEBUG: main.js - App creee, ajout Pinia')
app.use(pinia)
console.log('DEBUG: main.js - Pinia ajoute, ajout Router')
app.use(router)
console.log('DEBUG: main.js - Router ajoute, montage sur #app')
app.mount('#app')

console.log('DEBUG: main.js - App montee avec succes!')