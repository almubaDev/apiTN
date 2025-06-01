from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'nombre', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'nombre']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombre',)}),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'telefono', 'fecha_nacimiento', 'created_at']
    list_filter = ['created_at', 'fecha_nacimiento']
    search_fields = ['user__email', 'user__nombre', 'telefono']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuario', {'fields': ('user',)}),
        ('Información Personal', {
            'fields': ('fecha_nacimiento', 'telefono', 'biografia')
        }),
        ('Avatar', {'fields': ('avatar',)}),
        ('Fechas', {'fields': ('created_at', 'updated_at')}),
    )