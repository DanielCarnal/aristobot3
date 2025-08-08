import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Import views
import HeartbeatView from './views/HeartbeatView.vue'
import TradingManualView from './views/TradingManualView.vue'
import TradingBotView from './views/TradingBotView.vue'
import StrategiesView from './views/StrategiesView.vue'
import BacktestView from './views/BacktestView.vue'
import WebhooksView from './views/WebhooksView.vue'
import StatsView from './views/StatsView.vue'
import AccountView from './views/AccountView.vue'

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

createApp(App)
  .use(pinia)
  .use(router)
  .mount('#app')