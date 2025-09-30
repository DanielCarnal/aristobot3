@echo off
chcp 65001
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
echo ===============================================
echo    ARISTOBOT3.1 - Terminal 7 ()
echo    Service: Order Monitor
echo    Commande: run_order_monitor
echo ===============================================

REM Active conda et l'environnement
call C:\ProgramData\anaconda3\Scripts\activate.bat
call conda activate aristobot3
echo Environnement activé: %CONDA_DEFAULT_ENV%

REM Aller dans le dossier du backend
c:
cd /d C:\Users\dac\Documents\Python\Django\Aristobot3\backend
echo Dossier backend ouvert

:RESTART
echo.
echo [DEMARRAGE] Terminal 7 - Order Monitor Service
python manage.py run_order_monitor --verbose


echo.
echo ==================================================================
echo Script terminé. Que souhaitez-vous faire ?
echo [R] Redémarrer
echo [Q] Quitter
echo ==================================================================
choice /c RQ /n /m "Votre choix (R/Q) : "

if errorlevel 2 goto END
if errorlevel 1 goto RESTART

:END
echo Fermeture du script...
timeout /t 2 >nul
exit
pause
