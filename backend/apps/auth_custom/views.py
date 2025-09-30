# -*- coding: utf-8 -*-
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.conf import settings
from django.middleware.csrf import get_token
from .models import DebugMode

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Endpoint de connexion standard (garde la logique existante)"""    
    import logging
    logger = logging.getLogger(__name__)
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    logger.info(f"login_view - Tentative de connexion: {username}")
    
    if not username or not password:
        return Response(
            {'error': 'Nom d\'utilisateur et mot de passe requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        logger.info(f"login_view - Login réussi pour {username}, session_key: {request.session.session_key}")
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    
    logger.warning(f"login_view - Échec de connexion pour {username}")
    return Response(
        {'error': 'Identifiants invalides'},
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Endpoint de déconnexion standard"""
    logout(request)
    return Response({'message': 'Deconnecte'})

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Création compte (garde le modal existant)"""
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    
    if not username or not password:
        return Response(
            {'error': 'Nom d\'utilisateur et mot de passe requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Ce nom d\'utilisateur existe déjà'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )
        return Response({
            'message': 'Compte créé avec succès',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la création: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def status_view(request):
    """Info user connecté + mode debug"""
    user = request.user
    debug_enabled = getattr(settings, 'DEBUG_ARISTOBOT', False)
    debug_active = DebugMode.get_state()
    
    # Si pas authentifié, retourner seulement les infos debug
    if not user.is_authenticated:
        return Response({
            'user': None,
            'debug': {
                'enabled': debug_enabled,
                'active': debug_active,
            }
        })
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'ai_provider': user.ai_provider,
            'ai_enabled': user.ai_enabled,
            'theme': user.theme,
            'display_timezone': user.display_timezone,
        },
        'debug': {
            'enabled': debug_enabled,  # DEBUG_ARISTOBOT dans .env
            'active': debug_active,    # État du toggle en DB
        }
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_config_view(request):
    """Retourne {enabled: bool, active: bool}"""
    debug_enabled = getattr(settings, 'DEBUG_ARISTOBOT', False)
    debug_active = DebugMode.get_state()
    
    return Response({
        'enabled': debug_enabled,  # Visible seulement si DEBUG_ARISTOBOT=True
        'active': debug_active     # État actuel du mode debug
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_debug_view(request):
    """Active/désactive mode debug"""
    debug_enabled = getattr(settings, 'DEBUG_ARISTOBOT', False)
    
    if not debug_enabled:
        return Response(
            {'error': 'Mode debug non disponible (DEBUG_ARISTOBOT=False)'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    new_state = DebugMode.toggle()
    return Response({
        'message': f'Mode debug {"activé" if new_state else "désactivé"}',
        'active': new_state
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def debug_login_view(request):
    """Auto-login avec 'dev' si mode debug actif"""
    debug_enabled = getattr(settings, 'DEBUG_ARISTOBOT', False)
    debug_active = DebugMode.get_state()
    
    if not debug_enabled or not debug_active:
        return Response(
            {'error': 'Mode debug non disponible ou inactif'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        user = User.objects.get(username='dev')
        login(request, user)
        return Response({
            'message': 'Connexion automatique réussie',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    except User.DoesNotExist:
        return Response(
            {'error': 'Utilisateur dev non trouvé. Lancez "python manage.py init_aristobot"'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_auth_view(request):
    """Debug endpoint pour diagnostiquer l'authentification"""
    import logging
    logger = logging.getLogger(__name__)
    
    user = request.user
    session_key = request.session.session_key
    session_data = dict(request.session)
    
    logger.info(f"debug_auth - User: {user}")
    logger.info(f"debug_auth - Is authenticated: {user.is_authenticated}")
    logger.info(f"debug_auth - Session key: {session_key}")
    logger.info(f"debug_auth - Session data: {session_data}")
    logger.info(f"debug_auth - Headers: {dict(request.headers)}")
    
    return Response({
        'user': str(user),
        'is_authenticated': user.is_authenticated,
        'session_key': session_key,
        'session_data': session_data,
        'cookies': dict(request.COOKIES),
        'headers': dict(request.headers),
        'csrf_token': get_token(request)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token_view(request):
    """Endpoint pour récupérer le token CSRF"""
    return Response({
        'csrf_token': get_token(request)
    })
