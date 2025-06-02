# Archivo corregido: oraculoApi/management/commands/test_consulta_real.py

import os
import random
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from oraculoApi.models import Set, Mazo, Carta, Tirada, ItemDeTirada
from oraculoApi.services import gemini_service
from oraculoApi.serializers import CartaSerializer, TiradaSerializer

class Command(BaseCommand):
    help = 'Simula una consulta real de tarot completa paso a paso'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pregunta',
            type=str,
            default='¿Debería aceptar esa nueva oportunidad de trabajo que me ofrecieron?',
            help='Pregunta para la consulta de tarot'
        )
        parser.add_argument(
            '--mazo-id',
            type=int,
            default=1,
            help='ID del mazo a usar (default: 1)'
        )
        parser.add_argument(
            '--tirada-id',
            type=int,
            default=1,
            help='ID de la tirada a usar (default: 1)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada del proceso'
        )
        parser.add_argument(
            '--test-complex',
            action='store_true',
            help='Usar pregunta compleja de prueba'
        )
        parser.add_argument(
            '--test-simple',
            action='store_true',
            help='Usar pregunta simple de prueba'
        )

    def handle(self, *args, **options):
        # Seleccionar pregunta según opciones
        if options['test_complex']:
            pregunta = "¿Debería aceptar la oferta de trabajo en otra ciudad que me propuso mi ex jefe, considerando que esto significaría alejarme de mi pareja actual y empezar una nueva vida, pero también podría ser la oportunidad profesional que he estado esperando para crecer en mi carrera y mejorar mis ingresos?"
            self.stdout.write(self.style.WARNING("🧪 USANDO PREGUNTA COMPLEJA DE PRUEBA"))
        elif options['test_simple']:
            pregunta = "¿Mi relación actual tiene futuro?"
            self.stdout.write(self.style.WARNING("🧪 USANDO PREGUNTA SIMPLE DE PRUEBA"))
        else:
            pregunta = options['pregunta']
            
        mazo_id = options['mazo_id']
        tirada_id = options['tirada_id']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS("🔮 INICIANDO CONSULTA REAL DE TAROT 🔮"))
        self.stdout.write("=" * 70)
        
        try:
            # Paso 1: Obtener el mazo
            self.stdout.write("\n📚 PASO 1: Obteniendo información del mazo...")
            try:
                mazo = Mazo.objects.select_related('set').get(id=mazo_id)
                self.stdout.write(f"✅ Mazo encontrado: {mazo.nombre}")
                if verbose:
                    self.stdout.write(f"   📖 Descripción: {mazo.descripcion}")
                    self.stdout.write(f"   🔄 Permite inversiones: {mazo.permite_cartas_invertidas}")
                    self.stdout.write(f"   📚 Set: {mazo.set.nombre}")
                    self.stdout.write(f"   📚 Set descripción: {mazo.set.descripcion}")
            except Mazo.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Mazo con ID {mazo_id} no encontrado"))
                self._mostrar_mazos_disponibles()
                return
            
            # Paso 2: Obtener la tirada
            self.stdout.write("\n🎯 PASO 2: Obteniendo información de la tirada...")
            try:
                tirada = Tirada.objects.prefetch_related('items').get(id=tirada_id, mazo=mazo)
                self.stdout.write(f"✅ Tirada encontrada: {tirada.nombre}")
                if verbose:
                    self.stdout.write(f"   📊 Cantidad de cartas: {tirada.cantidad_cartas}")
                    self.stdout.write(f"   💰 Costo: {tirada.costo} créditos")
                    self.stdout.write(f"   📝 Descripción: {tirada.descripcion}")
                    
                    # Mostrar imagen si existe
                    if tirada.imagen:
                        self.stdout.write(f"   🖼️ Imagen: {tirada.imagen.url}")
                        
            except Tirada.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Tirada con ID {tirada_id} no encontrada para el mazo {mazo.nombre}"))
                self._mostrar_tiradas_disponibles(mazo)
                return
            
            # Paso 3: Obtener cartas disponibles
            self.stdout.write("\n🃏 PASO 3: Obteniendo cartas del mazo...")
            cartas_disponibles = list(mazo.cartas.all())
            self.stdout.write(f"✅ Cartas disponibles: {len(cartas_disponibles)}")
            
            if len(cartas_disponibles) < tirada.cantidad_cartas:
                self.stdout.write(self.style.ERROR(f"❌ No hay suficientes cartas. Necesarias: {tirada.cantidad_cartas}, Disponibles: {len(cartas_disponibles)}"))
                return
            
            # Paso 4: Seleccionar cartas al azar
            self.stdout.write("\n🎲 PASO 4: Seleccionando cartas al azar...")
            cartas_seleccionadas = random.sample(cartas_disponibles, tirada.cantidad_cartas)
            
            for i, carta in enumerate(cartas_seleccionadas, 1):
                self.stdout.write(f"   {i}. {carta.nombre} (#{carta.numero})")
            
            # Paso 5: Obtener posiciones de la tirada
            self.stdout.write("\n📍 PASO 5: Obteniendo posiciones de la tirada...")
            items_tirada = list(tirada.items.all().order_by('orden'))
            
            if len(items_tirada) != tirada.cantidad_cartas:
                self.stdout.write(self.style.ERROR(f"❌ Error en configuración: {len(items_tirada)} posiciones vs {tirada.cantidad_cartas} cartas"))
                if verbose:
                    self.stdout.write("📋 Posiciones configuradas:")
                    for item in items_tirada:
                        self.stdout.write(f"   • {item.orden}: {item.nombre_posicion}")
                return
            
            self.stdout.write(f"✅ Configuración correcta: {len(items_tirada)} posiciones")
            for item in items_tirada:
                self.stdout.write(f"   • {item.nombre_posicion}: {item.descripcion}")
            
            # Paso 6: Generar resultado con posiciones
            self.stdout.write("\n🔮 PASO 6: Generando resultado de la tirada...")
            cartas_resultado = []
            
            for i, carta in enumerate(cartas_seleccionadas):
                item_tirada = items_tirada[i]
                
                # Determinar orientación
                es_invertida = False
                if mazo.permite_cartas_invertidas:
                    es_invertida = random.choice([True, False])
                
                # Seleccionar significado
                significado_usado = carta.significado_invertida if es_invertida else carta.significado_normal
                
                carta_info = {
                    'carta': CartaSerializer(carta).data,
                    'posicion': item_tirada.nombre_posicion,
                    'descripcion_posicion': item_tirada.descripcion,
                    'es_invertida': es_invertida,
                    'significado_usado': significado_usado
                }
                cartas_resultado.append(carta_info)
                
                orientacion = "🔄 INVERTIDA" if es_invertida else "⬆️ DERECHA"
                self.stdout.write(f"   {i+1}. {item_tirada.nombre_posicion}: {carta.nombre} ({orientacion})")
                if verbose:
                    self.stdout.write(f"      📝 Función: {item_tirada.descripcion}")
                    self.stdout.write(f"      ⚡ Energía: {significado_usado[:100]}...")
            
            # Paso 7: Generar prompt para IA (CORREGIDO - Ahora incluye tirada)
            self.stdout.write("\n✍️ PASO 7: Creando prompt mejorado para Gemini...")
            prompt = gemini_service.crear_prompt_tarot(pregunta, mazo, tirada, cartas_resultado)
            
            if verbose:
                self.stdout.write("📝 Prompt generado (preview):")
                self.stdout.write("-" * 50)
                # Mostrar solo las primeras líneas del prompt
                prompt_lines = prompt.split('\n')[:20]
                for line in prompt_lines:
                    self.stdout.write(line)
                self.stdout.write("... (continúa)")
                self.stdout.write("-" * 50)
            
            tokens_estimados = len(prompt) // 4
            self.stdout.write(f"📊 Tokens estimados del prompt: ~{tokens_estimados}")
            self.stdout.write(f"💰 Costo estimado del input: ~${tokens_estimados * 0.075 / 1000000:.6f}")
            
            # Paso 8: Llamar a Gemini
            self.stdout.write("\n🤖 PASO 8: Consultando a Gemini 2.0 Flash-Lite...")
            self.stdout.write("⏳ Esperando respuesta de la IA...")
            
            try:
                start_time = timezone.now()
                interpretacion = gemini_service.generar_interpretacion_tarot(prompt)
                end_time = timezone.now()
                
                tiempo_respuesta = (end_time - start_time).total_seconds()
                tokens_respuesta = len(interpretacion) // 4
                costo_output = tokens_respuesta * 0.30 / 1000000
                costo_total = (tokens_estimados * 0.075 / 1000000) + costo_output
                
                self.stdout.write(f"✅ Respuesta recibida en {tiempo_respuesta:.2f} segundos")
                self.stdout.write(f"📊 Tokens de respuesta: ~{tokens_respuesta}")
                self.stdout.write(f"💰 Costo total estimado: ~${costo_total:.6f}")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error al consultar Gemini: {str(e)}"))
                self.stdout.write("💡 Mostrando interpretación de fallback...")
                interpretacion = gemini_service._get_mystical_fallback_interpretation()
                tiempo_respuesta = 0
                tokens_respuesta = len(interpretacion) // 4
                costo_total = 0
            
            # Paso 9: Mostrar resultados
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(self.style.SUCCESS("🎭 RESULTADO DE LA CONSULTA MÍSTICA 🎭"))
            self.stdout.write("=" * 70)
            
            self.stdout.write(f"\n❓ PREGUNTA:")
            self.stdout.write(f'"{pregunta}"')
            
            self.stdout.write(f"\n🎯 TIRADA UTILIZADA:")
            self.stdout.write(f"📖 Nombre: {tirada.nombre}")
            self.stdout.write(f"📝 Descripción: {tirada.descripcion}")
            self.stdout.write(f"💰 Costo: {tirada.costo} créditos")
            
            self.stdout.write(f"\n🃏 CARTAS REVELADAS:")
            for i, carta_info in enumerate(cartas_resultado, 1):
                orientacion = "🔄 Invertida" if carta_info['es_invertida'] else "⬆️ Derecha"
                self.stdout.write(f"\n{i}. 📍 {carta_info['posicion']}")
                self.stdout.write(f"   🎴 {carta_info['carta']['nombre']} ({orientacion})")
                self.stdout.write(f"   🎯 {carta_info['descripcion_posicion']}")
                if verbose:
                    self.stdout.write(f"   🔮 Energía: {carta_info['significado_usado'][:150]}...")
            
            self.stdout.write(f"\n🌟 INTERPRETACIÓN MÍSTICA:")
            self.stdout.write("-" * 50)
            self.stdout.write(interpretacion)
            self.stdout.write("-" * 50)
            
            # Paso 10: Estadísticas finales
            self.stdout.write(f"\n📈 ESTADÍSTICAS DE LA CONSULTA:")
            self.stdout.write(f"   ⏱️ Tiempo total de respuesta: {tiempo_respuesta:.2f}s")
            self.stdout.write(f"   📊 Tokens input: ~{tokens_estimados}")
            self.stdout.write(f"   📊 Tokens output: ~{tokens_respuesta}")
            self.stdout.write(f"   📊 Tokens totales: ~{tokens_estimados + tokens_respuesta}")
            self.stdout.write(f"   💰 Costo total: ~${costo_total:.6f} USD")
            if costo_total > 0:
                self.stdout.write(f"   💰 Consultas por $1: ~{1/costo_total:.0f}")
            
            # Generar JSON de respuesta (como lo haría la API)
            respuesta_api = {
                'pregunta': pregunta,
                'interpretacion_ia': interpretacion,
                'cartas': cartas_resultado,
                'tirada_info': TiradaSerializer(tirada).data,
                'timestamp': timezone.now().isoformat(),
                'estadisticas': {
                    'tiempo_respuesta_segundos': tiempo_respuesta,
                    'tokens_input': tokens_estimados,
                    'tokens_output': tokens_respuesta,
                    'costo_usd': costo_total
                }
            }
            
            if verbose:
                self.stdout.write(f"\n📋 RESPUESTA JSON (para desarrollo):")
                self.stdout.write("-" * 50)
                # Mostrar JSON compacto
                json_compact = json.dumps(respuesta_api, indent=2, ensure_ascii=False)
                if len(json_compact) > 1000:
                    self.stdout.write(json_compact[:1000] + "...")
                else:
                    self.stdout.write(json_compact)
                self.stdout.write("-" * 50)
            
            self.stdout.write(self.style.SUCCESS("\n🎉 ¡CONSULTA COMPLETADA EXITOSAMENTE! 🎉"))
            self.stdout.write("\n💡 Usa --test-complex o --test-simple para probar preguntas predefinidas")
            self.stdout.write("💡 Usa --verbose para ver información detallada")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error durante la consulta: {str(e)}"))
            self.stdout.write("🔧 Verifica que tengas datos de prueba en la base de datos")
            self.stdout.write("💡 Ejecuta: python manage.py migrate y carga algunos mazos/cartas de prueba")
            if verbose:
                import traceback
                self.stdout.write(f"\n🐛 Traceback completo:")
                self.stdout.write(traceback.format_exc())

    def _mostrar_mazos_disponibles(self):
        """Muestra los mazos disponibles si no se encuentra el solicitado"""
        mazos = Mazo.objects.select_related('set').all()
        if mazos:
            self.stdout.write("\n📚 Mazos disponibles:")
            for mazo in mazos:
                self.stdout.write(f"   ID {mazo.id}: {mazo.nombre} (Set: {mazo.set.nombre})")
        else:
            self.stdout.write("❌ No hay mazos configurados en el sistema")

    def _mostrar_tiradas_disponibles(self, mazo):
        """Muestra las tiradas disponibles para un mazo"""
        tiradas = mazo.tiradas.all()
        if tiradas:
            self.stdout.write(f"\n🎯 Tiradas disponibles para {mazo.nombre}:")
            for tirada in tiradas:
                self.stdout.write(f"   ID {tirada.id}: {tirada.nombre} ({tirada.cantidad_cartas} cartas, {tirada.costo} créditos)")
        else:
            self.stdout.write(f"❌ No hay tiradas configuradas para el mazo {mazo.nombre}")