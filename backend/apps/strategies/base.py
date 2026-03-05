# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class Strategy(ABC):
    """Classe abstraite de base pour toutes les strategies de trading Aristobot3.

    Toute strategie utilisateur doit heriter de cette classe et implementer
    les 5 methodes abstraites.

    Usage:
        class MaStrategie(Strategy):
            STRATEGY_PARAMS = {
                'ema_fast': {'default': 10, 'min': 2,  'max': 50,  'step': 1, 'type': 'int',   'label': 'EMA rapide'},
                'ema_slow': {'default': 20, 'min': 5,  'max': 200, 'step': 1, 'type': 'int',   'label': 'EMA lente'},
                'risk':     {'default': 0.1,'min': 0.01,'max': 1.0,'step': 0.01,'type':'float','label': 'Risque (fraction)'},
            }

            def should_long(self) -> bool:
                ema_fast = ta.ema(self.candles['close'], length=self.params['ema_fast'])
                ...
    """

    # Parametres configurables de la strategie.
    # Surcharger dans la sous-classe avec le format :
    #   {'nom_param': {'default': val, 'min': val, 'max': val,
    #                  'step': val, 'type': 'float'|'int', 'label': 'Label affiche'}}
    STRATEGY_PARAMS = {}

    def __init__(self, candles, balance, position=None, params=None):
        self.candles = candles
        self.balance = balance
        self.position = position
        # Fusion : defaults de la classe + surcharges fournies par le backtest/bot
        p = {k: v['default'] for k, v in self.STRATEGY_PARAMS.items()}
        if params:
            p.update(params)
        self.params = p

    @abstractmethod
    def should_long(self) -> bool:
        """Retourne True si la strategie doit ouvrir une position longue (achat)."""
        pass

    @abstractmethod
    def should_short(self) -> bool:
        """Retourne True si la strategie doit ouvrir une position courte (vente). Futures uniquement."""
        pass

    @abstractmethod
    def calculate_position_size(self) -> float:
        """Calcule la taille de la position en pourcentage du solde disponible (ex: 0.1 = 10%)."""
        pass

    @abstractmethod
    def calculate_stop_loss(self) -> float:
        """Calcule le pourcentage de stop loss (ex: 0.02 = 2% en dessous du prix d'entree)."""
        pass

    @abstractmethod
    def calculate_take_profit(self) -> float:
        """Calcule le pourcentage de take profit (ex: 0.04 = 4% au dessus du prix d'entree)."""
        pass
