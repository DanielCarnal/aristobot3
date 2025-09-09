::@echo off
chcp 65001
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
REM Active conda et l'environnement
call C:\ProgramData\anaconda3\Scripts\activate.bat
call conda activate aristobot3
echo Environnement activé: %CONDA_DEFAULT_ENV%

REM Aller dans le dossier du projet
c:
cd /d C:\Users\dac\Documents\Python\Django\Aristobot3
echo Dossier frontend ouvert


call cmd