#!/bin/bash
# =============================================================================
# ARISTOBOT3 - Webhook Receiver (Terminal 6)
# =============================================================================

PROJECT_DIR="/a0/usr/projects/Aristobot3"
BACKEND_DIR="$PROJECT_DIR/backend"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"
cd "$BACKEND_DIR" || exit 1

echo "========================================"
echo "🔗 Webhook Receiver (Terminal 6)"
echo "========================================"
echo "Dossier: $(pwd)"
echo "Logs: $LOG_DIR/webhook_receiver.log"
echo "========================================"

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Démarrage Webhook Receiver..." | tee -a "$LOG_DIR/webhook_receiver.log"
    python manage.py run_webhook_receiver 2>&1 | tee -a "$LOG_DIR/webhook_receiver.log"
    echo ""
    echo "[R] Redémarrer | [Q] Quitter"
    read -r -n 1 -p "Choix: " choice
    echo ""
    [[ "$choice" =~ ^[Qq]$ ]] && exit 0
done
