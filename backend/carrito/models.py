from django.db import models
from django.conf import settings
from productos.models import Producto

User = settings.AUTH_USER_MODEL

class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="carrito")
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.cantidad * self.producto.precio

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"


class Venta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ventas")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=50)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venta #{self.id} - {self.usuario.username}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario
