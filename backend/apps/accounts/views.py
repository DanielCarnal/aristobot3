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
    """Endpoint de connexion standard"""    
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
                'email': user.email
            }
        })
    
    return Response(
        {'error': 'Identifiants invalides'},
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Endpoint de deconnexion standard"""
    logout(request)
    return Response({'message': 'Deconnecte'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Retourne l'utilisateur actuellement connecte"""
    user = request.user
    
    # Vérifier si l'utilisateur est authentifié
    if not user.is_authenticated:
        return Response(
            {'error': 'Non authentifié'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'ai_provider': user.ai_provider,
        'ai_enabled': user.ai_enabled,
        'ai_model': user.ai_model,
        'ai_endpoint_url': user.ai_endpoint_url,
        'ai_generate_prompt': user.ai_generate_prompt,
        'ai_continue_prompt': user.ai_continue_prompt,
        'theme': user.theme,
        'display_timezone': user.display_timezone,
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    """Met a jour les preferences utilisateur"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"update_preferences - User: {request.user}")
    logger.info(f"update_preferences - Authenticated: {request.user.is_authenticated}")
    logger.info(f"update_preferences - Session key: {request.session.session_key}")
    logger.info(f"update_preferences - Cookies: {dict(request.COOKIES)}")
    logger.info(f"update_preferences - Headers: {dict(request.headers)}")
    logger.info(f"update_preferences - Auth classes: {getattr(request, '_authenticators', None)}")
    
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
    if 'ai_model' in request.data:
        user.ai_model = request.data['ai_model']
    if 'ai_generate_prompt' in request.data:
        user.ai_generate_prompt = request.data['ai_generate_prompt']
    if 'ai_continue_prompt' in request.data:
        user.ai_continue_prompt = request.data['ai_continue_prompt']
    if 'theme' in request.data:
        user.theme = request.data['theme']
    if 'display_timezone' in request.data:
        user.display_timezone = request.data['display_timezone']
    
    user.save()
    return Response({'message': 'Preferences mises a jour'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_ia_connection(request):
    """
    Teste la connexion au fournisseur IA configure pour l'utilisateur.

    Ollama : GET {endpoint}/api/tags — verifie que le serveur repond et que le modele est present.
    OpenRouter : GET https://openrouter.ai/api/v1/models — verifie que la cle API est valide.

    Retourne: {success: bool, message: str, models: list (Ollama seulement)}
    """
    import asyncio
    import aiohttp
    import logging
    logger = logging.getLogger(__name__)

    user = request.user

    if user.ai_provider == 'none' or not user.ai_enabled:
        return Response(
            {'success': False, 'message': "Aucun fournisseur IA configure. Activez OpenRouter ou Ollama."},
            status=status.HTTP_400_BAD_REQUEST
        )

    async def _test():
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:

            if user.ai_provider == 'ollama':
                endpoint = (user.ai_endpoint_url or 'http://localhost:11434').rstrip('/')
                model = user.ai_model or ''
                try:
                    async with session.get(f'{endpoint}/api/tags') as resp:
                        if resp.status != 200:
                            return {
                                'success': False,
                                'message': f"Ollama ne repond pas (HTTP {resp.status}). Verifiez l'URL : {endpoint}"
                            }
                        data = await resp.json()
                        available = [m.get('name', '') for m in data.get('models', [])]
                        if model and not any(model in name for name in available):
                            return {
                                'success': False,
                                'message': f"Serveur Ollama OK, mais le modele '{model}' n'est pas trouve.",
                                'models': available,
                            }
                        return {
                            'success': True,
                            'message': f"Connexion Ollama OK ({endpoint})" + (f" — modele '{model}' disponible." if model else "."),
                            'models': available,
                        }
                except Exception as e:
                    return {
                        'success': False,
                        'message': f"Impossible de joindre Ollama ({endpoint}) : {str(e)}"
                    }

            elif user.ai_provider == 'openrouter':
                api_key = user.decrypt_api_key()
                if not api_key:
                    return {'success': False, 'message': "Cle API OpenRouter manquante."}
                headers = {'Authorization': f'Bearer {api_key}'}
                try:
                    async with session.get(
                        'https://openrouter.ai/api/v1/models',
                        headers=headers
                    ) as resp:
                        if resp.status == 401:
                            return {'success': False, 'message': "Cle API OpenRouter invalide (HTTP 401)."}
                        if resp.status != 200:
                            return {'success': False, 'message': f"OpenRouter repond HTTP {resp.status}."}
                        return {'success': True, 'message': "Connexion OpenRouter OK — cle API valide."}
                except Exception as e:
                    return {'success': False, 'message': f"Impossible de joindre OpenRouter : {str(e)}"}

            return {'success': False, 'message': "Fournisseur IA inconnu."}

    try:
        result = asyncio.run(_test())
        http_status = status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)
    except Exception as e:
        logger.error(f"Erreur test IA: {e}")
        return Response(
            {'success': False, 'message': f"Erreur interne : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )