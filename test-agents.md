# Aristobot3 - Test des Agents Claude Code

## Commandes de test pour chaque agent

### Frontend Agent
```bash
> Use frontend-aristobot to create a real-time portfolio component with WebSocket integration
> Add a trading form with quantity ↔ USD conversion using frontend-aristobot  
> Use frontend-aristobot to implement the crypto dark theme with neon colors
```

### Backend Agent  
```bash
> Use backend-aristobot to create the trading_manual API endpoints
> Implement multi-tenant broker filtering with backend-aristobot
> Use backend-aristobot to add WebSocket consumers for real-time updates
```

### Architecte Agent
```bash
> Use architecte-aristobot to review the CCXT service communication pattern
> Design the strategy execution workflow with architecte-aristobot
> Use architecte-aristobot to plan the Redis channel optimization
```

### Debugger Agent
```bash
> Use debugger-aristobot to investigate why the Heartbeat signals aren't reaching Trading Engine
> Debug the CCXT rate limiting issues with debugger-aristobot
> Use debugger-aristobot to check multi-tenant query problems
```

### Heartbeat Specialist
```bash
> Use heartbeat-specialist to optimize the Binance WebSocket connection handling
> Implement signal deduplication logic with heartbeat-specialist
> Use heartbeat-specialist to add Redis channel health monitoring
```

### CCXT Service Specialist
```bash
> Use ccxt-service-specialist to implement the optimized exchange instance sharing
> Debug broker credential injection with ccxt-service-specialist
> Use ccxt-service-specialist to add rate limit monitoring
```

### Strategies Expert
```bash
> Use strategies-expert to create an EMA crossover strategy with risk management
> Implement a multi-timeframe strategy with strategies-expert
> Use strategies-expert to add Bollinger Bands mean reversion logic
```

## Pattern de coordination simulée

### Workflow complet
```bash
# 1. Planification architecturale
> Use architecte-aristobot to plan the new feature X implementation across all services

# 2. Implémentation backend  
> Use backend-aristobot to implement the API changes planned by architecte-aristobot

# 3. Implémentation frontend
> Use frontend-aristobot to create the UI for the feature designed by architecte-aristobot

# 4. Intégration services
> Use ccxt-service-specialist to handle the exchange integration aspects
> Use heartbeat-specialist for any real-time data requirements

# 5. Validation et tests
> Use debugger-aristobot to test the complete feature integration
```

### Consultation croisée
```bash
# Agent principal avec expertise complémentaire
> Use strategies-expert to create a new trading algorithm, consulting with architecte-aristobot about optimal service integration

# Multiple expertises
> Use backend-aristobot to implement this feature, consulting with ccxt-service-specialist about exchange integration and debugger-aristobot about error handling
```
