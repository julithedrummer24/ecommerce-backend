from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterAPIView.as_view(), name='register'),
    path('verify-registration/', views.VerifyRegistrationAPIView.as_view(), name='verify-registration'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('delete-account/', views.DeleteUserAPIView.as_view(), name='delete_account'),
    path('listar/', views.listar_usuarios, name='listar_usuarios'),
    path('eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
]
