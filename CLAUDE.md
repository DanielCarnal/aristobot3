# Aristobot3 - Configuration Claude Code

> ⚠️ **RÈGLES OBLIGATOIRES AVANT TOUT DÉVELOPPEMENT**
>
> Consulter [@DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) - **6 RÈGLES CRITIQUES NON NÉGOCIABLES**

---

## 📚 Documentation Principale

### Règles et Contraintes
@DEVELOPMENT_RULES.md → **OBLIGATOIRE** - Règles architecturales strictes (WebSockets, Stack, Design, APIs, Contraintes, Documentation)

### Architecture et Planification
@Aristobot3_1.md → Description complète projet et architecture fonctionnelle
@IMPLEMENTATION_PLAN.md → État d'avancement modules (Modules 1-3 ✅ Complete)
@docs/CODEBASE_MAP.md → **Carte auto-générée** du codebase (regénérer avec `/cartographer` avant commits majeurs)

### Architecture Détaillée
@_bmad-output/planning-artifacts/Terminal5_Exchange_Gateway.md → Documentation complète Terminal 5 (Exchange Gateway natif)

---

## 🔧 Imports Techniques

### Configuration et Environnement
@.claude-instructions → Directives opérationnelles Claude Code
@.env.example → Variables environnement (SECRET_KEY, REDIS_HOST, WEBHOOK_TOKEN)

### Modèles et Configuration Django
@backend/apps/core/models.py → Modèles Django core (HeartbeatStatus, Position, CandleHeartbeat)
@backend/aristobot/settings.py → Configuration Django complète
@backend/requirements.txt → Dépendances Python

### Services Critiques
@backend/apps/core/services/exchange_client.py → Client Exchange unifié (communication Terminal 5)
@backend/apps/core/consumers.py → WebSocket consumers (Heartbeat, Stream, Backtest, UserAccount)
@backend/apps/core/management/commands/run_heartbeat.py → Service Heartbeat (Terminal 2)
@backend/apps/core/management/commands/run_native_exchange_service.py → Exchange Gateway (Terminal 5)

### Frontend
@frontend/package.json → Dépendances Vue.js 3 (Pinia, Vue Router, Axios)

---

**Bot de trading crypto multi-exchange avec architecture 7-terminaux**

**Stack:** Django 4.2.15 + Vue 3 + PostgreSQL + Redis | **Performance:** APIs natives (~3x CCXT)
