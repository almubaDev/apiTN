from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class MetodoPago(models.Model):
    nombre = models.CharField(max_length=50, unique=True)  # "PayPal", "Flow", "Stripe"
    codigo = models.CharField(max_length=20, unique=True)  # "paypal", "flow", "stripe"
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=50, blank=True)  # Clase CSS del ícono
    color_boton = models.CharField(max_length=7, default='#007cba')  # Color hex del botón
    paises_soportados = models.JSONField(default=list)  # ["CL", "MX", "AR", "US", "GLOBAL"]
    activo = models.BooleanField(default=True)
    orden = models.IntegerField(default=0)  # Para ordenar los botones
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Método de Pago'
        verbose_name_plural = 'Métodos de Pago'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre
    
    def soporta_pais(self, codigo_pais):
        """
        Verificar si el método de pago soporta un país específico
        """
        return 'GLOBAL' in self.paises_soportados or codigo_pais in self.paises_soportados


class PaqueteCreditos(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    cantidad_creditos = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Para mostrar descuentos
    destacado = models.BooleanField(default=False)  # Marcar como "Más Popular"
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Paquete de Créditos'
        verbose_name_plural = 'Paquetes de Créditos'
        ordering = ['precio']
    
    def __str__(self):
        return f"{self.nombre} - {self.cantidad_creditos} créditos"
    
    @property
    def precio_por_credito(self):
        """
        Calcular precio por crédito individual
        """
        return round(float(self.precio) / self.cantidad_creditos, 3)
    
    @property
    def tiene_descuento(self):
        """
        Verificar si tiene precio anterior (descuento)
        """
        return self.precio_anterior and self.precio_anterior > self.precio
    
    @property
    def porcentaje_descuento(self):
        """
        Calcular porcentaje de descuento
        """
        if self.tiene_descuento:
            return round(((self.precio_anterior - self.precio) / self.precio_anterior) * 100)
        return 0


class BotonPago(models.Model):
    paquete = models.ForeignKey(PaqueteCreditos, on_delete=models.CASCADE, related_name='botones_pago')
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.CASCADE)
    url_base = models.URLField(blank=True)  # URL base del método de pago
    parametros_adicionales = models.JSONField(default=dict, blank=True)  # Parámetros específicos del método
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Botón de Pago'
        verbose_name_plural = 'Botones de Pago'
        unique_together = ['paquete', 'metodo_pago']
    
    def __str__(self):
        return f"{self.paquete.nombre} - {self.metodo_pago.nombre}"
    
    def generar_url_pago(self, user=None):
        """
        Generar URL de pago personalizada para el usuario
        """
        # Aquí se generaría la URL específica según el método de pago
        # Por ahora retornamos la URL base
        return self.url_base
    
    def es_disponible_para_pais(self, codigo_pais):
        """
        Verificar si el botón está disponible para un país específico
        """
        return self.activo and self.metodo_pago.soporta_pais(codigo_pais)


class TipoSuscripcion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    tiradas_incluidas = models.IntegerField(default=30)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Tipo de Suscripción'
        verbose_name_plural = 'Tipos de Suscripción'
        ordering = ['precio_mensual']
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio_mensual}/mes"


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    creditos_disponibles = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Billetera'
        verbose_name_plural = 'Billeteras'
    
    def __str__(self):
        return f"Wallet de {self.user.email} - {self.creditos_disponibles} créditos"
    
    def tiene_creditos_suficientes(self, cantidad):
        return self.creditos_disponibles >= cantidad
    
    def descontar_creditos(self, cantidad):
        if self.tiene_creditos_suficientes(cantidad):
            self.creditos_disponibles -= cantidad
            self.save()
            return True
        return False
    
    def agregar_creditos(self, cantidad):
        self.creditos_disponibles += cantidad
        self.save()


class Suscripcion(models.Model):
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('cancelada', 'Cancelada'),
        ('expirada', 'Expirada'),
        ('pendiente', 'Pendiente'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='suscripciones')
    tipo_suscripcion = models.ForeignKey(TipoSuscripcion, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activa')
    tiradas_usadas = models.IntegerField(default=0)
    auto_renovar = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Suscripción {self.tipo_suscripcion.nombre} de {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.fecha_fin:
            self.fecha_fin = self.fecha_inicio + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def esta_activa(self):
        return (self.estado == 'activa' and 
                self.fecha_inicio <= timezone.now() <= self.fecha_fin)
    
    def tiradas_disponibles(self):
        if self.esta_activa():
            return max(0, self.tipo_suscripcion.tiradas_incluidas - self.tiradas_usadas)
        return 0
    
    def usar_tirada(self):
        if self.tiradas_disponibles() > 0:
            self.tiradas_usadas += 1
            self.save()
            return True
        return False
    
    def renovar(self):
        if self.auto_renovar and self.estado == 'activa':
            self.fecha_inicio = self.fecha_fin
            self.fecha_fin = self.fecha_inicio + timedelta(days=30)
            self.tiradas_usadas = 0
            self.save()


class TransaccionCreditos(models.Model):
    TIPO_CHOICES = [
        ('compra', 'Compra'),
        ('uso', 'Uso'),
        ('regalo', 'Regalo'),
        ('reembolso', 'Reembolso'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transacciones_creditos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    descripcion = models.TextField()
    paquete_creditos = models.ForeignKey(PaqueteCreditos, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Transacción de Créditos'
        verbose_name_plural = 'Transacciones de Créditos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tipo} - {self.cantidad} créditos - {self.user.email}"


class HistorialConsultas(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='historial_consultas')
    pregunta = models.TextField()
    tirada_nombre = models.CharField(max_length=200)
    mazo_nombre = models.CharField(max_length=200)
    costo_creditos = models.IntegerField(default=0)
    uso_suscripcion = models.BooleanField(default=False)
    interpretacion = models.TextField()
    cartas_resultado = models.JSONField()  # Guardar las cartas y sus posiciones
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Historial de Consultas'
        verbose_name_plural = 'Historial de Consultas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Consulta de {self.user.email} - {self.created_at.strftime('%d/%m/%Y')}"


class PagoSuscripcion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
        ('reembolsado', 'Reembolsado'),
    ]
    
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    metodo_pago = models.CharField(max_length=50, blank=True)
    referencia_externa = models.CharField(max_length=200, blank=True)  # ID de la pasarela de pago
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pago de Suscripción'
        verbose_name_plural = 'Pagos de Suscripción'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pago {self.estado} - ${self.monto} - {self.suscripcion.user.email}"


class PagoCreditos(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
        ('reembolsado', 'Reembolsado'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pagos_creditos')
    paquete_creditos = models.ForeignKey(PaqueteCreditos, on_delete=models.CASCADE)
    boton_pago = models.ForeignKey(BotonPago, on_delete=models.SET_NULL, null=True, blank=True)  # Qué botón usó
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    metodo_pago = models.CharField(max_length=50, blank=True)
    referencia_externa = models.CharField(max_length=200, blank=True)
    datos_pago = models.JSONField(default=dict, blank=True)  # Datos adicionales del pago
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pago de Créditos'
        verbose_name_plural = 'Pagos de Créditos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pago {self.estado} - ${self.monto} - {self.user.email}"