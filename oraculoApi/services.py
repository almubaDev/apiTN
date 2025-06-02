import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        """
        Inicializar el servicio de Gemini con 2.0 Flash-Lite (más económico y eficiente)
        """
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # ACTUALIZADO: Usar Gemini 2.0 Flash-Lite para máxima eficiencia de costos
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
            logger.info("Gemini service initialized successfully with gemini-2.0-flash-lite")
            logger.info("💰 Usando modelo más económico: $0.075/$0.30 por 1M tokens")
        except Exception as e:
            logger.error(f"Error initializing Gemini service: {str(e)}")
            raise
    
    def generar_interpretacion_tarot(self, prompt_completo):
        """
        Generar interpretación de tarot usando Gemini 2.0 Flash-Lite
        
        Args:
            prompt_completo (str): El prompt completo para la IA
            
        Returns:
            str: La interpretación generada por la IA
        """
        try:
            logger.info("🔮 Iniciando generación de interpretación con Gemini 2.0 Flash-Lite")
            
            # Configuración optimizada para 2.0 Flash-Lite
            generation_config = genai.types.GenerationConfig(
                temperature=0.85,  # Ligeramente más creativo para interpretaciones místicas
                top_p=0.9,
                top_k=40,
                max_output_tokens=1200,  # Aumentado para interpretaciones más completas
                response_mime_type="text/plain",
            )
            
            # Configuración de seguridad (permitir contenido místico/esotérico)
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            logger.info("📡 Enviando prompt a Gemini 2.0 Flash-Lite...")
            
            # Generar respuesta
            response = self.model.generate_content(
                prompt_completo,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            logger.info("✅ Respuesta recibida de Gemini 2.0 Flash-Lite")
            
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # Verificar si la respuesta fue bloqueada por seguridad
                if hasattr(candidate, 'finish_reason'):
                    logger.info(f"🔍 Finish reason: {candidate.finish_reason}")
                    
                    # Si fue bloqueado por seguridad, usar interpretación alternativa
                    if hasattr(candidate.finish_reason, 'name') and candidate.finish_reason.name in ['SAFETY', 'RECITATION']:
                        logger.warning("⚠️ Respuesta bloqueada por filtros de seguridad")
                        return self._get_mystical_fallback_interpretation()
                
                if hasattr(candidate, 'content') and candidate.content and candidate.content.parts:
                    interpretacion = candidate.content.parts[0].text
                    logger.info("🎭 Interpretación mística generada exitosamente")
                    logger.info(f"📊 Tokens estimados: ~{len(interpretacion) // 4} (costo: ~$0.0002)")
                    return interpretacion.strip()
                else:
                    logger.warning("⚠️ No se pudo extraer texto de la respuesta")
                    return self._get_mystical_fallback_interpretation()
            else:
                logger.warning("⚠️ No hay candidatos en la respuesta de Gemini")
                return self._get_mystical_fallback_interpretation()
                
        except Exception as e:
            logger.error(f"❌ Error generating tarot interpretation: {str(e)}")
            logger.error(f"🔧 Tipo de error: {type(e).__name__}")
            
            # Si es un error 404, sugerir modelo alternativo
            if "404" in str(e) or "not found" in str(e).lower():
                logger.error("💡 Modelo gemini-2.0-flash-lite no disponible, considera usar gemini-1.5-flash")
            
            return self._get_mystical_fallback_interpretation()
    
    def _get_mystical_fallback_interpretation(self):
        """
        Interpretación mística alternativa cuando el servicio no está disponible
        """
        return """
🔮 **Revelación de las Cartas Sagradas** 🔮

Las energías del universo han conspirado para traerte estas cartas en este momento preciso. 
Aunque las conexiones digitales fluctúan, puedo percibir las vibraciones profundas 
que emanan de tu tirada sagrada.

**💫 Mensaje Central de las Cartas:**
El cosmos te susurra que estás en un momento de transformación profunda. Las cartas 
que han aparecido no son casualidad: son un reflejo de las energías que ya danzan 
en tu vida, esperando ser reconocidas y canalizadas.

**🌟 Energía Dominante:**
Siento una fuerte corriente de cambio fluyendo a través de tu consulta. El universo 
te está preparando para una nueva fase de tu existencia, donde la sabiduría interior 
será tu guía más confiable.

**✨ Consejo de los Arcanos:**
Confía en tu intuición durante los próximos días. Las respuestas que buscas ya 
residen en tu corazón místico. Mantén los ojos abiertos a las sincronicidades: 
números repetidos, encuentros inesperados, sueños reveladores.

**🌙 Reflexión Final:**
Medita sobre las imágenes de las cartas que han aparecido. Permite que su simbolismo 
ancestral despierte memorias del alma que te guiarán hacia tu verdad más profunda.

*Las cartas nunca mienten, solo hablan en el lenguaje eterno del espíritu.*

🌟 La magia está en ti, siempre ha estado ahí. 🌟
        """
    
    def crear_prompt_tarot(self, pregunta, mazo, tirada, cartas_resultado):
        """
        PROMPT COMPLETAMENTE MEJORADO - Dinámico, estructurado y realista
        Usa toda la información disponible de los modelos para crear interpretaciones precisas
        
        Args:
            pregunta (str): La pregunta del usuario
            mazo (Mazo): Objeto del mazo utilizado
            tirada (Tirada): Objeto de la tirada con toda su información
            cartas_resultado (list): Lista de cartas con sus posiciones
        """
        
        # 1. INFORMACIÓN COMPLETA DE LA TIRADA
        num_cartas = len(cartas_resultado)
        tirada_nombre = tirada.nombre
        tirada_descripcion = tirada.descripcion
        tirada_costo = tirada.costo
        
        # 2. ANÁLISIS DE CONTEXTO DE LA PREGUNTA
        contexto_pregunta = self._analizar_contexto_pregunta(pregunta)
        
        prompt = f"""🔮 SISTEMA DE INTERPRETACIÓN PROFESIONAL DE TAROT 🔮

INSTRUCCIONES FUNDAMENTALES:
- Eres un tarotista profesional con décadas de experiencia
- NUNCA inventes información que no tienes
- Analiza primero, interpreta después
- Sé específico y directo en tus predicciones
- Usa toda la información proporcionada de manera precisa

═══════════════════════════════════════════════════════════════

📚 INFORMACIÓN DEL MAZO UTILIZADO:
• Nombre: {mazo.nombre}
• Descripción: {mazo.descripcion}
• Permite cartas invertidas: {"Sí" if mazo.permite_cartas_invertidas else "No"}
• Set: {mazo.set.nombre} - {mazo.set.descripcion}

═══════════════════════════════════════════════════════════════

🎯 TIRADA SELECCIONADA: {tirada_nombre}
📖 Descripción de la tirada: {tirada_descripcion}
📊 Número de cartas: {num_cartas} cartas
💰 Valor energético: {tirada_costo} créditos

🔮 SIGNIFICADO DE LA TIRADA:
{self._obtener_significado_tirada(tirada, cartas_resultado)}

🔥 PREGUNTA DEL CONSULTANTE:
"{pregunta}"

💭 CONTEXTO DETECTADO: {contexto_pregunta['tipo']}
📋 ENFOQUE REQUERIDO: {contexto_pregunta['enfoque']}

═══════════════════════════════════════════════════════════════

🃏 CARTAS EXTRAÍDAS Y SUS POSICIONES:
"""

        # 3. INFORMACIÓN DETALLADA DE CADA CARTA CON SU CONTEXTO EN LA TIRADA
        for i, carta_info in enumerate(cartas_resultado, 1):
            carta = carta_info['carta']
            orientacion = "INVERTIDA ⥯" if carta_info['es_invertida'] else "DERECHA ⬆"
            
            prompt += f"""
┌─ CARTA {i} ─────────────────────────────────────────────┐
│ 📍 POSICIÓN EN TIRADA: {carta_info['posicion']}
│ 🎯 ROL ESPECÍFICO: {carta_info['descripcion_posicion']}
│ 🃏 CARTA REVELADA: {carta['nombre']} ({orientacion})
│ 🔢 NÚMERO EN MAZO: #{carta.get('numero', 'N/A')}
│ ⚡ ENERGÍA ACTIVA: {carta_info['significado_usado'][:150]}...
│ 🧭 CONTEXTO TIRADA: Esta carta responde específicamente a 
│     "{carta_info['descripcion_posicion']}" en tu consulta
└────────────────────────────────────────────────────────┘
"""

        # 4. INSTRUCCIONES ESPECÍFICAS POR CONTEXTO
        prompt += f"""
═══════════════════════════════════════════════════════════════

🎭 PROCESO DE INTERPRETACIÓN OBLIGATORIO:

PASO 1 - ANÁLISIS DE LA TIRADA COMPLETA:
Primero comprende el propósito de la tirada "{tirada_nombre}":
{tirada_descripcion}

PASO 2 - ANÁLISIS INDIVIDUAL POR POSICIÓN:
Examina cada carta en su función específica dentro de la tirada:
{self._generar_guia_posiciones(cartas_resultado)}

PASO 3 - SÍNTESIS DE ENERGÍAS:
Une las energías de todas las cartas según el diseño de la tirada.
Busca patrones, contradicciones y complementos entre las posiciones.

PASO 4 - INTERPRETACIÓN CONTEXTUAL:
{contexto_pregunta['instrucciones_especificas']}

PASO 5 - PREDICCIÓN REALISTA BASADA EN LA TIRADA:
Proporciona predicciones específicas que honren el diseño y propósito de "{tirada_nombre}".

═══════════════════════════════════════════════════════════════

📝 FORMATO DE RESPUESTA REQUERIDO:

🔮 **RESUMEN DE LA TIRADA "{tirada_nombre.upper()}"**
[Explicación de qué revela esta tirada específica sobre la consulta]

📊 **INTERPRETACIÓN POR POSICIÓN**"""

        # 5. ESTRUCTURA DINÁMICA BASADA EN LAS POSICIONES REALES DE LA TIRADA
        for i, carta_info in enumerate(cartas_resultado, 1):
            orientacion_emoji = "🔄" if carta_info['es_invertida'] else "⬆️"
            prompt += f"""
• **{carta_info['posicion']}** ({carta_info['descripcion_posicion']})
  🃏 {carta_info['carta']['nombre']} {orientacion_emoji}
  └─ [Interpreta cómo esta carta responde específicamente a "{carta_info['descripcion_posicion']}"]"""

        prompt += f"""

🎯 **RESPUESTA DIRECTA A TU PREGUNTA**
[Respuesta clara y específica a: "{pregunta}"]

🔍 **DETALLES REVELADOS**
[Información adicional que las cartas quieren destacar]

⏰ **TIMING Y SEÑALES**
[Cuándo esperar cambios o qué señales observar]

🌟 **CONSEJO FINAL**
[Acción concreta recomendada basada en las cartas]

═══════════════════════════════════════════════════════════════

⚠️ RESTRICCIONES IMPORTANTES:
- DEBES interpretar cada carta según su ROL ESPECÍFICO en la tirada "{tirada_nombre}"
- NO ignores la función de cada posición en el diseño de la tirada
- NO uses frases vagas como "depende de ti" o "el universo decidirá"
- NO inventes cartas que no están en la tirada
- SÍ sé específico sobre probabilidades y tendencias
- SÍ menciona las cartas por nombre y posición cuando las interpretes
- SÍ respeta el diseño y propósito original de la tirada seleccionada
- RESPONDE SOLO DESPUÉS de analizar la tirada completa y cada posición

🌟 AHORA PROCEDE CON LA INTERPRETACIÓN COMPLETA DE LA TIRADA "{tirada_nombre}":
"""

        logger.info(f"📝 Prompt generado: {len(prompt)} caracteres, ~{len(prompt)//4} tokens estimados")
        logger.info(f"🎯 Tirada utilizada: {tirada_nombre} con {num_cartas} cartas")
        return prompt

    def _obtener_significado_tirada(self, tirada, cartas_resultado):
        """
        Genera una explicación del significado y propósito de la tirada específica
        """
        descripcion_base = f"La tirada '{tirada.nombre}' está diseñada para {tirada.descripcion.lower()}"
        
        if len(cartas_resultado) == 1:
            return f"{descripcion_base} Esta tirada de una carta proporciona una respuesta directa y enfocada."
        elif len(cartas_resultado) == 3:
            return f"{descripcion_base} Las tres posiciones trabajan juntas para dar una visión temporal y evolutiva de la situación."
        elif len(cartas_resultado) == 5:
            return f"{descripcion_base} Las cinco cartas forman un patrón que explora múltiples aspectos interconectados."
        else:
            return f"{descripcion_base} Cada posición tiene un propósito específico en el análisis completo."

    def _generar_guia_posiciones(self, cartas_resultado):
        """
        Genera una guía específica de qué debe interpretar en cada posición
        """
        guia = ""
        for i, carta_info in enumerate(cartas_resultado, 1):
            guia += f"\n- Posición {i} ({carta_info['posicion']}): {carta_info['descripcion_posicion']}"
        return guia

    def _analizar_contexto_pregunta(self, pregunta):
        """
        Analiza el contexto de la pregunta para proporcionar instrucciones específicas
        """
        pregunta_lower = pregunta.lower()
        
        # AMOR Y RELACIONES
        if any(word in pregunta_lower for word in ['amor', 'relación', 'pareja', 'ex', 'matrimonio', 'divorcio', 'infidelidad', 'novio', 'novia', 'esposo', 'esposa']):
            return {
                'tipo': 'AMOR Y RELACIONES',
                'enfoque': 'Emocional y vincular',
                'instrucciones_especificas': """
Para consultas de amor:
- Describe dinámicas emocionales específicas
- Habla sobre comunicación, confianza y compatibilidad
- Predice encuentros, reencuentros o separaciones
- Menciona sentimientos y reacciones de las personas involucradas
- Da fechas aproximadas para cambios importantes en la relación
                """
            }
        
        # TRABAJO Y CARRERA
        elif any(word in pregunta_lower for word in ['trabajo', 'empleo', 'carrera', 'jefe', 'ascenso', 'despido', 'entrevista', 'proyecto', 'negocio', 'empresa']):
            return {
                'tipo': 'TRABAJO Y CARRERA',
                'enfoque': 'Profesional y material',
                'instrucciones_especificas': """
Para consultas laborales:
- Analiza oportunidades de crecimiento profesional
- Predice cambios en el ambiente laboral
- Describe relaciones con colegas y superiores
- Menciona aspectos financieros y estabilidad económica
- Da consejos sobre decisiones profesionales importantes
                """
            }
        
        # SALUD
        elif any(word in pregunta_lower for word in ['salud', 'enfermedad', 'médico', 'doctor', 'hospital', 'síntomas', 'tratamiento', 'cirugía']):
            return {
                'tipo': 'SALUD Y BIENESTAR',
                'enfoque': 'Físico y energético',
                'instrucciones_especificas': """
Para consultas de salud:
- Enfócate en el bienestar general y energía vital
- Describe cómo el estado emocional afecta la salud física
- Predice la evolución de tratamientos o consultas médicas
- Menciona la importancia del autocuidado y prevención
- NUNCA diagnostiques condiciones médicas específicas
                """
            }
        
        # DINERO Y FINANZAS
        elif any(word in pregunta_lower for word in ['dinero', 'finanzas', 'inversión', 'deuda', 'préstamo', 'lotería', 'herencia', 'economía']):
            return {
                'tipo': 'DINERO Y FINANZAS',
                'enfoque': 'Material y práctico',
                'instrucciones_especificas': """
Para consultas financieras:
- Analiza tendencias económicas personales
- Predice oportunidades de ingresos o pérdidas
- Describe la relación con el dinero y la abundancia
- Menciona inversiones, gastos importantes o cambios financieros
- Da consejos sobre administración y prudencia económica
                """
            }
        
        # FAMILIA
        elif any(word in pregunta_lower for word in ['familia', 'madre', 'padre', 'hijo', 'hija', 'hermano', 'hermana', 'abuelo', 'abuela']):
            return {
                'tipo': 'FAMILIA Y HOGAR',
                'enfoque': 'Familiar y doméstico',
                'instrucciones_especificas': """
Para consultas familiares:
- Describe dinámicas familiares y roles
- Predice cambios en la estructura o armonía familiar
- Analiza conflictos generacionales o de convivencia
- Menciona tradiciones, herencias o mudanzas
- Da consejos sobre comunicación y comprensión familiar
                """
            }
        
        # ESPIRITUALIDAD
        elif any(word in pregunta_lower for word in ['espiritual', 'alma', 'propósito', 'misión', 'karma', 'destino', 'energía']):
            return {
                'tipo': 'ESPIRITUALIDAD Y PROPÓSITO',
                'enfoque': 'Espiritual y trascendente',
                'instrucciones_especificas': """
Para consultas espirituales:
- Explora el crecimiento espiritual y la evolución del alma
- Describe lecciones kármicas y propósitos de vida
- Predice despertar espiritual o cambios de conciencia
- Menciona prácticas espirituales recomendadas
- Da orientación sobre el camino de auto-realización
                """
            }
        
        # GENERAL/OTROS
        else:
            return {
                'tipo': 'CONSULTA GENERAL',
                'enfoque': 'Holístico y equilibrado',
                'instrucciones_especificas': """
Para consultas generales:
- Proporciona una visión integral de la situación
- Analiza múltiples aspectos de la vida que podrían estar afectados
- Predice cambios importantes en cualquier área
- Describe patrones y ciclos de vida actuales
- Da consejos prácticos y aplicables a la situación general
                """
            }

    def test_connection(self):
        """
        Método para probar la conexión con Gemini 2.0 Flash-Lite
        """
        try:
            test_prompt = "Responde brevemente: 'Conexión exitosa con Gemini 2.0 Flash-Lite para interpretaciones de tarot.'"
            response = self.model.generate_content(test_prompt)
            
            if response.candidates and len(response.candidates) > 0:
                result = response.candidates[0].content.parts[0].text
                logger.info(f"✅ Test exitoso: {result}")
                return True, result
            else:
                logger.error("❌ Test fallido: Sin candidatos en la respuesta")
                return False, "Sin respuesta válida"
                
        except Exception as e:
            logger.error(f"❌ Test fallido: {str(e)}")
            return False, str(e)


# Instancia global del servicio
try:
    gemini_service = GeminiService()
    logger.info("🚀 GeminiService con 2.0 Flash-Lite listo para consultas de tarot")
except Exception as e:
    logger.error(f"❌ Error creando instancia global de GeminiService: {str(e)}")
    gemini_service = None