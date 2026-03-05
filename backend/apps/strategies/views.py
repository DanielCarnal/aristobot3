# -*- coding: utf-8 -*-
"""
STRATEGIES VIEWSET - Module 5

CRUD strategies + validation AST + assistant IA trimodal.
Patch M5 v2 : extract_params + apply_params (Taches 1-6).
"""

import ast
import asyncio
import logging
import re

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .models import Strategy
from .serializers import StrategySerializer, StrategyValidationSerializer
from .services import AIAssistService

logger = logging.getLogger(__name__)

# Imports interdits dans le code utilisateur
FORBIDDEN_IMPORTS = {'os', 'subprocess', 'sys', 'socket', 'importlib', 'ctypes', 'multiprocessing', 'shutil', 'pathlib'}

# Les 5 methodes obligatoires pour une strategie valide
REQUIRED_METHODS = {'should_long', 'should_short', 'calculate_position_size', 'calculate_stop_loss', 'calculate_take_profit'}

# =============================================================================
# PATCH M5 v2 — Helpers extraction / application des parametres
# =============================================================================

# Heuristiques de nommage : (nom_fonction, nom_kwarg) -> nom_suggere
NAMING_PATTERNS = {
    ('rsi',    'length'): 'rsi_period',
    ('ema',    'length'): 'ema_period',
    ('sma',    'length'): 'sma_period',
    ('hma',    'length'): 'hma_period',
    ('wma',    'length'): 'wma_period',
    ('atr',    'length'): 'atr_period',
    ('bbands', 'length'): 'bb_period',
    ('macd',   'fast'):   'macd_fast',
    ('macd',   'slow'):   'macd_slow',
    ('macd',   'signal'): 'macd_signal',
    ('stoch',  'k'):      'stoch_k',
    ('stoch',  'd'):      'stoch_d',
}


def _infer_context(node, method_node):
    """Infere le contexte textuel d un AST Constant dans une methode."""
    try:
        lines = ast.unparse(method_node).split('\n')
        node_str = str(node.value)
        for line in lines:
            if node_str in line:
                return line.strip()[:60]
    except Exception:
        pass
    return str(node.value)


def _infer_name(value, context, used_names):
    """Infere un nom de parametre depuis le contexte de l'appel."""
    for (func, kwarg), template in NAMING_PATTERNS.items():
        if func in context and kwarg in context:
            name = template
            if name in used_names:
                name = f"{template}_2"
            return name
    # Assignation simple : "rr = 1.5" -> nom de la variable
    if '=' in context and '==' not in context:
        varname = context.split('=')[0].strip()
        if varname.isidentifier():
            return varname
    # Fallback sequentiel
    i = 1
    while f"param_{i}" in used_names:
        i += 1
    return f"param_{i}"


