console.log('DEBUG: main-minimal.js - Debut')

import { createApp } from 'vue'
console.log('DEBUG: createApp importe')

const app = createApp({
  template: `
    <div>
      <h1>✅ Vue createApp fonctionne!</h1>
      <p>Aristobot3 - Test progressif</p>
      <p>Timestamp: {{ timestamp }}</p>
    </div>
  `,
  data() {
    return {
      timestamp: new Date().toLocaleString()
    }
  }
})

console.log('DEBUG: App Vue creee')
app.mount('#app')
console.log('DEBUG: App montee avec succes!')