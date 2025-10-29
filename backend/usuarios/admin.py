from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, CodigoVerificacion

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'rol', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'rol')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Información personal', {'fields': ('rol',)}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(CodigoVerificacion)
class CodigoVerificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'codigo', 'contexto', 'usado', 'creado_en', 'expira_en')
    search_fields = ('usuario__email', 'codigo')
    list_filter = ('contexto', 'usado')
