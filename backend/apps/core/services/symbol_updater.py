import asyncio
import ccxt.async_support as ccxt_async
from typing import Dict, List
from django.db import transaction
from django.utils import timezone
from apps.brokers.models import ExchangeSymbol
import logging

logger = logging.getLogger(__name__)

class SymbolUpdaterService:
    """
    Service pour mettre à jour les symboles disponibles sur les exchanges.
    Utilise ccxt en mode async pour des performances optimales.
    """
    
    @staticmethod
    async def update_exchange_symbols(exchange_name: str) -> Dict:
        """
        Met à jour les symboles pour un exchange donné.
        Retourne un dictionnaire avec les statistiques de mise à jour.
        """
        stats = {
            'exchange': exchange_name,
            'added': 0,
            'updated': 0,
            'deactivated': 0,
            'errors': []
        }
        
        try:
            # Créer une instance CCXT async pour l'exchange
            exchange_class = getattr(ccxt_async, exchange_name)
            exchange = exchange_class({
                'enableRateLimit': True,
                'rateLimit': 2000
            })
            
            try:
                # Charger les marchés
                markets = await exchange.load_markets()
                
                # Transaction pour la mise à jour atomique
                with transaction.atomic():
                    # Marquer tous les symboles existants comme inactifs
                    ExchangeSymbol.objects.filter(
                        exchange=exchange_name
                    ).update(active=False)
                    stats['deactivated'] = ExchangeSymbol.objects.filter(
                        exchange=exchange_name,
                        active=False
                    ).count()
                    
                    # Traiter chaque marché
                    for symbol, market in markets.items():
                        # On ne traite que les marchés spot actifs
                        if not market.get('active', False):
                            continue
                        
                        if market.get('type') not in ['spot', None]:
                            continue
                        
                        try:
                            # Extraire les informations
                            limits = market.get('limits', {})
                            precision = market.get('precision', {})
                            
                            # Créer ou mettre à jour le symbole
                            obj, created = ExchangeSymbol.objects.update_or_create(
                                exchange=exchange_name,
                                symbol=symbol,
                                type=market.get('type', 'spot'),
                                defaults={
                                    'base': market.get('base', ''),
                                    'quote': market.get('quote', ''),
                                    'active': True,
                                    'min_amount': limits.get('amount', {}).get('min'),
                                    'max_amount': limits.get('amount', {}).get('max'),
                                    'min_price': limits.get('price', {}).get('min'),
                                    'max_price': limits.get('price', {}).get('max'),
                                    'min_cost': limits.get('cost', {}).get('min'),
                                    'amount_precision': precision.get('amount'),
                                    'price_precision': precision.get('price'),
                                    'raw_info': market,
                                    'last_updated': timezone.now(),
                                }
                            )
                            
                            if created:
                                stats['added'] += 1
                            else:
                                stats['updated'] += 1
                                
                        except Exception as e:
                            logger.error(f"Erreur traitement symbole {symbol}: {e}")
                            stats['errors'].append(f"{symbol}: {str(e)}")
                    
                    # Supprimer les symboles qui ne sont plus actifs
                    deleted_count = ExchangeSymbol.objects.filter(
                        exchange=exchange_name,
                        active=False
                    ).delete()[0]
                    
                    logger.info(
                        f"Mise à jour {exchange_name}: "
                        f"{stats['added']} ajoutés, {stats['updated']} mis à jour, "
                        f"{deleted_count} supprimés"
                    )
                    
            finally:
                # Toujours fermer l'exchange
                await exchange.close()
                
        except Exception as e:
            logger.error(f"Erreur mise à jour exchange {exchange_name}: {e}")
            stats['errors'].append(str(e))
        
        return stats
    
    @staticmethod
    def update_symbols_sync(exchange_name: str) -> Dict:
        """
        Version synchrone pour appel depuis Django.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                SymbolUpdaterService.update_exchange_symbols(exchange_name)
            )
        finally:
            loop.close()