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

User = get_user_model()

def enviar_codigo_por_email(usuario, codigo):
    subject = "Tu código de verificación"
    message = f"Hola {usuario.username},\n\nTu código de verificación es: {codigo}\n\nEste código expira en 5 minutos."
    send_mail(subject, message, None, [usuario.email], fail_silently=False)

def generar_tokens_para_usuario(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# para envio de correos (mejorar y provar)
class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            # crear codigo de verificacion contexto 'registro' (6 digitos por defecto)
            codigo_obj = CodigoVerificacion.crear_para_usuario(usuario, minutos_validez=5, longitud=6, contexto='registro')
            enviar_codigo_por_email(usuario, codigo_obj.codigo)
            return Response({'detail': 'Usuario creado. Se envió un código al correo para verificar.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# # registro para pruebas class RegisterAPIView(APIView):
# class RegisterAPIView(APIView):
#     permission_classes = [permissions.AllowAny]

#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         if serializer.is_valid():
#             usuario = serializer.save()
#             codigo_obj = CodigoVerificacion.crear_para_usuario(
#                 usuario, minutos_validez=5, longitud=6, contexto='registro'
#             )
            
#             return Response({
#                 'detail': 'Usuario creado. Código de verificación generado (solo visible para pruebas).',
#                 'codigo_verificacion': codigo_obj.codigo,
#                 'username': usuario.username,
#                 'email': usuario.email
#             }, status=status.HTTP_201_CREATED)
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyRegistrationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data['username']
        code = serializer.validated_data['code']
        usuario = get_object_or_404(User, username=username)
        codigo_obj = CodigoVerificacion.objects.filter(usuario=usuario, contexto='registro').order_by('-creado_en').first()
        if not codigo_obj or not codigo_obj.es_valido() or codigo_obj.codigo != code:
            return Response({'detail': 'Código inválido o expirado.'}, status=status.HTTP_400_BAD_REQUEST)
        
        codigo_obj.usado = True
        codigo_obj.save()
        usuario.is_active = True
        usuario.save()
        tokens = generar_tokens_para_usuario(usuario)
        return Response({'detail': 'Verificado correctamente.', 'tokens': tokens}, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'detail': 'Credenciales inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)
        # si usuario (no verificado) no permitir login por credenciales; pedir verificar registro
        if not user.is_active:
            return Response({'detail': 'Usuario no verificado. Verifica tu correo.'}, status=status.HTTP_403_FORBIDDEN)
        # crear codigo para login
        codigo_obj = CodigoVerificacion.crear_para_usuario(user, minutos_validez=5, longitud=6, contexto='login')
        enviar_codigo_por_email(user, codigo_obj.codigo)
        return Response({'detail': 'Código enviado al correo. Usa /verify-login/ para completar.'}, status=status.HTTP_200_OK)


class VerifyLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data['username']
        code = serializer.validated_data['code']
        usuario = get_object_or_404(User, username=username)
        codigo_obj = CodigoVerificacion.objects.filter(usuario=usuario, contexto='login').order_by('-creado_en').first()
        if not codigo_obj or not codigo_obj.es_valido() or codigo_obj.codigo != code:
            return Response({'detail': 'Código inválido o expirado.'}, status=status.HTTP_400_BAD_REQUEST)
        codigo_obj.usado = True
        codigo_obj.save()
        tokens = generar_tokens_para_usuario(usuario)
        return Response({'detail': 'Login verificado correctamente.', 'tokens': tokens}, status=status.HTTP_200_OK)

def enviar_otp(usuario, codigo, motivo):
    asunto = "Tu código de verificación" if motivo != "registro" else "Activa tu cuenta"
    mensaje = f"Tu código es: {codigo}. Expira en 5 minutos."
    enviar_codigo_por_email(usuario.email, asunto, mensaje)



try:
    if hasattr(codigo_obj, "usado"):
        codigo_obj.usado = True
        codigo_obj.save(update_fields=["usado"])
except Exception:
    pass