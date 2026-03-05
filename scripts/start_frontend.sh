#!/bin/bash
# =============================================================================
# ARISTOBOT3 - Frontend Vue.js
# =============================================================================

PROJECT_DIR="/a0/usr/projects/Aristobot3"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"
cd "$FRONTEND_DIR" || exit 1

echo "========================================"
echo "🎨 Frontend Vue.js"
echo "========================================"
echo "Dossier: $(pwd)"
echo "Logs: $LOG_DIR/frontend.log"
echo "========================================"

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Démarrage Frontend..." | tee -a "$LOG_DIR/frontend.log"
    npm run dev 2>&1 | tee -a "$LOG_DIR/frontend.log"
    echo ""
    echo "[R] Redémarrer | [Q] Quitter"
    read -r -n 1 -p "Choix: " choice
    echo ""
    [[ "$choice" =~ ^[Qq]$ ]] && exit 0
done
