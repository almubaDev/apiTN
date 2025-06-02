from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import random
import logging  # AGREGADO: Import del módulo logging

from .models import Set, Mazo, Carta, Tirada, ItemDeTirada
from .serializers import (
    SetSerializer, MazoSerializer, CartaSerializer, TiradaSerializer,
    SetConMazosSerializer, MazoConTiradasSerializer, ConsultaTarotSerializer,
    RespuestaTarotSerializer, CartaEnTiradaSerializer
)
from .services import gemini_service

# AGREGADO: Configuración del logger
logger = logging.getLogger(__name__)


class SetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para obtener Sets de mazos
    """
    queryset = Set.objects.all()
    serializer_class = SetSerializer


class SetConMazosViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para obtener Sets con sus mazos incluidos
    """
    queryset = Set.objects.prefetch_related('mazos').all()
    serializer_class = SetConMazosSerializer


class MazoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para obtener Mazos
    """
    queryset = Mazo.objects.select_related('set').all()
    serializer_class = MazoSerializer


class MazoConTiradasViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para obtener Mazos con sus tiradas incluidas
    """
    queryset = Mazo.objects.select_related('set').prefetch_related('tiradas__items').all()
    serializer_class = MazoConTiradasSerializer


class CartaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para obtener Cartas
    """
    queryset = Carta.objects.select_related('mazo').all()
    serializer_class = CartaSerializer


class TiradaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para obtener Tiradas
    """
    queryset = Tirada.objects.select_related('mazo').prefetch_related('items').all()
    serializer_class = TiradaSerializer


@api_view(['POST'])
def consulta_tarot(request):
    """
    Endpoint principal para realizar consulta de tarot
    """
    serializer = ConsultaTarotSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    pregunta = data['pregunta']
    set_id = data['set_id']
    mazo_id = data['mazo_id']
    tirada_id = data['tirada_id']
    
    try:
        # Obtener objetos
        set_obj = get_object_or_404(Set, id=set_id)
        mazo = get_object_or_404(Mazo, id=mazo_id, set=set_obj)
        tirada = get_object_or_404(Tirada, id=tirada_id, mazo=mazo)
        
        # Obtener todas las cartas del mazo
        cartas_disponibles = list(mazo.cartas.all())
        
        if len(cartas_disponibles) < tirada.cantidad_cartas:
            return Response({
                'error': 'No hay suficientes cartas en el mazo para esta tirada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Seleccionar cartas al azar
        cartas_seleccionadas = random.sample(cartas_disponibles, tirada.cantidad_cartas)
        
        # Obtener items de tirada ordenados
        items_tirada = list(tirada.items.all().order_by('orden'))
        
        if len(items_tirada) != tirada.cantidad_cartas:
            return Response({
                'error': 'La configuración de la tirada no coincide con la cantidad de cartas'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generar resultado de cartas con posiciones
        cartas_resultado = []
        for i, carta in enumerate(cartas_seleccionadas):
            item_tirada = items_tirada[i]
            
            # Determinar si la carta va invertida
            es_invertida = False
            if mazo.permite_cartas_invertidas:
                es_invertida = random.choice([True, False])
            
            # Seleccionar significado según orientación
            significado_usado = carta.significado_invertida if es_invertida else carta.significado_normal
            
            carta_en_tirada = {
                'carta': CartaSerializer(carta).data,
                'posicion': item_tirada.nombre_posicion,
                'descripcion_posicion': item_tirada.descripcion,
                'es_invertida': es_invertida,
                'significado_usado': significado_usado
            }
            cartas_resultado.append(carta_en_tirada)
        
        # MEJORADO: Pasar el objeto tirada completo al método crear_prompt_tarot
        prompt = gemini_service.crear_prompt_tarot(pregunta, mazo, tirada, cartas_resultado)
        
        # Obtener interpretación de Gemini
        logger.info(f"Generando interpretación para tirada: {tirada.nombre}")
        interpretacion_ia = gemini_service.generar_interpretacion_tarot(prompt)
        
        logger.info("Interpretación generada exitosamente")
        
        # Preparar respuesta
        respuesta_data = {
            'pregunta': pregunta,
            'interpretacion_ia': interpretacion_ia,
            'cartas': cartas_resultado,
            'tirada_info': TiradaSerializer(tirada).data
        }
        
        return Response(respuesta_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en consulta de tarot: {str(e)}")
        logger.error(f"Tipo de error: {type(e).__name__}")
        return Response({
            'error': f'Error procesando consulta: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generar_prompt_ia(pregunta, mazo, cartas_resultado):
    """
    Genera el prompt que se enviará a la IA (MÉTODO LEGACY - Ya no se usa)
    """
    prompt = f"""Eres un experto tarotista que proporciona interpretaciones místicas pero prácticas.

INFORMACIÓN DEL MAZO:
Nombre: {mazo.nombre}
Descripción: {mazo.descripcion}

PREGUNTA DEL CONSULTANTE:
{pregunta}

CARTAS DE LA TIRADA:
"""
    
    for carta_info in cartas_resultado:
        carta = carta_info['carta']
        orientacion = "INVERTIDA" if carta_info['es_invertida'] else "NORMAL"
        
        prompt += f"""
Posición: {carta_info['posicion']}
Descripción de la posición: {carta_info['descripcion_posicion']}
Carta: {carta['nombre']} ({orientacion})
Significado: {carta_info['significado_usado']}
---
"""
    
    prompt += """
Da una interpretación completa, esotérica y mística pero práctica, relacionando las cartas entre sí y respondiendo a la pregunta. Usa género neutral para referirte al consultante ya que no sabemos si es hombre o mujer.
"""
    
    return prompt



