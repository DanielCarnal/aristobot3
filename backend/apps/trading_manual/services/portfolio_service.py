# -*- coding: utf-8 -*-
"""
Service pour calculs de portfolio
"""
import logging
from apps.core.services.exchange_client import ExchangeClient

logger = logging.getLogger(__name__)


class PortfolioService:
    """Service pour calculs de portfolio"""

    def __init__(self, user, broker):
        self.user = user
        self.broker = broker
        # 🔒 SÉCURITÉ: Passer user_id à ExchangeClient pour éviter faille multi-tenant
        self.exchange_client = ExchangeClient(user_id=user.id)

    async def get_portfolio_summary(self):
        """Resume complet du portfolio - OPTIMISÉ avec UNE SEULE requête batch"""
        # 1. Récupérer balance
        balance = await self.exchange_client.get_balance(self.broker.id)
        
        # 2. Identifier assets non-stables pour récupération prix
        tradable_assets = []
        for asset, data in balance.items():
            # 📍 CORRECTION: data est maintenant un dict avec 'total', 'available', etc.
            total_amount = data.get('total', 0) if isinstance(data, dict) else float(data)
            if asset not in ['USDT', 'USDC', 'USD'] and total_amount > 0:
                tradable_assets.append(asset)
        
        # 3. UNE SEULE requête batch pour tous les prix
        prices = {}
        if tradable_assets:
            from .trading_service import TradingService
            trading_service = TradingService(self.user, self.broker)
            prices = await trading_service.get_portfolio_prices(tradable_assets)
        
        # 4. Calculer total_value avec les prix récupérés
        total_usd = 0
        
        # Valeur en stablecoins - FORMAT NATIF CORRIGÉ
        for stable in ['USDT', 'USDC', 'USD']:
            if stable in balance:
                stable_data = balance[stable]
                stable_amount = stable_data.get('total', 0) if isinstance(stable_data, dict) else float(stable_data)
                total_usd += stable_amount
        
        # Valeur des autres assets avec prix batch - utilise normalized_balance
        for asset in tradable_assets:
            if asset in prices:
                # Utiliser directement la balance normalisée
                asset_balance_data = balance.get(asset, {})
                quantity = asset_balance_data.get('total', 0) if isinstance(asset_balance_data, dict) else float(asset_balance_data)
                if quantity > 0:
                    total_usd += float(quantity) * prices[asset]
                    logger.info(f"💰 Portfolio: {asset} = {quantity} × ${prices[asset]} = ${float(quantity) * prices[asset]:.2f}")
            else:
                logger.warning(f"⚠️ Portfolio: Prix manquant pour {asset}")
        
        logger.info(f"✅ Portfolio optimisé - 1 requête batch pour {len(tradable_assets)} assets - Total: ${total_usd:.2f}")
        
        # 5. Normaliser le format balance pour compatibilité frontend
        # Frontend attend: balance['total'][asset] = quantité
        normalized_balance = {
            'total': {},
            'free': {},
            'used': {}
        }
        
        for asset, data in balance.items():
            if isinstance(data, dict):
                normalized_balance['total'][asset] = data.get('total', 0)
                normalized_balance['free'][asset] = data.get('available', 0)
                normalized_balance['used'][asset] = data.get('frozen', 0)
            else:
                # Fallback si format simple
                normalized_balance['total'][asset] = float(data)
                normalized_balance['free'][asset] = float(data)
                normalized_balance['used'][asset] = 0
        
        logger.info(f"🎯 Balance normalisée pour frontend: {len(normalized_balance['total'])} assets")
        
        return {
            'balance': normalized_balance,  # Format compatible frontend
            'prices': prices,
            'total_value_usd': round(total_usd, 2)
        }
    
