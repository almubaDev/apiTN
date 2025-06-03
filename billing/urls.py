from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para los ViewSets
router = DefaultRouter()
router.register(r'paquetes-creditos', views.PaqueteCreditosViewSet)
router.register(r'tipos-suscripcion', views.TipoSuscripcionViewSet)

urlpatterns = [
    # URLs del router
    path('', include(router.urls)),
    
    # Wallet del usuario
    path('mi-wallet/', views.mi_wallet, name='mi-wallet'),
    
    # Suscripciones
    path('mi-suscripcion/', views.mi_suscripcion, name='mi-suscripcion'),
    path('suscribirse/', views.suscribirse, name='suscribirse'),
    path('cancelar-suscripcion/', views.cancelar_suscripcion, name='cancelar-suscripcion'),
    
    # Créditos - URLs existentes
    path('comprar-creditos/', views.comprar_creditos, name='comprar-creditos'),
    path('mis-transacciones/', views.mis_transacciones, name='mis-transacciones'),
    path('paquetes-con-botones/', views.paquetes_con_botones, name='paquetes-con-botones'),
    
    # NUEVAS URLs para flujo de pago externo
    path('generar-url-pago/', views.generar_url_pago, name='generar-url-pago'),
    path('verificar-pago/', views.verificar_pago, name='verificar-pago'),
    
    # Webhooks/confirmaciones de plataformas de pago
    path('paypal-ipn/', views.paypal_ipn, name='paypal-ipn'),
    path('flow-confirm/', views.flow_confirm, name='flow-confirm'),
    
    # Historial y consultas
    path('mi-historial-consultas/', views.mi_historial_consultas, name='mi-historial-consultas'),
    path('procesar-consulta-tarot/', views.procesar_consulta_tarot, name='procesar-consulta-tarot'),
    
    # Estadísticas y resúmenes
    path('estadisticas/', views.estadisticas_usuario, name='estadisticas-usuario'),
    path('resumen/', views.resumen_billing, name='resumen-billing'),
]