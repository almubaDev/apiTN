from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

from .models import CustomUser, Profile
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    ProfileSerializer, PasswordChangeSerializer, ProfileUpdateSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer
)

from django.template.loader import render_to_string
from django.core.mail import send_mail
import threading
import logging


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """
    Registro de nuevo usuario
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'message': 'Usuario creado exitosamente',
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    Login de usuario
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'message': 'Login exitoso',
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout de usuario
    """
    try:
        # Eliminar token
        request.user.auth_token.delete()
    except:
        pass

    logout(request)
    return Response({'message': 'Logout exitoso'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """
    Obtener perfil del usuario autenticado
    """
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    """
    Actualizar perfil del usuario autenticado
    """
    profile = get_object_or_404(Profile, user=request.user)
    serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Perfil actualizado exitosamente',
            'profile': ProfileSerializer(profile).data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    Cambiar contraseña del usuario autenticado
    """
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Regenerar token
        try:
            user.auth_token.delete()
        except:
            pass
        token = Token.objects.create(user=user)

        return Response({
            'message': 'Contraseña cambiada exitosamente',
            'token': token.key
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_detail(request):
    """
    Obtener detalles completos del usuario autenticado
    """
    user = request.user
    return Response({
        'user': UserSerializer(user).data,
        'profile': ProfileSerializer(user.profile).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """Solicitar reset de contraseña - Sin threading"""
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = CustomUser.objects.get(email=email)

        # Generar token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Crear enlace de reset
        reset_url = f"{settings.FRONTEND_URL}/password-reset/confirm/{uid}/{token}/"

        # Generar contenido del email
        from django.template.loader import render_to_string

        try:
            html_content = render_to_string('appWeb/emails/password_reset.html', {
                'reset_url': reset_url,
                'user_email': email,
            })
        except Exception as e:
            # Fallback a HTML simple si el template falla
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Recuperar Contraseña - Tarotnaútica</h2>
                <p>Haz clic en el siguiente enlace para restablecer tu contraseña:</p>
                <a href="{reset_url}" style="background: #8b5cf6; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px;">Restablecer Contraseña</a>
                <p>Este enlace expira en 1 hora.</p>
            </div>
            """

        plain_content = f"""
Tarotnaútica - Recuperación de Contraseña

Haz clic en este enlace para restablecer tu contraseña:
{reset_url}

Este enlace expira en 1 hora.

Si no solicitaste este cambio, ignora este email.

Saludos,
Equipo Tarotnaútica
"""

        # Enviar email SINCRONO pero con manejo de errores
        try:
            send_mail(
                subject='🔮 Recupera tu acceso a Tarotnaútica',
                message=plain_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_content,
                fail_silently=True,  # No fallar si hay problemas de email
            )
            print(f"Email enviado exitosamente a {email}")
        except Exception as e:
            print(f"Error enviando email: {str(e)}")
            # Continuar sin fallar - el usuario ya hizo la solicitud

        # Siempre responder exitosamente
        return Response({
            'message': 'Se ha enviado un enlace de recuperación a tu email'
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#)===============================================================================



#====================================================================================
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    """Confirmar reset de contraseña"""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
            user = CustomUser.objects.get(pk=uid)
            token = serializer.validated_data['token']

            if default_token_generator.check_token(user, token):
                user.set_password(serializer.validated_data['new_password'])
                user.save()

                return Response({
                    'message': 'Contraseña actualizada exitosamente'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Token inválido o expirado'
                }, status=status.HTTP_400_BAD_REQUEST)

        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)