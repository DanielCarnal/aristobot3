from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Endpoint de connexion"""
    # En mode DEBUG, connexion automatique avec user dev
    if settings.DEBUG and not request.data.get('username'):
        try:
            user = User.objects.get(username='dev')
            login(request, user)
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_dev': True
                }
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur dev non trouve. Lancez "python manage.py init_aristobot"'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Connexion normale
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Nom d\'utilisateur et mot de passe requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_dev': False
            }
        })
    
    return Response(
        {'error': 'Identifiants invalides'},
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Endpoint de deconnexion"""
    logout(request)
    # En mode DEBUG, reconnecter automatiquement avec dev
    if settings.DEBUG:
        try:
            user = User.objects.get(username='dev')
            login(request, user)
            return Response({'message': 'Deconnecte, reconnecte en tant que dev'})
        except User.DoesNotExist:
            pass
    return Response({'message': 'Deconnecte'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Retourne l'utilisateur actuellement connecte"""
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_dev': user.username == 'dev',
        'ai_provider': user.ai_provider,
        'ai_enabled': user.ai_enabled,
        'theme': user.theme,
        'display_timezone': user.display_timezone,
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    """Met a jour les preferences utilisateur"""
    user = request.user
    
    # Gestion des switches IA - activer l'un desactive l'autre
    if 'ai_provider' in request.data:
        provider = request.data['ai_provider']
        if provider != 'none':
            user.ai_provider = provider
            user.ai_enabled = True
        else:
            user.ai_enabled = False
            user.ai_provider = 'none'
    
    if 'ai_enabled' in request.data:
        user.ai_enabled = request.data['ai_enabled']
        if not user.ai_enabled:
            user.ai_provider = 'none'
    
    if 'ai_api_key' in request.data:
        user.ai_api_key = request.data['ai_api_key']
    if 'ai_endpoint_url' in request.data:
        user.ai_endpoint_url = request.data['ai_endpoint_url']
    if 'theme' in request.data:
        user.theme = request.data['theme']
    if 'display_timezone' in request.data:
        user.display_timezone = request.data['display_timezone']
    
    user.save()
    return Response({'message': 'Preferences mises a jour'})