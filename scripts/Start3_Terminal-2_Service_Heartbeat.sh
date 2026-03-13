#!/bin/bash
# ===============================================
#    ARISTOBOT3 - Terminal 2
#    Service: Heartbeat
#    Commande: run_heartbeat
# ===============================================
export PATH="/home/dac/miniconda3/bin:$PATH"
eval "$(/home/dac/miniconda3/bin/conda shell.bash hook)"
conda activate Aristobot3

echo "Environnement activé: $CONDA_DEFAULT_ENV"

cd ~/Dev/Aristobot3/backend
echo "Dossier backend ouvert"

while true; do
    echo ""
    echo "[DEMARRAGE] Terminal 2 - Service Heartbeat"
    python manage.py run_heartbeat

    echo ""
    echo "=================================================================="
    echo "Script terminé. Que souhaitez-vous faire ?"
    echo "[R] Redémarrer"
    echo "[Q] Quitter"
    echo "=================================================================="
    read -p "Votre choix (R/Q) : " choix
    case "$choix" in
        [Rr]) echo "Redémarrage..." ;;
        [Qq]) echo "Fermeture du script..."; sleep 2; exit 0 ;;
        *) echo "Choix invalide, redémarrage par défaut..." ;;
    esac
done
