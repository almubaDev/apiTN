import requests
import json
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .forms import LoginForm, RegisterForm, ProfileForm, ConsultaTarotForm, ContactForm


def render_password_reset_email(reset_url, user_email):
    """Helper para generar HTML del email de reset de password"""
    from django.template.loader import render_to_string

    html_content = render_to_string('appWeb/emails/password_reset.html', {
        'reset_url': reset_url,
        'user_email': user_email,
    })

    # Texto plano como fallback
    plain_content = f"""
        Tarotnaútica - Recuperación de Contraseña

        Hola,

        Recibimos tu solicitud para restablecer tu contraseña.

        Haz clic en este enlace para crear una nueva contraseña:
        {reset_url}

        Este enlace expira en 1 hora.

        Si no solicitaste este cambio, ignora este email.

        Saludos místicos,
        Equipo Tarotnaútica
        """

    return html_content, plain_content



def process_api_dates(data, date_fields=['created_at', 'updated_at', 'date_joined', 'last_login']):
    """
    Convierte campos de fecha de string a datetime objects en datos de API

    Args:
        data: dict o list - datos de la API
        date_fields: list - nombres de campos que contienen fechas

    Returns:
        Los mismos datos pero con fechas convertidas
    """
    if isinstance(data, list):
        return [process_api_dates(item, date_fields) for item in data]

    if isinstance(data, dict):
        processed_data = data.copy()
        for field in date_fields:
            if field in processed_data and isinstance(processed_data[field], str):
                try:
                    # Parse the ISO format datetime string
                    dt = parse_datetime(processed_data[field])
                    if dt:
                        # Si la fecha no tiene timezone, agregar UTC
                        if timezone.is_naive(dt):
                            dt = timezone.make_aware(dt)
                        processed_data[field] = dt
                except (ValueError, TypeError):
                    # Si hay error parseando, mantener el string original
                    pass
        return processed_data

    return data


class APIClient:
    """Cliente para consumir nuestra propia API"""

    def __init__(self, request=None):
        self.base_url = 'https://www.tarotnautica.store/api'
        self.request = request

    def _get_headers(self):
        """Obtener headers para las requests, incluyendo token si está autenticado"""
        headers = {'Content-Type': 'application/json'}
        if self.request and self.request.user.is_authenticated:
            try:
                token = self.request.user.auth_token.key
                headers['Authorization'] = f'Token {token}'
            except:
                pass
        return headers

    def get(self, endpoint, params=None):
        """Hacer GET request a la API"""
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                params=params or {}
            )
            return response.json() if response.status_code == 200 else None
        except:
            return None

    def post(self, endpoint, data=None):
        """Hacer POST request a la API"""
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                data=json.dumps(data or {})
            )
            return response
        except:
            return None


def home(request):
    """Página principal"""
    api = APIClient(request)

    # Obtener algunos sets destacados para mostrar en home
    sets_data = api.get('/oraculo/sets-con-mazos/')

    # Calcular total de mazos de todos los sets
    total_mazos = 0
    if sets_data:
        for set_item in sets_data:
            total_mazos += len(set_item.get('mazos', []))

    context = {
        'sets': sets_data[:3] if sets_data else [],  # Solo los primeros 3 para el home
        'total_mazos': total_mazos,  # Total de mazos disponibles
        'user_authenticated': request.user.is_authenticated,
    }

    return render(request, 'appWeb/home.html', context)


def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('appWeb:home')

    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            # Autenticar usando nuestra API
            api = APIClient(request)
            api_response = api.post('/users/login/', {
                'email': email,
                'password': password
            })

            if api_response and api_response.status_code == 200:
                # Login exitoso en API, ahora hacer login en Django
                user = authenticate(request, username=email, password=password)
                if user:
                    login(request, user)
                    if not remember_me:
                        request.session.set_expiry(0)  # Cerrar al cerrar navegador

                    messages.success(request, '¡Bienvenido de vuelta, místico viajero!')
                    next_url = request.GET.get('next', 'appWeb:home')
                    return redirect(next_url)

            messages.error(request, 'Credenciales incorrectas. Inténtalo de nuevo.')

    return render(request, 'appWeb/auth/login.html', {'form': form})


