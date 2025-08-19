# -*- coding: utf-8 -*-
"""
Service pour calculs de portfolio
"""
import logging
from apps.core.services.ccxt_client import CCXTClient

logger = logging.getLogger(__name__)


class PortfolioService:
    """Service pour calculs de portfolio"""
    
    def __init__(self, user, broker):
        self.user = user
        self.broker = broker
        self.ccxt_client = CCXTClient()
    
    async def get_portfolio_summary(self):
        """Resume complet du portfolio"""
        balance = await self.ccxt_client.get_balance(self.broker.id)
        positions = await self.get_open_positions()
        total_value = await self.calculate_total_value(balance, positions)
        
        return {
            'balance': balance,
            'positions': positions,
            'total_value_usd': total_value
        }
    
    async def calculate_total_value(self, balance, positions):
        """Calcule la valeur totale du portfolio en USD"""
        total_usd = 0
        
        # Valeur en stablecoins
        for stable in ['USDT', 'USDC', 'USD']:
            if stable in balance.get('total', {}):
                total_usd += float(balance['total'][stable])
        
        # Valeur des autres assets convertie en USD
        for asset, quantity in positions.items():
            if float(quantity) > 0:
                try:
                    # Recuperer le prix en USDT via CCXT
                    ticker_symbol = f"{asset}/USDT"
                    ticker = await self.ccxt_client.get_ticker(self.broker.id, ticker_symbol)
                    price_usd = float(ticker['last'])
                    total_usd += float(quantity) * price_usd
                except Exception as e:
                    logger.warning(f"Impossible de recuperer le prix pour {asset}: {e}")
                    # Continue sans ce asset
        
        return round(total_usd, 2)
    
    async def get_open_positions(self):
        """Positions ouvertes (non-USD/stable)"""
        # Filtre les balances non-nulles et non-stables
        balance = await self.ccxt_client.get_balance(self.broker.id)
        positions = {}
        
        for asset, data in balance.get('total', {}).items():
            if asset not in ['USDT', 'USDC', 'USD'] and float(data) > 0:
                positions[asset] = data
        
        return positions