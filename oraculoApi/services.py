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
                max_output_tokens=1000,  # Optimizado para respuestas concisas pero completas
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
    
    def crear_prompt_tarot(self, pregunta, mazo, cartas_resultado):
        """
        PROMPT MEJORADO - Crear el prompt que genera respuestas específicas y relevantes
        """
        prompt = f"""
        🧙‍♂️ Eres un tarotista profesional. Tu método es preciso y estructurado. No haces suposiciones: primero analizas, luego respondes.

        TU ORDEN DE LECTURA:

        1. Primero estudias el significado de cada carta revelada.
        2. Luego recibes la pregunta del consultante.
        3. Después conectas el mensaje de las cartas con la pregunta.
        4. Finalmente elaboras una predicción específica y clara.

        -------------------------------------
        🔮 MAZO UTILIZADO: {mazo.nombre}
        🌸 DESCRIPCIÓN DEL MAZO: {mazo.descripcion}
        -------------------------------------

        ✨ CARTAS EXTRAÍDAS:
        """

        for i, carta_info in enumerate(cartas_resultado, 1):
            carta = carta_info['carta']
            orientacion = "INVERTIDA" if carta_info['es_invertida'] else "DERECHA"

            prompt += f"""
        🔹 CARTA {i} - {carta_info['posicion'].upper()}:
        • Nombre: {carta['nombre']} ({orientacion})
        • Rol en la tirada: {carta_info['descripcion_posicion']}
        • Significado clave: {carta_info['significado_usado']}
        """

        prompt += f"""

        -------------------------------------
        🧿 AHORA RECIBE LA PREGUNTA:
        "{pregunta}"
        -------------------------------------

        Tu tarea es:

        ➡️ Paso 1: Conecta cada carta con la pregunta.
        ➡️ Paso 2: Interpreta cómo la energía de cada carta afecta el pasado, presente y futuro de lo preguntado.
        ➡️ Paso 3: Elabora una predicción clara y concreta, sin dar vueltas.

        🎯 ENFOQUE SEGÚN LA PREGUNTA:
        """

        # Agregamos enfoque contextual según pregunta
        if "médic" in pregunta.lower() or "salud" in pregunta.lower():
            prompt += """
        🏥 CONTEXTO MÉDICO: 
        - Di si la consulta médica irá bien o mal.
        - Describe cómo estará el médico, qué noticias se darán, si hay estudios o tratamientos.
        """
        elif "amor" in pregunta.lower():
            prompt += """
        💘 CONTEXTO AMOROSO:
        - Describe claramente qué pasará entre las personas involucradas.
        - Habla de emociones, reacciones, rupturas o acercamientos.
        """
        elif "trabajo" in pregunta.lower():
            prompt += """
        💼 CONTEXTO LABORAL:
        - Expón si habrá oportunidades, conflictos o resoluciones laborales.
        - Habla del futuro concreto del consultante en el trabajo.
        """
        else:
            prompt += """
        📌 CONSULTA GENERAL:
        - Responde exactamente lo que se pregunta.
        - No filosofes ni hables en abstracto.
        """

        prompt += f"""

        -------------------------------------
        🗝️ FORMATO DE RESPUESTA ESPERADO:

        **🔮 PREDICCIÓN CLARA:**
        [Resumen directo de lo que ocurrirá según las cartas]

        **📊 ANÁLISIS POR CARTA:**
        - Pasado - {cartas_resultado[0]['carta']['nombre']} ({'Invertida' if cartas_resultado[0]['es_invertida'] else 'Derecha'}): [cómo influye]
        - Presente - {cartas_resultado[1]['carta']['nombre']} ({'Invertida' if cartas_resultado[1]['es_invertida'] else 'Derecha'}): [impacto actual]
        - Futuro - {cartas_resultado[2]['carta']['nombre']} ({'Invertida' if cartas_resultado[2]['es_invertida'] else 'Derecha'}): [predicción exacta]

        **🔍 DETALLES REVELADOS:**
        [Información adicional que las cartas quieran destacar]

        **⏳ CUÁNDO OCURRIRÁ:**
        [Si es posible determinar un plazo o señal]

        ❌ PROHIBIDO:
        - Ser vago
        - Usar frases tipo “todo depende de ti”
        - Dar consejos sin responder primero

        RECUERDA: RESPONDE SOLO DESPUÉS DE ANALIZAR LAS CARTAS.

        ✨ RESPONDE AHORA:
        """

        return prompt





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