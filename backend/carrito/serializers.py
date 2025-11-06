from rest_framework import serializers
from .models import Carrito, ItemCarrito, Venta, DetalleVenta
from productos.models import Producto

class ItemCarritoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    precio = serializers.ReadOnlyField(source='producto.precio')
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = ItemCarrito
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio', 'subtotal']


class CarritoSerializer(serializers.ModelSerializer):
    usuario = serializers.ReadOnlyField(source='usuario.username')
    items = ItemCarritoSerializer(many=True, read_only=True)

    class Meta:
        model = Carrito
        fields = ['id', 'usuario', 'items']


class AgregarItemSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)


class VentaSerializer(serializers.ModelSerializer):
    detalles = serializers.SerializerMethodField()

    class Meta:
        model = Venta
        fields = ['id', 'usuario', 'total', 'metodo_pago', 'creado_en', 'detalles']

    def get_detalles(self, obj):
        return [
            {
                "producto": d.producto.nombre,
                "cantidad": d.cantidad,
                "precio_unitario": d.precio_unitario,
                "subtotal": d.subtotal()
            } for d in obj.detalles.all()
        ]
