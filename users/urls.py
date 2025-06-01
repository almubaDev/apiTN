from django.urls import path
from . import views



app_name = 'users'

urlpatterns = [
    # Autenticación
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Perfil de usuario
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update-profile'),
    path('profile/detail/', views.user_detail, name='user-detail'),
    
    # Cambio de contraseña
    path('change-password/', views.change_password, name='change-password'),
    # Recuperación de contraseña
    path('password-reset/', views.password_reset_request, name='password-reset'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password-reset-confirm'),
]