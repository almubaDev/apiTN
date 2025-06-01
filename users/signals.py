from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crear perfil automáticamente cuando se crea un usuario
    """
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Guardar perfil cuando se guarda el usuario
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()