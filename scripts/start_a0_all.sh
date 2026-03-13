#!/bin/bash
# =============================================================================
# ARISTOBOT3 - Démarrage Complet de l'Application
# =============================================================================

PROJECT_DIR="/a0/usr/projects/Aristobot3"
SCRIPTS_DIR="$PROJECT_DIR/scripts"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}🚀 ARISTOBOT3 - DÉMARRAGE COMPLET${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""

# Ordre de démarrage des services
echo -e "${BLUE}[1/7]${NC} Démarrage Backend Daphne..."
"$SCRIPTS_DIR/manage.sh" start backend
sleep 3

echo -e "${BLUE}[2/7]${NC} Démarrage Native Exchange Service..."
"$SCRIPTS_DIR/manage.sh" start exchange_service
sleep 2

echo -e "${BLUE}[3/7]${NC} Démarrage Heartbeat..."
"$SCRIPTS_DIR/manage.sh" start heartbeat
sleep 2

echo -e "${BLUE}[4/7]${NC} Démarrage Trading Engine..."
"$SCRIPTS_DIR/manage.sh" start trading_engine
sleep 2

echo -e "${BLUE}[5/7]${NC} Démarrage Webhook Receiver..."
"$SCRIPTS_DIR/manage.sh" start webhook_receiver
sleep 2

echo -e "${BLUE}[6/7]${NC} Démarrage Order Monitor..."
"$SCRIPTS_DIR/manage.sh" start order_monitor
sleep 2

echo -e "${BLUE}[7/7]${NC} Démarrage Frontend..."
"$SCRIPTS_DIR/manage.sh" start frontend

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ DÉMARRAGE COMPLET TERMINÉ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Pour vérifier le statut: ./scripts/manage.sh status all"
echo "Pour voir les logs: ./scripts/manage.sh logs <service>"
echo ""
