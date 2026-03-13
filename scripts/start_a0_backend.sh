#!/bin/bash
# =============================================================================
# ARISTOBOT3 - Backend Daphne Server (Terminal 1)
# =============================================================================

PROJECT_DIR="/a0/usr/projects/Aristobot3"
BACKEND_DIR="$PROJECT_DIR/backend"
LOG_DIR="$PROJECT_DIR/logs"

# Créer le dossier logs si nécessaire
mkdir -p "$LOG_DIR"

# Aller dans le dossier backend
cd "$BACKEND_DIR" || exit 1

echo "========================================"
echo "🚀 Démarrage Backend Daphne"
echo "========================================"
echo "Dossier: $(pwd)"
echo "Logs: $LOG_DIR/backend.log"
echo "Bind: 0.0.0.0:8000 (accessible depuis Docker)"
echo "========================================"

# Fonction de démarrage
start_daphne() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Démarrage de Daphne sur 0.0.0.0:8000..." | tee -a "$LOG_DIR/backend.log"
    daphne --bind 0.0.0.0 --port 8000 --verbosity 2 aristobot.asgi:application 2>&1 | tee -a "$LOG_DIR/backend.log"
}

# Boucle avec option de redémarrage
while true; do
    start_daphne
    echo ""
    echo "========================================"
    echo "Script terminé. Que souhaitez-vous faire?"
    echo "[R] Redémarrer"
    echo "[Q] Quitter"
    echo "========================================"
    read -r -n 1 -p "Votre choix (R/Q): " choice
    echo ""
    case $choice in
        [Rr]*) continue ;;
        [Qq]*) exit 0 ;;
        *) exit 0 ;;
    esac
done
