# Crear archivo: appWeb/middleware.py

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class TokenAuthMiddleware:
    """
    Middleware para manejar tokens de autenticación expirados o inválidos
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # URLs que NO requieren autenticación
        self.public_urls = [
            '/',
            '/login/',
            '/register/',
            '/password-reset/',
            '/password-reset/sent/',
            '/motor-nautica/',
            '/payment/success/',
            '/payment/cancel/',
            '/admin/',  # Admin tiene su propio sistema de auth
        ]

        # Prefijos de URLs públicas
        self.public_prefixes = [
            '/password-reset/confirm/',
            '/static/',
            '/media/',
            '/admin/',
            '/api/',  # Las APIs manejan su propia autenticación
        ]

    def __call__(self, request):
        # Verificar si la URL actual requiere autenticación
        if self._requires_authentication(request.path):
            # Si requiere auth pero el usuario no está autenticado
            if not request.user.is_authenticated:
                logger.info(f"Redirigiendo usuario no autenticado desde {request.path}")

                # Para requests AJAX, devolver JSON
                if self._is_ajax_request(request):
                    return JsonResponse({
                        'success': False,
                        'error': 'Sesión expirada',
                        'redirect': reverse('appWeb:login')
                    }, status=401)

                # Para requests normales, redirigir al login
                messages.warning(request, 'Tu sesión ha expirado. Por favor inicia sesión nuevamente.')
                return redirect(f"{reverse('appWeb:login')}?next={request.path}")

            # Si está autenticado pero hay problemas con el token
            elif hasattr(request.user, 'auth_token'):
                try:
                    # Verificar que el token existe y es válido
                    token = request.user.auth_token
                    if not token.key:
                        raise Exception("Token inválido")
                except Exception as e:
                    logger.warning(f"Token inválido para usuario {request.user.email}: {str(e)}")

                    # Logout y redirigir
                    logout(request)

                    if self._is_ajax_request(request):
                        return JsonResponse({
                            'success': False,
                            'error': 'Token de acceso inválido',
                            'redirect': reverse('appWeb:login')
                        }, status=401)

                    messages.error(request, 'Tu sesión ha expirado. Por favor inicia sesión nuevamente.')
                    return redirect(f"{reverse('appWeb:login')}?next={request.path}")

        response = self.get_response(request)
        return response

    def _requires_authentication(self, path):
        """
        Determina si una URL requiere autenticación
        """
        # Verificar URLs exactas públicas
        if path in self.public_urls:
            return False

        # Verificar prefijos públicos
        for prefix in self.public_prefixes:
            if path.startswith(prefix):
                return False

        # Por defecto, todas las demás rutas requieren autenticación
        return True

    def _is_ajax_request(self, request):
        """
        Detecta si es una petición AJAX
        """
        return (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            request.content_type == 'application/json' or
            'application/json' in request.headers.get('Accept', '')
        )

    def process_exception(self, request, exception):
        """
        Maneja excepciones relacionadas con autenticación
        """
        # Lista de excepciones que indican problemas de autenticación
        auth_exceptions = [
            'Token matching query does not exist',
            'User matching query does not exist',
            'Invalid token',
            'Token has expired',
        ]

        exception_str = str(exception)

        # Si la excepción está relacionada con autenticación
        if any(auth_error in exception_str for auth_error in auth_exceptions):
            logger.warning(f"Excepción de autenticación: {exception_str}")

            # Logout del usuario
            if hasattr(request, 'user') and request.user.is_authenticated:
                logout(request)

            # Para requests AJAX
            if self._is_ajax_request(request):
                return JsonResponse({
                    'success': False,
                    'error': 'Sesión expirada',
                    'redirect': reverse('appWeb:login')
                }, status=401)

            # Para requests normales
            messages.error(request, 'Tu sesión ha expirado. Por favor inicia sesión nuevamente.')
            return redirect(f"{reverse('appWeb:login')}?next={request.path}")

        # Si no es una excepción de auth, dejar que Django la maneje normalmente
        return None


class APITokenAuthMiddleware:
    """
    Middleware específico para manejar errores de token en las APIs
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Solo procesar rutas de API
        if request.path.startswith('/api/'):
            # Si hay error 401 o 403, asegurar que el frontend sepa que debe logout
            if response.status_code in [401, 403]:
                if hasattr(response, 'data') and isinstance(response.data, dict):
                    response.data['requires_logout'] = True
                elif response.content:
                    try:
                        import json
                        content = json.loads(response.content)
                        content['requires_logout'] = True
                        response.content = json.dumps(content).encode()
                    except:
                        pass

        return response

    def process_exception(self, request, exception):
        """
        Maneja excepciones en las APIs
        """
        if request.path.startswith('/api/'):
            auth_exceptions = [
                'Token matching query does not exist',
                'Invalid token',
                'Authentication credentials were not provided',
            ]

            if any(auth_error in str(exception) for auth_error in auth_exceptions):
                return JsonResponse({
                    'error': 'Token de autenticación inválido',
                    'requires_logout': True
                }, status=401)

        return None