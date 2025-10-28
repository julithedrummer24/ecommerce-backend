from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random

class Usuario(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('cliente', 'Cliente'),
    )
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=10, choices=ROLES, default='cliente')

    def __str__(self):
        return f"{self.username} ({self.rol})"


class CodigoVerificacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='codigos')
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)
    expiracion = models.DateTimeField()
    usado = models.BooleanField(default=False)
    contexto = models.CharField(max_length=20, default='login')  # 'registro' o 'login'

    @staticmethod
    def generar_codigo(longitud=6):
        if longitud == 4:
            return f"{random.randint(1000,9999)}"
        return f"{random.randint(100000,999999)}"

    @classmethod
    def crear_para_usuario(cls, usuario, minutos_validez=5, longitud=6, contexto='login'):
        codigo = cls.generar_codigo(longitud)
        expiracion = timezone.now() + timezone.timedelta(minutes=minutos_validez)
        return cls.objects.create(usuario=usuario, codigo=codigo, expiracion=expiracion, contexto=contexto)

    def es_valido(self):
        return (not self.usado) and (timezone.now() < self.expiracion)
