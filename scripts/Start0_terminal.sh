#!/bin/bash
# ===============================================
#    ARISTOBOT3 - Terminal 0
#    Ouvre un shell avec conda + env activé
# ===============================================
export PATH="/home/dac/miniconda3/bin:$PATH"
eval "$(/home/dac/miniconda3/bin/conda shell.bash hook)"
conda activate Aristobot3

echo "Environnement activé: $CONDA_DEFAULT_ENV"

cd ~/Dev/Aristobot3
echo "Dossier projet ouvert"

# Ouvre un shell interactif dans cet environnement
exec bash
