from rest_framework import serializers
from .models import (
    MetodoPago, PaqueteCreditos, BotonPago, TipoSuscripcion, Wallet, Suscripcion,
    TransaccionCreditos, HistorialConsultas, PagoSuscripcion, PagoCreditos
)


class MetodoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetodoPago
        fields = ['id', 'nombre', 'codigo', 'descripcion', 'icono', 'color_boton',
                 'paises_soportados', 'activo', 'orden']


class BotonPagoSerializer(serializers.ModelSerializer):
    metodo_pago = MetodoPagoSerializer(read_only=True)

    class Meta:
        model = BotonPago
        fields = ['id', 'metodo_pago', 'url_base', 'parametros_adicionales', 'activo']


class PaqueteCreditosSerializer(serializers.ModelSerializer):
    precio_por_credito = serializers.ReadOnlyField()
    tiene_descuento = serializers.ReadOnlyField()
    porcentaje_descuento = serializers.ReadOnlyField()
    botones_pago = BotonPagoSerializer(many=True, read_only=True)

    class Meta:
        model = PaqueteCreditos
        fields = ['id', 'nombre', 'descripcion', 'cantidad_creditos', 'precio',
                 'precio_anterior', 'precio_por_credito', 'tiene_descuento',
                 'porcentaje_descuento', 'destacado', 'activo', 'botones_pago']


class PaqueteCreditosSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple sin botones de pago para listas"""
    precio_por_credito = serializers.ReadOnlyField()
    tiene_descuento = serializers.ReadOnlyField()
    porcentaje_descuento = serializers.ReadOnlyField()

    class Meta:
        model = PaqueteCreditos
        fields = ['id', 'nombre', 'descripcion', 'cantidad_creditos', 'precio',
                 'precio_anterior', 'precio_por_credito', 'tiene_descuento',
                 'porcentaje_descuento', 'destacado', 'activo']


class TipoSuscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoSuscripcion
        fields = ['id', 'nombre', 'descripcion', 'precio_mensual', 'tiradas_incluidas', 'activo']


class WalletSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_nombre = serializers.CharField(source='user.nombre', read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'user_email', 'user_nombre', 'creditos_disponibles', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class SuscripcionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    tipo_nombre = serializers.CharField(source='tipo_suscripcion.nombre', read_only=True)
    tiradas_disponibles = serializers.SerializerMethodField()
    esta_activa = serializers.SerializerMethodField()

    class Meta:
        model = Suscripcion
        fields = ['id', 'user_email', 'tipo_suscripcion', 'tipo_nombre', 'fecha_inicio',
                 'fecha_fin', 'estado', 'tiradas_usadas', 'tiradas_disponibles',
                 'esta_activa', 'auto_renovar', 'created_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_tiradas_disponibles(self, obj):
        return obj.tiradas_disponibles()

    def get_esta_activa(self, obj):
        return obj.esta_activa()


class TransaccionCreditosSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    paquete_nombre = serializers.CharField(source='paquete_creditos.nombre', read_only=True)

    class Meta:
        model = TransaccionCreditos
        fields = ['id', 'user_email', 'tipo', 'cantidad', 'descripcion',
                 'paquete_creditos', 'paquete_nombre', 'created_at']
        read_only_fields = ['created_at']


class HistorialConsultasSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = HistorialConsultas
        fields = ['id', 'user_email', 'pregunta', 'tirada_nombre', 'mazo_nombre',
                 'costo_creditos', 'uso_suscripcion', 'interpretacion',
                 'cartas_resultado', 'created_at']
        read_only_fields = ['created_at']


class PagoSuscripcionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='suscripcion.user.email', read_only=True)
    tipo_suscripcion = serializers.CharField(source='suscripcion.tipo_suscripcion.nombre', read_only=True)

    class Meta:
        model = PagoSuscripcion
        fields = ['id', 'user_email', 'suscripcion', 'tipo_suscripcion', 'monto',
                 'estado', 'metodo_pago', 'referencia_externa', 'created_at']
        read_only_fields = ['created_at', 'updated_at']


class PagoCreditosSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    paquete_nombre = serializers.CharField(source='paquete_creditos.nombre', read_only=True)
    metodo_pago_nombre = serializers.CharField(source='boton_pago.metodo_pago.nombre', read_only=True)

    class Meta:
        model = PagoCreditos
        fields = ['id', 'user_email', 'paquete_creditos', 'paquete_nombre', 'boton_pago',
                 'metodo_pago_nombre', 'monto', 'estado', 'metodo_pago', 'referencia_externa', 'custom_id', 'created_at']
        read_only_fields = ['created_at', 'updated_at']


# Serializers para procesos específicos
class ComprarCreditosSerializer(serializers.Serializer):
    paquete_id = serializers.IntegerField()
    boton_pago_id = serializers.IntegerField()
    pais_usuario = serializers.CharField(max_length=2, required=False, default='CL')


class SuscribirseSerializer(serializers.Serializer):
    tipo_suscripcion_id = serializers.IntegerField()
    metodo_pago = serializers.CharField(max_length=50)


class EstadisticasUsuarioSerializer(serializers.Serializer):
    creditos_disponibles = serializers.IntegerField()
    suscripcion_activa = serializers.BooleanField()
    tiradas_disponibles_suscripcion = serializers.IntegerField()
    total_consultas = serializers.IntegerField()
    creditos_gastados_total = serializers.IntegerField()


class ResumenBillingSerializer(serializers.Serializer):
    wallet = WalletSerializer()
    suscripcion_activa = SuscripcionSerializer(allow_null=True)
    ultimas_transacciones = TransaccionCreditosSerializer(many=True)
    ultimas_consultas = HistorialConsultasSerializer(many=True)


class PaqueteConBotonesSerializer(serializers.Serializer):
    """Serializer para mostrar paquetes con botones filtrados por país"""
    paquete = PaqueteCreditosSerializer()
    botones_disponibles = BotonPagoSerializer(many=True)