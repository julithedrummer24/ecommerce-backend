import uuid
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail, BadHeaderError
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import RegisterSerializer, LoginSerializer, VerifySerializer
from .models import CodigoVerificacion
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import EmailMessage
from django.core.mail import EmailMessage, BadHeaderError


User = get_user_model()



def enviar_codigo_por_email(usuario, codigo, asunto="Tu código de verificación"):
    """
    Envía un correo de verificación en formato UTF-8 (compatible con ñ, tildes, etc.)
    """
    subject = str(asunto)
    message = (
        f"Hola {usuario.username},\n\n"
        f"Tu código de verificación es: {codigo}\n\n"
        "Este código expira en 5 minutos."
    )
    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[usuario.email],
        )
        email.content_subtype = "plain"
        email.encoding = "utf-8"
        email.send(fail_silently=False)
    except BadHeaderError:
        raise ValueError("Cabecera de correo inválida.")
    except Exception as e:
        raise ValueError(f"Error al enviar correo: {e}")




def generar_tokens_para_usuario(user):
    """Genera tokens JWT para el usuario."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario = serializer.save()
        codigo_obj = CodigoVerificacion.crear_para_usuario(
            usuario, minutos_validez=5, longitud=6, contexto='registro'
        )

        try:
            enviar_codigo_por_email(usuario, codigo_obj.codigo, asunto="Activa tu cuenta")
        except Exception as e:
            return Response({'detail': f'No se pudo enviar el correo: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        body = {'detail': 'Usuario creado. Se envió un código al correo para verificar.'}
        if getattr(settings, "DEBUG", False):
            body['codigo'] = codigo_obj.codigo  # visible en desarrollo

        return Response(body, status=status.HTTP_201_CREATED)


class VerifyRegistrationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        usuario = get_object_or_404(User, email=email)
        codigo_obj = CodigoVerificacion.objects.filter(
            usuario=usuario, contexto='registro'
        ).order_by('-creado_en').first()

        if not codigo_obj or not codigo_obj.es_valido() or codigo_obj.codigo != code:
            return Response({'detail': 'Código inválido o expirado.'}, status=status.HTTP_400_BAD_REQUEST)

        codigo_obj.usado = True
        codigo_obj.save()
        usuario.is_active = True
        usuario.save(update_fields=['is_active'])

        tokens = generar_tokens_para_usuario(usuario)
        return Response({'detail': 'Usuario verificado correctamente.', 'tokens': tokens}, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        usuario = get_object_or_404(User, email=email)

        user = authenticate(request, username=usuario.username, password=password)
        if user is None:
            return Response({'detail': 'Credenciales inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'detail': 'Usuario no verificado. Verifica tu correo.'}, status=status.HTTP_403_FORBIDDEN)

        # Crear código de login
        codigo_obj = CodigoVerificacion.crear_para_usuario(user, minutos_validez=5, longitud=6, contexto='login')

        try:
            enviar_codigo_por_email(user, codigo_obj.codigo, asunto="Código de acceso")
        except Exception as e:
            return Response({'detail': f'No se pudo enviar el correo: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        body = {'detail': 'Código de acceso enviado al correo. Usa /verify-login/ para completar.'}
        if getattr(settings, "DEBUG", False):
            body['codigo'] = codigo_obj.codigo  # visible solo en desarrollo
        return Response(body, status=status.HTTP_200_OK)


class VerifyLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        usuario = get_object_or_404(User, email=email)
        codigo_obj = CodigoVerificacion.objects.filter(usuario=usuario, contexto='login').order_by('-creado_en').first()

        if not codigo_obj or not codigo_obj.es_valido() or codigo_obj.codigo != code:
            return Response({'detail': 'Código inválido o expirado.'}, status=status.HTTP_400_BAD_REQUEST)

        codigo_obj.usado = True
        codigo_obj.save()

        tokens = generar_tokens_para_usuario(usuario)
        return Response({'detail': 'Inicio de sesión verificado correctamente.', 'tokens': tokens}, status=status.HTTP_200_OK)


class ReenviarCodigoAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'El correo es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        usuario = get_object_or_404(User, email=email)

        if usuario.is_active:
            return Response({'detail': 'El usuario ya está verificado.'}, status=status.HTTP_400_BAD_REQUEST)

        codigo_obj = CodigoVerificacion.crear_para_usuario(
            usuario, minutos_validez=5, longitud=6, contexto='registro'
        )

        try:
            enviar_codigo_por_email(usuario, codigo_obj.codigo, asunto="Reenvío de código de verificación")
        except Exception as e:
            return Response({'detail': f'No se pudo enviar el correo: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        body = {'detail': 'Nuevo código generado y enviado al correo.'}
        if getattr(settings, "DEBUG", False):
            body['codigo'] = codigo_obj.codigo

        return Response(body, status=status.HTTP_200_OK)
