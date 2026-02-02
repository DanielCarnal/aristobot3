---
workflow: bmad:bmb:workflows:agent
mode: CREATE
agent_name: debug-loguru
status: BUILD_COMPLETE
step: 8
date: 2026-02-01
---

## Agent Creation Complete

### Agent Summary

- **Name:** Lynx (debug-loguru)
- **Type:** Expert (stand-alone, sidecar)
- **Purpose:** Debug specialist pour Aristobot3 — instrumente automatiquement le code avec loguru, recherche dans les logs multi-terminaux, diagnostique les problemes, controle les niveaux de log en temps reel.
- **Status:** Ready for installation

### File Locations

- **Agent Config:** `_bmad-output/bmb-creations/debug-loguru/debug-loguru.agent.yaml`
- **Sidecar:** `_bmad-output/bmb-creations/debug-loguru/debug-loguru-sidecar/`
  - `memories.yaml` — Memoire des sessions (vide au demarrage)
  - `instructions.md` — Protocoles operationnels complets

### Capabilities

| Commande | Trigger | Fonction |
|----------|---------|----------|
| debug-loguru | DL | Entrée principale — auto-déduction des 4 modes |
| debug-memory | DM | Affiche les 5 dernières sessions memorisees |
| debug-bmad | DB | Delegation forcée a BMAD |

### 4 Modes (auto-déduits)

1. **INSTRUMENTE** — Scan fichier Python, propose diff lisible, insère loguru aux points stratégiques
2. **RECHERCHE** — Sélectionne terminaux, lance log_aggregator.py avec les bons arguments
3. **DIAGNOSTIQUE** — Analyse flow architecturel, détecte complexité (3 signaux), propose délégation BMAD si ≥2 signaux
4. **CONTROLE VIVANT** — Ajuste niveaux de log, rétention, query couverture debug

### Installation

Package comme module standalone avec `module.yaml` contenant `unitary: true`.

```
my-custom-stuff/
├── module.yaml                    # unitary: true
└── agents/
    └── debug-loguru/
        ├── debug-loguru.agent.yaml
        └── _memory/
            └── debug-loguru-sidecar/
                ├── memories.yaml
                └── instructions.md
```

📖 Documentation officielle : https://github.com/bmad-code-org/BMAD-METHOD/blob/main/docs/modules/bmb-bmad-builder/custom-content-installation.md#standalone-content-agents-workflows-tasks-tools-templates-prompts
