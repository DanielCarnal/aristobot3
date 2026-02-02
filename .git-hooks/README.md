# Git Hooks Aristobot3

Ce dossier contient les hooks Git personnalisés pour Aristobot3.

---

## 📋 Hooks Disponibles

### `pre-commit`

**Objectif :** Rappeler de régénérer `CODEBASE_MAP.md` quand l'architecture est modifiée.

**Déclencheurs :**
- Modifications dans `backend/apps/`
- Modifications dans `frontend/src/views/`
- Modifications dans `frontend/src/components/`

**Comportement :**
1. Détecte les fichiers architecture modifiés
2. Affiche la liste des fichiers concernés
3. Demande confirmation pour continuer le commit
4. Rappelle de régénérer avec `/cartographer`

---

## 🔧 Installation

### Méthode 1 : Installation Manuelle (Windows/Linux/Mac)

```bash
# Depuis la racine du projet Aristobot3

# Copier le hook dans .git/hooks/
cp .git-hooks/pre-commit .git/hooks/pre-commit

# Rendre exécutable (Linux/Mac uniquement)
chmod +x .git/hooks/pre-commit
```

### Méthode 2 : Script Automatique (Linux/Mac)

```bash
# Depuis la racine du projet
bash .git-hooks/install.sh
```

### Windows (Git Bash)

```bash
# Depuis Git Bash
cp .git-hooks/pre-commit .git/hooks/pre-commit
```

---

## ✅ Vérification Installation

```bash
# Vérifier que le hook existe
ls -la .git/hooks/pre-commit

# Tester le hook manuellement
.git/hooks/pre-commit
```

---

## 🚫 Désactivation Temporaire

Si vous devez temporairement désactiver le hook :

```bash
# Option 1 : Renommer
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Option 2 : Utiliser --no-verify lors du commit
git commit --no-verify -m "Message commit"
```

**⚠️ Attention :** Utiliser `--no-verify` désactive TOUS les hooks, pas seulement celui-ci.

---

## 📝 Exemple d'Utilisation

```bash
# Vous modifiez un fichier dans backend/apps/webhooks/
vim backend/apps/webhooks/views.py

# Vous stagez les modifications
git add backend/apps/webhooks/views.py

# Vous tentez de commit
git commit -m "Ajout endpoint webhook stats"

# Le hook détecte la modification et affiche:
# ⚠️  RAPPEL: Fichiers architecture modifiés détectés !
#    Fichiers modifiés dans:
#      - backend/apps/webhooks/views.py
#
#    📚 Avez-vous régénéré CODEBASE_MAP.md avec /cartographer ?
#    Continuer le commit ? (y/n)

# Vous répondez 'n', régénérez avec /cartographer, puis re-commitez
```

---

## 🔄 Mise à Jour des Hooks

Pour mettre à jour un hook après modification :

```bash
# Depuis la racine du projet
cp .git-hooks/pre-commit .git/hooks/pre-commit
```

---

## 📚 Référence

Pour plus de détails sur la maintenance documentation :

👉 **Voir [DEVELOPMENT_RULES.md](../DEVELOPMENT_RULES.md) RÈGLE #6**

---

**Hooks maintenus par :** Paige (Technical Writer)
**Dernière mise à jour :** 2026-02-02