def register_view(request):
    """Vista de registro"""
    if request.user.is_authenticated:
        return redirect('appWeb:home')

    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Registrar usando nuestra API
            api = APIClient(request)
            api_response = api.post('/users/register/', {
                'email': form.cleaned_data['email'],
                'nombre': form.cleaned_data['nombre'],
                'password': form.cleaned_data['password1'],
                'password_confirm': form.cleaned_data['password2']
            })

            if api_response and api_response.status_code == 201:
                # Usuario creado exitosamente, ahora hacer login automático
                user = authenticate(request, username=form.cleaned_data['email'], password=form.cleaned_data['password1'])
                if user:
                    login(request, user)
                    messages.success(request, '¡Bienvenido a Tarotnaútica! Tu cuenta ha sido creada exitosamente.')
                else:
                    messages.success(request, '¡Cuenta creada exitosamente! Por favor inicia sesión.')
                return redirect('appWeb:home')
            else:
                try:
                    error_data = api_response.json() if api_response and api_response.content else {}
                    for field, errors in error_data.items():
                        if isinstance(errors, list):
                            for error in errors:
                                messages.error(request, f'{field}: {error}')
                        else:
                            messages.error(request, f'{field}: {errors}')
                except:
                    messages.error(request, 'Error al crear la cuenta. Inténtalo de nuevo.')

    return render(request, 'appWeb/auth/register.html', {'form': form})


def logout_view(request):
    """Vista de logout"""
    if request.user.is_authenticated:
        # Logout en API también
        api = APIClient(request)
        api.post('/users/logout/')

    logout(request)
    messages.info(request, 'Has cerrado sesión. ¡Hasta pronto!')
    return redirect('appWeb:home')




def password_reset_view(request):
    """Vista para solicitar recuperación de contraseña"""
    if request.user.is_authenticated:
        return redirect('appWeb:home')

    if request.method == 'POST':
        email = request.POST.get('email')
        print(f"DEBUG - Email recibido: {email}")

        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email es requerido'
            })

        # Enviar solicitud a la API
        api = APIClient(request)
        print(f"DEBUG - Base URL de API: {api.base_url}")
        print(f"DEBUG - Headers: {api._get_headers()}")

        # Datos a enviar
        data = {'email': email}
        print(f"DEBUG - Datos a enviar: {data}")

        try:
            api_response = api.post('/users/password-reset/', data)
            print(f"DEBUG - Respuesta API: {api_response}")

            if api_response:
                print(f"DEBUG - Status code: {api_response.status_code}")
                print(f"DEBUG - Content type: {api_response.headers.get('content-type', 'unknown')}")
                print(f"DEBUG - Response content: {api_response.content}")

                if api_response.status_code == 200:
                    return JsonResponse({
                        'success': True,
                        'message': 'Se ha enviado un enlace de recuperación a tu email'
                    })
                else:
                    try:
                        error_data = api_response.json()
                        print(f"DEBUG - Error data parsed: {error_data}")
                    except:
                        print(f"DEBUG - No se pudo parsear JSON de error")

                    return JsonResponse({
                        'success': False,
                        'error': f'Error de API: {api_response.status_code}'
                    })
            else:
                print("DEBUG - No response from API")
                return JsonResponse({
                    'success': False,
                    'error': 'No hay respuesta de la API'
                })

        except Exception as e:
            print(f"DEBUG - Exception: {str(e)}")
            print(f"DEBUG - Exception type: {type(e)}")
            import traceback
            print(f"DEBUG - Traceback: {traceback.format_exc()}")

            return JsonResponse({
                'success': False,
                'error': f'Error de conexión: {str(e)}'
            })

    return render(request, 'appWeb/auth/password_reset_form.html')


def password_reset_sent_view(request):
    """Vista para mostrar que el email fue enviado"""
    return render(request, 'appWeb/auth/password_reset_sent.html')


