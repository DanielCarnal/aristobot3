# -*- coding: utf-8 -*-
"""
SERVICE IA - AIAssistService

Fournit l'assistance IA trimodale pour la creation et l'analyse de strategies.
Modes: generate (description -> code), assist (code -> ameliorations), describe (code -> description).
Providers supportes: OpenRouter, Ollama.
"""

import aiohttp
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    'generate': (
        "Tu es un expert en trading algorithmique Python. "
        "L'utilisateur va te decrire en langage naturel une strategie de trading. "
        "Tu dois generer le code Python COMPLET d'une classe qui herite de Strategy. "
        "OBLIGATOIRE : inclure STRATEGY_PARAMS avec TOUTES les valeurs numeriques utilisees. "
        "Format STRATEGY_PARAMS : "
        "{'nom': {'default': val, 'min': mn, 'max': mx, 'step': st, 'type': 'int'|'float', 'label': '...'}}. "
        "La classe Strategy de base a ces 5 methodes abstraites : "
        "should_long() -> bool, should_short() -> bool, "
        "calculate_position_size() -> float, calculate_stop_loss() -> float, "
        "calculate_take_profit() -> float. "
        "Importe pandas_ta as ta si tu utilises des indicateurs techniques. "
        "self.candles est un DataFrame Pandas avec colonnes : open, high, low, close, volume. "
        "Utilise self.params['nom'] pour toutes les valeurs numeriques. "
        "Reponds UNIQUEMENT avec le code Python, sans explication ni markdown."
    ),
    'continue': (
        "Tu es un expert en trading algorithmique Python. "
        "Voici une classe Strategy existante. L'utilisateur souhaite la modifier. "
        "REGLES STRICTES : "
        "1) Applique UNIQUEMENT la modification demandee. "
        "2) Ne change rien a ce qui n'est pas mentionne. "
        "3) Conserve STRATEGY_PARAMS intact sauf si la modification concerne les params. "
        "4) Conserve les 5 methodes obligatoires. "
        "Reponds UNIQUEMENT avec le code Python COMPLET modifie, sans explication ni markdown."
    ),
    'assist': (
        "Tu es un expert en trading algorithmique Python. "
        "L'utilisateur va te montrer le code d'une strategie de trading. "
        "Analyse ce code et propose des ameliorations concretes en francais : "
        "logique de signal, gestion du risque, indicateurs techniques complementaires, etc. "
        "Sois concis et pratique. Reponds en francais."
    ),
    'describe': (
        "Tu es un expert en trading algorithmique Python. "
        "L'utilisateur va te montrer le code d'une strategie de trading. "
        "Decris en 2-3 phrases simples et en francais ce que fait cette strategie : "
        "quand elle achete, quand elle vend, et sa gestion du risque. "
        "Sois clair et accessible, sans jargon technique Python."
    ),
}


class AIAssistService:
    """Service d'assistance IA pour la creation et l'analyse de strategies."""

    TIMEOUT = aiohttp.ClientTimeout(total=120)

    async def call_ai(self, user, mode: str, prompt: str) -> str:
        """
        Appelle le fournisseur IA configure pour l'utilisateur.

        Args:
            user: Instance User Django (avec ai_provider, ai_api_key, ai_model, ai_endpoint_url)
            mode: 'generate', 'continue', 'assist' ou 'describe'
            prompt: Le texte envoye a l'IA (description ou code)

        Returns:
            La reponse textuelle de l'IA

        Raises:
            ValueError: Si ai_provider='none' ou mode invalide
            Exception: Si l'appel API echoue
        """
        if user.ai_provider == 'none':
            raise ValueError("Aucun fournisseur IA configure. Configurez OpenRouter ou Ollama dans Mon Compte.")

        if mode not in SYSTEM_PROMPTS:
            raise ValueError(f"Mode IA invalide: {mode}. Valeurs acceptees: generate, continue, assist, describe")

        # Pre-prompts personnalises (user dev uniquement)
        if mode == 'generate':
            custom_prompt = getattr(user, 'ai_generate_prompt', '').strip()
            system_prompt = custom_prompt or SYSTEM_PROMPTS['generate']
        elif mode == 'continue':
            custom_prompt = getattr(user, 'ai_continue_prompt', '').strip()
            system_prompt = custom_prompt or SYSTEM_PROMPTS['continue']
        else:
            system_prompt = SYSTEM_PROMPTS[mode]

        if user.ai_provider == 'openrouter':
            return await self._call_openrouter(user, system_prompt, prompt)
        elif user.ai_provider == 'ollama':
            return await self._call_ollama(user, system_prompt, prompt)
        else:
            raise ValueError(f"Fournisseur IA inconnu: {user.ai_provider}")

    async def _call_openrouter(self, user, system_prompt: str, user_prompt: str) -> str:
        """Appelle l'API OpenRouter."""
        api_key = user.decrypt_api_key()
        if not api_key:
            raise ValueError("Cle API OpenRouter manquante. Configurez-la dans Mon Compte.")

        model = user.ai_model or 'openai/gpt-4o-mini'

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://aristobot3.local',
            'X-Title': 'Aristobot3',
        }
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        }

        async with aiohttp.ClientSession(timeout=self.TIMEOUT) as session:
            async with session.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Erreur OpenRouter {response.status}: {error_text[:200]}")
                data = await response.json()
                return data['choices'][0]['message']['content']

    async def _call_ollama(self, user, system_prompt: str, user_prompt: str) -> str:
        """Appelle l'API Ollama locale."""
        endpoint = user.ai_endpoint_url or 'http://localhost:11434'
        model = user.ai_model or 'llama3'

        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'stream': False,
        }

        async with aiohttp.ClientSession(timeout=self.TIMEOUT) as session:
            async with session.post(
                f'{endpoint.rstrip("/")}/api/chat',
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Erreur Ollama {response.status}: {error_text[:200]}")
                data = await response.json()
                return data['message']['content']
