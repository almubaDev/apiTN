from django.contrib import admin
from .models import (
    MetodoPago, PaqueteCreditos, BotonPago, TipoSuscripcion, Wallet, Suscripcion,
    TransaccionCreditos, HistorialConsultas, PagoSuscripcion, PagoCreditos
)

# Desregistrar modelos si ya están registrados (para evitar errores)
models_to_unregister = [
    PaqueteCreditos, TipoSuscripcion, Wallet, Suscripcion,
    TransaccionCreditos, HistorialConsultas, PagoSuscripcion, PagoCreditos
]

for model in models_to_unregister:
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'activo', 'orden', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre', 'codigo']
    ordering = ['orden', 'nombre']
    list_editable = ['activo', 'orden']


class BotonPagoInline(admin.TabularInline):
    model = BotonPago
    extra = 0
    fields = ['metodo_pago', 'url_base', 'activo']


@admin.register(PaqueteCreditos)
class PaqueteCreditosAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cantidad_creditos', 'precio', 'precio_por_credito', 'destacado', 'activo', 'created_at']
    list_filter = ['activo', 'destacado', 'created_at']
    search_fields = ['nombre']
    ordering = ['precio']
    list_editable = ['destacado', 'activo']
    inlines = [BotonPagoInline]
    
    def precio_por_credito(self, obj):
        return f"${obj.precio_por_credito:.3f}"
    precio_por_credito.short_description = 'Precio/Crédito'


@admin.register(BotonPago)
class BotonPagoAdmin(admin.ModelAdmin):
    list_display = ['paquete', 'metodo_pago', 'activo', 'created_at']
    list_filter = ['metodo_pago', 'activo', 'created_at']
    search_fields = ['paquete__nombre', 'metodo_pago__nombre']
    ordering = ['paquete', 'metodo_pago']


@admin.register(TipoSuscripcion)
class TipoSuscripcionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio_mensual', 'tiradas_incluidas', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre']
    ordering = ['precio_mensual']


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'creditos_disponibles', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'user__nombre']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo_suscripcion', 'estado', 'fecha_inicio', 'fecha_fin', 'tiradas_usadas']
    list_filter = ['estado', 'tipo_suscripcion', 'auto_renovar', 'created_at']
    search_fields = ['user__email', 'user__nombre']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'fecha_inicio'


@admin.register(TransaccionCreditos)
class TransaccionCreditosAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo', 'cantidad', 'paquete_creditos', 'created_at']
    list_filter = ['tipo', 'created_at']
    search_fields = ['user__email', 'user__nombre', 'descripcion']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(HistorialConsultas)
class HistorialConsultasAdmin(admin.ModelAdmin):
    list_display = ['user', 'tirada_nombre', 'mazo_nombre', 'costo_creditos', 'uso_suscripcion', 'created_at']
    list_filter = ['uso_suscripcion', 'created_at', 'mazo_nombre']
    search_fields = ['user__email', 'user__nombre', 'pregunta', 'tirada_nombre']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(PagoSuscripcion)
class PagoSuscripcionAdmin(admin.ModelAdmin):
    list_display = ['suscripcion', 'monto', 'estado', 'metodo_pago', 'created_at']
    list_filter = ['estado', 'metodo_pago', 'created_at']
    search_fields = ['suscripcion__user__email', 'referencia_externa']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PagoCreditos)
class PagoCreditosAdmin(admin.ModelAdmin):
    list_display = ['user', 'paquete_creditos', 'boton_pago', 'monto', 'estado', 'metodo_pago', 'created_at']
    list_filter = ['estado', 'metodo_pago', 'boton_pago__metodo_pago', 'created_at']
    search_fields = ['user__email', 'user__nombre', 'referencia_externa']
    readonly_fields = ['created_at', 'updated_at']