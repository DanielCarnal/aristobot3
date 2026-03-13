#!/bin/bash
# ===============================================
#    ARISTOBOT3 - Terminal 7
#    Service: Frontend Vue.js
#    Commande: npm run dev
# ===============================================
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

cd ~/Dev/Aristobot3/frontend
echo "Dossier frontend ouvert"

while true; do
    echo ""
    echo "[DEMARRAGE] Frontend Aristobot - npm run dev"
    npm run dev

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
