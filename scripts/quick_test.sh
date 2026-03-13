#!/bin/bash
# =============================================================================
# ARISTOBOT3 - Test Rapide
# =============================================================================

echo "========================================"
echo "🧪 TEST RAPIDE TERMINAL 6"
echo "========================================"
echo ""

echo "1. Test Health Check..."
curl -s http://localhost:8888/health
echo ""
echo ""

echo "2. Test Webhook PING..."
curl -s -X POST http://localhost:8888/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: aristobot_webhook_secret_dev_2026" \
  -d '{"Symbol":"BTCUSDT","Action":"PING"}'
echo ""
echo ""

echo "3. Nouvelle vérification Health (doit montrer 1 webhook reçu)..."
curl -s http://localhost:8888/health
echo ""
echo ""

echo "========================================"
echo "✅ TERMINE - Vérifie Terminal 6 pour logs"
echo "========================================"
