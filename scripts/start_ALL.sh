#!/bin/bash
# ===============================================
#    ARISTOBOT3 - Lancement complet via tmux
# ===============================================
# Ctrl+b 1-7  : changer de fenêtre
# Ctrl+b d    : détacher (services continuent)
# tmux attach -t aristobot : réattacher

SESSION="aristobot"
SCRIPTS_DIR="$HOME/Dev/Aristobot3/scripts"

# Vérifier que tmux est installé
if ! command -v tmux &>/dev/null; then
    echo "Erreur : tmux n'est pas installé."
    echo "Installez-le avec : sudo apt install tmux"
    exit 1
fi

# Tuer la session existante si elle existe
tmux kill-session -t "$SESSION" 2>/dev/null

# Window 1 : Backend Daphne (fenêtre initiale de la session)
tmux new-session -d -s "$SESSION" -n "Daphne" \
    "bash '$SCRIPTS_DIR/Start1_Terminal-1_Backend_Daphne.sh'; exec bash"

# Window 2 : Heartbeat
tmux new-window -t "$SESSION" -n "Heartbeat" \
    "bash '$SCRIPTS_DIR/Start3_Terminal-2_Service_Heartbeat.sh'; exec bash"

# Window 3 : Trading Engine
tmux new-window -t "$SESSION" -n "Trading" \
    "bash '$SCRIPTS_DIR/Start4_Terminal-3_Trading_Engine.sh'; exec bash"

# Window 4 : Exchange Service
tmux new-window -t "$SESSION" -n "Exchange" \
    "bash '$SCRIPTS_DIR/Start2_Terminal-5_Native_Exchange_Service.sh'; exec bash"

# Window 5 : Webhook Receiver
tmux new-window -t "$SESSION" -n "Webhook" \
    "bash '$SCRIPTS_DIR/Start5_Terminal-6_run_webhook_receiver.sh'; exec bash"

# Window 6 : Order Monitor
tmux new-window -t "$SESSION" -n "Orders" \
    "bash '$SCRIPTS_DIR/Start6_Terminal-7_Order_Monitor.sh'; exec bash"

# Window 7 : Frontend Vue.js
tmux new-window -t "$SESSION" -n "Frontend" \
    "bash '$SCRIPTS_DIR/Start7_Frontend_Aristobot.sh'; exec bash"

# Sélectionner la fenêtre 1 (Daphne) au démarrage
tmux select-window -t "$SESSION:Daphne"

# Attacher la session
tmux attach-session -t "$SESSION"
