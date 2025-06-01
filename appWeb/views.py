import requests
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.urls import reverse

from .forms import LoginForm, RegisterForm, ProfileForm, ConsultaTarotForm, ContactForm


class APIClient:
    """Cliente para consumir nuestra propia API"""
    
    def __init__(self, request=None):
        self.base_url = 'http://localhost:8000/api'
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
    
    context = {
        'sets': sets_data[:3] if sets_data else [],  # Solo los primeros 3 para el home
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
            api_response = requests.post('http://localhost:8000/api/users/login/', {
                'email': email,
                'password': password
            })
            
            if api_response.status_code == 200:
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
            api_response = requests.post('http://localhost:8000/api/users/register/', {
                'email': form.cleaned_data['email'],
                'nombre': form.cleaned_data['nombre'],
                'password': form.cleaned_data['password1'],
                'password_confirm': form.cleaned_data['password2']
            })
            
            if api_response.status_code == 201:
                messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.')
                return redirect('appWeb:login')
            else:
                error_data = api_response.json() if api_response.content else {}
                for field, errors in error_data.items():
                    if isinstance(errors, list):
                        for error in errors:
                            messages.error(request, f'{field}: {error}')
                    else:
                        messages.error(request, f'{field}: {errors}')
    
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


def sets_list(request):
    """Lista de sets de mazos"""
    api = APIClient(request)
    sets_data = api.get('/oraculo/sets-con-mazos/')
    
    context = {
        'sets': sets_data or [],
        'page_title': 'Explora los Misterios del Tarot'
    }
    
    return render(request, 'appWeb/sets/list.html', context)


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
def consulta_tarot(request, tirada_id):
    """Realizar consulta de tarot"""
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
                    # Guardar resultado en sesión y redirigir
                    request.session['consulta_resultado'] = consulta_response.json()
                    return redirect('appWeb:resultado_consulta', tirada_id=tirada_id)
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
    
    form = ProfileForm(instance=request.user.profile if hasattr(request.user, 'profile') else None)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, 
                         instance=request.user.profile if hasattr(request.user, 'profile') else None)
        if form.is_valid():
            # Actualizar perfil usando API
            profile_response = api.post('/users/profile/update/', {
                'fecha_nacimiento': form.cleaned_data.get('fecha_nacimiento'),
                'telefono': form.cleaned_data.get('telefono'),
                'biografia': form.cleaned_data.get('biografia'),
            })
            
            if profile_response and profile_response.status_code == 200:
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('appWeb:perfil')
    
    context = {
        'form': form,
        'user_data': user_data,
        'wallet': wallet_data,
        'estadisticas': estadisticas,
        'page_title': 'Tu Perfil Místico'
    }
    
    return render(request, 'appWeb/perfil/index.html', context)


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
    
    context = {
        'consultas': consultas_data or [],
        'page_title': 'Tu Viaje Místico'
    }
    
    return render(request, 'appWeb/perfil/historial.html', context)


def motor_nautica(request):
    """Página explicativa del Motor Náutica"""
    context = {
        'page_title': 'El Motor Náutica - Tecnología Mística'
    }
    
    return render(request, 'appWeb/motor_nautica.html', context)


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