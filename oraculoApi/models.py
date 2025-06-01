from django.db import models


class Set(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Set"
        verbose_name_plural = "Sets"


class Mazo(models.Model):
    set = models.ForeignKey(Set, on_delete=models.CASCADE, related_name='mazos')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    permite_cartas_invertidas = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.set.nombre} - {self.nombre}"
    
    class Meta:
        verbose_name = "Mazo"
        verbose_name_plural = "Mazos"


class Carta(models.Model):
    mazo = models.ForeignKey(Mazo, on_delete=models.CASCADE, related_name='cartas')
    numero = models.IntegerField()
    nombre = models.CharField(max_length=200)
    imagen = models.ImageField(upload_to='cartas/')
    significado_normal = models.TextField()
    significado_invertida = models.TextField()
    
    def __str__(self):
        return f"{self.mazo.nombre} - {self.numero}: {self.nombre}"
    
    class Meta:
        verbose_name = "Carta"
        verbose_name_plural = "Cartas"
        ordering = ['numero']
        unique_together = ['mazo', 'numero']


class Tirada(models.Model):
    mazo = models.ForeignKey(Mazo, on_delete=models.CASCADE, related_name='tiradas')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='tiradas/')
    cantidad_cartas = models.IntegerField()
    costo = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.mazo.nombre} - {self.nombre}"
    
    class Meta:
        verbose_name = "Tirada"
        verbose_name_plural = "Tiradas"


class ItemDeTirada(models.Model):
    tirada = models.ForeignKey(Tirada, on_delete=models.CASCADE, related_name='items')
    nombre_posicion = models.CharField(max_length=200)
    descripcion = models.TextField()
    orden = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.tirada.nombre} - {self.nombre_posicion}"
    
    class Meta:
        verbose_name = "Item de Tirada"
        verbose_name_plural = "Items de Tirada"
        ordering = ['orden']