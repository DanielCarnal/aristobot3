#!/bin/bash
# ===============================================
#    ARISTOBOT3 - Terminal 6
#    Service: Webhook Receiver
#    Commande: run_webhook_receiver
# ===============================================
export PATH="/home/dac/miniconda3/bin:$PATH"
eval "$(/home/dac/miniconda3/bin/conda shell.bash hook)"
conda activate Aristobot3

export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

echo "Environnement activé: $CONDA_DEFAULT_ENV"

cd ~/Dev/Aristobot3/backend
echo "Dossier backend ouvert"

while true; do
    echo ""
    echo "[DEMARRAGE] Terminal 6 - Webhook Receiver Service"
    python manage.py run_webhook_receiver

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
