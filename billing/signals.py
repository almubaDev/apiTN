from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Wallet, TransaccionCreditos


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    Crear wallet automáticamente cuando se crea un usuario y darle créditos de bienvenida
    """
    if created:
        wallet, wallet_created = Wallet.objects.get_or_create(user=instance)

        # Si se creó una nueva wallet, darle créditos de bienvenida
        if wallet_created:
            creditos_bienvenida = 5
            wallet.agregar_creditos(creditos_bienvenida)

            # Crear registro de transacción
            TransaccionCreditos.objects.create(
                user=instance,
                tipo='regalo',
                cantidad=creditos_bienvenida,
                descripcion='Créditos de bienvenida por registrarse en Tarotnaútica'
            )