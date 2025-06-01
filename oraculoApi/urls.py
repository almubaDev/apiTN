from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para los ViewSets
router = DefaultRouter()
router.register(r'sets', views.SetViewSet)
router.register(r'sets-con-mazos', views.SetConMazosViewSet, basename='set-con-mazos')
router.register(r'mazos', views.MazoViewSet)
router.register(r'mazos-con-tiradas', views.MazoConTiradasViewSet, basename='mazo-con-tiradas')
router.register(r'cartas', views.CartaViewSet)
router.register(r'tiradas', views.TiradaViewSet)

urlpatterns = [
    # URLs del router
    path('', include(router.urls)),
    
    # Endpoint principal para consulta de tarot
    path('consulta-tarot/', views.consulta_tarot, name='consulta-tarot'),
]