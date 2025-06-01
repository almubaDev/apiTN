from django.contrib import admin
from .models import Set, Mazo, Carta, Tirada, ItemDeTirada


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


@admin.register(Mazo)
class MazoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'set', 'permite_cartas_invertidas']
    list_filter = ['set', 'permite_cartas_invertidas']
    search_fields = ['nombre', 'set__nombre']


@admin.register(Carta)
class CartaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nombre', 'mazo']
    list_filter = ['mazo']
    search_fields = ['nombre', 'mazo__nombre']
    ordering = ['mazo', 'numero']


class ItemDeTiradaInline(admin.TabularInline):
    model = ItemDeTirada
    extra = 1
    ordering = ['orden']


@admin.register(Tirada)
class TiradaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'mazo', 'cantidad_cartas', 'costo']
    list_filter = ['mazo', 'costo']
    search_fields = ['nombre', 'mazo__nombre']
    inlines = [ItemDeTiradaInline]


@admin.register(ItemDeTirada)
class ItemDeTiradaAdmin(admin.ModelAdmin):
    list_display = ['nombre_posicion', 'tirada', 'orden']
    list_filter = ['tirada']
    ordering = ['tirada', 'orden']