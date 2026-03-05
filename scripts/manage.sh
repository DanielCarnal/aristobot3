#!/bin/bash
# =============================================================================
# ARISTOBOT3 - Script de Gestion des Services
# =============================================================================

PROJECT_DIR="/a0/usr/projects/Aristobot3"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Créer les dossiers nécessaires
mkdir -p "$LOG_DIR" "$PID_DIR"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Liste des services
SERVICES=("backend" "exchange_service" "heartbeat" "trading_engine" "webhook_receiver" "order_monitor" "frontend")

# Fonction pour afficher l'aide
show_help() {
    echo "Usage: $0 {start|stop|restart|status|logs} [service]"
    echo ""
    echo "Services disponibles:"
    echo "  backend          - Serveur Daphne (Backend Django)"
    echo "  exchange_service - Native Exchange Service"
    echo "  heartbeat        - Service Heartbeat"
    echo "  trading_engine   - Trading Engine"
    echo "  webhook_receiver - Webhook Receiver"
    echo "  order_monitor    - Order Monitor"
    echo "  frontend         - Frontend Vue.js"
    echo "  all              - Tous les services"
    echo ""
    echo "Commandes:"
    echo "  start   - Démarrer un service"
    echo "  stop    - Arrêter un service"
    echo "  restart - Redémarrer un service"
    echo "  status  - Vérifier le statut d'un service"
    echo "  logs    - Afficher les logs d'un service"
}

# Fonction pour démarrer un service
start_service() {
    local service=$1
    local script="$SCRIPTS_DIR/start_${service}.sh"
    local pid_file="$PID_DIR/${service}.pid"
    
    if [[ -f "$pid_file" ]] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        echo -e "${YELLOW}[WARNING]${NC} $service est déjà en cours d'exécution (PID: $(cat $pid_file))"
        return 1
    fi
    
    echo -e "${BLUE}[STARTING]${NC} $service..."
    nohup "$script" > "$LOG_DIR/${service}.log" 2>&1 &
    echo $! > "$pid_file"
    sleep 2
    
    if kill -0 $(cat "$pid_file") 2>/dev/null; then
        echo -e "${GREEN}[OK]${NC} $service démarré (PID: $(cat $pid_file))"
    else
        echo -e "${RED}[ERROR]${NC} Échec du démarrage de $service"
        rm -f "$pid_file"
    fi
}

# Fonction pour arrêter un service
stop_service() {
    local service=$1
    local pid_file="$PID_DIR/${service}.pid"
    
    if [[ ! -f "$pid_file" ]]; then
        echo -e "${YELLOW}[WARNING]${NC} $service n'est pas en cours d'exécution"
        return 1
    fi
    
    local pid=$(cat "$pid_file")
    echo -e "${BLUE}[STOPPING]${NC} $service (PID: $pid)..."
    
    kill $pid 2>/dev/null
    sleep 2
    
    if kill -0 $pid 2>/dev/null; then
        kill -9 $pid 2>/dev/null
    fi
    
    rm -f "$pid_file"
    echo -e "${GREEN}[OK]${NC} $service arrêté"
}

# Fonction pour vérifier le statut
status_service() {
    local service=$1
    local pid_file="$PID_DIR/${service}.pid"
    
    if [[ -f "$pid_file" ]] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        echo -e "${GREEN}[RUNNING]${NC} $service (PID: $(cat $pid_file))"
    else
        echo -e "${RED}[STOPPED]${NC} $service"
        [[ -f "$pid_file" ]] && rm -f "$pid_file"
    fi
}

# Fonction pour afficher les logs
logs_service() {
    local service=$1
    local log_file="$LOG_DIR/${service}.log"
    
    if [[ -f "$log_file" ]]; then
        tail -f "$log_file"
    else
        echo -e "${YELLOW}[WARNING]${NC} Pas de fichier log pour $service"
    fi
}

# Main
if [[ $# -lt 1 ]]; then
    show_help
    exit 1
fi

command=$1
service=${2:-"all"}

case $command in
    start)
        if [[ "$service" == "all" ]]; then
            for s in "${SERVICES[@]}"; do
                start_service $s
            done
        else
            start_service $service
        fi
        ;;
    stop)
        if [[ "$service" == "all" ]]; then
            for s in "${SERVICES[@]}"; do
                stop_service $s
            done
        else
            stop_service $service
        fi
        ;;
    restart)
        stop_service $service
        sleep 2
        start_service $service
        ;;
    status)
        if [[ "$service" == "all" ]]; then
            for s in "${SERVICES[@]}"; do
                status_service $s
            done
        else
            status_service $service
        fi
        ;;
    logs)
        logs_service $service
        ;;
    *)
        show_help
        ;;
esac
