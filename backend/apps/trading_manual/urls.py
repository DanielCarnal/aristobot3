# -*- coding: utf-8 -*-
"""
URLs Trading Manuel - Module 3
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'trades', views.TradeViewSet, basename='trade')

urlpatterns = [
    # ViewSets via router
    path('', include(router.urls)),
    
    # Portfolio
    path('portfolio/', views.PortfolioView.as_view(), name='portfolio'),
    path('balance/', views.BalanceView.as_view(), name='balance'),
    
    # Symboles  
    path('symbols/filtered/', views.SymbolFilteredView.as_view(), name='symbols-filtered'),
    path('exchange-info/<int:broker_id>/', views.ExchangeInfoView.as_view(), name='exchange-info'),
    
    # Trading
    path('calculate-trade/', views.CalculateTradeView.as_view(), name='calculate-trade'),
    path('validate-trade/', views.ValidateTradeView.as_view(), name='validate-trade'),
    path('execute-trade/', views.ExecuteTradeView.as_view(), name='execute-trade'),
    path('price/<path:symbol>/', views.CurrentPriceView.as_view(), name='current-price'),
    path('portfolio-prices/', views.PortfolioPricesView.as_view(), name='portfolio-prices'),
    
    # Ordres
    path('open-orders/', views.OpenOrdersView.as_view(), name='open-orders'),
    path('closed-orders/', views.ClosedOrdersView.as_view(), name='closed-orders'),
    path('cancel-order/', views.CancelOrderView.as_view(), name='cancel-order'),
    path('edit-order/', views.EditOrderView.as_view(), name='edit-order'),
    
    # Positions P&L Terminal 7
    path('positions/', views.PositionsView.as_view(), name='positions'),
]
