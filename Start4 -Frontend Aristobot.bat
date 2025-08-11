::@echo off
REM Active conda et l'environnement
call C:\ProgramData\anaconda3\Scripts\activate.bat
call conda activate aristobot3
echo Environnement activé: %CONDA_DEFAULT_ENV%

REM Aller dans le dossier du backend
c:
cd /d C:\Users\dac\Documents\Python\Django\Aristobot3\frontend
echo Dossier frontend ouvert
:RESTART
npm run dev
pause
REM -- Fin du processus Daphne, proposer redémarrage ou sortie --
echo.
echo ==================================================================
echo Script terminé. Que souhaitez-vous faire ?
echo [R] Redémarrer
echo [Q] Quitter
echo ==================================================================
choice /c rq /n /m "Votre choix (r/q) : "

if errorlevel 2 goto END
if errorlevel 1 goto RESTART

:END
echo Fermeture du script...
timeout /t 2 >nul
exit

