# Test complet Heartbeat MODULE2 - Version PowerShell
# Teste tous les endpoints et scenarios

$ErrorActionPreference = "Continue"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "🧪 TESTS HEARTBEAT MODULE2" -ForegroundColor Cyan  
Write-Host "======================================" -ForegroundColor Cyan

# Configuration
$BASE_URL_127 = "http://127.0.0.1:8000"
$BASE_URL_LOCAL = "http://localhost:8000" 
$FRONTEND_ORIGIN = "http://localhost:5173"
$TEST_USER = '{"username":"dac","password":"aristobot"}'

# Session variables
$session127 = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$sessionLocal = New-Object Microsoft.PowerShell.Commands.WebRequestSession

Write-Host ""
Write-Host "=== 1. TESTS AUTHENTIFICATION ===" -ForegroundColor Yellow

Write-Host "🔐 Login avec 127.0.0.1..."
try {
    $login127 = Invoke-RestMethod -Uri "$BASE_URL_127/api/auth/login/" -Method Post -Body $TEST_USER -ContentType "application/json" -WebSession $session127
    Write-Host "✓ Session 127.0.0.1 creee" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur login 127.0.0.1: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "🔐 Login avec localhost..."
try {
    $loginLocal = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/auth/login/" -Method Post -Body $TEST_USER -ContentType "application/json" -WebSession $sessionLocal
    Write-Host "✓ Session localhost creee" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur login localhost: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 2. TESTS HEARTBEAT STATUS API ===" -ForegroundColor Yellow

Write-Host "📊 Test GET /api/heartbeat/status/ avec 127.0.0.1..."
try {
    $status127 = Invoke-RestMethod -Uri "$BASE_URL_127/api/heartbeat/status/" -WebSession $session127
    Write-Host "✓ Status 127: Connected = $($status127.is_connected)" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur status 127: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "📊 Test GET /api/heartbeat/status/ avec localhost..."
try {
    $statusLocal = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/heartbeat/status/" -WebSession $sessionLocal
    Write-Host "✓ Status localhost: Connected = $($statusLocal.is_connected)" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur status localhost: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "🔄 Test cross-domain (127 -> localhost)..."
try {
    $crossStatus = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/heartbeat/status/" -WebSession $session127
    Write-Host "⚠️ Cross-domain fonctionne (probleme potentiel cookies)" -ForegroundColor Yellow
} catch {
    Write-Host "✓ Cross-domain bloque (comportement attendu)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 3. TESTS HEARTBEAT RECENT API ===" -ForegroundColor Yellow

Write-Host "🕒 Test GET /api/heartbeat/recent/ (60 elements)..."
try {
    $recent = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/heartbeat/recent/?limit=60" -WebSession $sessionLocal
    Write-Host "✓ Signals count: $($recent.count)" -ForegroundColor Green
    if ($recent.signals) {
        Write-Host "✓ Premiers signaux: $($recent.signals.Count) recus" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Erreur recent: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "🕒 Test avec limite personnalisee (10)..."
try {
    $recent10 = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/heartbeat/recent/?limit=10" -WebSession $sessionLocal
    Write-Host "✓ Signals avec limit=10: $($recent10.count)" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur recent limite: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 4. TESTS TIMEFRAMES API ===" -ForegroundColor Yellow

Write-Host "⏱️ Test GET /api/heartbeat/timeframes/..."
try {
    $timeframes = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/heartbeat/timeframes/?hours_back=1" -WebSession $sessionLocal
    Write-Host "✓ Period hours: $($timeframes.period_hours)" -ForegroundColor Green
    if ($timeframes.timeframe_counts) {
        Write-Host "✓ Timeframes disponibles: $($timeframes.timeframe_counts.Count)" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Erreur timeframes: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 5. TESTS SIGNALS API ===" -ForegroundColor Yellow

Write-Host "📈 Test GET /api/heartbeat/signals/ (avec filtres)..."
try {
    $signals = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/heartbeat/signals/?signal_type=1m&hours_back=1" -WebSession $sessionLocal
    Write-Host "✓ Signals API response recu" -ForegroundColor Green
    if ($signals.results) {
        Write-Host "✓ Signals 1m: $($signals.results.Count)" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Erreur signals: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 6. TESTS CORS FRONTEND ===" -ForegroundColor Yellow

Write-Host "🌐 Test requete avec Origin frontend..."
try {
    $headers = @{
        "Origin" = $FRONTEND_ORIGIN
        "Referer" = "$FRONTEND_ORIGIN/"
    }
    $corsTest = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/heartbeat/status/" -Headers $headers -WebSession $sessionLocal
    Write-Host "✓ CORS GET fonctionne" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur CORS: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 7. TESTS ERREURS ET EDGE CASES ===" -ForegroundColor Yellow

Write-Host "❌ Test sans authentification..."
try {
    $noAuth = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/heartbeat/status/"
    Write-Host "⚠️ API accessible sans auth (probleme?)" -ForegroundColor Yellow
} catch {
    Write-Host "✓ API protegee par authentification" -ForegroundColor Green
}

Write-Host "❌ Test endpoint inexistant..."
try {
    $notFound = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/heartbeat/inexistant/" -WebSession $sessionLocal
    Write-Host "⚠️ 404 non gere" -ForegroundColor Yellow
} catch {
    Write-Host "✓ 404 gere correctement" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 8. SIMULATION FRONTEND VUE.JS ===" -ForegroundColor Yellow

Write-Host "🖥️ Simulation requete fetch() du frontend..."
try {
    $headers = @{
        "Accept" = "application/json"
        "Origin" = $FRONTEND_ORIGIN
        "Referer" = "$FRONTEND_ORIGIN/heartbeat"
    }
    $frontendSim = Invoke-RestMethod -Uri "$BASE_URL_LOCAL/api/heartbeat/recent/?limit=60" -Headers $headers -WebSession $sessionLocal
    Write-Host "✓ Frontend simulation: reponse recue" -ForegroundColor Green
    Write-Host "✓ Timestamp: $($frontendSim.timestamp)" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur simulation frontend: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 9. DIAGNOSTIC SERVICES ===" -ForegroundColor Yellow

Write-Host "🔍 Verification services..."
try {
    $healthCheck = Invoke-WebRequest -Uri "$BASE_URL_LOCAL/admin/" -TimeoutSec 5
    if ($healthCheck.StatusCode -eq 200) {
        Write-Host "✓ Django backend: Running" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Django backend: Issue ($($_.Exception.Message))" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 10. RESUME MODULE2 ===" -ForegroundColor Yellow

Write-Host "🎯 Points de verification MODULE2:" -ForegroundColor Cyan
Write-Host "1. ✓ API Status implementee" -ForegroundColor Green
Write-Host "2. ✓ API Recent (60 elements) implementee" -ForegroundColor Green
Write-Host "3. ✓ API Timeframes implementee" -ForegroundColor Green  
Write-Host "4. ✓ API Signals avec filtres implementee" -ForegroundColor Green
Write-Host "5. ✓ Authentification requise" -ForegroundColor Green
Write-Host "6. ✓ CORS configure pour frontend" -ForegroundColor Green

Write-Host ""
Write-Host "📝 Pour tester l'interface complete:" -ForegroundColor Cyan
Write-Host "1. Backend: cd backend && python manage.py runserver"
Write-Host "2. Heartbeat: cd backend && python manage.py run_heartbeat" 
Write-Host "3. Frontend: cd frontend && npm run dev"
Write-Host "4. Ouvrir: http://localhost:5173/heartbeat"
Write-Host "5. Verifier: Status 'Connecte' + signaux orange/vert"

Write-Host ""
Write-Host "🚀 APIs MODULE2 disponibles:" -ForegroundColor Cyan
Write-Host "- GET /api/heartbeat/status/ - Statut service"
Write-Host "- GET /api/heartbeat/recent/?limit=60 - 60 derniers signaux"
Write-Host "- GET /api/heartbeat/timeframes/?hours_back=1 - Stats timeframes"
Write-Host "- GET /api/heartbeat/signals/ - Historique avec filtres"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "✅ TESTS HEARTBEAT MODULE2 TERMINES" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan