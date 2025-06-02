from django.urls import path
from . import views

app_name = 'appWeb'

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Explorar
    path('sets/', views.sets_list, name='sets_list'),
    path('sets/<int:set_id>/', views.set_detail, name='set_detail'),
    path('mazos/', views.mazos_list, name='mazos_list'),
    path('mazos/<int:mazo_id>/', views.mazo_detail, name='mazo_detail'),
    
    # Consulta de tarot
    path('consulta/mazo/<int:mazo_id>/', views.consulta_mazo, name='consulta_mazo'),
    path('consulta/<int:tirada_id>/', views.consulta_tarot, name='consulta_tarot'),
    path('consulta/<int:tirada_id>/resultado/', views.resultado_consulta, name='resultado_consulta'),
    
    # Perfil y billing
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('creditos/', views.comprar_creditos, name='comprar_creditos'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    path('historial/', views.historial_consultas, name='historial_consultas'),
    path('motor-nautica/', views.motor_nautica, name='motor_nautica'),
    
    # AJAX endpoints
    path('ajax/verificar-creditos/', views.verificar_creditos, name='verificar_creditos'),
    path('ajax/procesar-pago/', views.procesar_pago, name='procesar_pago'),
]