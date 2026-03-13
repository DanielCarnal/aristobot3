#!/bin/bash
# =============================================================================
# ARISTOBOT3 - Native Exchange Service (Terminal 5)
# =============================================================================

PROJECT_DIR="/a0/usr/projects/Aristobot3"
BACKEND_DIR="$PROJECT_DIR/backend"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"
cd "$BACKEND_DIR" || exit 1

echo "=============================================="
echo "🔄 Native Exchange Service (Terminal 5)"
echo "=============================================="
echo "Dossier: $(pwd)"
echo "Logs: $LOG_DIR/exchange_service.log"
echo "=============================================="

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Démarrage Native Exchange Service..." | tee -a "$LOG_DIR/exchange_service.log"
    python manage.py run_native_exchange_service --verbose 2>&1 | tee -a "$LOG_DIR/exchange_service.log"
    echo ""
    echo "========================================"
    echo "[R] Redémarrer | [Q] Quitter"
    echo "========================================"
    read -r -n 1 -p "Choix: " choice
    echo ""
    [[ "$choice" =~ ^[Qq]$ ]] && exit 0
done
