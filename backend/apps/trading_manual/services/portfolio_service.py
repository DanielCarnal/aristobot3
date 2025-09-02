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
        """Resume complet du portfolio - OPTIMISÉ avec UNE SEULE requête batch"""
        # 1. Récupérer balance
        balance = await self.ccxt_client.get_balance(self.broker.id)
        
        # 2. Identifier positions non-stables
        positions = {}
        tradable_assets = []
        for asset, data in balance.get('total', {}).items():
            if asset not in ['USDT', 'USDC', 'USD'] and float(data) > 0:
                positions[asset] = data
                tradable_assets.append(asset)
        
        # 3. UNE SEULE requête batch pour tous les prix
        prices = {}
        if tradable_assets:
            from .trading_service import TradingService
            trading_service = TradingService(self.user, self.broker)
            prices = await trading_service.get_portfolio_prices(tradable_assets)
        
        # 4. Calculer total_value avec les prix récupérés
        total_usd = 0
        
        # Valeur en stablecoins
        for stable in ['USDT', 'USDC', 'USD']:
            if stable in balance.get('total', {}):
                total_usd += float(balance['total'][stable])
        
        # Valeur des autres assets avec prix batch
        for asset, quantity in positions.items():
            if asset in prices:
                total_usd += float(quantity) * prices[asset]
                logger.info(f"💰 Portfolio: {asset} = {quantity} × ${prices[asset]} = ${float(quantity) * prices[asset]:.2f}")
            else:
                logger.warning(f"⚠️ Portfolio: Prix manquant pour {asset}")
        
        logger.info(f"✅ Portfolio optimisé - 1 requête batch pour {len(tradable_assets)} assets - Total: ${total_usd:.2f}")
        
        return {
            'balance': balance,
            'positions': positions,
            'prices': prices,  # Ajouter prix pour frontend
            'total_value_usd': round(total_usd, 2)
        }
    
