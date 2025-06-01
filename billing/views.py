from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db import models

from .models import (
    MetodoPago, PaqueteCreditos, BotonPago, TipoSuscripcion, Wallet, Suscripcion,
    TransaccionCreditos, HistorialConsultas, PagoSuscripcion, PagoCreditos
)
from .serializers import (
    MetodoPagoSerializer, PaqueteCreditosSerializer, PaqueteCreditosSimpleSerializer,
    BotonPagoSerializer, TipoSuscripcionSerializer, WalletSerializer,
    SuscripcionSerializer, TransaccionCreditosSerializer, HistorialConsultasSerializer,
    ComprarCreditosSerializer, SuscribirseSerializer, EstadisticasUsuarioSerializer,
    ResumenBillingSerializer
)


class MetodoPagoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para obtener métodos de pago disponibles
    """
    queryset = MetodoPago.objects.filter(activo=True)
    serializer_class = MetodoPagoSerializer
    permission_classes = [permissions.AllowAny]


class PaqueteCreditosViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para obtener paquetes de créditos disponibles
    """
    queryset = PaqueteCreditos.objects.filter(activo=True)
    serializer_class = PaqueteCreditosSimpleSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=True, methods=['get'], url_path='con-botones')
    def con_botones(self, request, pk=None):
        """
        Obtener paquete con botones de pago filtrados por país
        """
        paquete = self.get_object()
        pais_usuario = request.GET.get('pais', 'CL')
        
        # Filtrar botones disponibles para el país
        botones_disponibles = paquete.botones_pago.filter(
            activo=True,
            metodo_pago__activo=True
        )
        
        # Filtrar por país soportado
        botones_filtrados = []
        for boton in botones_disponibles:
            if boton.es_disponible_para_pais(pais_usuario):
                botones_filtrados.append(boton)
        
        data = {
            'paquete': PaqueteCreditosSerializer(paquete).data,
            'botones_disponibles': BotonPagoSerializer(botones_filtrados, many=True).data
        }
        
        return Response(data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def paquetes_con_botones(request):
    """
    Obtener todos los paquetes con sus botones de pago filtrados por país
    """
    pais_usuario = request.GET.get('pais', 'CL')
    paquetes = PaqueteCreditos.objects.filter(activo=True).order_by('precio')
    
    resultado = []
    for paquete in paquetes:
        # Filtrar botones disponibles para el país
        botones_disponibles = paquete.botones_pago.filter(
            activo=True,
            metodo_pago__activo=True
        )
        
        botones_filtrados = []
        for boton in botones_disponibles:
            if boton.es_disponible_para_pais(pais_usuario):
                botones_filtrados.append(boton)
        
        if botones_filtrados:  # Solo incluir paquetes con botones disponibles
            resultado.append({
                'paquete': PaqueteCreditosSerializer(paquete).data,
                'botones_disponibles': BotonPagoSerializer(botones_filtrados, many=True).data
            })
    
    return Response(resultado)


class TipoSuscripcionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para obtener tipos de suscripción disponibles
    """
    queryset = TipoSuscripcion.objects.filter(activo=True)
    serializer_class = TipoSuscripcionSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mi_wallet(request):
    """
    Obtener información de la wallet del usuario autenticado
    """
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    serializer = WalletSerializer(wallet)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mi_suscripcion(request):
    """
    Obtener suscripción activa del usuario autenticado
    """
    suscripcion = Suscripcion.objects.filter(
        user=request.user, 
        estado='activa'
    ).first()
    
    if suscripcion:
        serializer = SuscripcionSerializer(suscripcion)
        return Response(serializer.data)
    
    return Response({'message': 'No tienes suscripción activa'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mis_transacciones(request):
    """
    Obtener historial de transacciones de créditos del usuario
    """
    transacciones = TransaccionCreditos.objects.filter(user=request.user)[:20]
    serializer = TransaccionCreditosSerializer(transacciones, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mi_historial_consultas(request):
    """
    Obtener historial de consultas del usuario
    """
    consultas = HistorialConsultas.objects.filter(user=request.user)[:20]
    serializer = HistorialConsultasSerializer(consultas, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def comprar_creditos(request):
    """
    Comprar paquete de créditos usando un botón de pago específico
    """
    serializer = ComprarCreditosSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    paquete_id = serializer.validated_data['paquete_id']
    boton_pago_id = serializer.validated_data['boton_pago_id']
    pais_usuario = serializer.validated_data.get('pais_usuario', 'CL')
    
    try:
        paquete = get_object_or_404(PaqueteCreditos, id=paquete_id, activo=True)
        boton_pago = get_object_or_404(BotonPago, id=boton_pago_id, paquete=paquete, activo=True)
        
        # Verificar si el botón está disponible para el país del usuario
        if not boton_pago.es_disponible_para_pais(pais_usuario):
            return Response({
                'error': 'Método de pago no disponible en tu país'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Crear registro de pago
            pago = PagoCreditos.objects.create(
                user=request.user,
                paquete_creditos=paquete,
                boton_pago=boton_pago,
                monto=paquete.precio,
                metodo_pago=boton_pago.metodo_pago.codigo,
                estado='completado'  # En producción, esto sería 'pendiente' hasta confirmar pago
            )
            
            # Obtener o crear wallet
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            
            # Agregar créditos
            wallet.agregar_creditos(paquete.cantidad_creditos)
            
            # Crear transacción
            TransaccionCreditos.objects.create(
                user=request.user,
                tipo='compra',
                cantidad=paquete.cantidad_creditos,
                descripcion=f'Compra de {paquete.nombre} vía {boton_pago.metodo_pago.nombre}',
                paquete_creditos=paquete
            )
        
        return Response({
            'message': 'Créditos comprados exitosamente',
            'creditos_agregados': paquete.cantidad_creditos,
            'creditos_totales': wallet.creditos_disponibles,
            'metodo_usado': boton_pago.metodo_pago.nombre,
            'pago_id': pago.id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error procesando compra: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def suscribirse(request):
    """
    Crear nueva suscripción
    """
    serializer = SuscribirseSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    tipo_suscripcion_id = serializer.validated_data['tipo_suscripcion_id']
    metodo_pago = serializer.validated_data['metodo_pago']
    
    try:
        tipo_suscripcion = get_object_or_404(TipoSuscripcion, id=tipo_suscripcion_id, activo=True)
        
        # Verificar si ya tiene suscripción activa
        suscripcion_activa = Suscripcion.objects.filter(
            user=request.user,
            estado='activa'
        ).first()
        
        if suscripcion_activa and suscripcion_activa.esta_activa():
            return Response({
                'error': 'Ya tienes una suscripción activa'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Crear suscripción
            suscripcion = Suscripcion.objects.create(
                user=request.user,
                tipo_suscripcion=tipo_suscripcion,
                fecha_inicio=timezone.now()
            )
            
            # Crear registro de pago
            pago = PagoSuscripcion.objects.create(
                suscripcion=suscripcion,
                monto=tipo_suscripcion.precio_mensual,
                metodo_pago=metodo_pago,
                estado='completado'  # En producción, esto sería 'pendiente'
            )
        
        return Response({
            'message': 'Suscripción creada exitosamente',
            'suscripcion': SuscripcionSerializer(suscripcion).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Error procesando suscripción: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancelar_suscripcion(request):
    """
    Cancelar suscripción activa
    """
    suscripcion = Suscripcion.objects.filter(
        user=request.user,
        estado='activa'
    ).first()
    
    if not suscripcion:
        return Response({
            'error': 'No tienes suscripción activa para cancelar'
        }, status=status.HTTP_404_NOT_FOUND)
    
    suscripcion.estado = 'cancelada'
    suscripcion.auto_renovar = False
    suscripcion.save()
    
    return Response({
        'message': 'Suscripción cancelada exitosamente'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def estadisticas_usuario(request):
    """
    Obtener estadísticas del usuario
    """
    user = request.user
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    suscripcion_activa = Suscripcion.objects.filter(
        user=user,
        estado='activa'
    ).first()
    
    total_consultas = HistorialConsultas.objects.filter(user=user).count()
    creditos_gastados = TransaccionCreditos.objects.filter(
        user=user,
        tipo='uso'
    ).aggregate(total=models.Sum('cantidad'))['total'] or 0
    
    data = {
        'creditos_disponibles': wallet.creditos_disponibles,
        'suscripcion_activa': suscripcion_activa.esta_activa() if suscripcion_activa else False,
        'tiradas_disponibles_suscripcion': suscripcion_activa.tiradas_disponibles() if suscripcion_activa else 0,
        'total_consultas': total_consultas,
        'creditos_gastados_total': creditos_gastados
    }
    
    serializer = EstadisticasUsuarioSerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def resumen_billing(request):
    """
    Obtener resumen completo de billing del usuario
    """
    user = request.user
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    suscripcion_activa = Suscripcion.objects.filter(
        user=user,
        estado='activa'
    ).first()
    
    ultimas_transacciones = TransaccionCreditos.objects.filter(user=user)[:5]
    ultimas_consultas = HistorialConsultas.objects.filter(user=user)[:5]
    
    data = {
        'wallet': WalletSerializer(wallet).data,
        'suscripcion_activa': SuscripcionSerializer(suscripcion_activa).data if suscripcion_activa else None,
        'ultimas_transacciones': TransaccionCreditosSerializer(ultimas_transacciones, many=True).data,
        'ultimas_consultas': HistorialConsultasSerializer(ultimas_consultas, many=True).data
    }
    
    return Response(data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def procesar_consulta_tarot(request):
    """
    Procesar el pago/descuento de una consulta de tarot
    """
    costo_creditos = request.data.get('costo_creditos', 0)
    tirada_info = request.data.get('tirada_info', {})
    pregunta = request.data.get('pregunta', '')
    interpretacion = request.data.get('interpretacion', '')
    cartas_resultado = request.data.get('cartas_resultado', [])
    
    user = request.user
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Verificar si tiene suscripción activa con tiradas disponibles
    suscripcion_activa = Suscripcion.objects.filter(
        user=user,
        estado='activa'
    ).first()
    
    uso_suscripcion = False
    
    try:
        with transaction.atomic():
            # Priorizar uso de suscripción si está disponible
            if suscripcion_activa and suscripcion_activa.tiradas_disponibles() > 0:
                if suscripcion_activa.usar_tirada():
                    uso_suscripcion = True
                    costo_final = 0
                else:
                    return Response({
                        'error': 'Error usando tirada de suscripción'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Usar créditos
                if not wallet.tiene_creditos_suficientes(costo_creditos):
                    return Response({
                        'error': 'Créditos insuficientes'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                wallet.descontar_creditos(costo_creditos)
                costo_final = costo_creditos
                
                # Crear transacción de uso de créditos
                TransaccionCreditos.objects.create(
                    user=user,
                    tipo='uso',
                    cantidad=costo_creditos,
                    descripcion=f'Consulta de tarot - {tirada_info.get("nombre", "Tirada")}'
                )
            
            # Guardar en historial
            HistorialConsultas.objects.create(
                user=user,
                pregunta=pregunta,
                tirada_nombre=tirada_info.get('nombre', ''),
                mazo_nombre=tirada_info.get('mazo_nombre', ''),
                costo_creditos=costo_final,
                uso_suscripcion=uso_suscripcion,
                interpretacion=interpretacion,
                cartas_resultado=cartas_resultado
            )
        
        return Response({
            'message': 'Consulta procesada exitosamente',
            'uso_suscripcion': uso_suscripcion,
            'costo_creditos': costo_final,
            'creditos_restantes': wallet.creditos_disponibles,
            'tiradas_restantes_suscripcion': suscripcion_activa.tiradas_disponibles() if suscripcion_activa else 0
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error procesando consulta: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)