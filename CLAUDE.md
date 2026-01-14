# Aristobot3_1 - Configuration Claude Code

## **Le projet**
@Aristobot3_1.md
@IMPLEMENTATION_PLAN.md

## **Architecture complète**
Pour une vue d'ensemble détaillée de l'architecture, consulter [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md).

**Résumé**: Bot de trading crypto multi-exchange avec architecture 7-terminaux.
- **Stack**: Django 4.2.15 + Vue 3 + PostgreSQL + Redis
- **Performance**: APIs natives (~3x plus rapide que CCXT)
- **Status**: Modules 1-3 ✅ Complete | Trading Manuel, Heartbeat, User Account opérationnels
- **Structure**: Service centralisé (Terminal 5) avec clients natifs Bitget/Binance/Kraken

### Imports de contexte
@.claude-instructions
@.env.example
@backend/apps/core/models.py
@backend/aristobot/settings.py
@backend/requirements.txt
@frontend/package.json
### **Services et logique métier**
@backend/apps/core/services/exchange_client.py     # Client Exchange natif (remplace CCXT)
@backend/apps/core/consumers.py                     # WebSocket consumers
@backend/apps/core/management/commands/run_heartbeat.py              # Service Heartbeat (Terminal 2)
@backend/apps/core/management/commands/run_native_exchange_service.py # Service Exchange natif (Terminal 5)

Bot de trading crypto avec contexte technique complet chargé via imports.