def password_reset_confirm_view(request, uid, token):
    """Vista para confirmar recuperación de contraseña"""
    if request.user.is_authenticated:
        return redirect('appWeb:home')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')

        if not new_password or not new_password_confirm:
            return JsonResponse({
                'success': False,
                'error': 'Todos los campos son requeridos'
            })

        if new_password != new_password_confirm:
            return JsonResponse({
                'success': False,
                'error': 'Las contraseñas no coinciden'
            })

        # Enviar confirmación a la API
        api = APIClient(request)
        api_response = api.post('/users/password-reset-confirm/', {
            'uid': uid,
            'token': token,
            'new_password': new_password,
            'new_password_confirm': new_password_confirm
        })

        if api_response and api_response.status_code == 200:
            return JsonResponse({
                'success': True,
                'message': 'Contraseña actualizada exitosamente'
            })
        else:
            try:
                error_data = api_response.json() if api_response and api_response.content else {}
                error_message = error_data.get('error', 'Error al actualizar contraseña')
            except:
                error_message = 'Error al actualizar contraseña. Inténtalo de nuevo.'

            return JsonResponse({
                'success': False,
                'error': error_message
            })

    context = {
        'uid': uid,
        'token': token
    }
    return render(request, 'appWeb/auth/password_reset_confirm.html', context)


def sets_list(request):
    """Lista de sets de mazos"""
    api = APIClient(request)
    sets_data = api.get('/oraculo/sets-con-mazos/')

    context = {
        'sets': sets_data or [],
        'page_title': 'Explora los Misterios del Tarot'
    }

    return render(request, 'appWeb/sets/list.html', context)


def mazos_list(request):
    """Lista de mazos con filtros por sets"""
    import random

    api = APIClient(request)

    # Obtener todos los sets para el filtro
    sets_data = api.get('/oraculo/sets/')

    # Obtener mazos con información básica
    mazos_data = api.get('/oraculo/mazos/')

    # Obtener filtros de la URL
    set_ids = request.GET.getlist('sets')  # Para filtros múltiples por checkbox

    # Filtrar mazos por sets seleccionados si hay filtros
    if set_ids:
        mazos_filtrados = []
        for mazo in mazos_data or []:
            if str(mazo.get('set')) in set_ids:
                mazos_filtrados.append(mazo)
        mazos_data = mazos_filtrados

    # Obtener una carta aleatoria para cada mazo
    if mazos_data:
        for mazo in mazos_data:
            cartas_data = api.get('/oraculo/cartas/', {'mazo': mazo['id']})
            if cartas_data:
                # Seleccionar una carta aleatoria
                carta_aleatoria = random.choice(cartas_data)
                mazo['carta_aleatoria'] = carta_aleatoria
            else:
                mazo['carta_aleatoria'] = None

    context = {
        'mazos': mazos_data or [],
        'sets': sets_data or [],
        'selected_sets': set_ids,
        'page_title': 'Mazos Místicos'
    }

    return render(request, 'appWeb/mazos/list.html', context)


def set_detail(request, set_id):
    """Detalle de un set específico"""
    api = APIClient(request)
    set_data = api.get(f'/oraculo/sets-con-mazos/{set_id}/')

    if not set_data:
        messages.error(request, 'Set no encontrado.')
        return redirect('appWeb:sets_list')

    context = {
        'set': set_data,
        'page_title': set_data.get('nombre', 'Set de Tarot')
    }

    return render(request, 'appWeb/sets/detail.html', context)


def mazo_detail(request, mazo_id):
    """Detalle de un mazo específico"""
    api = APIClient(request)
    mazo_data = api.get(f'/oraculo/mazos-con-tiradas/{mazo_id}/')

    if not mazo_data:
        messages.error(request, 'Mazo no encontrado.')
        return redirect('appWeb:sets_list')

    context = {
        'mazo': mazo_data,
        'page_title': mazo_data.get('nombre', 'Mazo de Tarot')
    }

    return render(request, 'appWeb/mazos/detail.html', context)


@login_required
def consulta_mazo(request, mazo_id):
    """
    Vista para consulta de tiradas de un mazo específico
    """
    api = APIClient(request)

    # Obtener mazo con sus tiradas
    mazo_data = api.get(f'/oraculo/mazos-con-tiradas/{mazo_id}/')

    if not mazo_data:
        messages.error(request, 'Mazo no encontrado.')
        return redirect('appWeb:mazos_list')

    # Obtener información de créditos del usuario
    wallet_data = api.get('/billing/mi-wallet/')

    # Si es POST, manejar la consulta AJAX
    if request.method == 'POST':
        tirada_id = request.POST.get('tirada_id')
        pregunta = request.POST.get('pregunta')

        if not tirada_id or not pregunta:
            return JsonResponse({
                'success': False,
                'error': 'Datos incompletos'
            })

        # CAMBIO: Obtener datos completos de la tirada
        tirada_data = api.get(f'/oraculo/tiradas/{tirada_id}/')
        if not tirada_data:
            return JsonResponse({
                'success': False,
                'error': 'Tirada no encontrada'
            })

        costo = tirada_data.get('costo', 1)

        # Verificar créditos
        if not wallet_data or wallet_data.get('creditos_disponibles', 0) < costo:
            return JsonResponse({
                'success': False,
                'error': 'creditos_insuficientes',
                'creditos_necesarios': costo,
                'creditos_disponibles': wallet_data.get('creditos_disponibles', 0) if wallet_data else 0
            })

        # Realizar consulta - AHORA incluye toda la información de la tirada
        consulta_response = api.post('/oraculo/consulta-tarot/', {
            'pregunta': pregunta,
            'set_id': mazo_data['set'],
            'mazo_id': mazo_id,
            'tirada_id': tirada_id
        })

        if consulta_response and consulta_response.status_code == 200:
            resultado = consulta_response.json()

            # Procesar el pago de la consulta con información completa de la tirada
            billing_response = api.post('/billing/procesar-consulta-tarot/', {
                'costo_creditos': costo,
                'tirada_info': {
                    'nombre': tirada_data.get('nombre'),
                    'descripcion': tirada_data.get('descripcion'),  # NUEVO
                    'mazo_nombre': mazo_data.get('nombre'),
                    'cantidad_cartas': tirada_data.get('cantidad_cartas'),  # NUEVO
                },
                'pregunta': pregunta,
                'interpretacion': resultado.get('interpretacion_ia', ''),
                'cartas_resultado': resultado.get('cartas', [])
            })

            # VERIFICAR QUE EL BILLING SEA EXITOSO PRIMERO
            if billing_response and billing_response.status_code == 200:
                # Billing exitoso = créditos fueron descontados
                wallet_actualizada = api.get('/billing/mi-wallet/')
                creditos_finales = wallet_actualizada.get('creditos_disponibles', 0) if wallet_actualizada else 0
            else:
                # Billing falló = NO se descontaron créditos = cantidad original
                creditos_finales = wallet_data.get('creditos_disponibles', 0)

            return JsonResponse({
                'success': True,
                'resultado': resultado,
                'creditos_restantes': creditos_finales
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Error al procesar la consulta. Inténtalo de nuevo.'
            })

    # GET: Mostrar página de consulta
    context = {
        'mazo': mazo_data,
        'wallet': wallet_data,
        'page_title': f'Consulta con {mazo_data.get("nombre", "Mazo")}'
    }

    return render(request, 'appWeb/consulta/mazo.html', context)


@login_required
def consulta_tarot(request, tirada_id):
    """Realizar consulta de tarot (requiere descontar créditos o usar suscripción)"""
    api = APIClient(request)
    tirada_data = api.get(f'/oraculo/tiradas/{tirada_id}/')

    if not tirada_data:
        messages.error(request, 'Tirada no encontrada.')
        return redirect('appWeb:sets_list')

    # Verificar si tiene créditos suficientes
    wallet_data = api.get('/billing/mi-wallet/')
    costo = tirada_data.get('costo', 1)

    form = ConsultaTarotForm()

    if request.method == 'POST':
        form = ConsultaTarotForm(request.POST)
        if form.is_valid():
            # Verificar créditos antes de proceder
            if wallet_data and wallet_data.get('creditos_disponibles', 0) >= costo:
                # Realizar consulta
                consulta_response = api.post('/oraculo/consulta-tarot/', {
                    'pregunta': form.cleaned_data['pregunta'],
                    'set_id': tirada_data['mazo']['set'],
                    'mazo_id': tirada_data['mazo']['id'],
                    'tirada_id': tirada_id
                })

                if consulta_response and consulta_response.status_code == 200:
                    resultado = consulta_response.json()

                    # ✅ Descontar créditos o registrar tirada por suscripción
                    billing_response = api.post('/billing/procesar-consulta-tarot/', {
                        'costo_creditos': costo,
                        'tirada_info': {
                            'nombre': tirada_data.get('nombre'),
                            'descripcion': tirada_data.get('descripcion'),
                            'mazo_nombre': tirada_data['mazo']['nombre'],
                            'cantidad_cartas': tirada_data.get('cantidad_cartas'),
                        },
                        'pregunta': form.cleaned_data['pregunta'],
                        'interpretacion': resultado.get('interpretacion_ia', ''),
                        'cartas_resultado': resultado.get('cartas', [])
                    })

                    if billing_response and billing_response.status_code == 200:
                        # Guardar resultado en sesión y redirigir
                        request.session['consulta_resultado'] = resultado
                        return redirect('appWeb:resultado_consulta', tirada_id=tirada_id)
                    else:
                        messages.error(request, 'La consulta se generó pero no se pudo registrar el cobro.')
                else:
                    messages.error(request, 'Error al procesar la consulta. Inténtalo de nuevo.')
            else:
                messages.warning(request, 'No tienes suficientes créditos para esta consulta.')
                return redirect('appWeb:comprar_creditos')

    context = {
        'tirada': tirada_data,
        'form': form,
        'costo': costo,
        'creditos_disponibles': wallet_data.get('creditos_disponibles', 0) if wallet_data else 0,
        'page_title': f'Consulta: {tirada_data.get("nombre", "Tirada de Tarot")}'
    }

    return render(request, 'appWeb/consulta/form.html', context)


@login_required
def resultado_consulta(request, tirada_id):
    """Mostrar resultado de consulta"""
    resultado = request.session.get('consulta_resultado')

    if not resultado:
        messages.error(request, 'No hay resultado de consulta disponible.')
        return redirect('appWeb:sets_list')

    # Limpiar resultado de la sesión
    if 'consulta_resultado' in request.session:
        del request.session['consulta_resultado']

    context = {
        'resultado': resultado,
        'page_title': 'Tu Destino Revelado'
    }

    return render(request, 'appWeb/consulta/resultado.html', context)


@login_required
def perfil(request):
    """Perfil del usuario"""
    api = APIClient(request)

    # Obtener datos del usuario
    user_data = api.get('/users/profile/detail/')
    wallet_data = api.get('/billing/mi-wallet/')
    estadisticas = api.get('/billing/estadisticas/')

    # Procesar fechas en todos los datos
    user_data = process_api_dates(user_data)
    wallet_data = process_api_dates(wallet_data)
    estadisticas = process_api_dates(estadisticas)

    form = ProfileForm(instance=request.user.profile if hasattr(request.user, 'profile') else None)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES,
                         instance=request.user.profile if hasattr(request.user, 'profile') else None)
        if form.is_valid():
            # Actualizar perfil usando API
            profile_response = api.post('/users/profile/update/', {
                'fecha_nacimiento': form.cleaned_data.get('fecha_nacimiento').isoformat() if form.cleaned_data.get('fecha_nacimiento') else None,
                'telefono': form.cleaned_data.get('telefono'),
                'biografia': form.cleaned_data.get('biografia'),
            })

            if profile_response and profile_response.status_code == 200:
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('appWeb:perfil')
            else:
                messages.error(request, 'Error al actualizar el perfil.')

    context = {
        'form': form,
        'user_data': user_data,
        'wallet': wallet_data,
        'estadisticas': estadisticas,
        'page_title': 'Tu Perfil Místico'
    }

    return render(request, 'appWeb/perfil/index.html', context)


