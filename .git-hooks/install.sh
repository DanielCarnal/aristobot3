#!/bin/bash
#
# Script d'installation des Git Hooks Aristobot3
#

echo ""
echo "🔧 Installation Git Hooks Aristobot3"
echo "===================================="
echo ""

# Vérifier qu'on est à la racine du projet
if [ ! -d ".git" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet"
    echo "   (dossier contenant .git/)"
    exit 1
fi

# Copier le hook pre-commit
echo "📋 Installation pre-commit hook..."
cp .git-hooks/pre-commit .git/hooks/pre-commit

# Rendre exécutable
chmod +x .git/hooks/pre-commit

# Vérifier installation
if [ -f ".git/hooks/pre-commit" ]; then
    echo "✅ Hook pre-commit installé avec succès !"
    echo ""
    echo "📝 Le hook va maintenant rappeler de régénérer CODEBASE_MAP.md"
    echo "   quand des fichiers architecture sont modifiés."
    echo ""
    echo "📚 Voir .git-hooks/README.md pour plus de détails"
    echo ""
else
    echo "❌ Erreur lors de l'installation du hook"
    exit 1
fi

echo "✅ Installation terminée avec succès !"
echo ""
