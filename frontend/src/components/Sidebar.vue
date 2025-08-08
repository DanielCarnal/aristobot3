<template>
  <div class="sidebar">
    <div class="logo">
      <h2>Aristobot3</h2>
    </div>
    
    <nav class="nav-menu">
      <router-link to="/heartbeat" class="nav-item">
        <span>📡</span> Heartbeat
      </router-link>
      <router-link to="/trading-manual" class="nav-item">
        <span>📈</span> Trading Manuel
      </router-link>
      <router-link to="/trading-bot" class="nav-item">
        <span>🤖</span> Trading BOT
      </router-link>
      <router-link to="/strategies" class="nav-item">
        <span>⚡</span> Stratégies
      </router-link>
      <router-link to="/backtest" class="nav-item">
        <span>🔄</span> Backtest
      </router-link>
      <router-link to="/webhooks" class="nav-item">
        <span>🔗</span> Webhooks
      </router-link>
      <router-link to="/stats" class="nav-item">
        <span>📊</span> Statistiques
      </router-link>
      <router-link to="/account" class="nav-item">
        <span>👤</span> Mon compte
      </router-link>
    </nav>
  </div>
</template>

<style scoped>
.sidebar {
  width: 250px;
  background-color: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 1.5rem 1rem;
  border-bottom: 1px solid var(--color-border);
}

.logo h2 {
  color: var(--color-primary);
  font-weight: bold;
}

.nav-menu {
  flex: 1;
  padding: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover {
  background-color: rgba(0, 212, 255, 0.1);
  color: var(--color-primary);
}

.nav-item.router-link-active {
  background-color: rgba(0, 212, 255, 0.2);
  color: var(--color-primary);
  border-right: 3px solid var(--color-primary);
}

.nav-item span {
  margin-right: 0.75rem;
  font-size: 1.1rem;
}
</style>