@login_required
def editar_perfil(request):
    """Editar perfil del usuario - consume API"""
    api = APIClient(request)

    if request.method == 'POST':
        # Tomar datos del formulario y enviarlos a la API
        data = {}

        # Datos del profile
        if request.POST.get('fecha_nacimiento'):
            data['fecha_nacimiento'] = request.POST.get('fecha_nacimiento')

        if request.POST.get('biografia'):
            data['biografia'] = request.POST.get('biografia')

        # CORREGIDO: Usar el método correcto de APIClient
        try:
            response = requests.put(
                f"{api.base_url}/users/profile/update/",
                headers=api._get_headers(),
                data=json.dumps(data)
            )

            if response.status_code == 200:
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('appWeb:perfil')
            else:
                messages.error(request, f'Error al actualizar el perfil. Código: {response.status_code}')
        except Exception as e:
            messages.error(request, f'Error de conexión: {str(e)}')

    # GET: Mostrar formulario
    form = ProfileForm(instance=request.user.profile if hasattr(request.user, 'profile') else None)

    context = {
        'form': form,
        'page_title': 'Editar Perfil'
    }

    return render(request, 'appWeb/perfil/editar.html', context)


@login_required
@require_http_methods(["POST"])
def cambiar_password(request):
    """Cambiar contraseña usando la API"""
    api = APIClient(request)

    try:
        # Obtener datos del formulario
        data = {
            'old_password': request.POST.get('old_password'),
            'new_password': request.POST.get('new_password'),
            'new_password_confirm': request.POST.get('new_password_confirm')
        }

        print(f"DEBUG - Datos a enviar: {data}")

        # CORREGIDO: Usar APIClient correctamente
        response = api.post('/users/change-password/', data)

        if response and response.status_code == 200:
            print(f"DEBUG - Success: {response.json()}")
            # Logout del usuario por seguridad
            logout(request)
            return JsonResponse({
                'success': True,
                'message': 'Contraseña cambiada exitosamente'
            })
        else:
            print(f"DEBUG - Error status: {response.status_code if response else 'No response'}")
            if response:
                print(f"DEBUG - Error content: {response.content}")
                try:
                    error_data = response.json()
                    print(f"DEBUG - Error JSON: {error_data}")
                except:
                    error_data = {'error': f'HTTP {response.status_code}'}
            else:
                error_data = {'error': 'No response from API'}

            return JsonResponse({
                'success': False,
                'error': error_data.get('error', 'Error al cambiar contraseña')
            })

    except Exception as e:
        print(f"DEBUG - Exception: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error de conexión: {str(e)}'
        })


@login_required
def comprar_creditos(request):
    """Página para comprar créditos"""
    api = APIClient(request)

    # Obtener paquetes con botones de pago
    pais_usuario = 'CL'  # Por defecto, luego puedes detectarlo con GeoIP
    paquetes_data = api.get('/billing/paquetes-con-botones/', {'pais': pais_usuario})
    wallet_data = api.get('/billing/mi-wallet/')

    context = {
        'paquetes': paquetes_data or [],
        'wallet': wallet_data,
        'pais_usuario': pais_usuario,
        'page_title': 'Obtener Créditos Cósmicos'
    }

    return render(request, 'appWeb/billing/creditos.html', context)


@login_required
def historial_consultas(request):
    """Historial de consultas del usuario"""
    api = APIClient(request)
    consultas_data = api.get('/billing/mi-historial-consultas/')

    # Procesar fechas en los datos de la API
    consultas_procesadas = process_api_dates(consultas_data)

    context = {
        'consultas': consultas_procesadas or [],
        'page_title': 'Tu Viaje Místico'
    }

    return render(request, 'appWeb/perfil/historial.html', context)


def motor_nautica(request):
    """Página explicativa del Motor Náutica"""
    context = {
        'page_title': 'El Motor Náutica - Tecnología Mística'
    }

    return render(request, 'appWeb/motor_nautica.html', context)


# NUEVAS VISTAS para páginas de retorno de pago
@csrf_exempt
@require_http_methods(["GET", "POST"])
def payment_success(request):
    """
    Página de éxito del pago - Maneja tanto GET como POST
    """
    if request.method == 'POST':
        # Datos enviados directamente por PayPal
        return _procesar_retorno_paypal(request)
    else:
        # Verificación AJAX o acceso directo
        payment_reference = request.GET.get('ref')
        context = {
            'payment_reference': payment_reference,
            'page_title': 'Pago Exitoso'
        }
        return render(request, 'appWeb/payment/success.html', context)


