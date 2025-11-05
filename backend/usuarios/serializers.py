from rest_framework import serializers
from .models import Usuario

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Usuario
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.is_active = False
        usuario.rol= "cliente"
        usuario.save()
        return usuario


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class VerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()


# visualizar usuarios creados
class UsuarioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'rol']


class UpdateUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = Usuario
        fields = ['username', 'password']

    def update(self, instance, validated_data):
        username = validated_data.get('username', instance.username)
        password = validated_data.get('password', None)

        instance.username = username
        if password:
            instance.set_password(password)
        instance.save()
        return instance