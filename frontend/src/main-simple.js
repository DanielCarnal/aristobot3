console.log('DEBUG: main-simple.js - Test simple de Vite')

import { createApp } from 'vue'

console.log('DEBUG: Vue importe avec succes')

const app = createApp({
  template: `
    <div>
      <h1>Test Vite Simple</h1>
      <p>Si tu vois cette page, Vite fonctionne !</p>
      <p>Timestamp: {{ new Date().toLocaleString() }}</p>
    </div>
  `
})

console.log('DEBUG: App simple creee')

app.mount('#app')

console.log('DEBUG: App simple montee!')