def _procesar_retorno_paypal(request):
    """
    Procesar datos POST enviados por PayPal después del pago
    """
    import logging
    logger = logging.getLogger(__name__)

    # Extraer datos importantes de PayPal
    txn_id = request.POST.get('txn_id', '')
    custom_id = request.POST.get('custom', '')
    payment_status = request.POST.get('payment_status', '')
    mc_gross = request.POST.get('mc_gross', '')
    mc_currency = request.POST.get('mc_currency', '')
    payer_email = request.POST.get('payer_email', '')

    logger.info(f"PayPal POST recibido - Custom: {custom_id}, TxnID: {txn_id}, Status: {payment_status}")

    # Validaciones básicas
    if not custom_id or not txn_id:
        logger.error(f"Datos incompletos de PayPal: custom={custom_id}, txn_id={txn_id}")
        return render(request, 'appWeb/payment/cancel.html', {
            'error': 'Datos de pago incompletos'
        })

    try:
        # Importar modelos necesarios
        from billing.models import PagoCreditos, Wallet, TransaccionCreditos
        from django.db import transaction
        from django.utils import timezone

        # Buscar la compra por custom_id
        pago = PagoCreditos.objects.get(custom_id=custom_id, estado='pendiente')

        # Validaciones de seguridad básicas
        if payment_status != 'Completed':
            return render(request, 'appWeb/payment/cancel.html', {
                'error': f'Pago no completado: {payment_status}'
            })

        # Completar el pago
        with transaction.atomic():
            # Actualizar datos del pago
            pago.estado = 'completado'
            pago.datos_pago.update({
                'txn_id': txn_id,
                'payer_email': payer_email,
                'timestamp_completado': timezone.now().isoformat(),
                'origen': 'paypal_post_directo'
            })
            pago.save()

            # Agregar créditos al usuario
            wallet, created = Wallet.objects.get_or_create(user=pago.user)
            wallet.agregar_creditos(pago.paquete_creditos.cantidad_creditos)

            # Crear registro de transacción
            TransaccionCreditos.objects.create(
                user=pago.user,
                tipo='compra',
                cantidad=pago.paquete_creditos.cantidad_creditos,
                descripcion=f'Compra PayPal - {pago.paquete_creditos.nombre}',
                paquete_creditos=pago.paquete_creditos
            )

            logger.info(f"Pago completado: {custom_id} | Usuario: {pago.user.email}")

        # Redirigir a página de éxito con custom_id como referencia
        return redirect(f"/payment/success/?ref={custom_id}&source=paypal&status=completed")

    except Exception as e:
        logger.error(f"Error procesando retorno PayPal: {str(e)}")
        return render(request, 'appWeb/payment/cancel.html', {
            'error': 'Error procesando pago'
        })


def payment_cancel(request):
    """Página de pago cancelado"""
    payment_reference = request.GET.get('ref')

    context = {
        'payment_reference': payment_reference,
        'page_title': 'Pago Cancelado'
    }

    return render(request, 'appWeb/payment/cancel.html', context)


# AJAX Views
@login_required
@require_http_methods(["GET"])
def verificar_creditos(request):
    """AJAX: Verificar créditos disponibles"""
    api = APIClient(request)
    wallet_data = api.get('/billing/mi-wallet/')

    return JsonResponse({
        'creditos_disponibles': wallet_data.get('creditos_disponibles', 0) if wallet_data else 0
    })


@login_required
@require_http_methods(["POST"])
def procesar_pago(request):
    """AJAX: Procesar pago de créditos"""
    paquete_id = request.POST.get('paquete_id')
    boton_pago_id = request.POST.get('boton_pago_id')

    api = APIClient(request)
    response = api.post('/billing/comprar-creditos/', {
        'paquete_id': paquete_id,
        'boton_pago_id': boton_pago_id,
        'pais_usuario': 'CL'
    })

    if response and response.status_code == 200:
        return JsonResponse({
            'success': True,
            'message': 'Créditos agregados exitosamente',
            'data': response.json()
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Error al procesar el pago'
        })