from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .models import Carrito, ItemCarrito, Venta, DetalleVenta
from productos.models import Producto
from .serializers import CarritoSerializer, AgregarItemSerializer, VentaSerializer


class CarritoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        serializer = CarritoSerializer(carrito)
        return Response(serializer.data)

    def post(self, request):
        serializer = AgregarItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        producto = get_object_or_404(Producto, id=serializer.validated_data["producto_id"])
        cantidad = serializer.validated_data["cantidad"]

        if producto.stock < cantidad:
            return Response({"detail": "Stock insuficiente."}, status=400)

        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)
        item.cantidad = cantidad
        item.save()
        return Response({"detail": "Producto agregado o actualizado correctamente."}, status=200)

    def delete(self, request):
        producto_id = request.data.get("producto_id")
        carrito = get_object_or_404(Carrito, usuario=request.user)
        item = get_object_or_404(ItemCarrito, carrito=carrito, producto_id=producto_id)
        item.delete()
        return Response({"detail": "Producto eliminado del carrito."}, status=200)


class FinalizarCompraView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        metodo_pago = request.data.get("metodo_pago", "efectivo")
        carrito = get_object_or_404(Carrito, usuario=request.user)
        if not carrito.items.exists():
            return Response({"detail": "El carrito está vacío."}, status=400)

        total = sum(item.subtotal for item in carrito.items.all())

        venta = Venta.objects.create(usuario=request.user, total=total, metodo_pago=metodo_pago)
        for item in carrito.items.all():
            if item.producto.stock < item.cantidad:
                return Response({"detail": f"Stock insuficiente para {item.producto.nombre}"}, status=400)
            DetalleVenta.objects.create(
                venta=venta,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=item.producto.precio
            )
            item.producto.stock -= item.cantidad
            item.producto.save()
        carrito.items.all().delete()

        # Envío de correo
        cuerpo = f"""
        Hola {request.user.username}, gracias por tu compra.

        Total: ${total}
        Método de pago: {metodo_pago}

        Detalles:
        """ + "\n".join([f"- {d.producto.nombre} x{d.cantidad} = ${d.subtotal()}" for d in venta.detalles.all()])

        send_mail(
            subject="Factura de tu compra",
            message=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

        return Response({"detail": "Compra finalizada. Factura enviada al correo.", "venta": VentaSerializer(venta).data})
