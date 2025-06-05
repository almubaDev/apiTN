from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db import models
import uuid
import logging
from urllib.parse import urlencode

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

logger = logging.getLogger(__name__)


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
def generar_url_pago(request):
    """
    Generar formulario HTML PayPal en lugar de URL de redirección
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

        # Generar custom_id único para esta compra específica
        import uuid
        custom_id = f"TN-{uuid.uuid4().hex[:12].upper()}"

        # Crear registro de pago PENDIENTE con custom_id
        with transaction.atomic():
            pago = PagoCreditos.objects.create(
                user=request.user,
                paquete_creditos=paquete,
                boton_pago=boton_pago,
                monto=paquete.precio,
                metodo_pago=boton_pago.metodo_pago.codigo,
                estado='pendiente',
                referencia_externa=custom_id,
                custom_id=custom_id,
                datos_pago={
                    'pais_usuario': pais_usuario,
                    'timestamp': timezone.now().isoformat(),
                    'user_id': request.user.id,
                    'user_email': request.user.email,
                    'metodo': 'formulario_paypal'
                }
            )

        # En lugar de URL, devolver datos para generar formulario HTML
        base_url = request.build_absolute_uri('/')

        formulario_data = {
            'action': 'https://www.paypal.com/cgi-bin/webscr',
            'method': 'POST',
            'campos': {
                'cmd': '_xclick',
                'business': 'alan.munoz.b@gmail.com',  # CAMBIAR por tu email PayPal
                'item_name': f'Tarotnaútica - {paquete.nombre}',
                'amount': str(paquete.precio),
                'currency_code': 'USD',
                'custom': custom_id,
                'return': f"{base_url}payment/success/",
                'cancel_return': f"{base_url}payment/cancel/",
                'rm': '2',
                'no_shipping': '1',
                'no_note': '1'
            }
        }

        return Response({
            'success': True,
            'tipo': 'formulario',
            'formulario': formulario_data,
            'custom_id': custom_id,
            'paquete_nombre': paquete.nombre,
            'monto': str(paquete.precio)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Error generando formulario de pago: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



 #========================================================================

def _generar_url_segun_metodo(boton_pago, pago, request):
    """
    Generar URL específica según el método de pago
    """
    base_url = request.build_absolute_uri('/')
    success_url = f"{base_url}payment/success/"
    cancel_url = f"{base_url}payment/cancel/"

    metodo = boton_pago.metodo_pago.codigo

    if metodo == 'paypal':
        # Si es un enlace directo de PayPal, usarlo tal como está
        if boton_pago.url_base and 'paypal.com/ncp/payment/' in boton_pago.url_base:
            return boton_pago.url_base  # PayPal ya tiene configurado el retorno
        else:
            # Código original para enlaces automáticos
            paypal_params = {
                'cmd': '_xclick',
                'business': 'sb-47kcn18204925@business.example.com',
                'item_name': f'Tarotnaútica - {pago.paquete_creditos.nombre}',
                'item_number': pago.referencia_externa,
                'amount': str(pago.monto),
                'currency_code': 'USD',
                'return': f"{success_url}?ref={pago.referencia_externa}",
                'cancel_return': f"{cancel_url}?ref={pago.referencia_externa}",
                'notify_url': f"{base_url}api/billing/paypal-ipn/",
                'custom': pago.referencia_externa
            }

            paypal_base = "https://www.sandbox.paypal.com/cgi-bin/webscr"
            return f"{paypal_base}?{urlencode(paypal_params)}"

    elif metodo == 'flow':
        flow_params = {
            'commerceOrder': pago.referencia_externa,
            'subject': f'Tarotnaútica - {pago.paquete_creditos.nombre}',
            'amount': int(pago.monto * 100),
            'email': pago.user.email,
            'urlReturn': f"{success_url}?ref={pago.referencia_externa}"
        }
        return f"{base_url}payment/bank-transfer/?ref={pago.referencia_externa}"

    elif metodo == 'transferencia':
        return f"{base_url}payment/bank-transfer/?ref={pago.referencia_externa}"

    else:
        return f"{boton_pago.url_base}?ref={pago.referencia_externa}&amount={pago.monto}"



@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verificar_pago(request):
    """
    Verificar el estado de un pago - VERSIÓN CORREGIDA para custom_id
    """
    payment_ref = request.GET.get('ref')
    source = request.GET.get('source')
    status_param = request.GET.get('status')

    logger.info(f"Verificando pago - Ref: {payment_ref}, Source: {source}, Status: {status_param}")

    if not payment_ref:
        return Response({
            'error': 'Referencia de pago requerida'
        }, status=status.HTTP_400_BAD_REQUEST)

    # ===================================================================
    # CASO 1: PAGO DIRECTO DE PAYPAL COMPLETADO
    # ===================================================================
    if source == 'paypal' and status_param == 'completed':
        logger.info(f"Procesando pago directo de PayPal: {payment_ref}")

        try:
            # Buscar el pago por custom_id
            pago = PagoCreditos.objects.filter(custom_id=payment_ref).first()

            if pago:
                if pago.estado == 'completado':
                    # Ya procesado anteriormente
                    logger.info(f"Pago ya completado: {payment_ref}")
                    return Response({
                        'success': True,
                        'estado': 'completado',
                        'paquete_nombre': pago.paquete_creditos.nombre,
                        'creditos_agregados': pago.paquete_creditos.cantidad_creditos,
                        'creditos_totales': pago.user.wallet.creditos_disponibles,
                        'monto': str(pago.monto),
                        'fecha_pago': pago.updated_at.isoformat()
                    })
                else:
                    # Completar pago pendiente
                    logger.info(f"Completando pago pendiente: {payment_ref}")
                    _procesar_pago_completado(pago)
                    return Response({
                        'success': True,
                        'estado': 'completado',
                        'paquete_nombre': pago.paquete_creditos.nombre,
                        'creditos_agregados': pago.paquete_creditos.cantidad_creditos,
                        'creditos_totales': pago.user.wallet.creditos_disponibles,
                        'monto': str(pago.monto),
                        'fecha_pago': pago.updated_at.isoformat()
                    })
            else:
                # NO EXISTE EL PAGO - Error
                logger.warning(f"Pago no encontrado: {payment_ref}")
                return Response({
                    'error': 'Pago no encontrado',
                    'referencia': payment_ref
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error procesando pago PayPal {payment_ref}: {str(e)}")
            return Response({
                'error': f'Error procesando pago: {str(e)}',
                'referencia': payment_ref
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ===================================================================
    # CASO 2: BÚSQUEDA NORMAL EN BASE DE DATOS
    # ===================================================================
    try:
        # Buscar por custom_id
        pago = PagoCreditos.objects.get(custom_id=payment_ref)

        if pago.estado == 'completado':
            return Response({
                'success': True,
                'estado': 'completado',
                'paquete_nombre': pago.paquete_creditos.nombre,
                'creditos_agregados': pago.paquete_creditos.cantidad_creditos,
                'creditos_totales': pago.user.wallet.creditos_disponibles,
                'monto': str(pago.monto),
                'fecha_pago': pago.updated_at.isoformat()
            })
        elif pago.estado == 'pendiente':
            # Auto-completar si han pasado más de 5 segundos
            tiempo_transcurrido = (timezone.now() - pago.created_at).total_seconds()
            if tiempo_transcurrido > 5:
                _procesar_pago_completado(pago)
                return Response({
                    'success': True,
                    'estado': 'completado',
                    'paquete_nombre': pago.paquete_creditos.nombre,
                    'creditos_agregados': pago.paquete_creditos.cantidad_creditos,
                    'creditos_totales': pago.user.wallet.creditos_disponibles,
                    'monto': str(pago.monto),
                    'fecha_pago': pago.updated_at.isoformat()
                })
            else:
                return Response({
                    'success': True,
                    'estado': 'pendiente',
                    'mensaje': 'Verificando pago...'
                })
        else:
            return Response({
                'success': False,
                'error': f'El pago está en estado: {pago.estado}'
            })

    except PagoCreditos.DoesNotExist:
        return Response({
            'error': 'Pago no encontrado. Si acabas de completar el pago, contacta soporte.',
            'referencia': payment_ref,
            'source': source,
            'status': status_param
        }, status=status.HTTP_404_NOT_FOUND)


# ===================================================================
# FUNCIÓN NUEVA: _crear_pago_desde_paypal_success
# ===================================================================
def _crear_pago_desde_paypal_success(payment_ref, request):
    """
    Crear un pago cuando viene confirmación de PayPal pero no tenemos registro
    Esta función maneja el caso donde el usuario completó el pago en PayPal
    pero por alguna razón no se creó el registro inicial en nuestra DB
    """
    try:
        # 1. VERIFICAR QUE HAYA UN USUARIO AUTENTICADO
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            logger.error(f"❌ Usuario no autenticado para pago {payment_ref}")
            return Response({
                'error': 'Para completar el pago debes iniciar sesión',
                'referencia': payment_ref,
                'accion_requerida': 'login'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 2. OBTENER EL PAQUETE A USAR
        # OPCIÓN A: Usar el paquete más básico por defecto
        paquete = PaqueteCreditos.objects.filter(activo=True).order_by('precio').first()

        # OPCIÓN B: Si tienes una forma de detectar qué paquete era, úsala aquí
        # Por ejemplo, si la referencia tiene un patrón que indica el paquete:
        # if 'PREMIUM' in payment_ref:
        #     paquete = PaqueteCreditos.objects.filter(nombre__icontains='premium').first()

        if not paquete:
            logger.error(f"❌ No hay paquetes disponibles para {payment_ref}")
            return Response({
                'error': 'No hay paquetes disponibles. Contacta soporte.',
                'referencia': payment_ref
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info(f"📦 Usando paquete por defecto: {paquete.nombre} para {payment_ref}")

        # 3. CREAR EL PAGO EN TRANSACCIÓN ATÓMICA
        with transaction.atomic():
            # Verificar que no exista ya (doble verificación)
            pago_existente = PagoCreditos.objects.filter(referencia_externa=payment_ref).first()
            if pago_existente:
                logger.info(f"✅ Pago ya existe, procesándolo: {payment_ref}")
                if pago_existente.estado != 'completado':
                    _procesar_pago_completado(pago_existente)
                return Response({
                    'success': True,
                    'estado': 'completado',
                    'paquete_nombre': pago_existente.paquete_creditos.nombre,
                    'creditos_agregados': pago_existente.paquete_creditos.cantidad_creditos,
                    'creditos_totales': pago_existente.user.wallet.creditos_disponibles,
                    'monto': str(pago_existente.monto),
                    'fecha_pago': pago_existente.updated_at.isoformat()
                })

            # Crear el pago como completado
            pago = PagoCreditos.objects.create(
                user=request.user,
                paquete_creditos=paquete,
                monto=paquete.precio,
                estado='completado',  # Ya completado porque PayPal lo confirmó
                metodo_pago='paypal',
                referencia_externa=payment_ref,
                datos_pago={
                    'origen': 'paypal_success_page',
                    'confirmado_automaticamente': True,
                    'timestamp': timezone.now().isoformat(),
                    'user_email': request.user.email,
                    'source': 'paypal',
                    'status': 'completed',
                    'nota': 'Pago creado desde página de éxito - no existía registro previo'
                }
            )

            # Obtener o crear wallet
            wallet, wallet_created = Wallet.objects.get_or_create(user=request.user)

            # Agregar créditos
            creditos_antes = wallet.creditos_disponibles
            wallet.agregar_creditos(paquete.cantidad_creditos)
            creditos_despues = wallet.creditos_disponibles

            # Crear registro de transacción
            TransaccionCreditos.objects.create(
                user=request.user,
                tipo='compra',
                cantidad=paquete.cantidad_creditos,
                descripcion=f'Compra vía PayPal (auto-creado) - Ref: {payment_ref}',
                paquete_creditos=paquete
            )

            logger.info(f"✅ Pago creado exitosamente: {payment_ref} | Usuario: {request.user.email} | Créditos: {creditos_antes} → {creditos_despues}")

            return Response({
                'success': True,
                'estado': 'completado',
                'paquete_nombre': paquete.nombre,
                'creditos_agregados': paquete.cantidad_creditos,
                'creditos_totales': wallet.creditos_disponibles,
                'monto': str(paquete.precio),
                'fecha_pago': pago.created_at.isoformat(),
                'nota': 'Pago procesado automáticamente desde PayPal'
            })

    except Exception as e:
        logger.error(f"💥 Error creando pago desde PayPal success {payment_ref}: {str(e)}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")

        return Response({
            'error': f'Error procesando pago: {str(e)}',
            'referencia': payment_ref,
            'solucion': 'Contacta soporte con esta referencia para resolver manualmente'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================================================
# FUNCIÓN MEJORADA: _procesar_pago_completado
# ===================================================================
def _procesar_pago_completado(pago):
    """
    Procesar un pago como completado (agregar créditos)
    Versión mejorada con mejor logging y validaciones
    """
    try:
        with transaction.atomic():
            # Verificar que no esté ya completado
            if pago.estado == 'completado':
                logger.info(f"ℹ️ Pago {pago.referencia_externa} ya estaba completado")
                return

            logger.info(f"🔄 Procesando pago como completado: {pago.referencia_externa}")

            # Actualizar estado del pago
            pago.estado = 'completado'
            pago.save()

            # Obtener o crear wallet
            wallet, created = Wallet.objects.get_or_create(user=pago.user)
            creditos_antes = wallet.creditos_disponibles

            # Agregar créditos
            wallet.agregar_creditos(pago.paquete_creditos.cantidad_creditos)
            creditos_despues = wallet.creditos_disponibles

            # Crear transacción (verificar que no exista)
            transaccion_existente = TransaccionCreditos.objects.filter(
                user=pago.user,
                tipo='compra',
                paquete_creditos=pago.paquete_creditos,
                descripcion__icontains=pago.referencia_externa
            ).first()

            if not transaccion_existente:
                TransaccionCreditos.objects.create(
                    user=pago.user,
                    tipo='compra',
                    cantidad=pago.paquete_creditos.cantidad_creditos,
                    descripcion=f'Compra de {pago.paquete_creditos.nombre} vía {pago.metodo_pago} - Ref: {pago.referencia_externa}',
                    paquete_creditos=pago.paquete_creditos
                )
                logger.info(f"📝 Transacción registrada para {pago.referencia_externa}")
            else:
                logger.info(f"ℹ️ Transacción ya existía para {pago.referencia_externa}")

            logger.info(f"✅ Pago {pago.referencia_externa} completado | Usuario: {pago.user.email} | Créditos: {creditos_antes} → {creditos_despues}")

    except Exception as e:
        logger.error(f"💥 Error procesando pago completado {pago.referencia_externa}: {str(e)}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
        raise

# FUNCIÓN MANTENIDA PARA RETROCOMPATIBILIDAD (pero modificada)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def comprar_creditos(request):
    """
    DEPRECATED: Usar generar_url_pago en su lugar
    Mantenida solo para retrocompatibilidad
    """
    # Redirigir a la nueva función
    return generar_url_pago(request)


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
    print(">>> [DEBUG] Entrando a procesar_consulta_tarot")

    try:
        costo_creditos = int(request.data.get('costo_creditos', 0))
    except ValueError:
        return Response({'error': 'Costo inválido'}, status=status.HTTP_400_BAD_REQUEST)

    tirada_info = request.data.get('tirada_info', {})
    pregunta = request.data.get('pregunta', '')
    interpretacion = request.data.get('interpretacion', '')
    cartas_resultado = request.data.get('cartas_resultado', [])

    user = request.user
    wallet, created = Wallet.objects.get_or_create(user=user)
    print(f">>> [DEBUG] Créditos antes: {wallet.creditos_disponibles}")

    suscripcion_activa = Suscripcion.objects.filter(
        user=user,
        estado='activa'
    ).first()

    uso_suscripcion = False

    try:
        with transaction.atomic():
            if suscripcion_activa and suscripcion_activa.tiradas_disponibles() > 0:
                if suscripcion_activa.usar_tirada():
                    uso_suscripcion = True
                    costo_final = 0
                    print(">>> [DEBUG] Usando tirada de suscripción")
                else:
                    return Response({
                        'error': 'Error usando tirada de suscripción'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                if not wallet.tiene_creditos_suficientes(costo_creditos):
                    print(">>> [DEBUG] Créditos insuficientes")
                    return Response({
                        'error': 'Créditos insuficientes'
                    }, status=status.HTTP_400_BAD_REQUEST)

                wallet.descontar_creditos(costo_creditos)
                print(">>> [DEBUG] Créditos después: ", wallet.creditos_disponibles)
                costo_final = costo_creditos

                TransaccionCreditos.objects.create(
                    user=user,
                    tipo='uso',
                    cantidad=costo_creditos,
                    descripcion=f'Consulta de tarot - {tirada_info.get("nombre", "Tirada")}'
                )
                print(">>> [DEBUG] Transacción registrada")

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

            print(">>> [DEBUG] Consulta registrada en historial")

        return Response({
            'message': 'Consulta procesada exitosamente',
            'uso_suscripcion': uso_suscripcion,
            'costo_creditos': costo_final,
            'creditos_restantes': wallet.creditos_disponibles,
            'tiradas_restantes_suscripcion': suscripcion_activa.tiradas_disponibles() if suscripcion_activa else 0
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(">>> [ERROR] Excepción procesando consulta:", str(e))
        return Response({
            'error': f'Error procesando consulta: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# NUEVAS FUNCIONES PLACEHOLDER PARA WEBHOOKS (implementar según necesidades)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def paypal_ipn(request):
    """
    Manejar notificaciones IPN de PayPal
    TODO: Implementar verificación y procesamiento real de PayPal
    """
    # Verificar que la notificación viene de PayPal
    # Procesar el pago
    # Actualizar estado en base de datos
    return Response({'status': 'received'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def flow_confirm(request):
    """
    Manejar confirmación de Flow
    TODO: Implementar verificación y procesamiento real de Flow
    """
    # Verificar que la confirmación viene de Flow
    # Procesar el pago
    # Actualizar estado en base de datos
    return Response({'status': 'received'}, status=status.HTTP_200_OK)