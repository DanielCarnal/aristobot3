#!/bin/bash
# ===============================================
#    ARISTOBOT3 - Terminal 5 (Exchange Gateway)
#    Service: Native Exchange Service
#    Commande: run_native_exchange_service
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
    echo "[DEMARRAGE] Terminal 5 - Native Exchange Service"
    python manage.py run_native_exchange_service --verbose

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
