from django.urls import path
from .views import CarritoView, FinalizarCompraView

urlpatterns = [
    path('carrito/', CarritoView.as_view(), name='carrito'),
    path('finalizar-compra/', FinalizarCompraView.as_view(), name='finalizar_compra'),
]
