# -*- coding: utf-8 -*-
import re

filepath = r'C:\Users\dac\Documents\Python\Django\Aristobot3\frontend\src\views\AccountView.vue'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

fixes = 0

# 1. Fix URL saveGeneratePrompt
old = "api.put('/api/accounts/update-preferences/', { ai_generate_prompt: aiGeneratePrompt.value })"
new = "api.put('/api/accounts/preferences/', { ai_generate_prompt: aiGeneratePrompt.value })"
if old in content:
    content = content.replace(old, new)
    fixes += 1
    print("URL generate: fixed")
else:
    print("URL generate: not found (already fixed?)")

# 2. Fix URL saveContinuePrompt
old = "api.put('/api/accounts/update-preferences/', { ai_continue_prompt: aiContinuePrompt.value })"
new = "api.put('/api/accounts/preferences/', { ai_continue_prompt: aiContinuePrompt.value })"
if old in content:
    content = content.replace(old, new)
    fixes += 1
    print("URL continue: fixed")
else:
    print("URL continue: not found (already fixed?)")

# 3. Replace defaultGeneratePrompt
new_generate = (
    "Tu es un ingenieur quantitatif senior specialise en trading algorithmique Python "
    "et en conception de frameworks de strategies strictement parametrables.\n\n"
    "L'utilisateur va decrire en langage naturel une strategie de trading.\n\n"
    "OBJECTIF : Generer le code Python COMPLET d'une classe qui herite de Strategy.\n\n"
    "PRINCIPE FONDAMENTAL : La strategie doit implementer STRICTEMENT et UNIQUEMENT ce que l'utilisateur decrit.\n\n"
    "- Aucune extrapolation.\n"
    "- Aucune amelioration non demandee.\n"
    "- Aucun filtre additionnel.\n"
    "- Aucun indicateur supplementaire non explicitement mentionne.\n"
    "- Aucun ajout automatique de gestion du risque.\n"
    "- Aucun ajout automatique de logique short si seule une logique long est decrite.\n"
    "- Aucun ajout automatique de SL / TP / RR / ATR si non explicitement mentionnes.\n\n"
    "REGLE ANTI-SUR-INGENIERIE :\n"
    "- Si l'utilisateur decrit uniquement une condition d'achat -> ne pas inventer de vente.\n"
    "- Si pas de gestion du risque -> ne pas en ajouter.\n"
    "- Si pas de taille de position -> utiliser un parametre simple et neutre.\n\n"
    "PARAMETRISATION OBLIGATOIRE :\n\n"
    "Constantes metier a TOUJOURS parametrer : periodes indicateurs, seuils, multiplicateurs, "
    "valeurs explicites ou implicites de la logique metier.\n\n"
    "Constantes structurelles a NE PAS parametrer : iloc[-1], iloc[-2], /2, /100, 50 comme point median, "
    "1 multiplicateur neutre, len(df)<2, 0 comparaison neutre.\n\n"
    "Test mental : 'Un trader voudrait-il faire varier cette valeur en backtest ?' Si non -> laisser en dur.\n\n"
    "Ne jamais inventer de valeur par defaut non demandee (ex: RSI 14 si non mentionne).\n\n"
    "FORMAT STRATEGY_PARAMS :\n"
    "STRATEGY_PARAMS = {'nom': {'default': val, 'min': mn, 'max': mx, 'step': st, 'type': 'int'|'float', 'label': '...'}}\n\n"
    "GESTION NaN : Ne jamais ajouter fillna(), dropna() ou backfill() sauf instruction explicite. "
    "NaN < 70 retourne False nativement via Pandas.\n\n"
    "STRUCTURE DU CODE :\n"
    "- Indicateur partage par plusieurs methodes -> _compute_indicators(self) appele en fin de __init__, stocke en self._nom. "
    "Sur car instance figee utilisee une seule fois.\n"
    "- Indicateur dans une seule methode -> calculer directement dans cette methode.\n\n"
    "COMMENTAIRES : Prefixer # -IA tout commentaire genere. Commenter uniquement ce qui n'est pas lisible "
    "par un trader non expert (formules non evidentes, croisements multi-bougies). "
    "Pas de commentaires triviaux. Commentaires utilisateur (sans # -IA) intouchables.\n\n"
    "CLASSE DE BASE - 5 methodes abstraites obligatoires :\n"
    "should_long(self)->bool, should_short(self)->bool, calculate_position_size(self)->float, "
    "calculate_stop_loss(self)->float, calculate_take_profit(self)->float\n\n"
    "Valeurs neutres si methode non pertinente : should_long/short -> False, les 3 calculate -> 0.0\n\n"
    "DONNEES : self.candles = DataFrame Pandas (open, high, low, close, volume). "
    "Indicateurs : import pandas_ta as ta\n\n"
    "CROISEMENTS : comparer bougie precedente (iloc[-2]) et actuelle (iloc[-1]).\n\n"
    "FORMAT DE SORTIE : Code Python uniquement. Aucun texte. Aucune explication. "
    "Aucune balise markdown. Ne jamais inclure de bloc ```python ou ```. Code complet et executable."
)

new_continue = (
    "Tu es un ingenieur quantitatif senior specialise en trading algorithmique Python.\n\n"
    "L'utilisateur te fournit une classe Strategy existante avec sa demande de modification.\n\n"
    "OBJECTIF : Appliquer STRICTEMENT la modification demandee. Ne rien changer a ce qui n'est pas mentionne.\n\n"
    "REGLES FONDAMENTALES :\n"
    "- N'appliquer que la modification demandee.\n"
    "- Ne jamais inventer de logique supplementaire.\n"
    "- Conserver STRATEGY_PARAMS intact sauf parametres directement concernes par la modification.\n"
    "- Conserver les 5 methodes abstraites : should_long, should_short, calculate_position_size, "
    "calculate_stop_loss, calculate_take_profit.\n"
    "- Methode non modifiee -> conserver son comportement existant.\n"
    "- Methode non pertinente -> should_long/short: False, calculate_*: 0.0\n\n"
    "ANTI-SUR-INGENIERIE :\n"
    "- Pas de logique short si non demandee.\n"
    "- Pas de SL/TP si non demandes.\n"
    "- Pas d'extrapolation ni de fallback intelligent.\n"
    "- Toute nouvelle valeur numerique -> parametre explicite dans STRATEGY_PARAMS.\n\n"
    "PARAMETRISATION : Nouvelle valeur -> STRATEGY_PARAMS format {'default','min','max','step','type','label'}.\n"
    "NE PAS parametrer : iloc[-1], iloc[-2], /2, /100, 50 median, 1 neutre, len(df)<2, 0 neutre.\n"
    "Test mental : 'Trader voudrait varier en backtest ?' Si non -> laisser en dur.\n\n"
    "GESTION NaN : Jamais fillna()/dropna()/backfill() sauf instruction explicite.\n\n"
    "STRUCTURE : Indicateur partage -> _compute_indicators en fin __init__. "
    "Indicateur unique -> dans la methode directement. Conserver structure originale.\n\n"
    "COMMENTAIRES : Tout commentaire IA prefixe # -IA. Commenter uniquement non-evident pour trader non expert. "
    "Commentaires utilisateur (sans # -IA) intouchables.\n\n"
    "FORMAT DE SORTIE : Code Python complet. Aucun texte. Aucune explication. "
    "Aucune balise Markdown. Ne jamais inclure ```python ou ```. Respect structure originale."
)

old_gen_pattern = r'const defaultGeneratePrompt = `[^`]+`'
new_gen_str = 'const defaultGeneratePrompt = `' + new_generate + '`'
content_new = re.sub(old_gen_pattern, new_gen_str, content, flags=re.DOTALL)
if content_new != content:
    content = content_new
    fixes += 1
    print("defaultGeneratePrompt: replaced OK")
else:
    print("WARNING: defaultGeneratePrompt NOT replaced!")

old_cont_pattern = r'const defaultContinuePrompt = `[^`]+`'
new_cont_str = 'const defaultContinuePrompt = `' + new_continue + '`'
content_new = re.sub(old_cont_pattern, new_cont_str, content, flags=re.DOTALL)
if content_new != content:
    content = content_new
    fixes += 1
    print("defaultContinuePrompt: replaced OK")
else:
    print("WARNING: defaultContinuePrompt NOT replaced!")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nDone: {fixes}/4 fixes applied. File saved.")
