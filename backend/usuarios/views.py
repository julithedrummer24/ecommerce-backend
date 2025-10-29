from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import RegisterSerializer, LoginSerializer, VerifySerializer
from .models import CodigoVerificacion
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.crypto import get_random_string

User = get_user_model()


def enviar_codigo_por_email(usuario, codigo, asunto= None):
    subject = "Tu código de verificación"
    message = f"Hola {usuario.username},\n\nTu código de verificación es: {codigo}\n\nEste código expira en 5 minutos."
    send_mail(subject, message, None, [usuario.email], fail_silently=False)


def generar_tokens_para_usuario(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            codigo_obj = CodigoVerificacion.crear_para_usuario(
                usuario, minutos_validez=5, longitud=6, contexto='registro'
            )
            enviar_codigo_por_email(usuario, codigo_obj.codigo)
            return Response({'detail': 'Usuario creado. Se envió un código al correo para verificar.'},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyRegistrationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        if not email or not code:
            return Response({'detail': 'El correo y el código son requeridos.'},
                            status=status.HTTP_400_BAD_REQUEST)

        usuario = get_object_or_404(User, email=email)
        codigo_obj = CodigoVerificacion.objects.filter(usuario=usuario, contexto='registro').order_by('-creado_en').first()

        if not codigo_obj or not codigo_obj.es_valido() or codigo_obj.codigo != code:
            return Response({'detail': 'Código inválido o expirado.'},
                            status=status.HTTP_400_BAD_REQUEST)

        codigo_obj.usado = True
        codigo_obj.save()
        usuario.is_active = True
        usuario.save()

        tokens = generar_tokens_para_usuario(usuario)
        return Response({'detail': 'Usuario verificado correctamente.', 'tokens': tokens},
                        status=status.HTTP_200_OK)


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
            return Response({'detail': 'Usuario no verificado. Verifica tu correo.'},
                            status=status.HTTP_403_FORBIDDEN)

        # crear código de login
        codigo_obj = CodigoVerificacion.crear_para_usuario(user, minutos_validez=5, longitud=6, contexto='login')
        enviar_codigo_por_email(user, codigo_obj.codigo)

        return Response({'detail': 'Código de acceso enviado al correo. Usa /verify-login/ para completar.'},
                        status=status.HTTP_200_OK)


class VerifyRegistrationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        usuario = get_object_or_404(User, email=email)
        codigo_obj = CodigoVerificacion.objects.filter(usuario=usuario, contexto='registro').order_by('-creado_en').first()

        if not codigo_obj or not codigo_obj.es_valido() or codigo_obj.codigo != code:
            return Response({'detail': 'Código inválido o expirado.'}, status=status.HTTP_400_BAD_REQUEST)

        codigo_obj.usado = True
        codigo_obj.save()
        usuario.is_active = True
        usuario.save()

        tokens = generar_tokens_para_usuario(usuario)
        return Response({'detail': 'Verificado correctamente.', 'tokens': tokens}, status=status.HTTP_200_OK)

class VerifyLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        if not email or not code:
            return Response({'detail': 'El correo y el código son requeridos.'},
                            status=status.HTTP_400_BAD_REQUEST)

        usuario = get_object_or_404(User, email=email)
        codigo_obj = CodigoVerificacion.objects.filter(usuario=usuario, contexto='login').order_by('-creado_en').first()

        if not codigo_obj or not codigo_obj.es_valido() or codigo_obj.codigo != code:
            return Response({'detail': 'Código inválido o expirado.'},
                            status=status.HTTP_400_BAD_REQUEST)

        codigo_obj.usado = True
        codigo_obj.save()

        tokens = generar_tokens_para_usuario(usuario)
        return Response({'detail': 'Inicio de sesión verificado correctamente.', 'tokens': tokens},
                        status=status.HTTP_200_OK)


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
            usuario,
            minutos_validez=5,
            longitud=6,
            contexto='registro'
        )

        return Response({
            'detail': 'Nuevo código generado exitosamente.',
            'codigo': codigo_obj.codigo
        }, status=status.HTTP_200_OK)
