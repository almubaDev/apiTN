import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        """
        Inicializar el servicio de Gemini
        """
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("Gemini service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gemini service: {str(e)}")
            raise
    
    def generar_interpretacion_tarot(self, prompt_completo):
        """
        Generar interpretación de tarot usando Gemini
        
        Args:
            prompt_completo (str): El prompt completo para la IA
            
        Returns:
            str: La interpretación generada por la IA
        """
        try:
            # Configuración de generación
            generation_config = genai.types.GenerationConfig(
                temperature=0.8,  # Creatividad moderada
                top_p=0.9,
                top_k=40,
                max_output_tokens=1200,  # Límite de tokens de salida
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
            
            # Generar respuesta
            response = self.model.generate_content(
                prompt_completo,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if response.candidates and len(response.candidates) > 0:
                interpretacion = response.candidates[0].content.parts[0].text
                logger.info("Tarot interpretation generated successfully")
                return interpretacion.strip()
            else:
                logger.warning("No candidates in Gemini response")
                return self._get_fallback_interpretation()
                
        except Exception as e:
            logger.error(f"Error generating tarot interpretation: {str(e)}")
            return self._get_fallback_interpretation()
    
    def _get_fallback_interpretation(self):
        """
        Interpretación de respaldo en caso de error
        """
        return """
        En este momento, las energías cósmicas están en transición y no puedo acceder 
        completamente a los mensajes que las cartas quieren transmitirte. Te sugiero 
        que repitas la consulta en unos momentos, cuando las vibraciones estén más 
        alineadas. Las cartas que han aparecido en tu tirada contienen mensajes 
        importantes para ti, mantén la mente abierta a las señales que el universo 
        te está enviando a través de otros medios.
        """
    
    def crear_prompt_tarot(self, pregunta, mazo, cartas_resultado):
        """
        Crear el prompt completo para la interpretación de tarot
        
        Args:
            pregunta (str): Pregunta del consultante
            mazo (object): Objeto Mazo con información
            cartas_resultado (list): Lista de cartas con sus posiciones
            
        Returns:
            str: Prompt completo para enviar a Gemini
        """
        prompt = f"""Eres un experto tarotista con décadas de experiencia que proporciona interpretaciones místicas, profundas y prácticas. Tu don especial es conectar las energías de las cartas entre sí para revelar mensajes precisos y útiles.

INFORMACIÓN SAGRADA DEL MAZO:
Nombre del Mazo: {mazo.nombre}
Propósito Esotérico: {mazo.descripcion}
Energía de Inversión: {'Permite cartas invertidas (energías bloqueadas o internas)' if mazo.permite_cartas_invertidas else 'Solo energías directas'}

PREGUNTA DEL CONSULTANTE:
"{pregunta}"

CARTAS REVELADAS EN LA TIRADA:
"""
        
        for i, carta_info in enumerate(cartas_resultado, 1):
            carta = carta_info['carta']
            orientacion = "INVERTIDA (Energía bloqueada/interna)" if carta_info['es_invertida'] else "DERECHA (Energía activa/externa)"
            
            prompt += f"""
--- CARTA {i} ---
Posición en la Tirada: {carta_info['posicion']}
Significado de la Posición: {carta_info['descripcion_posicion']}
Carta Revelada: {carta['nombre']} ({orientacion})
Mensaje de la Carta: {carta_info['significado_usado']}
{"="*50}
"""
        
        prompt += f"""

INSTRUCCIONES PARA LA INTERPRETACIÓN:

1. CONEXIÓN ENERGÉTICA: Analiza cómo las energías de todas las cartas se conectan entre sí para formar un mensaje coherente y revelador.

2. RESPUESTA DIRECTA: Responde específicamente a la pregunta planteada, no evadas ni generalices.

3. INTERPRETACIÓN PROFUNDA: 
   - Explica el significado de cada carta en su posición específica
   - Revela las conexiones ocultas entre las cartas
   - Proporciona insights que el consultante no podría obtener por sí mismo

4. CONSEJO PRÁCTICO: Ofrece orientación concreta y acciones específicas que el consultante puede tomar.

5. PERSPECTIVA TEMPORAL: Si es relevante, menciona timeframes aproximados (próximas semanas, meses, etc.).

6. TONO MÍSTICO PERO REALISTA: Usa lenguaje esotérico apropiado pero mantén la interpretación práctica y útil.

7. GÉNERO NEUTRAL: Usa "le/les" o términos neutros ya que no conocemos el género del consultante.

REVELA AHORA LOS SECRETOS QUE LAS CARTAS GUARDAN:
"""
        
        return prompt


# Instancia global del servicio
gemini_service = GeminiService()