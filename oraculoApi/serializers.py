from rest_framework import serializers
from .models import Set, Mazo, Carta, Tirada, ItemDeTirada


class SetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Set
        fields = ['id', 'nombre', 'descripcion']


class MazoSerializer(serializers.ModelSerializer):
    set_nombre = serializers.CharField(source='set.nombre', read_only=True)
    
    class Meta:
        model = Mazo
        fields = ['id', 'set', 'set_nombre', 'nombre', 'descripcion', 'permite_cartas_invertidas']


class CartaSerializer(serializers.ModelSerializer):
    mazo_nombre = serializers.CharField(source='mazo.nombre', read_only=True)
    
    class Meta:
        model = Carta
        fields = ['id', 'mazo', 'mazo_nombre', 'numero', 'nombre', 'imagen', 
                 'significado_normal', 'significado_invertida']


class ItemDeTiradaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemDeTirada
        fields = ['id', 'nombre_posicion', 'descripcion', 'orden']


class TiradaSerializer(serializers.ModelSerializer):
    mazo_nombre = serializers.CharField(source='mazo.nombre', read_only=True)
    items = ItemDeTiradaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Tirada
        fields = ['id', 'mazo', 'mazo_nombre', 'nombre', 'descripcion', 
                 'imagen', 'cantidad_cartas', 'costo', 'items']


# Serializers para el flujo principal de consulta
class SetConMazosSerializer(serializers.ModelSerializer):
    mazos = MazoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Set
        fields = ['id', 'nombre', 'descripcion', 'mazos']


class MazoConTiradasSerializer(serializers.ModelSerializer):
    tiradas = TiradaSerializer(many=True, read_only=True)
    set_nombre = serializers.CharField(source='set.nombre', read_only=True)
    
    class Meta:
        model = Mazo
        fields = ['id', 'set', 'set_nombre', 'nombre', 'descripcion', 
                 'permite_cartas_invertidas', 'tiradas']


# Serializer para la respuesta de la consulta de tarot
class ConsultaTarotSerializer(serializers.Serializer):
    pregunta = serializers.CharField()
    set_id = serializers.IntegerField()
    mazo_id = serializers.IntegerField()
    tirada_id = serializers.IntegerField()


class CartaEnTiradaSerializer(serializers.Serializer):
    carta = CartaSerializer()
    posicion = serializers.CharField()
    descripcion_posicion = serializers.CharField()
    es_invertida = serializers.BooleanField()
    significado_usado = serializers.CharField()


class RespuestaTarotSerializer(serializers.Serializer):
    pregunta = serializers.CharField()
    interpretacion_ia = serializers.CharField()
    cartas = CartaEnTiradaSerializer(many=True)
    tirada_info = TiradaSerializer()