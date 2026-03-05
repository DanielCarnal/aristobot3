#!/bin/bash
# =============================================================================
# ARISTOBOT3 - Order Monitor (Terminal 7)
# =============================================================================

PROJECT_DIR="/a0/usr/projects/Aristobot3"
BACKEND_DIR="$PROJECT_DIR/backend"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"
cd "$BACKEND_DIR" || exit 1

echo "========================================"
echo "📊 Order Monitor (Terminal 7)"
echo "========================================"
echo "Dossier: $(pwd)"
echo "Logs: $LOG_DIR/order_monitor.log"
echo "========================================"

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Démarrage Order Monitor..." | tee -a "$LOG_DIR/order_monitor.log"
    python manage.py run_order_monitor --verbose 2>&1 | tee -a "$LOG_DIR/order_monitor.log"
    echo ""
    echo "[R] Redémarrer | [Q] Quitter"
    read -r -n 1 -p "Choix: " choice
    echo ""
    [[ "$choice" =~ ^[Qq]$ ]] && exit 0
done
