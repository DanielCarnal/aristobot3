@echo off

REM -- Activer conda et l'environnement --
call C:\ProgramData\anaconda3\Scripts\activate.bat
call conda activate aristobot3
echo Environnement activé: %CONDA_DEFAULT_ENV%

REM -- Aller dans le dossier du backend --
cd /d C:\Users\dac\Documents\Python\Django\Aristobot3\backend
echo Dossier backend ouvert

REM -- Afficher le contenu du dossier --
dir
:RESTART
REM -- Lancer Daphne --
echo 🚀 Lancement de Daphne...
daphne --verbosity 2 aristobot.asgi:application

REM -- Fin du processus Daphne, proposer redémarrage ou sortie --
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