def _infer_range(value, vtype):
    """Calcule min / max / step suggeres selon le type et la valeur."""
    if vtype == 'int':
        v = int(value)
        mn = max(1, v // 4)
        mx = v * 4
        return mn, mx, 1
    else:
        v = float(value)
        mn = round(v * 0.1, 4)
        mx = round(v * 10, 4)
        step = round(v * 0.1, 4)
        return mn, mx, step


def _infer_label(name):
    """Produit un libelle lisible depuis un nom snake_case."""
    return name.replace('_', ' ').title()


def _extract_params(code):
    """
    Analyse le code AST et retourne les litteraux numeriques candidats
    qui ne sont pas encore parametres dans STRATEGY_PARAMS.

    Retourne : {'new_literals': [...], 'already_parameterized': [...]}
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {'new_literals': [], 'already_parameterized': []}

    # Trouver la classe heritant de Strategy
    cls_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                name = base.id if isinstance(base, ast.Name) else ''
                if name == 'Strategy':
                    cls_node = node
                    break
        if cls_node:
            break

    if not cls_node:
        return {'new_literals': [], 'already_parameterized': []}

    # Extraire les defaults deja dans STRATEGY_PARAMS
    existing_defaults = set()
    existing_names = []
    existing_params = []
    for stmt in cls_node.body:
        if (isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == 'STRATEGY_PARAMS'):
            try:
                sp = ast.literal_eval(stmt.value)
                for k, v in sp.items():
                    existing_defaults.add(v.get('default'))
                    existing_names.append(k)
                    existing_params.append({
                        'name':          k,
                        'label':         v.get('label', _infer_label(k)),
                        'default':       v.get('default', 0),
                        'min':           v.get('min', 0),
                        'max':           v.get('max', 100),
                        'step':          v.get('step', 1),
                        'type':          v.get('type', 'int'),
                        'replace_value': None,
                        'context':       'existant',
                        'occurrences':   0,
                    })
            except (ValueError, TypeError):
                pass
            break

    EXCLUDED_INDICES = {-1, 0, 1}
    code_lines = code.split('\n')
    found = {}  # value -> {'context': str, 'context_full': str, 'lineno': int, 'occurrences': int}

    for method in cls_node.body:
        if not isinstance(method, ast.FunctionDef):
            continue
        for node in ast.walk(method):
            if not isinstance(node, ast.Constant):
                continue
            if not isinstance(node.value, (int, float)):
                continue
            v = node.value
            if v in EXCLUDED_INDICES:
                continue
            if v in existing_defaults:
                continue
            lineno = getattr(node, 'lineno', None)
            if lineno and lineno <= len(code_lines):
                context_full = code_lines[lineno - 1].strip()
            else:
                context_full = _infer_context(node, method)
            context_short = context_full[:60]
            if v not in found:
                found[v] = {
                    'context': context_short,
                    'context_full': context_full,
                    'lineno': lineno,
                    'occurrences': 0,
                }
            found[v]['occurrences'] += 1

    new_literals = []
    used_names = set(existing_names)
    for value, info in found.items():
        name = _infer_name(value, info['context'], used_names)
        used_names.add(name)
        vtype = 'int' if isinstance(value, int) else 'float'
        mn, mx, step = _infer_range(value, vtype)
        new_literals.append({
            'value': value,
            'suggested_name': name,
            'suggested_label': _infer_label(name),
            'suggested_default': value,
            'suggested_min': mn,
            'suggested_max': mx,
            'suggested_step': step,
            'suggested_type': vtype,
            'context': info['context'],
            'context_full': info['context_full'],
            'lineno': info['lineno'],
            'occurrences': info['occurrences'],
        })

    return {
        'new_literals': new_literals,
        'already_parameterized': existing_names,
        'existing_params': existing_params,
    }


def _replace_literal_in_methods(code, value, replacement):
    """
    Remplace toutes les occurrences du litteral numerique 'value' dans les
    corps de methodes par 'replacement', en excluant le bloc STRATEGY_PARAMS.

    Strategie : remplacement ligne par ligne en sautant les lignes appartenant
    a STRATEGY_PARAMS (entre le debut du dict et la fermeture du dict).
    """
    value_str = str(value)
    # Pattern word-boundary : evite de remplacer "14" dans "140"
    pattern = re.compile(r'(?<![.\w])' + re.escape(value_str) + r'(?!\w)')

    lines = code.split('\n')
    result = []
    inside_strategy_params = False
    brace_depth = 0

    for line in lines:
        stripped = line.strip()

        # Detecter debut STRATEGY_PARAMS = {
        if re.match(r'STRATEGY_PARAMS\s*=\s*\{', stripped):
            inside_strategy_params = True
            brace_depth = line.count('{') - line.count('}')
            result.append(line)
            continue

        if inside_strategy_params:
            brace_depth += line.count('{') - line.count('}')
            result.append(line)
            if brace_depth <= 0:
                inside_strategy_params = False
            continue

        # Remplacement hors STRATEGY_PARAMS
        new_line = pattern.sub(replacement, line)
        result.append(new_line)

    return '\n'.join(result)


def _upsert_strategy_params(code, params):
    """
    Insere ou met a jour le bloc STRATEGY_PARAMS dans la classe Strategy.

    - Si STRATEGY_PARAMS existe : remplace le bloc existant en fusionnant
      les entrees presentes avec les nouveaux params.
    - Si absent : insere apres la ligne 'class XXX(Strategy):'.

    Format produit :
        STRATEGY_PARAMS = {
            'nom': {'label': '...', 'default': val, 'min': mn, 'max': mx, 'step': st, 'type': 'int'},
        }
    """
    # Construire le dict final
    # 1. Lire les params deja dans le code (si present)
    existing_sp = {}
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if (isinstance(base, ast.Name) and base.id == 'Strategy'):
                        for stmt in node.body:
                            if (isinstance(stmt, ast.Assign)
                                    and len(stmt.targets) == 1
                                    and isinstance(stmt.targets[0], ast.Name)
                                    and stmt.targets[0].id == 'STRATEGY_PARAMS'):
                                try:
                                    existing_sp = ast.literal_eval(stmt.value)
                                except (ValueError, TypeError):
                                    existing_sp = {}
                                break
    except SyntaxError:
        pass

    # 2. Construire le dict final uniquement depuis params (source de verite frontale)
    # Ne pas partir de existing_sp : les existingParams sont toujours envoyes complets
    # depuis la modale, donc existing_sp causerait des doublons si une cle est renommee.
    merged = {}
    for p in params:
        name = p.get('name', '').strip()
        if not name:
            continue
        merged[name] = {
            'label':   p.get('label', _infer_label(name)),
            'default': p.get('default', 0),
            'min':     p.get('min', 0),
            'max':     p.get('max', 100),
            'step':    p.get('step', 1),
            'type':    p.get('type', 'int'),
        }

    # 3. Serialiser en texte Python inlinant les valeurs litterales
    def _sp_line(k, v):
        default_repr = repr(v['default'])
        min_repr     = repr(v['min'])
        max_repr     = repr(v['max'])
        step_repr    = repr(v['step'])
        type_repr    = repr(v['type'])
        label_repr   = repr(v['label'])
        return (
            f"        '{k}': {{"
            f"'label': {label_repr}, "
            f"'default': {default_repr}, "
            f"'min': {min_repr}, "
            f"'max': {max_repr}, "
            f"'step': {step_repr}, "
            f"'type': {type_repr}"
            f"}},"
        )

    sp_lines = ["    STRATEGY_PARAMS = {"]
    for k, v in merged.items():
        sp_lines.append(_sp_line(k, v))
    sp_lines.append("    }")
    sp_block = '\n'.join(sp_lines)

    # 4. Remplacer le bloc existant ou inserer apres la ligne class
    lines = code.split('\n')
    result = []
    i = 0
    sp_replaced = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detecter STRATEGY_PARAMS = { et sauter tout le bloc existant
        if re.match(r'STRATEGY_PARAMS\s*=\s*\{', stripped) and not sp_replaced:
            # Sauter les lignes jusqu'a la fermeture du dict
            brace_depth = line.count('{') - line.count('}')
            i += 1
            while i < len(lines) and brace_depth > 0:
                brace_depth += lines[i].count('{') - lines[i].count('}')
                i += 1
            # Inserer le nouveau bloc
            result.append(sp_block)
            sp_replaced = True
            continue

        result.append(line)

        # Inserer apres 'class XXX(Strategy):' si STRATEGY_PARAMS absent
        if not sp_replaced and re.match(r'class\s+\w+\s*\(.*Strategy.*\)\s*:', stripped):
            result.append(sp_block)
            sp_replaced = True

        i += 1

    return '\n'.join(result)


def _ensure_init_params(code):
    """
    Garantit que __init__ de la classe Strategy accepte params=None
    et appelle super().__init__(..., params).

    Transformations :
      def __init__(self, candles, balance, position=None):
        -> def __init__(self, candles, balance, position=None, params=None):

      super().__init__(candles, balance, position)
        -> super().__init__(candles, balance, position, params)
    """
    # 1. Ajouter params=None dans la signature si absent
    def _patch_signature(m):
        sig = m.group(0)
        # Si params deja present, ne rien faire
        if 'params' in sig:
            return sig
        # Remplacer la fermeture ')' de la signature
        sig = re.sub(r'\)\s*:', lambda mm: ', params=None):', sig, count=1)
        return sig

    code = re.sub(
        r'def\s+__init__\s*\(self\s*,[^)]+\)\s*:',
        _patch_signature,
        code
    )

    # 2. Ajouter params dans l'appel super().__init__ si present sans params
    def _patch_super(m):
        call = m.group(0)
        if 'params' in call:
            return call
        # Ajouter params avant la fermeture de l'appel
        call = re.sub(r'\)\s*$', ', params)', call)
        return call

    code = re.sub(
        r'super\(\)\.__init__\([^)]+\)',
        _patch_super,
        code
    )

    return code


def _apply_params(code, params):
    """
    Applique la liste de params au code :
    1. Renomme self.params['ancien'] -> self.params['nouveau'] pour les params renommes.
    2. Remplace les litteraux numeriques dans les methodes.
    3. Met a jour / insere STRATEGY_PARAMS.
    4. S'assure que __init__ accepte params=None.
    """
    # Etape 1 : renommage des params existants (original_name != name)
    for p in params:
        original = p.get('original_name', '').strip()
        new_name = p.get('name', '').strip()
        if original and new_name and original != new_name:
            code = re.sub(
                rf"self\.params\['{re.escape(original)}'\]",
                f"self.params['{new_name}']",
                code
            )

    # Etape 2 : remplacement des litteraux numeriques
    to_replace = [p for p in params if p.get('replace_value') is not None]
    for p in to_replace:
        code = _replace_literal_in_methods(
            code,
            p['replace_value'],
            f"self.params['{p['name']}']"
        )
    code = _upsert_strategy_params(code, params)
    code = _ensure_init_params(code)
    return code


class AIAssistThrottle(UserRateThrottle):
    rate = '10/min'


def _validate_strategy_code(code: str) -> dict:
    """
    Valide le code Python d'une strategie.
    Retourne {'valid': bool, 'errors': list}.
    """
    errors = []

    # 1. Validation syntaxe Python
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {'valid': False, 'errors': [f"Syntaxe: {e.msg} (ligne {e.lineno})"]}

    # 2. Verifier les imports interdits
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split('.')[0]
                if module in FORBIDDEN_IMPORTS:
                    errors.append(f"Import interdit: '{module}'")
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or '').split('.')[0]
            if module in FORBIDDEN_IMPORTS:
                errors.append(f"Import interdit: '{module}'")

    if errors:
        return {'valid': False, 'errors': errors}

    # 3. Trouver une classe heritant de Strategy
    strategy_classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = ''
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr
                if base_name == 'Strategy':
                    strategy_classes.append(node)
                    break

    if not strategy_classes:
        return {'valid': False, 'errors': ["Aucune classe heritant de Strategy trouvee"]}

    # 4. Verifier les 5 methodes obligatoires (sur la premiere classe Strategy trouvee)
    cls_node = strategy_classes[0]
    defined_methods = {
        n.name for n in ast.walk(cls_node)
        if isinstance(n, ast.FunctionDef)
    }
    missing = REQUIRED_METHODS - defined_methods
    if missing:
        errors.append(f"Methodes manquantes: {', '.join(sorted(missing))}")
        return {'valid': False, 'errors': errors}

    # 5. Extraire STRATEGY_PARAMS si present (evaluation statique AST)
    params_schema = {}
    for stmt in cls_node.body:
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id == 'STRATEGY_PARAMS'
        ):
            try:
                params_schema = ast.literal_eval(stmt.value)
            except (ValueError, TypeError):
                pass  # STRATEGY_PARAMS non evaluable statiquement — ignore
            break

    return {'valid': True, 'errors': [], 'params_schema': params_schema}


class StrategyViewSet(viewsets.ModelViewSet):
    """ViewSet CRUD pour les strategies de trading."""

    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Multi-tenant strict : uniquement les strategies de l'utilisateur courant
        return Strategy.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='validate_code')
    def validate_code(self, request, pk=None):
        """
        POST /api/strategies/{id}/validate_code/
        Valide syntaxiquement le code Python d'une strategie.
        """
        strategy = self.get_object()
        serializer = StrategyValidationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code']
        result = _validate_strategy_code(code)
        return Response(result)

    @action(
        detail=False,
        methods=['post'],
        url_path='ai-assist',
        throttle_classes=[AIAssistThrottle]
    )
    def ai_assist(self, request):
        """
        POST /api/strategies/ai-assist/
        Assistant IA : generate / continue / assist / describe / chat.

        Mode chat : is_first_turn=True -> utilise 'generate', False -> utilise 'continue'.
        """
        mode = request.data.get('mode')
        description = request.data.get('description', '')
        code = request.data.get('code', '')
        is_first_turn = request.data.get('is_first_turn', False)

        # Validation mode
        if mode not in ('generate', 'assist', 'describe', 'chat'):
            return Response(
                {'error': "Mode invalide. Valeurs acceptees: generate, assist, describe, chat"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mode chat : routing vers generate ou continue
        if mode == 'chat':
            if not description.strip():
                return Response(
                    {'error': "Le champ 'description' (message) est obligatoire en mode chat"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if is_first_turn:
                actual_mode = 'generate'
                if code.strip():
                    prompt = f"{description}\n\n## Code actuel :\n```python\n{code}\n```"
                else:
                    prompt = description
            else:
                actual_mode = 'continue'
                prompt = f"## Code actuel :\n```python\n{code}\n```\n\n## Modification demandee :\n{description}"
        else:
            actual_mode = mode
            # Validation champs selon le mode
            if mode == 'generate' and not description.strip():
                return Response(
                    {'error': "Le champ 'description' est obligatoire en mode 'generate'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if mode in ('assist', 'describe') and not code.strip():
                return Response(
                    {'error': "Le champ 'code' est obligatoire en mode 'assist' ou 'describe'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Construire le prompt selon le mode
            if mode == 'generate':
                prompt = description
            else:
                prompt = code

        # Appel IA
        service = AIAssistService()
        try:
            result = asyncio.run(service.call_ai(request.user, actual_mode, prompt))
            return Response({'result': result})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur appel IA: {e}")
            return Response(
                {'error': f"Erreur lors de l'appel IA: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    # -------------------------------------------------------------------------
    # Patch M5 v2 — Extraction et application des parametres de strategie
    # -------------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='extract-params')
    def extract_params(self, request):
        """
        POST /api/strategies/extract-params/
        Analyse le code AST et retourne les litteraux numeriques candidats
        qui ne sont pas encore parametres dans STRATEGY_PARAMS.

        Input  : { "code": "..." }
        Output : { "new_literals": [...], "already_parameterized": [...] }
        """
        code = request.data.get('code', '')
        result = _extract_params(code)
        return Response(result)

    @action(detail=False, methods=['post'], url_path='apply-params')
    def apply_params(self, request):
        """
        POST /api/strategies/apply-params/
        Applique la liste de params au code : remplacement des litteraux,
        mise a jour de STRATEGY_PARAMS, patch __init__.

        Input  : { "code": "...", "params": [...] }
        Output : { "code": "..." }
        """
        code = request.data.get('code', '')
        params = request.data.get('params', [])
        try:
            new_code = _apply_params(code, params)
            return Response({'code': new_code})
        except Exception as e:
            logger.error(f"Erreur apply_params: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
