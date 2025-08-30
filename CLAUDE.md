# Aristobot3 - Configuration Claude Code

## **Le projet**
@Aristobot3.md
@IMPLEMENTATION_PLAN.md

### Imports de contexte
@.claude-instructions
@.env.example
@backend/apps/core/models.py
@backend/aristobot/settings.py
@backend/requirements.txt
@frontend/package.json
### **Services et logique métier**
@backend/apps/core/services/ccxt_client.py     # Client CCXT
@backend/apps/core/consumers.py                # WebSocket consumers
@backend/apps/core/management/commands/run_heartbeat.py  # Service Heartbeat

Bot de trading crypto avec contexte technique complet chargé via imports.
