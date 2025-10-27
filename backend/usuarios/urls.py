from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterAPIView.as_view(), name='register'),
    path('verify-registration/', views.VerifyRegistrationAPIView.as_view(), name='verify-registration'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('verify-login/', views.VerifyLoginAPIView.as_view(), name='verify-login'),
]
