from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import EmailMessage, BadHeaderError
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, LoginSerializer, VerifySerializer, UsuarioListSerializer
from .models import CodigoVerificacion
from .models import Usuario
from rest_framework.decorators import api_view, permission_classes
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

# ==== FUNCIONES AUXILIARES ====

def enviar_codigo_por_email(usuario, codigo, asunto="Código de verificación"):
    """Envía el código de verificación por correo (UTF-8, compatible con tildes y ñ)."""
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
    """Genera tokens JWT para un usuario."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

# ==== VISTAS PRINCIPALES ====

class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario = serializer.save()
        codigo_obj = CodigoVerificacion.crear_para_usuario(
            usuario, minutos_validez=5, longitud=6, contexto="registro"
        )

        try:
            enviar_codigo_por_email(usuario, codigo_obj.codigo, asunto="Verifica tu cuenta")
        except Exception as e:
            return Response({"detail": f"No se pudo enviar el correo: {e}"}, status=500)

        body = {"detail": "Usuario creado. Código enviado al correo."}
        if settings.DEBUG:
            body["codigo"] = codigo_obj.codigo
        return Response(body, status=status.HTTP_201_CREATED)


class VerifyRegistrationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        usuario = get_object_or_404(User, email=email)
        codigo_obj = (
            CodigoVerificacion.objects.filter(usuario=usuario, contexto="registro")
            .order_by("-creado_en")
            .first()
        )

        if not codigo_obj or not codigo_obj.es_valido() or codigo_obj.codigo != code:
            return Response({"detail": "Código inválido o expirado."}, status=400)

        codigo_obj.usado = True
        codigo_obj.save()
        usuario.is_active = True
        usuario.save(update_fields=["is_active"])

        tokens = generar_tokens_para_usuario(usuario)
        return Response({"detail": "Cuenta verificada correctamente.", "tokens": tokens}, status=200)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        usuario = get_object_or_404(User, email=email)
        user = authenticate(request, username=usuario.username, password=password)

        if user is None:
            return Response({"detail": "Credenciales inválidas."}, status=401)
        if not user.is_active:
            return Response({"detail": "Usuario no verificado."}, status=403)

        tokens = generar_tokens_para_usuario(user)
        return Response({"detail": "Inicio de sesión exitoso.", "tokens": tokens}, status=200)


class DeleteUserAPIView(APIView):
    """Permite eliminar cuenta propia o, si es admin, la de cualquier usuario."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        user_id = request.query_params.get("user_id")

        if user.is_staff and user_id:
            try:
                usuario_obj = User.objects.get(id=user_id)
                usuario_obj.delete()
                return Response({"detail": f"Usuario {usuario_obj.email} eliminado por admin."}, status=200)
            except User.DoesNotExist:
                return Response({"detail": "Usuario no encontrado."}, status=404)

        user.delete()
        return Response({"detail": "Tu cuenta ha sido eliminada correctamente."}, status=200)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def listar_usuarios(request):
    usuarios = Usuario.objects.all()
    serializer = UsuarioListSerializer(usuarios, many=True)
    return Response(serializer.data)



@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def eliminar_usuario(request, user_id):
    try:
        usuario = Usuario.objects.get(id=user_id)
        usuario.delete()
        return Response({'message': 'Usuario eliminado correctamente.'}, status=200)
    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado.'}, status=404)
