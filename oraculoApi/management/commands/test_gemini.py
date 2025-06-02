# Crear archivo: oraculoApi/management/commands/test_gemini.py

import os
from django.core.management.base import BaseCommand
import google.generativeai as genai
from django.conf import settings

class Command(BaseCommand):
    help = 'Prueba la conexión con Gemini y lista modelos disponibles'

    def handle(self, *args, **options):
        try:
            # Configurar API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            self.stdout.write("🔍 Listando modelos disponibles...")
            
            # Listar modelos disponibles
            models = genai.list_models()
            
            self.stdout.write("\n📋 Modelos Gemini disponibles:")
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    self.stdout.write(f"  ✅ {model.name}")
                else:
                    self.stdout.write(f"  ❌ {model.name} (no soporta generateContent)")
            
            # Probar modelo recomendado
            self.stdout.write("\n🧪 Probando gemini-1.5-flash...")
            
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content("Di 'Conexión exitosa con Gemini' en una frase mística")
                
                if response.candidates and len(response.candidates) > 0:
                    self.stdout.write(self.style.SUCCESS(f"✅ Respuesta: {response.candidates[0].content.parts[0].text}"))
                else:
                    self.stdout.write(self.style.ERROR("❌ No se recibió respuesta válida"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error con gemini-1.5-flash: {str(e)}"))
                
                # Probar modelo alternativo
                self.stdout.write("\n🔄 Probando gemini-1.5-pro...")
                try:
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    response = model.generate_content("Di 'Conexión exitosa' brevemente")
                    
                    if response.candidates and len(response.candidates) > 0:
                        self.stdout.write(self.style.SUCCESS(f"✅ Respuesta con gemini-1.5-pro: {response.candidates[0].content.parts[0].text}"))
                    else:
                        self.stdout.write(self.style.ERROR("❌ No se recibió respuesta válida con gemini-1.5-pro"))
                        
                except Exception as e2:
                    self.stdout.write(self.style.ERROR(f"❌ Error con gemini-1.5-pro: {str(e2)}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error general: {str(e)}"))
            self.stdout.write("💡 Verifica que GEMINI_API_KEY esté configurado correctamente")