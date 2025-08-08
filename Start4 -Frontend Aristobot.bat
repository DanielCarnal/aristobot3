::@echo off
REM Active conda et l'environnement
call C:\ProgramData\anaconda3\Scripts\activate.bat
call conda activate aristobot3
echo Environnement activé: %CONDA_DEFAULT_ENV%

REM Aller dans le dossier du backend
c:
cd /d C:\Users\dac\Documents\Python\Django\Aristobot3\frontend
echo Dossier frontend ouvert

npm run dev

pause
