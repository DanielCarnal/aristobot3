# Party Mode — Gotcha #3 : Deux Systèmes Pub/Sub

**Date :** 2026-02-05
**Contexte :** Audit des gotchas identifiés par Cartographer (docs/CODEBASE_MAP.md)
**Facilitateur :** Claude Code

---

## Participants

| Agent | Rôle | Perspective apportée |
|-------|------|---------------------|
| 🏗️ Winston | Architecte système | Mise en place du cadre technique, analyse des deux systèmes |
| 🔬 Dr. Quinn | Résolutrice de problèmes | Analyse de la cause racine, évaluation des options de unification |
| 🚀 Barry | Solo dev pragmatique | Verdict coût/bénéfice du changement |
| 📋 John | Product Manager | Perspective utilisateur, risque futur sur les prochains modules |

---

## Sujet de la discussion

Aristobot3 utilise deux systèmes de communication Pub/Sub indépendants entre ses terminaux backend :

- **Django Channels** (`channel_layer.group_send`) — utilisé pour envoyer des données vers le frontend via les consumers WebSocket
- **Redis natif** (`redis.asyncio publish/subscribe`) — utilisé par Terminal 6 (Webhook Receiver) pour publier vers Terminal 3 (Trading Engine)

Ces deux systèmes sont **incompatibles** : un message publié dans l'un n'arrive jamais dans l'autre, sans erreur ni log.

La question posée à la réunion : c'était une erreur ? Faut-il unifier ?

---

## Analyse : Quelles fonctionnalités sont touchées ?

Trois flux de communication sont concernés par cette split :

**1. Heartbeat vers Terminal 3 (stratégies)**
Terminal 2 reçoit une bougie fermée de Binance et la pousse vers Terminal 3 via Django Channels. Fonctionne parce que les deux sont des management commands Django et ont accès au même `channel_layer`.

**2. Heartbeat vers le frontend (affichage)**
Même canal Django Channels. Le navigateur reçoit les signaux en temps réel via les consumers WebSocket dans Daphne. Pas de problème.

**3. Webhooks TradingView vers Terminal 3**
Terminal 6 reçoit le POST depuis TradingView, publie sur Redis natif. Terminal 3 écoute sur Redis natif. Fonctionne parce que les deux côtés utilisent le même langage.

**Ce qui n'est pas touché :**
- Le frontend — il ne sait rien de cette split. Il ne parle qu'aux consumers WebSocket dans Daphne.
- Terminal 5 (Exchange Gateway) — il utilise un troisième pattern : une file de requêtes Redis avec réponse sur une clé unique. C'est du request/response, pas du Pub/Sub.

---

## Analyse : C'était une erreur ?

**Conclusion unanime : Non.**

La cause racine est claire. Terminal 6 existe séparé de Django pour une raison précise : il doit recevoir les webhooks TradingView depuis Internet avec une latence minimale. Le middleware Django complet sur le chemin critique de la réception d'un endpoint qui fait littéralement trois choses (recevoir, valider un token, publier) serait un surcoût architectural injustifié.

Puisque Terminal 6 ne tourne pas dans Django, il ne peut pas accéder à `channel_layer`. Il **doit** utiliser Redis natif. Le deuxième système existe donc comme conséquence directe de cette décision — qui est elle-même correcte.

C'est un **trade-off**, pas un bug.

---

## Analyse : Faut-il unifier ?

Deux options ont été étudiées :

**Option A : Faire de Terminal 6 un management command Django**
- Pros : tout le monde parle le même langage, plus de split
- Cons : on casse exactement la raison pour laquelle Terminal 6 existe séparé. Le surcoût Django sur la réception des webhooks est précisément ce qu'on voulait éviter.
- Verdict : non

**Option B : Faire publier Terminal 2 sur les deux systèmes**
- Pros : Terminal 3 n'écoute plus qu'un seul système (Redis natif)
- Cons : Terminal 2 fait deux publications pour chaque signal. Duplication de données. Complique un code qui fonctionne.
- Verdict : non

**Verdict de Barry (pragmatique) :** Les deux options ajoutent de la complexité pour résoudre un problème qui n'en est pas un. Le coût d'un changement — temps de développement, risque de régression — dépasse largement le bénéfice, qui est uniquement un gain de mental overhead pour les développeurs.

---

## Décisions prises

| # | Décision | Responsable |
|---|----------|-------------|
| 1 | Le code reste tel quel. Aucune modification des deux systèmes Pub/Sub. | — |
| 2 | La règle de décision (quel système utiliser quand) est écrite dans **DEVELOPMENT_RULES.md**, section Règle #2, "Deux Systèmes Pub/Sub". | ✅ fait |
| 3 | Une explication accessible au PO est ajoutée dans **Aristobot3_1.md**, section 3 "Comment les services parlent entre eux". | ✅ fait |

---

## Risque résiduel

Le seul risque identifié est celui de **John** : quand les Modules 5, 6, 7 seront développés, chaque nouveau signal entre terminaux devra être publié dans le bon système. Si la règle n'est pas consultée avant de développer, le résultat sera un silence complet — pas d'erreur, le message disparaît.

La mitigation : la règle est maintenant dans DEVELOPMENT_RULES.md, le fichier lu en priorité par Claude Code avant tout développement.

---

*Document généré suite à la réunion Party Mode du 2026-02-05. Validé par les participants.*
