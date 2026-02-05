# -*- coding: utf-8 -*-
"""
Service de mise à jour des symboles - VERSION CORRIGÉE
Corrige les erreurs PostgreSQL sur valeurs décimales trop grandes
"""
import asyncio
import ccxt
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
    Version corrigée qui gère les limites PostgreSQL.
    """
    
    @staticmethod
    def safe_decimal_value(value):
        """
        Filtre les valeurs décimales pour éviter les erreurs PostgreSQL
        
        PostgreSQL DecimalField(max_digits=20, decimal_places=8) ne peut pas 
        stocker des valeurs > 10^12 (999999999999.99999999)
        """
        if value is None:
            return None
        try:
            val = float(value)
            # Limite PostgreSQL: valeur absolue < 10^12
            if abs(val) > 999999999999:
                logger.debug(f"Valeur trop grande ignorée: {val}")
                return None
            if val == 0:
                return None  # Ignorer les zéros
            return value
        except (ValueError, TypeError, OverflowError):
            logger.debug(f"Valeur invalide ignorée: {value}")
            return None
    
    @staticmethod
    def update_exchange_symbols_sync(exchange_name: str) -> Dict:
        """
        Met à jour les symboles pour un exchange donné (version synchrone).
        Version corrigée avec gestion des limites PostgreSQL.
        """
        stats = {
            'exchange': exchange_name,
            'added': 0,
            'updated': 0,
            'deactivated': 0,
            'errors': [],
            'filtered_values': 0
        }
        
        try:
            # Créer une instance CCXT synchrone pour l'exchange
            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class({
                'enableRateLimit': True,
                'rateLimit': 2000
            })
            
            try:
                # Charger les marchés
                markets = exchange.load_markets()
                
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
                            
                            # Filtrer les valeurs avec logging
                            min_amount = SymbolUpdaterService.safe_decimal_value(limits.get('amount', {}).get('min'))
                            max_amount = SymbolUpdaterService.safe_decimal_value(limits.get('amount', {}).get('max'))
                            min_price = SymbolUpdaterService.safe_decimal_value(limits.get('price', {}).get('min'))
                            max_price = SymbolUpdaterService.safe_decimal_value(limits.get('price', {}).get('max'))
                            min_cost = SymbolUpdaterService.safe_decimal_value(limits.get('cost', {}).get('min'))
                            
                            # Compter les valeurs filtrées
                            original_values = [
                                limits.get('amount', {}).get('min'),
                                limits.get('amount', {}).get('max'),
                                limits.get('price', {}).get('min'),
                                limits.get('price', {}).get('max'),
                                limits.get('cost', {}).get('min')
                            ]
                            filtered_values = [min_amount, max_amount, min_price, max_price, min_cost]
                            filtered_count = sum(1 for orig, filt in zip(original_values, filtered_values) 
                                               if orig is not None and filt is None)
                            if filtered_count > 0:
                                stats['filtered_values'] += filtered_count
                                logger.debug(f"Symbole {symbol}: {filtered_count} valeurs filtrées")
                            
                            # Créer ou mettre à jour le symbole avec valeurs filtrées
                            obj, created = ExchangeSymbol.objects.update_or_create(
                                exchange=exchange_name,
                                symbol=symbol,
                                type=market.get('type', 'spot'),
                                defaults={
                                    'base': market.get('base', ''),
                                    'quote': market.get('quote', ''),
                                    'active': True,
                                    'min_amount': min_amount,
                                    'max_amount': max_amount,
                                    'min_price': min_price,
                                    'max_price': max_price,
                                    'min_cost': min_cost,
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
                        f"{deleted_count} supprimés, {stats['filtered_values']} valeurs filtrées"
                    )
                    
            finally:
                # Fermer l'exchange si possible
                if hasattr(exchange, 'close'):
                    exchange.close()
                
        except Exception as e:
            logger.error(f"Erreur mise à jour exchange {exchange_name}: {e}")
            stats['errors'].append(str(e))
        
        return stats
    
    @staticmethod
    async def update_exchange_symbols(exchange_name: str) -> Dict:
        """
        Met à jour les symboles pour un exchange donné (version async).
        Version corrigée avec gestion des limites PostgreSQL.
        """
        stats = {
            'exchange': exchange_name,
            'added': 0,
            'updated': 0,
            'deactivated': 0,
            'errors': [],
            'filtered_values': 0
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
                            
                            # Filtrer les valeurs avec logging
                            min_amount = SymbolUpdaterService.safe_decimal_value(limits.get('amount', {}).get('min'))
                            max_amount = SymbolUpdaterService.safe_decimal_value(limits.get('amount', {}).get('max'))
                            min_price = SymbolUpdaterService.safe_decimal_value(limits.get('price', {}).get('min'))
                            max_price = SymbolUpdaterService.safe_decimal_value(limits.get('price', {}).get('max'))
                            min_cost = SymbolUpdaterService.safe_decimal_value(limits.get('cost', {}).get('min'))
                            
                            # Compter les valeurs filtrées
                            original_values = [
                                limits.get('amount', {}).get('min'),
                                limits.get('amount', {}).get('max'),
                                limits.get('price', {}).get('min'),
                                limits.get('price', {}).get('max'),
                                limits.get('cost', {}).get('min')
                            ]
                            filtered_values = [min_amount, max_amount, min_price, max_price, min_cost]
                            filtered_count = sum(1 for orig, filt in zip(original_values, filtered_values) 
                                               if orig is not None and filt is None)
                            if filtered_count > 0:
                                stats['filtered_values'] += filtered_count
                                logger.debug(f"Symbole {symbol}: {filtered_count} valeurs filtrées")
                            
                            # Créer ou mettre à jour le symbole avec valeurs filtrées
                            obj, created = ExchangeSymbol.objects.update_or_create(
                                exchange=exchange_name,
                                symbol=symbol,
                                type=market.get('type', 'spot'),
                                defaults={
                                    'base': market.get('base', ''),
                                    'quote': market.get('quote', ''),
                                    'active': True,
                                    'min_amount': min_amount,
                                    'max_amount': max_amount,
                                    'min_price': min_price,
                                    'max_price': max_price,
                                    'min_cost': min_cost,
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
                        f"{deleted_count} supprimés, {stats['filtered_values']} valeurs filtrées"
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
        return SymbolUpdaterService.update_exchange_symbols_sync(exchange_name)