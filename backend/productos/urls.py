from django.urls import path
from . import views

urlpatterns = [
    # ADMIN
    path('admin/categorias/', views.categorias_admin, name='categorias_admin'),
    path('admin/categorias/<int:pk>/', views.categoria_detalle, name='categoria_detalle'),
    path('admin/productos/', views.productos_admin, name='productos_admin'),
    path('admin/productos/<int:pk>/', views.producto_detalle, name='producto_detalle'),

    path("inventario/", views.inventario_admin, name="inventario_admin"), 

    # PÚBLICO
    path('publico/categorias/<int:categoria_id>/productos/', views.productos_por_categoria, name='productos_por_categoria'),
]
