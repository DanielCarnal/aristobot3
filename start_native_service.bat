@echo off
:: Configuration UTF-8 pour emojis
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: Activation environnement Conda
call C:\ProgramData\anaconda3\Scripts\activate.bat aristobot3

:: Démarrage service natif
cd /d "C:\Users\dac\Documents\Python\Django\Aristobot3\backend"
python manage.py run_native_exchange_service --verbose

pause