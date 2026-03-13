# PLAN : Création du script start_ALL.sh avec tmux

## Objectif
Créer un script `start_ALL.sh` qui lance les 7 services Aristobot3
chacun dans sa propre fenêtre tmux, dans une session nommée "aristobot".

## Prérequis
- tmux installé : `sudo apt install tmux`
- Les scripts Start*.sh déjà présents et exécutables dans `~/Dev/Aristobot3/scripts/`
- Si pas encore exécutables : `chmod +x ~/Dev/Aristobot3/scripts/Start*.sh`

## Fichier à créer
**Chemin** : `~/Dev/Aristobot3/scripts/start_ALL.sh`

## Contenu exact du script

```bash
#!/bin/bash
# ===============================================
#    ARISTOBOT3 - Lancement complet via tmux
#    Lance tous les services dans des fenêtres tmux
# ===============================================

SESSION="aristobot"
SCRIPTS_DIR="$HOME/Dev/Aristobot3/scripts"

# Si une session existe déjà, on la tue et on repart proprement
tmux kill-session -t $SESSION 2>/dev/null

# Créer la session tmux avec la première fenêtre : Backend Daphne
tmux new-session -d -s $SESSION -n "Daphne" \
    "bash '$SCRIPTS_DIR/Start1_Termina_1_Backend_Daphne.sh'; exec bash"

# Fenêtre 2 : Heartbeat
tmux new-window -t $SESSION -n "Heartbeat" \
    "bash '$SCRIPTS_DIR/Start3_Terminal_2_Service_Heartbeat.sh'; exec bash"

# Fenêtre 3 : Trading Engine
tmux new-window -t $SESSION -n "Trading" \
    "bash '$SCRIPTS_DIR/Start4_Terminal_3_Trading_Engine.sh'; exec bash"

# Fenêtre 4 : Exchange Service
tmux new-window -t $SESSION -n "Exchange" \
    "bash '$SCRIPTS_DIR/Start2_Terminal_5_Native_Exchange_Service.sh'; exec bash"

# Fenêtre 5 : Webhook Receiver
tmux new-window -t $SESSION -n "Webhook" \
    "bash '$SCRIPTS_DIR/Start5_Terminal_6_run_webhook_receiver.sh'; exec bash"

# Fenêtre 6 : Order Monitor
tmux new-window -t $SESSION -n "OrderMon" \
    "bash '$SCRIPTS_DIR/Start6_Terminal_7_Order_Monitor.sh'; exec bash"

# Fenêtre 7 : Frontend Vue.js
tmux new-window -t $SESSION -n "Frontend" \
    "bash '$SCRIPTS_DIR/Start7_Frontend_Aristobot.sh'; exec bash"

# Revenir sur la première fenêtre (Daphne)
tmux select-window -t $SESSION:0

# Attacher la session tmux dans le terminal courant
tmux attach-session -t $SESSION
```

## Après création du fichier

```bash
# Rendre exécutable
chmod +x ~/Dev/Aristobot3/scripts/start_ALL.sh

# Tester
bash ~/Dev/Aristobot3/scripts/start_ALL.sh
```

## Navigation tmux
| Raccourci       | Action                        |
|-----------------|-------------------------------|
| `Ctrl+b 0` à `6`| Aller à la fenêtre N          |
| `Ctrl+b n`      | Fenêtre suivante              |
| `Ctrl+b p`      | Fenêtre précédente            |
| `Ctrl+b w`      | Liste toutes les fenêtres     |
| `Ctrl+b d`      | Détacher (services continuent)|
| `tmux attach`   | Réattacher la session         |
| `Ctrl+b &`      | Fermer la fenêtre courante    |

## Notes importantes
- Le `; exec bash` après chaque script garde la fenêtre ouverte si le script se termine
- Les noms de fenêtres sont visibles dans la barre tmux en bas
- Si les noms de scripts ont changé (renommage), adapter les chemins en conséquence
- Vérifier les noms exacts des scripts avec : `ls ~/Dev/Aristobot3/scripts/Start*.sh`
